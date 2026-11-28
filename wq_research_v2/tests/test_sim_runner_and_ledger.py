"""Offline tests for SimRunner, WeightedSlotSemaphore (GLB=2 slots), SQLite WAL resume, and Quick/Full accounting."""
from __future__ import annotations

import json
from pathlib import Path

from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker
from wq_research_v2.sim_runner import (
    SimRunner,
    WeightedSlotSemaphore,
    extract_sharpe_2y_from_checks,
    pack_multisim_batches,
)


class _MockResponse:
    def __init__(self, status_code: int, body: dict | str = "", headers: dict | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.text = json.dumps(body) if isinstance(body, dict) else body

    def json(self):
        return json.loads(self.text) if self.text else {}


class _MockClient:
    def __init__(self, fail_post: bool = False) -> None:
        self.fail_post = fail_post
        self.post_calls = 0

    def post(self, endpoint: str, **kwargs):
        self.post_calls += 1
        if self.fail_post:
            return _MockResponse(503, {"error": "down"})
        return _MockResponse(201, {}, {"Location": "https://api.worldquantbrain.com/simulations/SIM1"})

    def get(self, endpoint: str, **kwargs):
        if endpoint.endswith("/SIM1"):
            return _MockResponse(200, {"status": "COMPLETE", "children": ["C1", "C2"]})
        if endpoint.endswith("/C1"):
            return _MockResponse(200, {"alpha": "AID001"})
        if endpoint.endswith("/C2"):
            return _MockResponse(200, {"alpha": "AID002"})
        if endpoint.endswith("/AID001"):
            return _MockResponse(200, {"id": "AID001", "is": {"sharpe": 1.9, "fitness": 1.3, "turnover": 0.12, "margin": 0.0018, "returns": 0.12, "checks": []}})
        if endpoint.endswith("/AID002"):
            return _MockResponse(200, {"id": "AID002", "is": {"sharpe": 1.1, "fitness": 0.9, "turnover": 0.25, "margin": 0.0011, "returns": 0.09, "checks": []}})
        return _MockResponse(404, {})


def test_weighted_slot_semaphore_glb_consumes_two_slots() -> None:
    sem = WeightedSlotSemaphore(max_slots=4)
    assert sem.acquire(weight=2, timeout=0.1) is True
    assert sem.available == 2
    assert sem.acquire(weight=2, timeout=0.1) is True
    assert sem.available == 0
    assert sem.acquire(weight=1, timeout=0.05) is False
    sem.release(weight=2)
    assert sem.available == 2


def test_pack_multisim_rebalances_trailing_singleton() -> None:
    items = [{"id": i} for i in range(9)]
    batches = pack_multisim_batches(items, batch_size=8)
    assert [len(b) for b in batches] == [7, 2]


def test_sim_runner_executes_dedups_and_separates_quick_vs_full(tmp_path: Path) -> None:
    ledger = LedgerStore(tmp_path / "ledger.db")
    qt = QuotaTracker(ledger)
    client = _MockClient()
    runner = SimRunner(client, ledger, qt, max_slots=4, poll_interval_sec=0.01)

    spec = {
        "batch_id": "EXP-T0-01",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "model264",
        "settings": {"neutralization": "INDUSTRY", "decay": 0, "delay": 1},
        "items": [
            {"expression": "rank(mdl264_1l_fmc)", "source_side": "ADMIN_ORIGINAL", "template_id": "S0-A1"},
            {"expression": "rank(mdl264_1l_icc)", "source_side": "TOP100_2026Q4", "template_id": "S0-T1"},
        ],
    }
    bid, runnable, skipped = runner.prepare_batch_tasks(spec, simulation_mode="FULL")
    assert len(runnable) == 2 and len(skipped) == 0
    res = runner.run_prepared_tasks(bid, runnable, batch_size=8)
    assert res["completed"] == 2

    # Second identical prepare must dedup-skip both!
    _, runnable2, skipped2 = runner.prepare_batch_tasks({**spec, "batch_id": "EXP-T0-02"}, simulation_mode="FULL")
    assert len(runnable2) == 0 and len(skipped2) == 2

    # Quick mode on same expressions counts separately, does not inflate full_valid_completed_count
    bid_q, runnable_q, _ = runner.prepare_batch_tasks({**spec, "batch_id": "EXP-T0-Q"}, simulation_mode="QUICK")
    assert len(runnable_q) == 2
    runner.run_prepared_tasks(bid_q, runnable_q, batch_size=8)

    est_day = runnable[0]["est_platform_date"]
    summary = ledger.compute_daily_summary(est_day)
    assert summary["full_valid_completed_count"] == 2
    assert summary["quick_screened_count"] == 2
    assert summary["admin_source_ratio"] == 0.5
    ledger.close()


def test_reconcile_once_never_resends_on_post_failure(tmp_path: Path) -> None:
    ledger = LedgerStore(tmp_path / "ledger.db")
    qt = QuotaTracker(ledger)
    client = _MockClient(fail_post=True)
    runner = SimRunner(client, ledger, qt, max_slots=2)

    spec = {
        "batch_id": "EXP-FAIL-01",
        "region": "DEU",
        "universe": "TOP500",
        "settings": {"neutralization": "INDUSTRY", "decay": 0, "delay": 1},
        "items": [
            {"expression": "rank(mdl264_1l_fmc)", "source_side": "ADMIN_ORIGINAL"},
            {"expression": "rank(mdl264_1l_icc)", "source_side": "TOP100_2026Q4"},
        ],
    }
    bid, runnable, _ = runner.prepare_batch_tasks(spec, simulation_mode="FULL")
    res = runner.run_prepared_tasks(bid, runnable, batch_size=8)
    assert client.post_calls == 1  # NEVER resent!
    assert res["unobserved"] == 2
    est_day = runnable[0]["est_platform_date"]
    assert ledger.compute_daily_summary(est_day)["unobserved_count"] == 2
    # On daemon restart, already-reconciled RESULTS_UNOBSERVED fingerprints must NOT be re-queued!
    _, runnable_restart, skipped_restart = runner.prepare_batch_tasks(spec, simulation_mode="FULL")
    assert len(runnable_restart) == 0 and len(skipped_restart) == 2
    assert ledger.get_task_status(runnable[0]["task_id"]) == "RESULTS_UNOBSERVED"
    ledger.close()


def test_extract_sharpe_2y_from_checks_strictly_ignores_ladder_sharpe() -> None:
    """T03 guard: sharpe_2y must ONLY take LOW_2Y_SHARPE, never IS_LADDER_SHARPE."""
    # Case 1: Only IS_LADDER_SHARPE present (e.g. gJrA5ONJ) -> None
    only_ladder = [{"name": "IS_LADDER_SHARPE", "result": "FAIL", "value": 1.56, "limit": 1.58}]
    assert extract_sharpe_2y_from_checks(only_ladder) is None

    # Case 2: Only LOW_2Y_SHARPE present -> 2.15
    only_2y = [{"name": "LOW_2Y_SHARPE", "result": "PASS", "value": 2.15, "limit": 1.58}]
    assert extract_sharpe_2y_from_checks(only_2y) == 2.15

    # Case 3: Both present with IS_LADDER_SHARPE appearing first -> strictly takes LOW_2Y_SHARPE (1.85)
    both = [
        {"name": "IS_LADDER_SHARPE", "result": "PASS", "value": 2.42, "limit": 1.58},
        {"name": "LOW_2Y_SHARPE", "result": "PASS", "value": 1.85, "limit": 1.58},
    ]
    assert extract_sharpe_2y_from_checks(both) == 1.85
