"""Route ⑤ (`super_alpha_own_v1`) — SuperAlpha (type=SUPER) D1-Only runner.

Completely isolated from the RA mainline (`data/wq_v2_ledger.db`): dedicated SQLite
`data/sa_own_ledger.db`, dedicated log prefix `[TRACK:super_alpha_own_v1]`, and its
own daily simulation budget (default 400/day). SuperAlpha SHARES the platform 5,000/day
simulation limit with Regular/Python alphas, but has a SEPARATE daily submission quota
(1 SuperAlpha/day, independent of 4 Regular/day). This module only backtests SuperAlpha;
it never submits.

Hard invariants (mirrors AGENTS.md + auth_session):
- D1-Only: settings.delay == 1 enforced everywhere.
- Never POST /alphas/{id}/submit (no submit method here; final submission is manual).
- MAX_WORKERS = 3 (SA simulations are heavier than RA; forum-tested by JR23144).
- Reconcile-once-never-resend on network/timeout/429/missing-ID.
- Selection/combo are SuperAlpha dialect (own / not(own) / in(datacategories,..) /
  prod_correlation / operator_count / ...), NOT regular FASTEXPR — they must NOT be
  routed through the RA ExprValidator.

Methodology sources (8:2 priority, all read before implementation):
- 王哥 ZS59763: SELECTION 框架 v1/v2/v25 (turnover/long_count 分层, prod_corr∈区间, op_count∈[2,8]).
- 贺六浑 JR23144: own 三五 SA 断点续传架构 (random color + neutralization + datacategory 排除, MAX_WORKERS=3).
- Admin KH94146: SuperAlpha 合集 (combo=1 等权起步, Selection Limit + Neutralization 两大超参).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.config_loader import DATA_DIR
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date


# ---------------------------------------------------------------------------
# Route identity
# ---------------------------------------------------------------------------
SA_TRACK_ID = "super_alpha_own_v1"
SA_TRACK_NAME_ZH = "SuperAlpha 独立路线 (SuperAlpha Own v1.0)"
SA_LOG_PREFIX = "[TRACK:super_alpha_own_v1]"

# SuperAlpha concurrency: heavier than RA; forum-tested ceiling.
SA_MAX_WORKERS = 3

# Default daily simulation budget for SuperAlpha (user 2026-11-28: 400/day).
SA_DEFAULT_DAILY_BUDGET = 400

# SuperAlpha selectionLimit legal range (official OPTIONS: 10..1000).
SA_SELECTION_LIMIT_MIN = 10
SA_SELECTION_LIMIT_MAX = 1000

# selectionHandling enum (official OPTIONS).
SA_SELECTION_HANDLINGS = frozenset({"POSITIVE", "NON_ZERO", "NON_NAN"})

# componentActivation enum (IS initial study; OS reality-check before finalize).
SA_COMPONENT_ACTIVATIONS = frozenset({"IS", "OS"})

DEDICATED_SA_LEDGER = DATA_DIR / "sa_own_ledger.db"


SA_LEDGER_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 15000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sa_batches (
    batch_id            TEXT PRIMARY KEY,
    region              TEXT NOT NULL,
    universe            TEXT NOT NULL,
    delay               INTEGER NOT NULL CHECK (delay = 1),
    selection           TEXT NOT NULL,
    combo               TEXT NOT NULL,
    selection_limit     INTEGER NOT NULL,
    selection_handling  TEXT NOT NULL,
    neutralization      TEXT,
    component_activation TEXT NOT NULL,
    status              TEXT NOT NULL,
    created_at_utc      TEXT NOT NULL,
    updated_at_utc      TEXT NOT NULL,
    est_platform_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sa_tasks (
    task_id                 TEXT PRIMARY KEY,
    batch_id                TEXT NOT NULL REFERENCES sa_batches(batch_id),
    payload_fingerprint     TEXT NOT NULL,
    region                  TEXT NOT NULL,
    universe                TEXT NOT NULL,
    delay                   INTEGER NOT NULL CHECK (delay = 1),
    selection               TEXT NOT NULL,
    combo                   TEXT NOT NULL,
    settings_json           TEXT NOT NULL,
    status                  TEXT NOT NULL CHECK (status IN (
        'QUEUED','SUBMITTED','COMPLETED','PENDING_RECONCILE','RESULTS_UNOBSERVED',
        'SYNTAX_ERROR','DEDUP_SKIPPED','RATE_LIMITED_429','FAILED_TECH'
    )),
    alpha_id                TEXT,
    sharpe                  REAL,
    fitness                 REAL,
    turnover                REAL,
    margin                  REAL,
    returns                 REAL,
    prod_correlation        REAL,
    self_correlation        REAL,
    checks_json             TEXT,
    reconcile_attempts      INTEGER NOT NULL DEFAULT 0 CHECK (reconcile_attempts <= 1),
    error_reason            TEXT,
    submitted_at_utc        TEXT,
    completed_at_utc        TEXT,
    est_platform_date       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sa_fp ON sa_tasks(payload_fingerprint, status);
CREATE INDEX IF NOT EXISTS idx_sa_est ON sa_tasks(est_platform_date, status);
"""


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sa_payload_fingerprint(selection: str, combo: str, settings: dict[str, Any]) -> str:
    """Deterministic fingerprint for SuperAlpha dedup (never conflate with RA fingerprints)."""
    canonical = {
        "selection": str(selection).strip(),
        "combo": str(combo).strip(),
        "settings": {k: settings.get(k) for k in sorted(settings)},
    }
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return "sa:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_sa_payload(
    selection: str,
    combo: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    """Build a native BRAIN SUPER simulation payload (single SA per POST, no multi-sim batch)."""
    if not str(selection or "").strip():
        raise ValueError("SuperAlpha selection expression must not be empty")
    if not str(combo or "").strip():
        raise ValueError("SuperAlpha combo expression must not be empty")

    s = dict(settings or {})
    if s.get("delay") != 1:
        raise ValueError(f"D1-Only violation: delay={s.get('delay')!r}")
    if not s.get("region") or not s.get("universe"):
        raise ValueError("SuperAlpha settings require region and universe")

    s["instrumentType"] = s.get("instrumentType", "EQUITY")
    s["language"] = s.get("language", "FASTEXPR")
    s["visualization"] = False

    limit = int(s.get("selectionLimit", 100))
    s["selectionLimit"] = max(SA_SELECTION_LIMIT_MIN, min(SA_SELECTION_LIMIT_MAX, limit))

    handling = str(s.get("selectionHandling", "POSITIVE")).upper()
    if handling not in SA_SELECTION_HANDLINGS:
        raise ValueError(f"Invalid selectionHandling: {handling!r}")
    s["selectionHandling"] = handling

    activation = str(s.get("componentActivation", "IS")).upper()
    if activation not in SA_COMPONENT_ACTIVATIONS:
        raise ValueError(f"Invalid componentActivation: {activation!r}")
    s["componentActivation"] = activation

    return {
        "type": "SUPER",
        "settings": s,
        "selection": str(selection).strip(),
        "combo": str(combo).strip(),
    }


