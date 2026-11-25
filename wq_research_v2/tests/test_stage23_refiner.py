"""Offline unit tests for Stage-2 (1.3-1.4 mild param ladder) & Stage-3 (1.6+ Sub-Universe rescue)."""
from __future__ import annotations

from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.stage23_refiner import build_all_stage23_refiner_specs


def test_stage23_refiner_specs_pass_all_static_gates_and_balance() -> None:
    specs = build_all_stage23_refiner_specs()
    assert len(specs) >= 25

    batch_ids = [s["batch_id"] for s in specs]
    assert len(batch_ids) == len(set(batch_ids)), "Duplicate batch_id in stage23_refiner!"

    alpha0_map = {
        "raw_volume_indicator_6": 0,
        "raw_volume_indicator_3": 0,
        "raw_volume_indicator_5": 0,
        "normalized_volume_indicator_2": 0,
    }
    validator = ExprValidator()
    admin_cnt = 0
    top_cnt = 0
    for spec in specs:
        assert spec["settings"]["delay"] == 1
        assert spec["settings"]["visualization"] is False
        assert 0 <= int(spec["settings"]["decay"]) <= 6
        assert 0.04 <= float(spec["settings"]["truncation"]) <= 0.08
        if spec["region"] == "ASI":
            assert spec["settings"]["maxTrade"] == "ON"
        for item in spec["items"]:
            rep = validator.validate(
                item["expression"],
                spec["settings"],
                queue_type=spec["queue_type"],
                field_alpha_counts=alpha0_map if spec["queue_type"] == "UNUSED_ALPHA0" else None,
            )
            assert rep.valid, f"Failed {spec['batch_id']} -> {item['expression']}: {rep.errors}"
            if item["source_side"] == "ADMIN_ORIGINAL":
                admin_cnt += 1
            elif item["source_side"] == "TOP100_2026Q4":
                top_cnt += 1

    assert admin_cnt == top_cnt and admin_cnt > 0
