"""Unit tests for Route ④ (`alphaforge_agy_dsh_v4`) P0/P1/P2 guards, feedback loop, roster & CLI."""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from scripts.ops.launch_alphaforge_v4 import verify_dsh_events

from wq_research_v2.alphaforge_v4 import (
    attribute_ppa_first_routing,
    build_agy_cli_command,
    build_controller_prompt,
    build_dsh_subagent_brief,
    build_failure_feedback_packet,
    build_platform_day_funnel,
    evaluate_dispatch_preflight,
    resolve_region_thread_cap,
    select_three_plus_one_roster,
)
from wq_research_v2.cli import main as cli_main
from wq_research_v2.expr_validator import compute_payload_fingerprint
from wq_research_v2.ledger_store import LedgerStore


def test_p0_preflight_blocks_premature_alpha0_and_enforces_caps() -> None:
    # Mirrors real 2026-11-28 incident: normal_completed=3384 < 4500 MUST block UNUSED_ALPHA0
    blocked = evaluate_dispatch_preflight(
        region="USA",
        queue_type="UNUSED_ALPHA0",
        normal_completed_today=3384,
        alpha0_switch_threshold=4500,
        requested_threads=6,
    )
    assert blocked.allowed is False
    assert any("PREMATURE_ALPHA0_BLOCKED" in r for r in blocked.block_reasons)
    assert blocked.effective_threads == 4

    # Allowed once normal_completed >= 4500
    allowed = evaluate_dispatch_preflight(
        region="GLB",
        queue_type="UNUSED_ALPHA0",
        normal_completed_today=4504,
        alpha0_switch_threshold=4500,
        requested_threads=5,
    )
    assert allowed.allowed is True
    assert allowed.effective_threads == 3  # GLB hard cap <= 3
    assert resolve_region_thread_cap("GLB", 8) == (3, True)
    assert resolve_region_thread_cap("EUR", 8) == (4, True)


def test_p0_preflight_blocks_stage3_quick_decision3_and_unobserved_resend(tmp_path: Path) -> None:
    db_path = tmp_path / "test_ledger.db"
    ledger = LedgerStore(db_path=db_path)
    try:
        expr = "group_rank(ts_decay_linear(ts_backfill(mdl177_dvm_ttmgfp_alt, 21), 10), subindustry)"
        settings = {
            "region": "EUR",
            "universe": "TOP2500",
            "delay": 1,
            "neutralization": "SUBINDUSTRY",
            "decay": 0,
            "truncation": 0.04,
            "visualization": False,
            "simulationMode": "FULL",
        }
        fp, dedup_key = compute_payload_fingerprint(expr, settings)
        ledger.create_batch(
            batch_id="b-1",
            hypothesis_id="HYP-1",
            queue_type="NORMAL",
            source_side="MIXED_4_4",
            region="EUR",
            universe="TOP2500",
            delay=1,
            simulation_mode="FULL",
            slots_required=1,
            est_platform_date="2026-11-28",
        )
        ledger.upsert_sim_task(
            {
                "task_id": "t-unobs-1",
                "batch_id": "b-1",
                "payload_fingerprint": fp,
                "canonical_dedup_key": dedup_key,
                "source_side": "ADMIN_ORIGINAL",
                "queue_type": "NORMAL",
                "region": "EUR",
                "universe": "TOP2500",
                "delay": 1,
                "simulation_mode": "FULL",
                "expression": expr,
                "settings_json": json.dumps(settings),
                "status": "RESULTS_UNOBSERVED",
                "reconcile_attempts": 1,
                "est_platform_date": "2026-11-28",
            }
        )

        # Re-dispatching an already RESULTS_UNOBSERVED fingerprint MUST be blocked
        res_dup = evaluate_dispatch_preflight(
            region="EUR",
            queue_type="NORMAL",
            normal_completed_today=100,
            expression=expr,
            settings=settings,
            stage="STAGE_3",
            simulation_mode="FULL",
            ledger=ledger,
        )
        assert res_dup.allowed is False
        assert any("FINGERPRINT_ALREADY_RECORDED" in r for r in res_dup.block_reasons)

        # Stage 3 QUICK must be blocked
        res_quick = evaluate_dispatch_preflight(
            region="EUR",
            queue_type="NORMAL",
            normal_completed_today=100,
            stage="STAGE_3",
            simulation_mode="QUICK",
        )
        assert res_quick.allowed is False
        assert any("STAGE34_FULL_LOCKED" in r for r in res_quick.block_reasons)

        # Decision #3 forbidden operator (+) must be blocked
        res_bad_op = evaluate_dispatch_preflight(
            region="USA",
            queue_type="NORMAL",
            normal_completed_today=100,
            expression="rank(close) + rank(open)",
            settings={"region": "USA", "universe": "TOP3000", "delay": 1, "neutralization": "SUBINDUSTRY"},
            stage="STAGE_3",
            simulation_mode="FULL",
        )
        assert res_bad_op.allowed is False
        assert any("AST_GATE_FAIL" in r for r in res_bad_op.block_reasons)
    finally:
        ledger.close()


