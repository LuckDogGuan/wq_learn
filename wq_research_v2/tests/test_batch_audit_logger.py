"""Offline unit tests for batch_audit_logger, COMPLETED_FULL immutability guard, and SC_PASS tagging."""
from __future__ import annotations

import json

from wq_research_v2.batch_audit_logger import (
    _parse_checks_zero_fail,
    build_batch_audit_report,
    classify_checks_state,
    render_batch_audit_markdown,
)
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import current_est_platform_date
from wq_research_v2.tagger import (
    PC_HIGH_TAG,
    SC_HIGH_TAG,
    SC_PASS_TAG,
    USEFUL_TAG,
    compute_merged_tags,
    format_sc_pc_alias,
    sort_passing_candidates_margin_first,
)


def test_dedup_never_overwrites_completed_full_task(tmp_path) -> None:
    """Regression guard: restarting daemon / re-preparing batch_id MUST NOT wipe COMPLETED_FULL rows."""
    ledger = LedgerStore(tmp_path / "immutable.db")
    try:
        est = current_est_platform_date()
        ledger.create_batch(
            "B-IMMUT", hypothesis_id="H1", queue_type="NORMAL", source_side="MIXED_4_4",
            region="EUR", universe="TOP2500", delay=1, simulation_mode="FULL", slots_required=1,
        )
        base = {
            "task_id": "B-IMMUT-000",
            "batch_id": "B-IMMUT",
            "payload_fingerprint": "fp-immut-000",
            "canonical_dedup_key": "dk-immut-000",
            "source_side": "ADMIN_ORIGINAL",
            "queue_type": "NORMAL",
            "region": "EUR",
            "universe": "TOP2500",
            "delay": 1,
            "dataset_id": "model25",
            "primary_field_id": "value_momentum_region_percentile",
            "simulation_mode": "FULL",
            "expression": "group_zscore(value_momentum_region_percentile, industry)",
            "settings_json": '{"region":"EUR","delay":1,"neutralization":"CROWDING","decay":4,"truncation":0.06}',
            "status": "QUEUED",
            "est_platform_date": est,
        }
        ledger.upsert_sim_task(base)
        ledger.mark_task_completed(
            "B-IMMUT-000",
            simulation_mode="FULL",
            alpha_id="A_WINNER",
            sharpe=2.15,
            fitness=1.65,
            turnover=0.07,
            margin=0.0018,
            sharpe_2y=2.40,
            checks_json=json.dumps([{"name": "LOW_SUB_UNIVERSE_SHARPE", "result": "PASS", "value": 1.2}]),
        )

        # Simulate restart attempting to overwrite with DEDUP_SKIPPED or QUEUED
        overwrite_attempt = dict(base, status="DEDUP_SKIPPED", error_reason="Duplicate payload_fingerprint in ledger")
        ledger.upsert_sim_task(overwrite_attempt)

        row = ledger._conn.execute("SELECT status, alpha_id, sharpe FROM sim_tasks WHERE task_id='B-IMMUT-000'").fetchone()
        assert row["status"] == "COMPLETED_FULL"
        assert row["alpha_id"] == "A_WINNER"
        assert abs(float(row["sharpe"]) - 2.15) < 1e-6
    finally:
        ledger.close()


