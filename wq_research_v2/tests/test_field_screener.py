"""Offline tests for Stage-0 WebDataScope-1.0.6/data D1 field screening & Huazi Ge 4 gaps."""
from __future__ import annotations

import pytest

from wq_research_v2.config_loader import WDS_DATA_DIR
from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.field_screener import (
    CLASSROOM_HUAZIGE_SEED_RULES,
    FieldScreener,
    build_datafield_inspection_probes,
    compute_expression_nesting_metrics,
    is_fake_single_vector_probe,
)
from wq_research_v2.wds_adapter import compute_region_d1_gaps


def test_classroom_huazige_seed_rules_probes_and_nesting_governance() -> None:
    assert CLASSROOM_HUAZIGE_SEED_RULES["stage12_standardized_clean_defaults"]["default_decay"] == 0
    assert CLASSROOM_HUAZIGE_SEED_RULES["stage12_standardized_clean_defaults"]["default_neutralization"] == "SUBINDUSTRY"
    assert CLASSROOM_HUAZIGE_SEED_RULES["stage12_standardized_clean_defaults"]["fast_mode_allowed"] is True
    assert CLASSROOM_HUAZIGE_SEED_RULES["stage3_controlled_variable_optimization"]["simulation_mode_locked"] == "FULL"
    assert CLASSROOM_HUAZIGE_SEED_RULES["stage3_controlled_variable_optimization"]["standard_decay_poll"] == [0, 5, 20]
    assert CLASSROOM_HUAZIGE_SEED_RULES["deferred_strict_switches"]["scheduled_activation_date"] == "2026-12-10"

    probes = build_datafield_inspection_probes("mdl31_ab1_ass_tvr_last_qtr", "MATRIX")
    assert len(probes) == 8
    validator = ExprValidator()
    for p in probes:
        assert p["recommended_settings"]["delay"] == 1
        assert p["recommended_settings"]["decay"] == 0
        assert p["recommended_settings"]["neutralization"] == "NONE"
        rep = validator.validate(
            p["expression"],
            {
                "region": "USA",
                "universe": "TOP3000",
                "delay": 1,
                "decay": 0,
                "neutralization": "NONE",
                "truncation": 0.04,
            },
        )
        assert rep.valid, f"Probe invalid: {p['probe_id']} -> {rep.errors}"

    clean_m = compute_expression_nesting_metrics(
        "group_rank(ts_decay_linear(ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21), 10), subindustry)"
    )
    assert clean_m["nesting_tag"] == "CLEAN_LE4_LAYERS"
    assert clean_m["is_over_nested"] is False

    deep_m = compute_expression_nesting_metrics(
        "tail(vector_neut(group_rank(ts_decay_linear(min(rank(ts_backfill(a, 21)), min(rank(ts_backfill(b, 21)), rank(ts_backfill(c, 21)))), 22), subindustry), rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"
    )
    assert deep_m["nesting_tag"] == "OVER_NESTED_TEMP_PC_FIX"
    assert deep_m["is_over_nested"] is True
    assert deep_m["nesting_depth"] >= 6


def test_blacklists_trap_fields_and_fake_vector_rule() -> None:
    fs = FieldScreener()
    assert fs.is_dataset_blacklisted("GLB", "earnings5")[0]
    assert fs.is_dataset_blacklisted("ASI", "other36")[0]
    assert not fs.is_dataset_blacklisted("DEU", "model264")[0]

    assert fs.is_trap_field("anl93_top_analyst")
    assert fs.is_trap_field("mdl307_cusip")
    assert not fs.is_trap_field("mdl264_1l_fmc")

    assert is_fake_single_vector_probe(1.50, 1.51) is True
    assert is_fake_single_vector_probe(1.50, 1.85) is False

    ok, _ = fs.validate_live_field({"id": "mdl264_1l_fmc", "type": "MATRIX", "dateCoverage": 1.0})
    assert ok
    ok2, reason2 = fs.validate_live_field({"id": "bad_f", "type": "MATRIX", "dateCoverage": 0.35})
    assert not ok2 and "LOW_DATE_COVERAGE" in reason2

    # KZ79256 30% Fundamental cap
    assert fs.check_fundamental_quota_cap(40, 20)[0]
    assert not fs.check_fundamental_quota_cap(60, 18)[0]


@pytest.mark.skipif(not WDS_DATA_DIR.exists(), reason="WebDataScope-1.0.6/data not installed")
def test_real_webdatascope_d1_only_and_gbr_deu_blindspot() -> None:
    # GBR and DEU are absent in snapshot -> explicit REGION_NOT_IN_SNAPSHOT
    deu = compute_region_d1_gaps("DEU")
    assert deu["status"] == "REGION_NOT_IN_SNAPSHOT"
    assert deu["fallback_prior_region"] == "EUR"

    glb = compute_region_d1_gaps("GLB")
    assert glb["status"] == "OK"
    assert glb["delay"] == 1
    assert glb["dataset_count"] > 100
    assert any(d["is_blue_ocean"] for d in glb["datasets"])

    fs = FieldScreener()
    out = fs.screen_regions_offline(["GLB", "ASI", "CHN", "DEU", "GBR"], top_datasets_per_region=10, include_exact_bin_tiers=False)
    assert out["delay_locked"] == 1
    assert out["regions"]["DEU"]["status"] == "REGION_NOT_IN_SNAPSHOT"
    assert out["regions"]["GLB"]["selected_count"] == 10
    # Ensure JX79797 global blacklist datasets are excluded
    all_ds = {d["dataset_id"] for d in out["ranked_datasets"]}
    assert "earnings5" not in all_ds
    assert "model194" not in all_ds

    # Verify exact .bin archive tiering works via legacy webdata_quality.build_ledger
    out_exact = fs.screen_regions_offline(["GLB", "CHN", "DEU"], top_datasets_per_region=20, include_exact_bin_tiers=True)
    assert out_exact["regions"]["DEU"]["status"] == "REGION_NOT_IN_SNAPSHOT"
    glb_ds = out_exact["regions"]["GLB"]["datasets"]
    chn_ds = out_exact["regions"]["CHN"]["datasets"]
    assert len(glb_ds) > 0 and len(chn_ds) > 0
    assert any((d.get("wds_prior") or {}).get("exact_bin_t1_count", 0) > 0 for d in glb_ds)
    assert any((d.get("wds_prior") or {}).get("exact_bin_t1_count", 0) > 0 for d in chn_ds)