def test_p0_p1_p2_platform_day_funnel_accounting_and_progress(tmp_path: Path) -> None:
    db_path = tmp_path / "funnel.db"
    ledger = LedgerStore(db_path=db_path)
    try:
        checks_pass = json.dumps([{"name": "LOW_SHARPE", "result": "PASS"}, {"name": "LOW_2Y_SHARPE", "result": "PASS"}])
        checks_pending = json.dumps([{"name": "LOW_SHARPE", "result": "PENDING"}])
        rows = [
            ("t1", "NORMAL", "FULL", "COMPLETED_FULL", "A001", checks_pass, "2026-11-28T01:00:00+00:00", "2026-11-28T01:05:00+00:00"),
            # Duplicate alpha_id row to verify deduplication
            ("t1b", "NORMAL", "FULL", "COMPLETED_FULL", "A001", checks_pass, "2026-11-28T01:06:00+00:00", "2026-11-28T01:07:00+00:00"),
            ("t2", "NORMAL", "FULL", "COMPLETED_FULL", "A002", checks_pending, "2026-11-28T01:10:00+00:00", "2026-11-28T01:15:00+00:00"),
            ("t3", "UNUSED_ALPHA0", "QUICK", "COMPLETED_QUICK", "A003", checks_pass, "2026-11-28T02:00:00+00:00", "2026-11-28T02:02:00+00:00"),
            ("t4", "NORMAL", "FULL", "PENDING_RECONCILE", None, None, "2026-11-28T02:10:00+00:00", None),
            ("t5", "UNUSED_ALPHA0", "FULL", "RESULTS_UNOBSERVED", None, None, "2026-11-28T02:20:00+00:00", None),
        ]
        ledger.create_batch(
            batch_id="b-day",
            hypothesis_id="HYP-DAY",
            queue_type="NORMAL",
            source_side="MIXED_4_4",
            region="USA",
            universe="TOP3000",
            delay=1,
            simulation_mode="FULL",
            slots_required=1,
            est_platform_date="2026-11-27",
        )
        for tid, qt, mode, st, aid, chks, sub_t, comp_t in rows:
            ledger.upsert_sim_task(
                {
                    "task_id": tid,
                    "batch_id": "b-day",
                    "payload_fingerprint": f"fp-{tid}",
                    "canonical_dedup_key": f"dk-{tid}",
                    "source_side": "ADMIN_ORIGINAL",
                    "queue_type": qt,
                    "region": "USA",
                    "universe": "TOP3000",
                    "delay": 1,
                    "simulation_mode": mode,
                    "expression": "rank(close)",
                    "settings_json": "{}",
                    "status": st,
                    "alpha_id": aid,
                    "checks_json": chks,
                    "submitted_at_utc": sub_t,
                    "completed_at_utc": comp_t,
                    "est_platform_date": "2026-11-27",
                }
            )
    finally:
        ledger.close()

    now_dt = datetime.datetime(2026, 11, 28, 3, 0, 0, tzinfo=datetime.timezone.utc)
    rep = build_platform_day_funnel(
        db_path,
        est_platform_date="2026-11-27",
        restart_at_utc="2026-11-28T01:00:00+00:00",
        now_utc=now_dt,
    )
    assert rep["db_found"] is True
    assert rep["completed_full"] == 3
    assert rep["completed_quick"] == 1
    assert rep["unique_completed_alphas"] == 3  # A001 deduplicated
    assert rep["verified_zero_fail_full_alphas"] == 1  # Only A001 verified
    assert rep["unverified_full_alphas"] == 1  # A002 pending checks NOT counted as pass
    assert rep["by_queue"]["NORMAL"]["pending_reconcile"] == 1
    assert rep["by_queue"]["UNUSED_ALPHA0"]["results_unobserved"] == 1
    assert rep["progress_metrics"]["last_completed_utc"] == "2026-11-28T02:02:00+00:00"
    assert rep["progress_metrics"]["oldest_pending_age_sec"] == 3000.0
    assert rep["progress_metrics"]["first_completion_after_restart_sec"] == 300.0
    assert rep["unit_yield"]["verified_zero_fail_per_100_full"] == 33.33