def test_batch_audit_logger_counts_stages_and_classifies_best_bad_timeout(tmp_path) -> None:
    db_path = tmp_path / "audit.db"
    ledger = LedgerStore(db_path)
    try:
        est = current_est_platform_date()
        for bid, reg, ds in [("B-BEST", "EUR", "model25"), ("B-BAD", "CHN", "other496"), ("B-TO", "EUR", "model238")]:
            ledger.create_batch(
                bid, hypothesis_id="H", queue_type="NORMAL", source_side="MIXED_4_4",
                region=reg, universe="TOP2500", delay=1, simulation_mode="FULL", slots_required=1,
            )

        # BEST batch: 1 zero-fail S3 winner + 1 S2 hit
        for idx, (aid, sh, fit, fails) in enumerate([
            ("EUR_S3", 2.05, 1.45, [{"name": "LOW_SUB_UNIVERSE_SHARPE", "result": "PASS"}]),
            ("EUR_S2", 1.35, 0.80, [{"name": "LOW_SHARPE", "result": "FAIL"}]),
        ]):
            tid = f"B-BEST-{idx:03d}"
            ledger.upsert_sim_task({
                "task_id": tid, "batch_id": "B-BEST", "payload_fingerprint": f"fp-{tid}",
                "canonical_dedup_key": f"dk-{tid}", "source_side": "ADMIN_ORIGINAL",
                "template_id": "S3FIN-ADM-01_CROWDING", "queue_type": "NORMAL",
                "region": "EUR", "universe": "TOP2500", "delay": 1, "dataset_id": "model25",
                "primary_field_id": "val_mom", "simulation_mode": "FULL",
                "expression": f"rank(f_{idx})",
                "settings_json": '{"neutralization":"CROWDING","decay":4,"truncation":0.06}',
                "status": "QUEUED", "est_platform_date": est,
            })
            ledger.mark_task_completed(
                tid, simulation_mode="FULL", alpha_id=aid, sharpe=sh, fitness=fit,
                turnover=0.07, margin=0.0014, sharpe_2y=2.2, checks_json=json.dumps(fails),
            )

        # BAD CHN double-negative mirage batch
        for idx in range(8):
            tid = f"B-BAD-{idx:03d}"
            ledger.upsert_sim_task({
                "task_id": tid, "batch_id": "B-BAD", "payload_fingerprint": f"fp-{tid}",
                "canonical_dedup_key": f"dk-{tid}", "source_side": "TOP100_2026Q4",
                "template_id": "RA-TOP-01", "queue_type": "NORMAL",
                "region": "CHN", "universe": "TOP2000U", "delay": 1, "dataset_id": "other496",
                "primary_field_id": "oth496_x", "simulation_mode": "FULL",
                "expression": f"rank(g_{idx})",
                "settings_json": '{"neutralization":"SUBINDUSTRY","decay":0,"truncation":0.04}',
                "status": "QUEUED", "est_platform_date": est,
            })
            ledger.mark_task_completed(
                tid, simulation_mode="FULL", alpha_id=f"CHN_{idx}", sharpe=-2.1, fitness=-1.2,
                turnover=0.06, margin=-0.0018, sharpe_2y=-1.5,
            )

        # TIMEOUT batch
        for idx in range(4):
            tid = f"B-TO-{idx:03d}"
            ledger.upsert_sim_task({
                "task_id": tid, "batch_id": "B-TO", "payload_fingerprint": f"fp-{tid}",
                "canonical_dedup_key": f"dk-{tid}", "source_side": "ADMIN_ORIGINAL",
                "template_id": "RA-ADM-01", "queue_type": "NORMAL",
                "region": "EUR", "universe": "TOP2500", "delay": 1, "dataset_id": "model238",
                "primary_field_id": "m238_x", "simulation_mode": "FULL",
                "expression": f"rank(h_{idx})",
                "settings_json": '{"neutralization":"STATISTICAL","decay":0,"truncation":0.04}',
                "status": "RESULTS_UNOBSERVED", "error_reason": "Poll timeout", "est_platform_date": est,
            })
    finally:
        ledger.close()

    rep = build_batch_audit_report(db_path)
    ov = rep["overall_funnel"]
    assert ov["completed_full"] == 10
    assert ov["unobserved"] == 4
    assert ov["stage1_pass_sh080"] == 2
    assert ov["stage2_pass_sh125"] == 2
    assert ov["stage3_pass_sh158_fit1"] == 1
    assert ov["stage3_verified_zero_fail"] == 1
    assert rep["grade_counts"]["BEST"] == 1
    assert rep["grade_counts"]["BAD"] == 1
    assert rep["grade_counts"]["TIMEOUT_BUG"] == 1

    md = render_batch_audit_markdown(rep)
    assert "B-BEST" in md and "B-BAD" in md and "B-TO" in md
    assert "一阶段 (`Sh≥0.80`) 过 `2` 个" in md


def test_sc_pass_tag_transitions() -> None:
    tags, changed = compute_merged_tags(["AQP202611"], SC_PASS_TAG)
    assert changed and tags == ["AQP202611", SC_PASS_TAG]

    # Promoting SC_PASS -> Useful cleanly strips SC_PASS while preserving competition tags
    tags2, changed2 = compute_merged_tags(tags, USEFUL_TAG)
    assert changed2 and tags2 == [USEFUL_TAG, "AQP202611"]

    # Marking SC_IS_HIGHT strips both Useful and SC_PASS
    tags3, changed3 = compute_merged_tags([USEFUL_TAG, SC_PASS_TAG, "AQP202611"], SC_HIGH_TAG)
    assert changed3 and tags3 == ["AQP202611", SC_HIGH_TAG]

    # Marking PC_IS_HIGHT keeps SC_PASS intact while stripping Useful
    tags4, changed4 = compute_merged_tags([USEFUL_TAG, SC_PASS_TAG], PC_HIGH_TAG)
    assert changed4 and tags4 == [SC_PASS_TAG, PC_HIGH_TAG]


