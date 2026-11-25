"""Offline unit tests for zero-barrier continuous rolling multi-region pipeline & burst-429 protection."""
from __future__ import annotations

import json
import threading
import time
from typing import Any

from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker
from wq_research_v2.sim_runner import SimRunner, WeightedSlotSemaphore, pack_multisim_batches


class _FakeResp:
    def __init__(self, status_code: int, payload: Any = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = "" if payload is None else json.dumps(payload)

    def json(self) -> Any:
        return self._payload


class _FakeBrainClient:
    """Simulates multi-region concurrent POST pacing, transient pre-creation 429, and child alpha fetch."""

    def __init__(self, fail_first_post_429: bool = False) -> None:
        self._lock = threading.Lock()
        self.post_times: list[float] = []
        self.post_count = 0
        self.fail_first_post_429 = fail_first_post_429
        self._did_429 = False
        self._sim_children: dict[str, list[str]] = {}

    def post(self, path: str, json: Any = None, timeout: int = 45) -> _FakeResp:
        with self._lock:
            self.post_times.append(time.monotonic())
            self.post_count += 1
            if self.fail_first_post_429 and not self._did_429:
                self._did_429 = True
                return _FakeResp(429, {"detail": "SIMULATION_LIMIT_EXCEEDED"}, {"Retry-After": "0.05"})
            sid = f"SIM_{self.post_count}"
            n = len(json) if isinstance(json, list) else 1
            self._sim_children[sid] = [f"{sid}_C{i}" for i in range(n)]
        return _FakeResp(201, {}, {"Location": f"/simulations/{sid}", "X-RateLimit-Remaining": "4500", "X-RateLimit-Limit": "5000"})

    def get(self, path: str, timeout: int = 30) -> _FakeResp:
        if path.startswith("/simulations/SIM_") and "_C" not in path:
            sid = path.split("/")[-1]
            time.sleep(0.05)
            return _FakeResp(200, {"status": "COMPLETE", "children": self._sim_children[sid]})
        if path.startswith("/simulations/SIM_") and "_C" in path:
            cid = path.split("/")[-1]
            return _FakeResp(200, {"alpha": f"A_{cid}"})
        if path.startswith("/alphas/"):
            aid = path.split("/")[-1]
            return _FakeResp(
                200,
                {
                    "id": aid,
                    "is": {"sharpe": 1.65, "fitness": 1.15, "turnover": 0.08, "margin": 0.0015, "returns": 0.09, "checks": []},
                },
            )
        return _FakeResp(404, {})


def test_weighted_semaphore_enforces_global_and_per_region_caps() -> None:
    sem = WeightedSlotSemaphore(max_slots=4, max_per_region=2)
    assert sem.try_acquire(1, region="EUR") is True
    assert sem.try_acquire(1, region="EUR") is True
    # 3rd EUR blocked by max_per_region=2 even though 2 global slots remain!
    assert sem.try_acquire(1, region="EUR") is False
    # USA immediately fills the remaining 2 global slots -> 2 EUR + 2 USA = 4 concurrent!
    assert sem.try_acquire(1, region="USA") is True
    assert sem.try_acquire(1, region="USA") is True
    assert sem.available == 0
    assert sem.region_in_flight("EUR") == 2
    assert sem.region_in_flight("USA") == 2
    sem.release(1, region="EUR")
    assert sem.try_acquire(1, region="EUR") is True


def test_pack_multisim_batches_respects_gold_8_ceiling() -> None:
    items = [{"id": i} for i in range(17)]
    chunks = pack_multisim_batches(items, batch_size=10)
    assert [len(c) for c in chunks] == [8, 7, 2]
    assert all(2 <= len(c) <= 8 for c in chunks)


def test_rolling_pipeline_staggers_posts_and_recovers_pre_creation_429(tmp_path) -> None:
    ledger = LedgerStore(tmp_path / "rolling.db")
    quota = QuotaTracker(ledger)
    client = _FakeBrainClient(fail_first_post_429=True)
    runner = SimRunner(
        client,
        ledger,
        quota,
        max_slots=4,
        max_per_region=2,
        post_stagger_sec=0.05,
        max_post_429_retries=2,
        poll_interval_sec=0.01,
    )
    try:
        prepared = []
        for idx, reg in enumerate(["EUR", "USA", "EUR", "USA"]):
            uni = "TOP2500" if reg == "EUR" else "TOP3000"
            spec = {
                "batch_id": f"ROLL-{reg}-{idx}",
                "region": reg,
                "universe": uni,
                "dataset_id": "model25",
                "settings": {"region": reg, "universe": uni, "delay": 1, "neutralization": "INDUSTRY", "decay": 0, "truncation": 0.04, "visualization": False},
                "items": [
                    {"expression": f"rank(ts_mean(close, {5 + j + idx * 10}))", "source_side": "ADMIN_ORIGINAL", "template_id": "T1"}
                    for j in range(4)
                ],
            }
            bid, runnable, _ = runner.prepare_batch_tasks(spec, simulation_mode="FULL")
            prepared.append({"batch_id": bid, "region": reg, "tasks": runnable})

        callbacks: list[tuple[str, str, int]] = []
        summary = runner.run_continuous_rolling_batches(
            prepared,
            batch_size=8,
            on_batch_complete=lambda bid, reg, n, res, el: callbacks.append((bid, reg, res["completed"])),
        )
        assert summary["batches_done"] == 4
        assert summary["completed"] == 16
        assert summary["unobserved"] == 0
        assert len(callbacks) == 4
        # Verify POST pacing lock actually staggered consecutive POSTs (at least 45ms apart)
        diffs = [b - a for a, b in zip(client.post_times, client.post_times[1:])]
        assert all(d >= 0.035 for d in diffs), f"POSTs collided too closely: {diffs}"
    finally:
        ledger.close()