def test_p1_ppa_first_attribution_distinguishes_trap_and_403() -> None:
    expr_ppa_shape = "group_rank(ts_decay_linear(ts_backfill(mdl177_dvm_ttmgfp_alt, 21), 10), subindustry)"
    trap = attribute_ppa_first_routing(
        expr_ppa_shape,
        checks=[
            {"name": "POWER_POOL_CORRELATION", "result": "FAIL"},
            {"name": "LOW_SHARPE", "result": "PASS"},
        ],
        target_track="RA",
        ui_error_hint="Prod Correlation FAIL",
    )
    assert trap["ppa_eligible_structure"] is True
    assert trap["unique_non_exempt_ops"] == 2  # ts_backfill exempt
    assert trap["unique_non_exempt_fields"] == 1  # subindustry exempt
    assert trap["attribution"] == "PPA_FIRST_FALLBACK_TRAP"

    http403 = attribute_ppa_first_routing(expr_ppa_shape, checks=[], target_track="RA", http_status=403)
    assert http403["attribution"] == "PLATFORM_HTTP_403_BLOCKED"

    unverified = attribute_ppa_first_routing(expr_ppa_shape, checks=[], target_track="RA")
    assert unverified["attribution"] == "UNVERIFIED_OR_PENDING_CHECKS"


