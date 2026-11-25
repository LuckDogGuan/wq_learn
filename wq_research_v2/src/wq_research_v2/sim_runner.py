"""Slot-weighted concurrent Multi-Simulation engine (D1-Only, native QUICK/FULL, reconcile-once).

Key invariants:
- Hard asserts settings["delay"] == 1 and visualization == False
- Weighted SlotSemaphore: GLB atomically acquires 2 slots; all other regions acquire 1 slot
- Packs 2..10 items per multi-sim batch (auto-rebalances trailing singleton batch)
- Pre-flight ExprValidator (10 hard gates) + Ledger dedup + Blacklist check
- Reconcile-once-never-resend on network/timeout/429/missing-ID -> RESULTS_UNOBSERVED
"""
from __future__ import annotations

import datetime
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date


class WeightedSlotSemaphore:
    """Thread-safe global + per-region weighted semaphore.

    Enforces:
    - Global concurrent slot cap (`max_slots`, e.g. 4; GLB atomically consumes weight=2)
    - Per-region concurrent slot cap (`max_per_region`, e.g. 2) so 2 EUR + 2 USA = 4 threads
      run smoothly in parallel without triggering single-region concurrency 429s!
    """

    def __init__(self, max_slots: int = 8, *, max_per_region: Optional[int] = None) -> None:
        if max_slots < 2:
            raise ValueError("max_slots must be >= 2 to support GLB 2-slot batches")
        self.max_slots = int(max_slots)
        self.max_per_region = int(max_per_region) if max_per_region is not None and max_per_region > 0 else self.max_slots
        self._available = int(max_slots)
        self._region_in_flight: dict[str, int] = {}
        self._cond = threading.Condition()

    @property
    def available(self) -> int:
        with self._cond:
            return self._available

    def region_in_flight(self, region: str) -> int:
        with self._cond:
            return int(self._region_in_flight.get(str(region).upper(), 0))

    def _can_acquire_locked(self, weight: int, region: Optional[str]) -> bool:
        if self._available < weight:
            return False
        if region:
            reg = str(region).upper()
            reg_cap = max(weight, self.max_per_region)
            if self._region_in_flight.get(reg, 0) + weight > reg_cap:
                return False
        return True

    def acquire(self, weight: int = 1, timeout: Optional[float] = None, *, region: Optional[str] = None) -> bool:
        w = int(weight)
        if w < 1 or w > self.max_slots:
            raise ValueError(f"Invalid slot weight {w} for max_slots={self.max_slots}")
        deadline = (time.monotonic() + timeout) if timeout is not None else None
        reg = str(region).upper() if region else None
        with self._cond:
            while not self._can_acquire_locked(w, reg):
                if deadline is not None:
                    rem = deadline - time.monotonic()
                    if rem <= 0:
                        return False
                    self._cond.wait(timeout=rem)
                else:
                    self._cond.wait()
            self._available -= w
            if reg:
                self._region_in_flight[reg] = self._region_in_flight.get(reg, 0) + w
            return True

    def try_acquire(self, weight: int = 1, *, region: Optional[str] = None) -> bool:
        w = int(weight)
        reg = str(region).upper() if region else None
        with self._cond:
            if not self._can_acquire_locked(w, reg):
                return False
            self._available -= w
            if reg:
                self._region_in_flight[reg] = self._region_in_flight.get(reg, 0) + w
            return True

    def release(self, weight: int = 1, *, region: Optional[str] = None) -> None:
        w = int(weight)
        reg = str(region).upper() if region else None
        with self._cond:
            self._available = min(self.max_slots, self._available + w)
            if reg:
                cur = self._region_in_flight.get(reg, 0) - w
                if cur <= 0:
                    self._region_in_flight.pop(reg, None)
                else:
                    self._region_in_flight[reg] = cur
            self._cond.notify_all()


