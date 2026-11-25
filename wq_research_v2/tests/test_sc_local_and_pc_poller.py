"""Offline tests for portable LocalSCEngine (zero false-0.0, self-exclusion, N×N matrix) & PCPoller (200 empty body)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.pc_poller import PCPoller, classify_readonly_check_payload
from wq_research_v2.sc_local import LocalSCEngine


def _make_pnl(seed: int, n: int = 300) -> tuple[list[str], list[float]]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-03", periods=n, freq="B").strftime("%Y-%m-%d").tolist()
    pnls = np.cumsum(rng.normal(0.001, 0.01, size=n)).tolist()
    return dates, pnls


def test_local_sc_never_returns_false_zero_and_excludes_self(tmp_path: Path) -> None:
    eng = LocalSCEngine(tmp_path / "sc_cache.db")
    dates, p1 = _make_pnl(1)
    _, p2 = _make_pnl(2)
    s1 = pd.Series(p1, index=dates)

    # Empty cache -> CACHE_STALE, max_corr=None (NEVER 0.0!)
    r_stale = eng.evaluate_sc("CAND1", "GBR", s1)
    assert r_stale.sc_state == "CACHE_STALE" and r_stale.max_corr is None

    # Populate USA OS alpha, query DEU -> NO_PEERS_IN_REGION, max_corr=None
    eng.upsert_os_alpha(
        alpha_id="OS_USA_1", region="USA", universe="TOP3000", delay=1,
        is_ppa=False, sharpe=2.1, date_submitted="2026-09-01", dates=dates, pnls=p1,
    )
    r_deu = eng.evaluate_sc("CAND1", "DEU", s1)
    assert r_deu.sc_state == "NO_PEERS_IN_REGION" and r_deu.max_corr is None

    # Self-exclusion: querying OS_USA_1 against USA with only itself -> NO_PEERS_IN_REGION
    r_self = eng.evaluate_sc("OS_USA_1", "USA", s1)
    assert r_self.sc_state == "NO_PEERS_IN_REGION"

    # Add identical series under OS_USA_2 -> SC_READY_HIGH (~1.0)
    eng.upsert_os_alpha(
        alpha_id="OS_USA_2", region="USA", universe="TOP3000", delay=1,
        is_ppa=True, sharpe=1.9, date_submitted="2026-09-02", dates=dates, pnls=p2,
    )
    r_high = eng.evaluate_sc("CAND_DUP", "USA", s1, pool_mode="REGULAR_ALL")
    assert r_high.sc_state == "SC_READY_HIGH" and r_high.max_corr is not None and r_high.max_corr > 0.99

    # Non-overlapping dates -> PENDING_NO_OVERLAP, max_corr=None
    s_old = pd.Series(p1, index=pd.date_range("2010-01-01", periods=len(p1), freq="B").strftime("%Y-%m-%d"))
    r_no_ov = eng.evaluate_sc("CAND_OLD", "USA", s_old, pool_mode="REGULAR_ALL")
    assert r_no_ov.sc_state == "PENDING_NO_OVERLAP" and r_no_ov.max_corr is None

    # Pairwise N×N matrix & greedy orthogonal subset
    s2 = pd.Series(p2, index=dates)
    s1_near = pd.Series([v * 1.01 for v in p1], index=dates)
    mat = eng.compute_pairwise_matrix({"A": s1, "A_DUP": s1_near, "B": s2})
    kept, pruned = eng.select_orthogonal_subset(["A", "A_DUP", "B"], mat, max_pairwise_corr=0.68)
    assert kept == ["A", "B"]
    assert len(pruned) == 1 and pruned[0]["alpha_id"] == "A_DUP"
    eng.close()


class _PCMockClient:
    def __init__(self, prod_code: int, prod_body: str, check_code: int = 200, check_body: str = "") -> None:
        self.prod_code = prod_code
        self.prod_body = prod_body
        self.check_code = check_code
        self.check_body = check_body

    def get(self, endpoint: str, **kwargs):
        class _R:
            def __init__(self, c, t):
                self.status_code = c
                self.text = t
        if endpoint.endswith("/correlations/prod"):
            return _R(self.prod_code, self.prod_body)
        return _R(self.check_code, self.check_body)


def test_pc_poller_handles_200_empty_body_and_rescue_band(tmp_path: Path) -> None:
    ledger = LedgerStore(tmp_path / "ledger.db")

    # 200 empty body -> PENDING_PC_COMPUTING (never 0!)
    p1 = PCPoller(_PCMockClient(200, ""), ledger).poll_once("AID1", "GBR")
    assert p1.status == "PENDING_PC_COMPUTING" and p1.pc_max is None

    # Empty checks -> PENDING (never PASS!)
    st, _, _ = classify_readonly_check_payload(200, json.dumps({"is": {"checks": []}}))
    assert st == "PENDING"

    # PC=0.62 + checks PASS -> PC_READY_PASS
    chk_ok = json.dumps({"is": {"checks": [{"name": "LOW_SHARPE", "result": "PASS", "value": 2.1}]}})
    p2 = PCPoller(_PCMockClient(200, json.dumps({"max": 0.62, "min": -0.1}), 200, chk_ok), ledger).poll_once("AID2", "GBR")
    assert p2.status == "PC_READY_PASS" and p2.check_status == "PASS"

    # PC=0.72 -> PC_READY_HIGH + RESCUE_CANDIDATE_SIGNED_POWER
    p3 = PCPoller(_PCMockClient(200, json.dumps({"max": 0.72}), 200, chk_ok), ledger).poll_once("AID3", "GBR")
    assert p3.status == "PC_READY_HIGH" and p3.rescue_hint == "RESCUE_CANDIDATE_SIGNED_POWER"
    ledger.close()
