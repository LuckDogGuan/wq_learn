"""Offline tests for Route ⑤ SuperAlpha runner (sa_runner.py): payload, ledger, reconcile-once, budget."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wq_research_v2 import cli
from wq_research_v2.quota_tracker import QuotaTracker
from wq_research_v2.sa_runner import (
    SA_DEFAULT_DAILY_BUDGET,
    SA_MAX_WORKERS,
    SaOwnLedger,
    SaRunner,
    build_sa_payload,
    default_combo_equal_weight,
    default_own_selection,
    sa_payload_fingerprint,
)


class _MockResponse:
    def __init__(self, status_code: int, body: dict | str = "", headers: dict | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.text = json.dumps(body) if isinstance(body, dict) else body

    def json(self):
        return json.loads(self.text) if self.text else {}


class _MockClient:
    def __init__(self) -> None:
        self.post_calls = 0
        self.deleted = False

    def post(self, endpoint: str, **kwargs):
        self.post_calls += 1
        return _MockResponse(201, {}, {"Location": "/simulations/SIM1"})

    def get(self, endpoint: str, **kwargs):
        if endpoint.endswith("/SIM1"):
            return _MockResponse(200, {"status": "COMPLETE", "alpha": "SA001"})
        if endpoint.endswith("/SA001"):
            return _MockResponse(200, {
                "id": "SA001",
                "is": {"sharpe": 5.2, "fitness": 5.1, "turnover": 0.11, "margin": 0.002, "returns": 0.2, "prodCorrelation": 0.42, "selfCorrelation": 0.1, "checks": []},
            })
        return _MockResponse(404, {})

    def delete_simulation(self, endpoint: str, **kwargs):
        self.deleted = True
        return _MockResponse(204, {})


def _base_spec() -> dict:
    return {
        "batch_id": "SA-T-01",
        "region": "EUR",
        "universe": "TOP2500",
        "selection": "own && (prod_correlation > 0) && (prod_correlation < 0.6)",
        "combo": "1",
        "settings": {"neutralization": "SUBINDUSTRY", "selectionLimit": 100},
        "items": [{}],
    }


def test_build_sa_payload_enforces_d1_only() -> None:
    with pytest.raises(ValueError, match="D1-Only"):
        build_sa_payload("own", "1", {"region": "EUR", "universe": "TOP2500", "delay": 0})


def test_build_sa_payload_shape_and_clamps() -> None:
    p = build_sa_payload("own && (prod_correlation < 0.6)", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1, "selectionLimit": 99999})
    assert p["type"] == "SUPER"
    assert p["selection"] == "own && (prod_correlation < 0.6)"
    assert p["combo"] == "1"
    assert p["settings"]["delay"] == 1
    assert p["settings"]["visualization"] is False
    assert p["settings"]["selectionLimit"] == 1000  # clamped to max
    assert p["settings"]["selectionHandling"] == "POSITIVE"
    assert p["settings"]["componentActivation"] == "IS"


def test_build_sa_payload_rejects_bad_enums() -> None:
    with pytest.raises(ValueError, match="selectionHandling"):
        build_sa_payload("own", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1, "selectionHandling": "BAD"})
    with pytest.raises(ValueError, match="componentActivation"):
        build_sa_payload("own", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1, "componentActivation": "BAD"})
    with pytest.raises(ValueError, match="selection"):
        build_sa_payload("", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1})


def test_sa_fingerprint_stable_and_prefixed() -> None:
    a = sa_payload_fingerprint("own", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1})
    b = sa_payload_fingerprint("own", "1", {"region": "EUR", "universe": "TOP2500", "delay": 1})
    c = sa_payload_fingerprint("own", "2", {"region": "EUR", "universe": "TOP2500", "delay": 1})
    assert a == b and a != c and a.startswith("sa:")


def test_default_templates_sane() -> None:
    assert "own" in default_own_selection()
    assert "prod_correlation" in default_own_selection()
    assert default_combo_equal_weight() == "1"
    assert SA_DEFAULT_DAILY_BUDGET == 400
    assert SA_MAX_WORKERS == 3


def test_sa_cli_stops_before_post_when_super_is_unavailable(monkeypatch, tmp_path, capsys) -> None:
    class Auth:
        def __init__(self, **kwargs):
            pass

        def authenticate(self):
            pass

        def close(self):
            pass

        def request(self, method, endpoint, **kwargs):
            assert (method, endpoint) == ("OPTIONS", "/simulations")
            choices = [{"value": "REGULAR"}, {"value": "REGION_AGNOSTIC"}]
            return _MockResponse(200, {"actions": {"POST": {"type": {"choices": choices}}}})

    def unexpected_ledger():
        pytest.fail("The CLI must stop before opening either ledger")

    monkeypatch.setattr(cli, "BrainAuthSession", Auth)
    monkeypatch.setattr(cli, "LedgerStore", unexpected_ledger)
    monkeypatch.setattr(cli, "SaOwnLedger", unexpected_ledger)
    spec = tmp_path / "sa.json"
    spec.write_text(json.dumps(_base_spec()), encoding="utf-8")

    assert cli.main(["sa", "run", "--spec", str(spec)]) == 1
    assert json.loads(capsys.readouterr().out)["super_simulation_available"] is False


def test_sa_runner_prepare_run_dedup_and_metrics(tmp_path: Path) -> None:
    ledger = SaOwnLedger(tmp_path / "sa.db")
    qt = QuotaTracker(ledger)
    client = _MockClient()
    runner = SaRunner(client, ledger, qt, daily_budget=400, poll_interval_sec=0.01)

    bid, runnable, skipped = runner.prepare_batch_tasks(_base_spec())
    assert len(runnable) == 1 and len(skipped) == 0
    res = runner.run_prepared_tasks(bid, runnable)
    assert res["completed"] == 1 and res["unobserved"] == 0

    # Metrics persisted, incl. the SuperAlpha-关键 prod_correlation
    est_day = runnable[0]["est_platform_date"]
    assert ledger.completed_today_count(est_day) == 1

    # Second identical prepare must dedup-skip
    _, runnable2, skipped2 = runner.prepare_batch_tasks({**_base_spec(), "batch_id": "SA-T-02"})
    assert len(runnable2) == 0 and len(skipped2) == 1
    ledger.close()


def test_sa_runner_reconcile_once_never_resends(tmp_path: Path) -> None:
    ledger = SaOwnLedger(tmp_path / "sa.db")
    qt = QuotaTracker(ledger)

    class _FailClient:
        def post(self, endpoint: str, **kwargs):
            return _MockResponse(503, {"error": "down"})
        def get(self, endpoint: str, **kwargs):
            return _MockResponse(404, {})

    runner = SaRunner(_FailClient, ledger, qt)
    bid, runnable, _ = runner.prepare_batch_tasks(_base_spec())
    res = runner.run_prepared_tasks(bid, runnable)
    assert res["unobserved"] == 1
    assert ledger.get_task_status(runnable[0]["task_id"]) == "RESULTS_UNOBSERVED"
    # Restart dedup: the unobserved fingerprint must not re-queue
    _, runnable2, skipped2 = runner.prepare_batch_tasks({**_base_spec(), "batch_id": "SA-T-03"})
    assert len(runnable2) == 0 and len(skipped2) == 1
    ledger.close()


def test_sa_runner_daily_budget_guard(tmp_path: Path) -> None:
    ledger = SaOwnLedger(tmp_path / "sa.db")
    qt = QuotaTracker(ledger)
    client = _MockClient()
    runner = SaRunner(client, ledger, qt, daily_budget=1, poll_interval_sec=0.01)

    bid, runnable, _ = runner.prepare_batch_tasks(_base_spec())
    runner.run_prepared_tasks(bid, runnable)

    # Budget already consumed (1 completed >= 1) -> next task must be rate-limited, not POSTed
    bid2, runnable2, _ = runner.prepare_batch_tasks({**_base_spec(), "batch_id": "SA-T-04", "items": [{"combo": "2"}]})
    res2 = runner.run_prepared_tasks(bid2, runnable2)
    assert res2["completed"] == 0
    assert ledger.get_task_status(runnable2[0]["task_id"]) == "RATE_LIMITED_429"
    ledger.close()