def pack_multisim_batches(items: list[dict[str, Any]], batch_size: int = 8) -> list[list[dict[str, Any]]]:
    """Pack items into batches of 2..8 (Gold multi-sim ceiling), rebalancing a trailing 1-item tail when possible."""
    bs = max(2, min(8, int(batch_size)))
    if not items:
        return []
    if len(items) <= bs:
        return [list(items)]
    batches = [items[i : i + bs] for i in range(0, len(items), bs)]
    if len(batches) >= 2 and len(batches[-1]) == 1 and len(batches[-2]) > 2:
        moved = batches[-2].pop()
        batches[-1].insert(0, moved)
    return batches


def build_sim_payload(
    expression: str,
    settings: dict[str, Any],
    *,
    simulation_mode: str = "FULL",
) -> dict[str, Any]:
    """Build native BRAIN REGULAR simulation payload preserving QUICK/FULL and maxPosition."""
    s = dict(settings)
    if s.get("delay") != 1:
        raise ValueError(f"D1-Only violation: delay={s.get('delay')!r}")
    mode = simulation_mode.upper()
    if mode not in ("QUICK", "FULL"):
        raise ValueError(f"Invalid simulationMode: {mode!r}")
    s["instrumentType"] = s.get("instrumentType", "EQUITY")
    s["language"] = s.get("language", "FASTEXPR")
    s["visualization"] = False
    s["simulationMode"] = mode
    return {
        "type": "REGULAR",
        "settings": s,
        "regular": expression.strip(),
    }


