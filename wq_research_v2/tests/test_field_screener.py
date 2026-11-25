"""Offline tests for Stage-0 WebDataScope-1.0.6/data D1 field screening & Huazi Ge 4 gaps."""
from __future__ import annotations

import pytest

from wq_research_v2.config_loader import WDS_DATA_DIR
from wq_research_v2.field_screener import FieldScreener, is_fake_single_vector_probe
from wq_research_v2.wds_adapter import compute_region_d1_gaps


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
