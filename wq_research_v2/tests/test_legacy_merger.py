"""Unit tests for legacy_core -> wq_research_v2 read-only streaming merger & screener."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from wq_research_v2.legacy_merger import (
    classify_expression_compliance,
    classify_optimization_tier,
    merge_all_legacy_to_v2,
    query_legacy_candidates,
    summarize_legacy_pool,
)


def test_decision3_compliance_and_traps() -> None:
    ok1, v1 = classify_expression_compliance("group_rank(ts_decay_linear(min(rank(a), rank(b)), 22), subindustry)")
    assert ok1 is True and v1 == []

    ok2, v2 = classify_expression_compliance("rank(a) + rank(b)")
    assert ok2 is False and "FORBIDDEN_ADD" in v2

    ok3, v3 = classify_expression_compliance("trade_when(volume > 0, rank(a), -1)")
    assert ok3 is False and "FORBIDDEN_TRADE_WHEN" in v3

    ok4, v4 = classify_expression_compliance("ts_target_tvr_decay(rank(a), lambda_min=0, lambda_max=5, target_tvr=0.1)")
    assert ok4 is True and "TRAP_LAMBDA_MAX_GT_1" in v4


def test_tier_classification_rules() -> None:
    t_os, _ = classify_optimization_tier(
        region="USA", sharpe=2.5, fitness=1.5, turnover=0.05, margin=0.002,
        sharpe_2y=2.2, legacy_sc=0.3, is_already_os=True, decision3_compliant=True, violations=[],
    )
    assert t_os == "ALREADY_OS"

    t_s, _ = classify_optimization_tier(
        region="USA", sharpe=1.80, fitness=1.20, turnover=0.06, margin=0.0018,
        sharpe_2y=2.10, legacy_sc=0.45, is_already_os=False, decision3_compliant=True, violations=[],
    )
    assert t_s == "TIER_S_READY_CHECK"

    t_a, hint_a = classify_optimization_tier(
        region="EUR", sharpe=1.75, fitness=0.92, turnover=0.08, margin=0.0012,
        sharpe_2y=1.40, legacy_sc=0.50, is_already_os=False, decision3_compliant=True, violations=[],
    )
    assert t_a == "TIER_A_PARAM_TUNE" and "2Y_SHARPE<1.58" in hint_a

    t_b, _ = classify_optimization_tier(
        region="USA", sharpe=1.90, fitness=1.30, turnover=0.07, margin=0.0015,
        sharpe_2y=2.00, legacy_sc=0.40, is_already_os=False, decision3_compliant=False, violations=["FORBIDDEN_ADD"],
    )
    assert t_b == "TIER_B_REFACTOR_OP"


def test_streaming_merge_and_screen_end_to_end(tmp_path: Path) -> None:
    # Build synthetic read-only legacy JSONL + catalog.db + os_pnl_cache.db
    runtime = tmp_path / "runtime_data"
    (runtime / "template_usage").mkdir(parents=True)
    (runtime / "hill_climbing_source").mkdir(parents=True)

    # Create synthetic catalog.db with D1 and D0 datasets
    cat_db = runtime / "catalog.db"
    c = sqlite3.connect(str(cat_db))
    c.execute(
        'CREATE TABLE datasets_USA_TOP3000 (id TEXT PRIMARY KEY, name TEXT, region TEXT, delay INT, universe TEXT, '
        'category_id TEXT, subcategory_id TEXT, coverage REAL, dateCoverage REAL, valueScore REAL, '
        'userCount INT, alphaCount INT, fieldCount INT, pyramidMultiplier REAL, dateUpdated TEXT)'
    )
    c.execute(
        "INSERT INTO datasets_USA_TOP3000 VALUES ('model31','M31','USA',1,'TOP3000','model','sub',0.9,0.95,4.0,10,20,30,1.4,'2026-08-01')"
    )
    c.execute(
        "INSERT INTO datasets_USA_TOP3000 VALUES ('d0_set','D0','USA',0,'TOP3000','model','sub',0.9,0.95,4.0,10,20,30,1.4,'2026-08-01')"
    )
    c.commit()
    c.close()

    # Create synthetic os_pnl_cache.db
    sc_db = tmp_path / "os_pnl_cache.db"
    sc = sqlite3.connect(str(sc_db))
    sc.execute("CREATE TABLE os_alphas (alpha_id TEXT PRIMARY KEY)")
    sc.execute("INSERT INTO os_alphas VALUES ('OS_DONE_1')")
    sc.commit()
    sc.close()

    # Write synthetic template_usage JSONL (includes D0 row which MUST be dropped)
    tu = runtime / "template_usage" / "events.jsonl"
    tu.write_text(
        "\n".join([
            json.dumps({
                "alpha_id": "USA_READY_1", "region": "USA", "universe": "TOP3000", "delay": 1,
                "dataset_id": "model31", "expression": "group_rank(mdl31_x, subindustry)",
                "neutralization": "INDUSTRY", "decay": 4, "sharpe": 1.85, "fitness": 1.25,
                "turnover": 0.06, "margin": 0.0018, "sharpe_2y": 2.1, "sc": 0.42, "hard_pass": True,
            }),
            json.dumps({
                "alpha_id": "D0_SKIP_1", "region": "USA", "universe": "TOP3000", "delay": 0,
                "dataset_id": "model31", "expression": "rank(x)", "sharpe": 3.0, "fitness": 2.0,
            }),
            json.dumps({
                "alpha_id": "OS_DONE_1", "region": "USA", "universe": "TOP3000", "delay": 1,
                "dataset_id": "model31", "expression": "rank(y)", "sharpe": 2.1, "fitness": 1.4,
            }),
        ]),
        encoding="utf-8",
    )

    # Write synthetic hill_climbing_source JSONL (coalesces with an alpha needing Decision #3 refactor)
    hc = runtime / "hill_climbing_source" / "events.jsonl"
    hc.write_text(
        json.dumps({
            "event": "SOURCE_STATUS",
            "alpha_id": "USA_REFACT_1",
            "record": {
                "alpha_id": "USA_REFACT_1", "region": "USA", "universe": "TOP3000", "delay": 1,
                "expression": "rank(a) + rank(b)", "sharpe": 1.95, "fitness": 1.35, "sc_value": 0.35,
                "settings": {"region": "USA", "universe": "TOP3000", "decay": 2, "neutralization": "SUBINDUSTRY"},
            },
        }) + "\n",
        encoding="utf-8",
    )

    target_db = tmp_path / "wq_v2_ledger.db"
    res = merge_all_legacy_to_v2(target_db=target_db, runtime_dir=runtime, sc_cache_db=sc_db)
    assert res["d1_unique_alphas_merged"] == 3  # D0_SKIP_1 excluded!
    assert res["datasets_merged"] == 1          # d0_set excluded!
    assert res["tier_counts"]["TIER_S_READY_CHECK"] == 1
    assert res["tier_counts"]["TIER_B_REFACTOR_OP"] == 1
    assert res["tier_counts"]["ALREADY_OS"] == 1

    # Query screen
    cands = query_legacy_candidates(target_db=target_db, regions=["USA"], min_sharpe=1.5, exclude_os=True)
    ids = [r["alpha_id"] for r in cands]
    assert ids == ["USA_READY_1", "USA_REFACT_1"]

    summary = summarize_legacy_pool(target_db=target_db)
    assert summary["total_legacy_d1_alphas"] == 3
    assert summary["total_legacy_d1_datasets"] == 1