def test_p1_failure_feedback_and_pivot_budget() -> None:
    fb_continue = build_failure_feedback_packet(
        direction_id="USA-AIEQ-SENT3",
        parent_alpha_id="LL86Rx8e",
        region="USA",
        universe="TOP3000",
        dataset_id="ai_equity_alpha",
        primary_failure="HIGH_PC",
        numeric_evidence={"local_sc": 0.4754, "pc_max": 0.7303, "ge070": 2},
        tried_variables=["neutralization=SUBINDUSTRY->RAM"],
        next_falsifiable_hypothesis="仅叠加 tail(0.25, 0.75, 0.5) 检查 PC 是否降至 <0.70 且 Sharpe 保持 >=1.58",
        consecutive_same_failure_batches=1,
        pivot_budget_batches=2,
        pc_state="PC_HIGH",
        neutralization="REVERSION_AND_MOMENTUM",
    )
    assert fb_continue["pivot_budget"]["decision"] == "CONTINUE_SINGLE_AXIS_FIX"
    assert "历史经验复用卡" in fb_continue["reused_experience_card"]

    fb_pivot = build_failure_feedback_packet(
        direction_id="ASI-MF120-Q5STR2",
        parent_alpha_id="MPgw26wL",
        region="ASI",
        universe="MINVOL1M",
        dataset_id="multifactor_return_pred",
        primary_failure="LOW_ASI_JPN_SHARPE",
        numeric_evidence={"jpn_sharpe": 0.91, "threshold": 1.00},
        tried_variables=["adv20>0.35/0.38", "false=0.26/0.27"],
        next_falsifiable_hypothesis="停止同族门控，换向 analyst_consensus",
        consecutive_same_failure_batches=2,
        pivot_budget_batches=2,
    )
    assert fb_pivot["pivot_budget"]["decision"] == "QUARANTINE_FAMILY_AND_PIVOT"

    # PENDING / RESULTS_UNOBSERVED must NOT burn strategy pivot budget
    fb_pending = build_failure_feedback_packet(
        direction_id="ASI-CONF",
        parent_alpha_id="S3-r35",
        region="ASI",
        universe="MINVOL1M",
        dataset_id="multifactor_return_pred",
        primary_failure="RESULTS_UNOBSERVED",
        numeric_evidence={"unobserved": 8},
        tried_variables=[],
        next_falsifiable_hypothesis="等待排查平台原因，不重发未观测指纹",
        consecutive_same_failure_batches=3,
        pivot_budget_batches=2,
    )
    assert fb_pending["pivot_budget"]["decision"] == "EXCLUDE_FROM_FAILURE_BUDGET_HOLD"
    assert fb_pending["pivot_budget"]["excluded_as_pending_or_platform_fault"] is True


def test_p2_three_plus_one_roster_orthogonality_and_margin_priority() -> None:
    cands = [
        {"alpha_id": "C1", "family_id": "fam_a", "zero_fail_verified": True, "sc": 0.30, "pc": 0.62, "margin_bp": 12.0, "sharpe": 1.9, "pyramid_slot_empty": True, "pyramid_multiplier": 1.5},
        {"alpha_id": "C1_CLONE", "family_id": "fam_a", "zero_fail_verified": True, "sc": 0.31, "pc": 0.63, "margin_bp": 9.0, "sharpe": 2.0, "pyramid_slot_empty": True, "pyramid_multiplier": 1.5},
        {"alpha_id": "C2", "family_id": "fam_b", "zero_fail_verified": True, "sc": 0.40, "pc": 0.65, "margin_bp": 18.5, "sharpe": 1.8, "pyramid_slot_empty": True, "pyramid_multiplier": 1.3},
        {"alpha_id": "C3", "family_id": "fam_c", "zero_fail_verified": True, "sc": 0.25, "pc": 0.59, "margin_bp": 14.0, "sharpe": 2.1, "pyramid_slot_empty": False, "pyramid_multiplier": 1.4},
        {"alpha_id": "C4_BAK", "family_id": "fam_d", "zero_fail_verified": True, "sc": 0.22, "pc": 0.61, "margin_bp": 11.0, "sharpe": 1.7, "pyramid_slot_empty": False, "pyramid_multiplier": 1.2},
        {"alpha_id": "BAD_PC", "family_id": "fam_e", "zero_fail_verified": True, "sc": 0.20, "pc": 0.72, "margin_bp": 25.0, "sharpe": 2.4},
    ]
    roster = select_three_plus_one_roster(cands)
    assert roster["auto_submit_allowed"] is False
    assert [x["alpha_id"] for x in roster["primaries"]] == ["C1", "C2", "C3"]
    assert [x["alpha_id"] for x in roster["backups"]] == ["C4_BAK"]
    assert roster["primary_shortfall"] == 0
    assert roster["backup_shortfall"] == 0
    rej_ids = {r["alpha_id"] for r in roster["rejected"]}
    assert "BAD_PC" in rej_ids
    assert "C1_CLONE" in rej_ids