def test_sc_pc_alias_format_and_margin_first_ranking() -> None:
    assert format_sc_pc_alias(0.36, 0.7816) == "SC 0.360 PC 0.782"
    assert format_sc_pc_alias(0.2691, 0.6599) == "SC 0.269 PC 0.660"
    assert format_sc_pc_alias(None, None) is None

    ranked = sort_passing_candidates_margin_first([
        {"alpha_id": "A_LOW_MGN", "margin_bp": 12.0, "sharpe": 2.4, "fitness": 2.0},
        {"alpha_id": "B_HIGH_MGN", "margin_bp": 35.4, "sharpe": 1.9, "fitness": 1.5},
        {"alpha_id": "C_MID_MGN", "margin_bp": 18.6, "sharpe": 2.5, "fitness": 2.3},
    ])
    assert [x["alpha_id"] for x in ranked] == ["B_HIGH_MGN", "C_MID_MGN", "A_LOW_MGN"]


def test_classify_checks_state_three_states_and_mode_split(tmp_path) -> None:
    """T04 guard: PENDING/ERROR/empty checks must be UNVERIFIED (not VERIFIED_ZERO_FAIL), and FULL vs QUICK split."""
    assert classify_checks_state(None) == ("UNVERIFIED", [])
    assert classify_checks_state("[]") == ("UNVERIFIED", [])
    assert classify_checks_state(json.dumps([{"name": "LOW_SHARPE", "result": "PASS"}, {"name": " matches_themes", "result": "WARNING"}])) == (
        "VERIFIED_ZERO_FAIL",
        [],
    )
    assert classify_checks_state(json.dumps([{"name": "LOW_SHARPE", "result": "PASS"}, {"name": "SELF_CORRELATION", "result": "PENDING"}])) == (
        "UNVERIFIED",
        ["SELF_CORRELATION:PENDING"],
    )
    assert classify_checks_state(json.dumps([{"name": "PROD_CORRELATION", "result": "ERROR"}])) == (
        "UNVERIFIED",
        ["PROD_CORRELATION:ERROR"],
    )
    assert classify_checks_state(json.dumps([{"name": "LOW_2Y_SHARPE", "result": "FAIL"}])) == (
        "HAS_FAIL",
        ["LOW_2Y_SHARPE"],
    )
    assert _parse_checks_zero_fail(json.dumps([{"name": "SELF_CORRELATION", "result": "PENDING"}]))[0] is False

    db_path = tmp_path / "split_modes.db"
    ledger = LedgerStore(db_path)
    try:
        est = current_est_platform_date()
        ledger.create_batch("B-MIX", hypothesis_id="H", queue_type="NORMAL", source_side="MIXED_4_4", region="USA", universe="TOP3000", delay=1, simulation_mode="FULL", slots_required=1)
        for idx, (mode, st, chk_res) in enumerate([
            ("FULL", "COMPLETED_FULL", "PASS"),
            ("QUICK", "COMPLETED_QUICK", "PENDING"),
        ]):
            tid = f"B-MIX-{idx}"
            ledger.upsert_sim_task({
                "task_id": tid, "batch_id": "B-MIX", "payload_fingerprint": f"fp-{tid}",
                "canonical_dedup_key": f"dk-{tid}", "source_side": "ADMIN_ORIGINAL",
                "template_id": "T1", "queue_type": "NORMAL", "region": "USA", "universe": "TOP3000",
                "delay": 1, "dataset_id": "model31", "primary_field_id": "f1",
                "simulation_mode": mode, "expression": f"rank(x_{idx})",
                "settings_json": '{"neutralization":"SUBINDUSTRY"}', "status": "QUEUED", "est_platform_date": est,
            })
            ledger.mark_task_completed(
                tid, simulation_mode=mode, alpha_id=f"A_{idx}", sharpe=1.75, fitness=1.15,
                turnover=0.06, margin=0.0012, sharpe_2y=1.80,
                checks_json=json.dumps([{"name": "LOW_SHARPE", "result": chk_res}]),
            )
    finally:
        ledger.close()

    rep = build_batch_audit_report(db_path)
    ov = rep["overall_funnel"]
    assert ov["completed_full"] == 1
    assert ov["completed_quick"] == 1
    assert ov["completed_total"] == 2
    assert ov["stage3_verified_zero_fail"] == 1
    assert ov["stage3_unverified_checks"] == 1
