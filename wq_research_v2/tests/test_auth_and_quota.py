"""Offline tests for BrainAuthSession (10m refresh, 10s reconnect, /submit block) & QuotaTracker (EST DST, 429)."""
from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wq_research_v2.auth_session import BiometricsRequiredError, BrainAuthSession
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date


class _FakeResp:
    def __init__(self, status_code: int = 200, headers: dict | None = None, text: str = "{}") -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text

    def json(self):
        import json
        return json.loads(self.text)


def test_est_dst_boundary_beijing_1300_winter_and_1200_summer() -> None:
    # Winter EST (UTC-5): 2026-11-25 12:59 CST (04:59 UTC) -> 2026-11-24 EST
    bj_winter_before = datetime.datetime(2026, 11, 25, 4, 59, tzinfo=datetime.timezone.utc)
    bj_winter_after = datetime.datetime(2026, 11, 25, 5, 1, tzinfo=datetime.timezone.utc)
    assert current_est_platform_date(bj_winter_before) == "2026-11-24"
    assert current_est_platform_date(bj_winter_after) == "2026-11-25"

    # Summer EDT (UTC-4): 2026-07-15 11:59 CST (03:59 UTC) -> 2026-07-14 EDT
    bj_summer_before = datetime.datetime(2026, 7, 15, 3, 59, tzinfo=datetime.timezone.utc)
    bj_summer_after = datetime.datetime(2026, 7, 15, 4, 1, tzinfo=datetime.timezone.utc)
    assert current_est_platform_date(bj_summer_before) == "2026-07-14"
    assert current_est_platform_date(bj_summer_after) == "2026-07-15"


def test_quota_tracker_records_headers_and_share_core_429_backoff(tmp_path: Path) -> None:
    ledger = LedgerStore(tmp_path / "ledger.db")
    sleeps: list[float] = []
    now = [100.0]
    qt = QuotaTracker(ledger, clock=lambda: now[0], sleeper=lambda s: sleeps.append(s))

    # Normal 201 captures limit/remaining/reset
    snap1 = qt.observe_response(
        "/simulations",
        _FakeResp(201, {"X-Ratelimit-Limit": "5000", "X-Ratelimit-Remaining": "4992", "X-Ratelimit-Reset": "3600"}),
    )
    assert snap1.limit_val == 5000
    assert snap1.remaining_val == 4992

    # 429 with X-RateLimit-Reset (no Retry-After) respects reset
    snap2 = qt.observe_response("/simulations", _FakeResp(429, {"X-RateLimit-Reset": "12"}))
    assert snap2.http_status == 429
    waited = qt.wait_if_circuit_open()
    assert waited == pytest.approx(12.0, abs=0.1)
    assert sleeps and sleeps[-1] == pytest.approx(12.0, abs=0.1)

    # 429 with no headers uses Share Core ladder (attempt 1 -> 10s)
    snap3 = qt.observe_response("/simulations", _FakeResp(429, {}))
    assert qt.compute_wait_seconds(snap3, attempt=1) == 10.0
    ledger.close()


def test_auth_session_blocks_submit_and_unconfirmed_patch_and_handles_biometrics() -> None:
    fake_sess = MagicMock()
    fake_sess.cookies = {}
    fake_sess.post.return_value = _FakeResp(201)
    fake_sess.request.return_value = _FakeResp(200)

    auth = BrainAuthSession(session_factory=lambda: fake_sess)
    auth._username = "user@example.com"
    auth._password = "redacted"

    with pytest.raises(PermissionError, match="Formal Alpha Submission"):
        auth.post("/alphas/ABC123/submit")

    with pytest.raises(PermissionError, match="explicit_user_confirmed"):
        auth.patch("/alphas/ABC123", json={"tags": ["test"]})

    # Biometrics persona pause
    fake_sess.post.return_value = _FakeResp(401, {"WWW-Authenticate": "persona"})
    with pytest.raises(BiometricsRequiredError):
        auth.authenticate(force=True)
    assert auth.paused_needs_biometrics is True
    auth.close()