def test_dsh_verification_uses_ordered_tool_receipts() -> None:
    profile = {"default_provider": "dsh-opencode-go", "default_model": "deepseek-v4.1-flash"}
    provider, model = profile.values()
    binding = {
        "mode": "hub", "enabled": True, "escalate_on_failure": False,
        "bindings": {"flash": {"provider": provider, "model": model}},
    }
    probe = {"tool_call_verified": True, "provider": provider, "model": model}
    worker = {
        "id": "hub-test", "status": "done", "provider": provider, "model": model,
        "toolCalls": 1, "result": "alphaforge_agy_dsh_v4", "tokens": {"input": 10, "output": 5},
    }
    events = [
        {
            "type": "item.completed",
            "item": {
                "type": "mcp_tool_call", "server": "dsh_crew", "tool": tool, "status": "completed",
                "result": {"content": [{"type": "text", "text": json.dumps(data)}], "structured_content": None},
            },
        }
        for tool, data in zip(("dsh_worker_config", "dsh_worker_probe", "dsh_run_worker"), (binding, probe, worker))
    ]
    message = {"type": "item.completed", "item": {"type": "agent_message", "text": "ALPHAFORGE_VERIFY_OK"}}
    assert verify_dsh_events([*events, message], profile)["job_id"] == "hub-test"
    assert not verify_dsh_events([*events[:2], message], profile)["ok"]
    assert not verify_dsh_events([events[1], events[0], events[2]], profile)["ok"]
    worker["toolCalls"] = 0
    events[2]["item"]["result"]["content"][0]["text"] = json.dumps(worker)
    assert not verify_dsh_events(events, profile)["ok"]
    worker["toolCalls"] = 1
    worker["status"] = "timeout"
    events[2]["item"]["result"]["content"][0]["text"] = json.dumps(worker)
    assert not verify_dsh_events(events, profile)["ok"]


def test_agy_cli_command_and_dsh_brief_generation(capsys) -> None:
    brief = build_dsh_subagent_brief(
        task_goal="核验 USA/ai_equity_alpha PC 分布与单轴 tail 假设",
        region="USA",
        universe="TOP3000",
        dataset_id="ai_equity_alpha",
        readonly_evidence=[r"C:\Wq\WorldQuant Brain\docs\agents\CORE_STATE.json"],
        acceptance_criteria=["列出 [V] 数值证据与 1 条单轴假设"],
        failure_code="HIGH_PC",
    )
    assert "alphaforge_agy_dsh_v4" in brief
    assert "历史经验复用卡" in brief
    assert "严禁递归调用 DSH/子代理" in brief

    prompt = build_controller_prompt(region="USA", universe="TOP3000", dataset_id="ai_equity_alpha", failure_code="HIGH_PC")
    assert len(prompt.encode("utf-8")) < 8192
    assert "dsh_worker_probe" in prompt
    assert "Codex CLI" in prompt and "forge handoff" in prompt

    cmd = build_agy_cli_command(prompt, agy_bin="agy", interactive=False, effort="high")
    assert cmd[0] == "agy"
    assert "--print" in cmd
    assert "--effort" in cmd

    # Smoke test CLI `forge` offline subcommands
    assert cli_main(["forge", "handoff"]) == 0
    handoff_output = capsys.readouterr().out
    handoff = json.loads(handoff_output)
    assert handoff["default_track_id"] == "alphaforge_agy_dsh_v4"
    assert 0 < len(handoff["latest_cases"]["effective_cases"]) <= 3
    assert 0 < len(handoff["latest_cases"]["ineffective_cases"]) <= 3
    assert len(handoff_output.encode("utf-8")) < 5000

    assert cli_main(["forge", "experience", "--region", "USA", "--dataset", "ai_equity_alpha", "--failure", "HIGH_PC"]) == 0
    out = capsys.readouterr().out
    assert "历史经验复用卡" in out

    assert cli_main(["forge", "preflight", "--region", "USA", "--queue", "UNUSED_ALPHA0", "--normal-completed", "3384"]) == 2
    out2 = capsys.readouterr().out
    assert "PREMATURE_ALPHA0_BLOCKED" in out2