# ---------------------------------------------------------------------------
# 王哥 + 贺六浑 + admin 精选 Selection / Combo 模板（默认基线，可被 spec 覆盖）
# ---------------------------------------------------------------------------
def default_own_selection(region_universe_note: str = "") -> str:
    """王哥 SELECTION v2 own 基线：prod_corr 区间 + op_count 上下界 + decay/truncation 经济含义过滤."""
    return (
        "own && (prod_correlation > 0) && (prod_correlation < 0.6) "
        "&& (operator_count >= 2) && (operator_count <= 8) "
        "&& (datafield_count <= 4) && (decay <= 5) && (truncation <= 0.1) "
        "&& (universe != 'ILLIQUID_MINVOL1M')"
    )


def default_combo_equal_weight() -> str:
    """等权是第一基准（WL13229 + 韩国研究员 + 王哥共识）：稳健性最高、过拟合风险最低."""
    return "1"


# ---------------------------------------------------------------------------
# Dedicated SuperAlpha ledger (isolated from the RA mainline ledger)
# ---------------------------------------------------------------------------
class SaOwnLedger:
    """Thread-safe SQLite WAL persistence for SuperAlpha backtests (data/sa_own_ledger.db)."""

    def __init__(self, db_path: Path = DEDICATED_SA_LEDGER) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SA_LEDGER_SCHEMA_SQL)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create_batch(
        self,
        batch_id: str,
        *,
        region: str,
        universe: str,
        selection: str,
        combo: str,
        settings: dict[str, Any],
        status: str = "QUEUED",
    ) -> None:
        now = _utc_now()
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO sa_batches (
                    batch_id, region, universe, delay, selection, combo, selection_limit,
                    selection_handling, neutralization, component_activation, status,
                    created_at_utc, updated_at_utc, est_platform_date
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id, region.upper(), universe.upper(), selection, combo,
                    int(settings.get("selectionLimit", 100)),
                    str(settings.get("selectionHandling", "POSITIVE")),
                    settings.get("neutralization"),
                    str(settings.get("componentActivation", "IS")),
                    status, now, now, current_est_platform_date(),
                ),
            )
            self._conn.commit()

    def update_batch_progress(self, batch_id: str, status: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sa_batches SET status=?, updated_at_utc=? WHERE batch_id=?",
                (status, _utc_now(), batch_id),
            )
            self._conn.commit()

    def has_completed_fingerprint(self, payload_fingerprint: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM sa_tasks WHERE payload_fingerprint=? AND status IN "
                "('COMPLETED','SUBMITTED','PENDING_RECONCILE','RESULTS_UNOBSERVED') LIMIT 1",
                (payload_fingerprint,),
            ).fetchone()
            return row is not None

    def get_task_status(self, task_id: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT status FROM sa_tasks WHERE task_id=? LIMIT 1", (task_id,)
            ).fetchone()
            return str(row["status"]) if row is not None else None

    def upsert_task(self, task: dict[str, Any]) -> None:
        if task.get("delay", 1) != 1:
            raise ValueError("D1-Only violation in sa_tasks")
        incoming = str(task.get("status") or "")
        task_id = str(task.get("task_id") or "")
        # Immutable guard: never let a non-terminal status overwrite completed/unobserved.
        if task_id and incoming not in ("COMPLETED",):
            existing = self.get_task_status(task_id)
            if existing in ("COMPLETED", "RESULTS_UNOBSERVED"):
                return
        cols = [
            "task_id", "batch_id", "payload_fingerprint", "region", "universe",
            "delay", "selection", "combo", "settings_json", "status", "alpha_id",
            "sharpe", "fitness", "turnover", "margin", "returns", "prod_correlation",
            "self_correlation", "checks_json", "reconcile_attempts", "error_reason",
            "submitted_at_utc", "completed_at_utc", "est_platform_date",
        ]
        vals = [task.get(c) for c in cols]
        idx = cols.index("reconcile_attempts")
        if vals[idx] is None:
            vals[idx] = 0
        placeholders = ",".join("?" for _ in cols)
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO sa_tasks ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
            self._conn.commit()

    def mark_completed(self, task_id: str, *, alpha_id: str, metrics: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """
                UPDATE sa_tasks SET status='COMPLETED', alpha_id=?, sharpe=?, fitness=?,
                    turnover=?, margin=?, returns=?, prod_correlation=?, self_correlation=?,
                    checks_json=?, completed_at_utc=?, est_platform_date=?
                WHERE task_id=?
                """,
                (
                    alpha_id, metrics.get("sharpe"), metrics.get("fitness"),
                    metrics.get("turnover"), metrics.get("margin"), metrics.get("returns"),
                    metrics.get("prod_correlation"), metrics.get("self_correlation"),
                    metrics.get("checks_json"), _utc_now(), current_est_platform_date(), task_id,
                ),
            )
            self._conn.commit()

    def mark_pending_reconcile(self, task_id: str, reason: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sa_tasks SET status='PENDING_RECONCILE', error_reason=? WHERE task_id=?",
                (reason, task_id),
            )
            self._conn.commit()

    def mark_unobserved(self, task_id: str, reason: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sa_tasks SET status='RESULTS_UNOBSERVED', reconcile_attempts=1, error_reason=? WHERE task_id=?",
                (reason, task_id),
            )
            self._conn.commit()

    def get_resumable_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sa_tasks WHERE status IN ('QUEUED','SUBMITTED','PENDING_RECONCILE') ORDER BY batch_id, task_id"
            ).fetchall()
            return [dict(r) for r in rows]

    def completed_today_count(self, est_platform_date: Optional[str] = None) -> int:
        day = est_platform_date or current_est_platform_date()
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM sa_tasks WHERE est_platform_date=? AND status='COMPLETED'",
                (day,),
            ).fetchone()
            return int(row["c"]) if row else 0