class SimRunner:
    """Concurrent slot-mapped simulation runner backed by SQLite Checkpoint ledger."""

    def __init__(
        self,
        client: Any,
        ledger: LedgerStore,
        quota: QuotaTracker,
        *,
        validator: Optional[ExprValidator] = None,
        blacklist_registry: Any = None,
        max_slots: int = 4,
        max_per_region: Optional[int] = 2,
        post_stagger_sec: float = 2.0,
        max_post_429_retries: int = 2,
        poll_interval_sec: float = 5.0,
        poll_timeout_sec: float = 900.0,
    ) -> None:
        self.client = client
        self.ledger = ledger
        self.quota = quota
        self.validator = validator or ExprValidator()
        self.blacklist = blacklist_registry
        self.max_slots = max(2, min(8, int(max_slots)))
        self.max_per_region = int(max_per_region) if max_per_region is not None and max_per_region > 0 else self.max_slots
        self.post_stagger_sec = max(0.0, float(post_stagger_sec))
        self.max_post_429_retries = max(0, int(max_post_429_retries))
        self.semaphore = WeightedSlotSemaphore(self.max_slots, max_per_region=self.max_per_region)
        self._post_lock = threading.Lock()
        self._last_post_monotonic = 0.0
        self.poll_interval_sec = float(poll_interval_sec)
        self.poll_timeout_sec = float(poll_timeout_sec)

    @staticmethod
    def slot_weight_for_region(region: str) -> int:
        return 2 if str(region).upper() == "GLB" else 1

    def prepare_batch_tasks(
        self,
        spec: dict[str, Any],
        *,
        simulation_mode: str = "FULL",
        field_alpha_counts: Optional[dict[str, int]] = None,
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """Validate, deduplicate, blacklist-filter, and persist QUEUED tasks to SQLite."""
        batch_id = spec.get("batch_id") or f"EXP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        region = str(spec["region"]).upper()
        universe = str(spec["universe"]).upper()
        queue_type = str(spec.get("queue_type", "NORMAL")).upper()
        mode = simulation_mode.upper()
        base_settings = dict(spec.get("settings") or {})
        base_settings.setdefault("region", region)
        base_settings.setdefault("universe", universe)
        base_settings.setdefault("delay", 1)
        base_settings["visualization"] = False
        base_settings["simulationMode"] = mode

        self.ledger.create_batch(
            batch_id=batch_id,
            hypothesis_id=spec.get("hypothesis_id"),
            queue_type=queue_type,
            source_side=str(spec.get("source_side", "MIXED_4_4")),
            region=region,
            universe=universe,
            delay=int(base_settings["delay"]),
            simulation_mode=mode,
            slots_required=self.slot_weight_for_region(region),
            status="QUEUED",
        )

        runnable: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        est_day = current_est_platform_date()

        for idx, item in enumerate(spec.get("items") or []):
            expr = str(item["expression"]).strip()
            item_settings = dict(base_settings)
            item_settings.update(item.get("settings_override") or {})
            item_settings["visualization"] = False
            item_settings["simulationMode"] = mode

            rep = self.validator.validate(
                expr,
                item_settings,
                queue_type=queue_type,
                field_alpha_counts=field_alpha_counts,
                is_ppa=bool(item.get("is_ppa", False)),
            )
            task_id = f"{batch_id}-{idx:03d}"
            task_row = {
                "task_id": task_id,
                "batch_id": batch_id,
                "payload_fingerprint": rep.payload_fingerprint,
                "canonical_dedup_key": rep.canonical_dedup_key,
                "parent_baseline_alpha_id": item.get("parent_baseline_alpha_id"),
                "parent_quick_task_id": item.get("parent_quick_task_id"),
                "parent_family_id": item.get("parent_family_id") or batch_id,
                "single_changed_axis": item.get("single_changed_axis"),
                "atlas_layer": item.get("atlas_layer"),
                "template_id": item.get("template_id"),
                "source_side": item.get("source_side", "ADMIN_ORIGINAL"),
                "author_id": item.get("author_id"),
                "canonical_post_id": item.get("canonical_post_id"),
                "queue_type": queue_type,
                "region": region,
                "universe": universe,
                "delay": 1,
                "dataset_id": item.get("dataset_id") or spec.get("dataset_id"),
                "primary_field_id": item.get("primary_field_id") or (rep.fields_used[0] if rep.fields_used else None),
                "simulation_mode": mode,
                "expression": expr,
                "settings_json": json.dumps(item_settings, sort_keys=True),
                "status": "QUEUED",
                "est_platform_date": est_day,
            }

            if not rep.valid:
                task_row["status"] = "SYNTAX_ERROR"
                task_row["error_reason"] = "; ".join(rep.errors)
                self.ledger.upsert_sim_task(task_row)
                skipped.append(task_row)
                continue

            if self.ledger.get_task_status(task_id) in ("COMPLETED_FULL", "COMPLETED_QUICK"):
                task_row["status"] = "DEDUP_SKIPPED"
                task_row["error_reason"] = "Task already completed in ledger (preserved immutable)"
                skipped.append(task_row)
                continue

            if self.ledger.has_completed_fingerprint(rep.payload_fingerprint):
                task_row["status"] = "DEDUP_SKIPPED"
                task_row["error_reason"] = "Duplicate payload_fingerprint in ledger"
                self.ledger.upsert_sim_task(task_row)
                skipped.append(task_row)
                continue

            if self.blacklist is not None:
                blocked, bl_rec = self.blacklist.is_blocked(
                    region=region,
                    universe=universe,
                    delay=1,
                    dataset_id=task_row["dataset_id"],
                    field_id=task_row["primary_field_id"],
                    method_id=task_row["template_id"],
                )
                if blocked:
                    task_row["status"] = "BLACKLIST_SKIPPED"
                    task_row["error_reason"] = f"Blocked by {bl_rec['record_id']}: {bl_rec['why_unusable']}"
                    self.ledger.upsert_sim_task(task_row)
                    skipped.append(task_row)
                    continue

            self.ledger.upsert_sim_task(task_row)
            runnable.append(task_row)

        return batch_id, runnable, skipped

    def run_prepared_tasks(
        self,
        batch_id: str,
        tasks: list[dict[str, Any]],
        *,
        batch_size: int = 8,
    ) -> dict[str, Any]:
        """Dispatch packed multi-sim chunks concurrently using weighted slot semaphore."""
        if not tasks:
            return {"batch_id": batch_id, "completed": 0, "unobserved": 0, "errors": 0}
        chunks = pack_multisim_batches(tasks, batch_size=batch_size)
        region = tasks[0]["region"]
        weight = self.slot_weight_for_region(region)
        max_workers = max(1, self.max_slots // weight)

        summary = {"batch_id": batch_id, "completed": 0, "unobserved": 0, "errors": 0}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = [pool.submit(self._run_chunk, batch_id, chunk, weight) for chunk in chunks]
            for fut in as_completed(futs):
                res = fut.result()
                summary["completed"] += res["completed"]
                summary["unobserved"] += res["unobserved"]
                summary["errors"] += res["errors"]

        self.ledger.update_batch_progress(batch_id, "DONE")
        return summary

    def _pace_post_submission(self) -> None:
        """Enforce global POST /simulations pacing so concurrent threads never collide on the same second."""
        if self.post_stagger_sec <= 0:
            return
        with self._post_lock:
            now = time.monotonic()
            wait = (self._last_post_monotonic + self.post_stagger_sec) - now
            if wait > 0:
                time.sleep(wait)
            self._last_post_monotonic = time.monotonic()

    def _run_chunk(
        self,
        batch_id: str,
        chunk: list[dict[str, Any]],
        weight: int,
        *,
        already_acquired: bool = False,
    ) -> dict[str, int]:
        region = str(chunk[0]["region"]).upper() if chunk else ""
        if not already_acquired:
            self.semaphore.acquire(weight=weight, region=region)
        slot_released = False

        def _release_slot_once() -> None:
            nonlocal slot_released
            if not slot_released:
                self.semaphore.release(weight=weight, region=region)
                slot_released = True

        try:
            payloads = [
                build_sim_payload(
                    t["expression"],
                    json.loads(t["settings_json"]),
                    simulation_mode=t["simulation_mode"],
                )
                for t in chunk
            ]
            body: Any = payloads if len(payloads) > 1 else payloads[0]

            resp = None
            for attempt in range(self.max_post_429_retries + 1):
                self.quota.wait_if_circuit_open()
                self._pace_post_submission()
                now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for t in chunk:
                    t["status"] = "SUBMITTED"
                    t["submitted_at_utc"] = now_utc
                    self.ledger.upsert_sim_task(t)

                try:
                    resp = self.client.post("/simulations", json=body, timeout=45)
                except Exception as exc:
                    _release_slot_once()
                    return self._reconcile_once_chunk(chunk, None, f"POST exception: {type(exc).__name__}")

                if resp.status_code == 429 and attempt < self.max_post_429_retries:
                    # HTTP 429 on POST /simulations rejects BEFORE creation (zero quota spent, no Location).
                    # Release slot temporarily during cooldown so other regions/finishing polls stay smooth.
                    _release_slot_once()
                    retry_hdr = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
                    try:
                        backoff = float(retry_hdr) if retry_hdr else (15.0 * (attempt + 1))
                    except ValueError:
                        backoff = 15.0 * (attempt + 1)
                    time.sleep(max(3.0, min(backoff, 60.0)))
                    self.semaphore.acquire(weight=weight, region=region)
                    slot_released = False
                    continue
                break

            if resp is None or resp.status_code not in (200, 201):
                code = resp.status_code if resp is not None else "NONE"
                _release_slot_once()
                return self._reconcile_once_chunk(chunk, None, f"POST HTTP {code}")

            progress_url = resp.headers.get("Location") or resp.headers.get("location")
            self.ledger.update_batch_progress(batch_id, "RUNNING", progress_url=progress_url)
            if not progress_url:
                _release_slot_once()
                return self._reconcile_once_chunk(chunk, None, "Missing Location header")

            # Poll simulation until server finishes, then IMMEDIATELY release the simulation slot
            # BEFORE fetching 8x2 child alpha metadata payloads -> maximizes slot utilization!
            poll_res = self._poll_progress_raw(chunk, progress_url)
            _release_slot_once()
            if poll_res["kind"] == "DONE":
                return self._ingest_completed_progress(chunk, poll_res["data"])
            return self._reconcile_once_chunk(chunk, progress_url, poll_res["reason"])
        finally:
            _release_slot_once()

    def _poll_progress_raw(self, chunk: list[dict[str, Any]], progress_url: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.poll_timeout_sec
        while time.monotonic() < deadline:
            try:
                resp = self.client.get(progress_url, timeout=30)
            except Exception as exc:
                return {"kind": "FAIL", "reason": f"Poll exception: {type(exc).__name__}"}

            if resp.status_code == 429:
                self.quota.wait_if_circuit_open()
                continue
            if resp.status_code >= 500:
                return {"kind": "FAIL", "reason": f"Poll HTTP {resp.status_code}"}

            retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
            if retry_after:
                try:
                    wait = max(0.5, min(float(retry_after), 30.0))
                except ValueError:
                    wait = self.poll_interval_sec
                time.sleep(wait)
                continue

            data = resp.json() if (resp.text or "").strip() else {}
            status = str(data.get("status", "")).upper()
            if status in ("COMPLETE", "WARNING", "ERROR") or data.get("alpha") or data.get("children"):
                return {"kind": "DONE", "data": data}
            time.sleep(self.poll_interval_sec)

        return {"kind": "FAIL", "reason": "Poll timeout"}

    def _poll_progress(self, chunk: list[dict[str, Any]], progress_url: str) -> dict[str, int]:
        poll_res = self._poll_progress_raw(chunk, progress_url)
        if poll_res["kind"] == "DONE":
            return self._ingest_completed_progress(chunk, poll_res["data"])
        return self._reconcile_once_chunk(chunk, progress_url, poll_res["reason"])

    def _fetch_child_alpha_id(self, child_id: str) -> Optional[str]:
        try:
            cresp = self.client.get(f"/simulations/{child_id}", timeout=30)
            cdata = cresp.json() if cresp.status_code == 200 and (cresp.text or "").strip() else {}
            return cdata.get("alpha")
        except Exception:
            return None

    def _fetch_alpha_payload(self, aid: str) -> Optional[dict[str, Any]]:
        try:
            aresp = self.client.get(f"/alphas/{aid}", timeout=30)
            return aresp.json() if aresp.status_code == 200 else {}
        except Exception:
            return None

    def _ingest_completed_progress(self, chunk: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, int]:
        completed = unobserved = errors = 0
        children = data.get("children")
        alpha_ids: list[Optional[str]] = []

        if isinstance(children, list) and len(chunk) > 1:
            with ThreadPoolExecutor(max_workers=min(4, max(1, len(children)))) as fetch_pool:
                alpha_ids = list(fetch_pool.map(self._fetch_child_alpha_id, children))
        else:
            alpha_ids.append(data.get("alpha"))

        valid_pairs = [(idx, alpha_ids[idx]) for idx in range(len(chunk)) if idx < len(alpha_ids) and alpha_ids[idx]]
        alpha_payloads: dict[int, Optional[dict[str, Any]]] = {}
        if valid_pairs:
            with ThreadPoolExecutor(max_workers=min(4, len(valid_pairs))) as meta_pool:
                futs = {meta_pool.submit(self._fetch_alpha_payload, aid): idx for idx, aid in valid_pairs}
                for fut in as_completed(futs):
                    alpha_payloads[futs[fut]] = fut.result()

        for idx, t in enumerate(chunk):
            aid = alpha_ids[idx] if idx < len(alpha_ids) else None
            if not aid:
                self.ledger.mark_reconcile_failed_unobserved(t["task_id"], "Missing child alpha_id")
                unobserved += 1
                continue
            adata = alpha_payloads.get(idx)
            if adata is None:
                self.ledger.mark_reconcile_failed_unobserved(t["task_id"], "Alpha fetch error")
                unobserved += 1
                continue

            ism = adata.get("is") or {}
            checks = ism.get("checks") or []
            rn = ism.get("riskNeutralized") or {}
            sh_2y = None
            for chk in checks:
                if chk.get("name") in ("LOW_2Y_SHARPE", "IS_LADDER_SHARPE") and chk.get("value") is not None:
                    sh_2y = float(chk["value"])
                    break
            self.ledger.mark_task_completed(
                t["task_id"],
                simulation_mode=t["simulation_mode"],
                alpha_id=aid,
                sharpe=ism.get("sharpe"),
                fitness=ism.get("fitness"),
                turnover=ism.get("turnover"),
                margin=ism.get("margin"),
                returns=ism.get("returns"),
                sharpe_2y=sh_2y,
                rn_sharpe=rn.get("sharpe"),
                rn_fitness=rn.get("fitness"),
                checks_json=json.dumps(checks, ensure_ascii=False),
            )
            completed += 1

        return {"completed": completed, "unobserved": unobserved, "errors": errors}

    def run_continuous_rolling_batches(
        self,
        prepared_batches: list[dict[str, Any]],
        *,
        batch_size: int = 8,
        should_stop: Optional[Any] = None,
        on_batch_complete: Optional[Any] = None,
    ) -> dict[str, int]:
        """Zero-barrier continuous rolling multi-region pipeline.

        Instead of waiting for all 4 slots in a wave to finish before launching the next wave,
        keeps all `max_slots` (up to `max_per_region` per region) continuously saturated across
        mixed regions (e.g. 2 EUR + 2 USA = 4 concurrent 8-alpha Multi-Sims).
        """
        pending_queue: list[tuple[str, str, int, list[dict[str, Any]]]] = []
        for pb in prepared_batches:
            bid = str(pb["batch_id"])
            reg = str(pb["region"]).upper()
            w = self.slot_weight_for_region(reg)
            for chunk in pack_multisim_batches(pb["tasks"], batch_size=batch_size):
                pending_queue.append((bid, reg, w, chunk))

        summary = {"batches_done": 0, "completed": 0, "unobserved": 0, "errors": 0}
        if not pending_queue:
            return summary

        active_futs: dict[Any, tuple[str, str, int, float]] = {}
        with ThreadPoolExecutor(max_workers=self.max_slots) as pool:
            while pending_queue or active_futs:
                # 1. Fill every available global + per-region slot without waiting for slow stragglers!
                if pending_queue and not (should_stop and should_stop()):
                    dispatched = True
                    while dispatched and pending_queue:
                        dispatched = False
                        for i, (bid, reg, w, chunk) in enumerate(pending_queue):
                            if self.semaphore.try_acquire(weight=w, region=reg):
                                pending_queue.pop(i)
                                fut = pool.submit(self._run_chunk, bid, chunk, w, already_acquired=True)
                                active_futs[fut] = (bid, reg, len(chunk), time.monotonic())
                                dispatched = True
                                break

                if not active_futs:
                    if should_stop and should_stop():
                        break
                    # Avoid spin if remaining items exceed capacity (shouldn't happen)
                    time.sleep(0.5)
                    continue

                # 2. Wait only until the FIRST active simulation finishes, then immediately refill!
                done_set = set()
                for fut in as_completed(list(active_futs.keys())):
                    done_set.add(fut)
                    break

                for fut in done_set:
                    bid, reg, n_items, t0 = active_futs.pop(fut)
                    elapsed = round(time.monotonic() - t0, 1)
                    try:
                        res = fut.result()
                    except Exception:
                        res = {"completed": 0, "unobserved": n_items, "errors": 1}
                    self.ledger.update_batch_progress(bid, "DONE")
                    summary["batches_done"] += 1
                    summary["completed"] += res["completed"]
                    summary["unobserved"] += res["unobserved"]
                    summary["errors"] += res["errors"]
                    if on_batch_complete is not None:
                        on_batch_complete(bid, reg, n_items, res, elapsed)

        return summary

    def _reconcile_once_chunk(
        self,
        chunk: list[dict[str, Any]],
        progress_url: Optional[str],
        reason: str,
    ) -> dict[str, int]:
        """Reconcile-once-never-resend protocol: read-only check once, else RESULTS_UNOBSERVED."""
        for t in chunk:
            self.ledger.mark_task_pending_reconcile(t["task_id"], reason)

        if progress_url:
            try:
                resp = self.client.get(progress_url, timeout=30)
                if resp.status_code == 200 and (resp.text or "").strip():
                    data = resp.json()
                    if data.get("alpha") or data.get("children"):
                        return self._ingest_completed_progress(chunk, data)
            except Exception:
                pass

        for t in chunk:
            self.ledger.mark_reconcile_failed_unobserved(t["task_id"], f"Unobserved after 1 reconcile: {reason}")
        return {"completed": 0, "unobserved": len(chunk), "errors": 0}
