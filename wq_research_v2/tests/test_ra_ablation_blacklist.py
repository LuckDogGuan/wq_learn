"""Offline tests for D1RAEvaluator, AblationEngine (Decision #3), and BlacklistRegistry (200-sample scope & restore)."""
from __future__ import annotations

from pathlib import Path

import pytest

from wq_research_v2.ablation_engine import build_dual_branch_ablation, build_sign_flip_expression
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.ra_evaluator import D1RAEvaluator, evaluate_turnover_action, margin_to_bps


def test_ra_evaluator_d1_gates_flat_kill_and_margin_bps() -> None:
    ev = D1RAEvaluator()
    assert margin_to_bps(0.012267) == 122.67

    # Flat PnL kill (<8 active years or >=200 flat days)
    r_flat = ev.evaluate("F1", region="DEU", delay=1, sharpe=2.0, fitness=1.5, turnover=0.1, margin=0.002, active_years=5)
    assert r_flat.gate_status == "GATE0_REJECTED_FLAT"

    # Negative Sharpe < -1.2 triggers sign flip
    r_neg = ev.evaluate("N1", region="DEU", delay=1, sharpe=-1.45, fitness=-0.9, turnover=0.1, margin=0.001)
    assert r_neg.needs_sign_flip is True

    # Full Gate-4 pass on non-CHN D1
    r_pass = ev.evaluate(
        "P1", region="DEU", delay=1, sharpe=2.1, fitness=1.4, turnover=0.15, margin=0.0018, returns=0.12,
        active_years=10, max_flat_streak_days=3,
        is_checks=[{"name": "LOW_SHARPE", "result": "PASS"}, {"name": "LOW_2Y_SHARPE", "result": "PASS"}],
        sc_state="NO_PEERS_IN_REGION", pc_status="PC_READY_PASS", check_status="PASS",
    )
    assert r_pass.tier1_passed and r_pass.tier2_passed
    assert r_pass.gate_status == "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"

    # CHN stricter bar (Sharpe 1.9 < 2.08 fails Tier-1)
    r_chn = ev.evaluate("C1", region="CHN", delay=1, sharpe=1.90, fitness=1.2, turnover=0.15, margin=0.0025, returns=0.10)
    assert not r_chn.tier1_passed and "CHN_LOW_SHARPE" in r_chn.failed_checks


def test_ablation_engine_zero_add_and_anti_recursion_flip() -> None:
    assert build_sign_flip_expression("rank(x)") == "reverse(rank(x))"
    assert build_sign_flip_expression("reverse(rank(x))") == "rank(x)"

    items = build_dual_branch_ablation(
        "ts_delta(ts_backfill(vec_avg(snt26_top50pctranking),500),55)",
        "ts_decay_linear(ts_backfill(mad_underweight_rating_score,5),378)",
        region="DEU",
        universe="TOP500",
        base_settings={"neutralization": "INDUSTRY", "decay": 0},
        include_max=True,
    )
    assert len(items) == 6
    assert all(it["validation_ok"] for it in items)
    assert all("+" not in it["expression"] and "*" not in it["expression"] for it in items)


def test_blacklist_registry_forbids_operator_and_supports_scoped_restore(tmp_path: Path) -> None:
    ledger = LedgerStore(tmp_path / "ledger.db")
    bl = BlacklistRegistry(ledger, export_dir=tmp_path / "blk_md")

    # Never blacklist OPERATOR
    with pytest.raises(ValueError, match="OPERATOR"):
        bl.register_demotion(
            record_id="BLK-BAD", level="FAST_DEMOTED", target_type="OPERATOR",
            region="DEU", universe="TOP500", dataset_id="model264", field_id=None,
            method_id="ts_mean", param_axis=None, valid_sample_count=30,
            positive_control_alpha_id="POS1", evidence_alpha_ids=["E1"],
            failed_check_dist={"LOW_SHARPE": 30}, why_unusable="bad", dissent_and_rescue=["retry"],
        )

    # SCOPE_BLACKLISTED requires >= 200 samples
    with pytest.raises(ValueError, match="200"):
        bl.register_demotion(
            record_id="BLK-SHORT", level="SCOPE_BLACKLISTED", target_type="FIELD",
            region="DEU", universe="TOP500", dataset_id="model264", field_id="bad_f",
            method_id=None, param_axis=None, valid_sample_count=62,
            positive_control_alpha_id="POS1", evidence_alpha_ids=["E1"],
            failed_check_dist={"LOW_SHARPE": 62}, why_unusable="weak", dissent_and_rescue=["try decay"],
        )

    # PARAM_COMBO scope: blocks decay=0, allows decay=5, and supports audited restore
    rec = bl.register_demotion(
        record_id="BLK-20261125-001", level="SCOPE_BLACKLISTED", target_type="PARAM_COMBO",
        region="DEU", universe="TOP500", dataset_id="model264", field_id="f_test",
        method_id="S0-A1", param_axis="decay=0", valid_sample_count=200,
        positive_control_alpha_id="POS_CTRL_1", evidence_alpha_ids=["A1", "A2"],
        failed_check_dist={"HIGH_TURNOVER": 200}, why_unusable="High TVR at decay=0",
        dissent_and_rescue=["Switch to decay=5 or ts_mean(22)"],
    )
    assert rec["status"] == "ACTIVE"
    assert (tmp_path / "blk_md" / "BLK-20261125-001.md").exists()
    assert bl.is_blocked(region="DEU", universe="TOP500", field_id="f_test", method_id="S0-A1", param_axis="decay=0")[0]
    assert not bl.is_blocked(region="DEU", universe="TOP500", field_id="f_test", method_id="S0-A1", param_axis="decay=5")[0]

    restored = bl.restore("BLK-20261125-001", "Verified rescue after nested group_rank")
    assert restored["status"] == "RESTORED"
    assert not bl.is_blocked(region="DEU", universe="TOP500", field_id="f_test", method_id="S0-A1", param_axis="decay=0")[0]
    ledger.close()


def test_evaluate_turnover_action_high_vs_low_skip_and_tail_guard() -> None:
    # Low turnover (< 8%) -> MUST skip turnover reduction!
    low = evaluate_turnover_action(0.052, expression="group_rank(x, subindustry)", region="USA")
    assert low["action"] == "SKIP_LOW_TURNOVER"
    assert low["recommended_steps"] == []

    # Normal turnover (8%..18%) -> KEEP_NORMAL
    mid = evaluate_turnover_action(0.12, expression="group_rank(x, subindustry)", region="EUR")
    assert mid["action"] == "KEEP_NORMAL"

    # High turnover (> 18%) -> REDUCE_HIGH_TURNOVER, and blocks hump when tail(newval=0) or ASI
    hi_ok = evaluate_turnover_action(0.28, expression="group_rank(x, subindustry)", region="USA")
    assert hi_ok["action"] == "REDUCE_HIGH_TURNOVER"
    assert any("hump" in s for s in hi_ok["recommended_steps"])
    assert "trade_when" in hi_ok["forbidden_ops"]

    hi_tail = evaluate_turnover_action(0.28, expression="tail(vector_neut(x, y), lower=-0.25, upper=0.25, newval=0)", region="USA")
    assert hi_tail["action"] == "REDUCE_HIGH_TURNOVER"
    assert not any("hump" in s for s in hi_tail["recommended_steps"])

    hi_asi = evaluate_turnover_action(0.32, expression="group_rank(x, country)", region="ASI")
    assert hi_asi["action"] == "REDUCE_HIGH_TURNOVER"
    assert not any("hump" in s for s in hi_asi["recommended_steps"])