# ---------------------------------------------------------------------------
# SuperAlpha runner (single-SA-per-POST, MAX_WORKERS=3, reconcile-once)
# ---------------------------------------------------------------------------
class SaRunner:
    """Concurrent SuperAlpha backtester with dedicated checkpoint ledger + daily budget guard."""

    def __init__(
        self,
        client: Any,
        ledger: SaOwnLedger,
        quota: QuotaTracker,
        *,
        daily_budget: int = SA_DEFAULT_DAILY_BUDGET,
        max_workers: int = SA_MAX_WORKERS,
        post_stagger_sec: float = 2.0,
        poll_interval_sec: float = 5.0,
        poll_timeout_sec: float = 900.0,
        stall_timeout_sec: float = 300.0,
    ) -> None:
        self.client = client
        self.ledger = ledger
        self.quota = quota
        self.daily_budget = max(1, int(daily_budget))
        self.max_workers = max(1, min(SA_MAX_WORKERS, int(max_workers)))
        self.post_stagger_sec = max(0.0, float(post_stagger_sec))
        self.poll_interval_sec = float(poll_interval_sec)
        self.poll_timeout_sec = float(poll_timeout_sec)
        self.stall_timeout_sec = max(0.0, float(stall_timeout_sec))
        self._post_lock = threading.Lock()
        self._last_post_monotonic = 0.0

    def prepare_batch_tasks(self, spec: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """Validate, dedup and persist QUEUED SuperAlpha tasks to the isolated ledger."""
        batch_id = spec.get("batch_id") or f"SA-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        region = str(spec["region"]).upper()
        universe = str(spec["universe"]).upper()
        base_settings = dict(spec.get("settings") or {})
        base_settings.setdefault("region", region)
        base_settings.setdefault("universe", universe)
        base_settings.setdefault("delay", 1)
        base_settings.setdefault("selectionLimit", 100)
        base_settings.setdefault("selectionHandling", "POSITIVE")
        base_settings.setdefault("componentActivation", "IS")

        base_selection = str(spec.get("selection") or default_own_selection()).strip()
        base_combo = str(spec.get("combo") or default_combo_equal_weight()).strip()

        self.ledger.create_batch(
            batch_id=batch_id,
            region=region,
            universe=universe,
            selection=base_selection,
            combo=base_combo,
            settings=base_settings,
        )

        runnable: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        est_day = current_est_platform_date()

        items = spec.get("items") or [{}]
        for idx, item in enumerate(items):
            selection = str(item.get("selection") or base_selection).strip()
            combo = str(item.get("combo") or base_combo).strip()
            item_settings = dict(base_settings)
            item_settings.update(item.get("settings_override") or {})
            item_settings["visualization"] = False

            try:
                payload = build_sa_payload(selection, combo, item_settings)
            except ValueError as exc:
                skipped.append({"item": idx, "reason": f"SYNTAX_ERROR: {exc}"})
                continue

            task_id = f"{batch_id}-{idx:03d}"
            fp = sa_payload_fingerprint(selection, combo, item_settings)
            task_row = {
                "task_id": task_id,
                "batch_id": batch_id,
                "payload_fingerprint": fp,
                "region": region,
                "universe": universe,
                "delay": 1,
                "selection": selection,
                "combo": combo,
                "settings_json": json.dumps(item_settings, sort_keys=True),
                "status": "QUEUED",
                "est_platform_date": est_day,
            }

            if self.ledger.has_completed_fingerprint(fp):
                task_row["status"] = "DEDUP_SKIPPED"
                task_row["error_reason"] = "Duplicate SuperAlpha payload_fingerprint in ledger"
                self.ledger.upsert_task(task_row)
                skipped.append({"item": idx, "reason": "DEDUP_SKIPPED"})
                continue

            self.ledger.upsert_task(task_row)
            runnable.append(task_row)

        return batch_id, runnable, skipped

    def run_prepared_tasks(self, batch_id: str, tasks: list[dict[str, Any]]) -> dict[str, int]:
        if not tasks:
            return {"batch_id": batch_id, "completed": 0, "unobserved": 0, "errors": 0}

        summary = {"batch_id": batch_id, "completed": 0, "unobserved": 0, "errors": 0}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futs = [pool.submit(self._run_one, t) for t in tasks]
            for fut in as_completed(futs):
                res = fut.result()
                summary["completed"] += res["completed"]
                summary["unobserved"] += res["unobserved"]
                summary["errors"] += res["errors"]

        self.ledger.update_batch_progress(batch_id, "DONE")
        return summary

    def _pace_post_submission(self) -> None:
        if self.post_stagger_sec <= 0:
            return
        with self._post_lock:
            now = time.monotonic()
            wait = (self._last_post_monotonic + self.post_stagger_sec) - now
            if wait > 0:
                time.sleep(wait)
            self._last_post_monotonic = time.monotonic()

    def _budget_exhausted(self) -> bool:
        return self.ledger.completed_today_count() >= self.daily_budget

    def _run_one(self, task: dict[str, Any]) -> dict[str, int]:
        if self._budget_exhausted():
            self.ledger.upsert_task({**task, "status": "RATE_LIMITED_429", "error_reason": "SA daily budget exhausted"})
            return {"completed": 0, "unobserved": 0, "errors": 1}

        payload = build_sa_payload(
            task["selection"], task["combo"], json.loads(task["settings_json"])
        )

        self.quota.wait_if_circuit_open()
        self._pace_post_submission()
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        task["status"] = "SUBMITTED"
        task["submitted_at_utc"] = now_utc
        self.ledger.upsert_task(task)

        try:
            resp = self.client.post("/simulations", json=payload, timeout=45)
        except Exception as exc:
            return self._reconcile_once(task, None, f"POST exception: {type(exc).__name__}")

        if resp.status_code not in (200, 201):
            code = resp.status_code
            if code == 429:
                self.ledger.upsert_task({**task, "status": "RATE_LIMITED_429", "error_reason": "HTTP 429 on POST"})
                return {"completed": 0, "unobserved": 0, "errors": 1}
            return self._reconcile_once(task, None, f"POST HTTP {code}")

        progress_url = resp.headers.get("Location") or resp.headers.get("location")
        if not progress_url:
            return self._reconcile_once(task, None, "Missing Location header")

        poll_res = self._poll_progress_raw(task, progress_url)
        if poll_res["kind"] == "DONE":
            return self._ingest_completed(task, poll_res["data"])
        return self._reconcile_once(
            task,
            progress_url,
            poll_res["reason"],
            cancel_zombie=bool(poll_res.get("cancel_zombie", False)),
        )

    def _poll_progress_raw(self, task: dict[str, Any], progress_url: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.poll_timeout_sec
        last_progress: Optional[float] = None
        last_progress_change_ts = time.monotonic()
        while time.monotonic() < deadline:
            try:
                resp = self.client.get(progress_url, timeout=30)
            except Exception as exc:
                return {"kind": "FAIL", "reason": f"Poll exception: {type(exc).__name__}"}
            if resp.status_code == 429:
                self.quota.wait_if_circuit_open()
                time.sleep(max(2.0, self.poll_interval_sec))
                continue
            if resp.status_code >= 500:
                return {"kind": "FAIL", "reason": f"Poll HTTP {resp.status_code}"}

            data = {}
            if (resp.text or "").strip():
                try:
                    data = resp.json()
                except Exception:
                    data = {}

            status = str(data.get("status", "")).upper()
            retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")

            prog = data.get("progress")
            if isinstance(prog, (int, float)):
                prog_f = float(prog)
                if last_progress is None or prog_f != last_progress:
                    last_progress = prog_f
                    last_progress_change_ts = time.monotonic()
                elif self.stall_timeout_sec > 0 and (time.monotonic() - last_progress_change_ts) >= self.stall_timeout_sec:
                    return {
                        "kind": "FAIL",
                        "reason": f"Poll stalled at progress={last_progress:.2f}",
                        "cancel_zombie": True,
                    }

            if retry_after:
                try:
                    time.sleep(max(0.5, min(float(retry_after), 30.0)))
                except ValueError:
                    time.sleep(self.poll_interval_sec)
                continue

            if status in ("COMPLETE", "WARNING", "ERROR") or data.get("alpha"):
                return {"kind": "DONE", "data": data}
            time.sleep(self.poll_interval_sec)

        return {"kind": "FAIL", "reason": "Poll timeout", "cancel_zombie": True}

    def _ingest_completed(self, task: dict[str, Any], data: dict[str, Any]) -> dict[str, int]:
        aid = data.get("alpha")
        if not aid:
            err = f"Sim ERROR: {str(data.get('message') or '')[:120]}" if str(data.get("status", "")).upper() == "ERROR" else "Missing SuperAlpha alpha_id"
            self.ledger.mark_unobserved(task["task_id"], err)
            return {"completed": 0, "unobserved": 1, "errors": 0}

        metrics = self._fetch_sa_metrics(aid)
        if metrics is None:
            self.ledger.mark_unobserved(task["task_id"], "SuperAlpha metrics fetch error")
            return {"completed": 0, "unobserved": 1, "errors": 0}

        self.ledger.mark_completed(task["task_id"], alpha_id=aid, metrics=metrics)
        return {"completed": 1, "unobserved": 0, "errors": 0}

    def _fetch_sa_metrics(self, aid: str) -> Optional[dict[str, Any]]:
        for attempt in range(3):
            try:
                aresp = self.client.get(f"/alphas/{aid}", timeout=30)
                if aresp.status_code == 429:
                    time.sleep(max(1.0, min(3.0 * (attempt + 1), 15.0)))
                    continue
                if aresp.status_code == 200 and (aresp.text or "").strip():
                    adata = aresp.json()
                    ism = adata.get("is") or {}
                    return {
                        "sharpe": ism.get("sharpe"),
                        "fitness": ism.get("fitness"),
                        "turnover": ism.get("turnover"),
                        "margin": ism.get("margin"),
                        "returns": ism.get("returns"),
                        "prod_correlation": ism.get("prodCorrelation"),
                        "self_correlation": ism.get("selfCorrelation"),
                        "checks_json": json.dumps(ism.get("checks") or [], ensure_ascii=False),
                    }
                if attempt < 2:
                    time.sleep(1.5)
            except Exception:
                if attempt < 2:
                    time.sleep(1.5)
        return None

    def _reconcile_once(
        self,
        task: dict[str, Any],
        progress_url: Optional[str],
        reason: str,
        *,
        cancel_zombie: bool = False,
    ) -> dict[str, int]:
        self.ledger.mark_pending_reconcile(task["task_id"], reason)

        if progress_url:
            try:
                resp = self.client.get(progress_url, timeout=30)
                if resp.status_code == 200 and (resp.text or "").strip():
                    data = resp.json()
                    if data.get("alpha"):
                        return self._ingest_completed(task, data)
                if cancel_zombie and resp.status_code == 200 and hasattr(self.client, "delete_simulation"):
                    try:
                        self.client.delete_simulation(progress_url, timeout=20)
                    except Exception:
                        pass
            except Exception:
                pass

        self.ledger.mark_unobserved(task["task_id"], f"Unobserved after 1 reconcile: {reason}")
        return {"completed": 0, "unobserved": 1, "errors": 0}
