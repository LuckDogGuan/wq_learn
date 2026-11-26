"""Unit tests for the 6-Angle First-Principles PC-Breakout Laboratory (S3-r10-PCLAB)."""
from __future__ import annotations

from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.pc_breakout_lab import build_pc_breakout_lab_s3r10_specs


def test_pc_breakout_lab_passes_all_static_gates_and_operator_diversity() -> None:
    specs = build_pc_breakout_lab_s3r10_specs()
    assert len(specs) == 42
    total_items = sum(len(s["items"]) for s in specs)
    assert total_items == 336

    batch_ids = [s["batch_id"] for s in specs]
    assert len(batch_ids) == len(set(batch_ids)), "Duplicate batch_id in pc_breakout_lab!"
    assert any(b.startswith("S3-r13-USA-E5M-HIGHMGN-") for b in batch_ids), "Missing S3-r13 High-Margin Finisher!"

    validator = ExprValidator()
    all_ops: set[str] = set()
    admin_cnt = 0
    top_cnt = 0

    for spec in specs:
        assert spec["settings"]["delay"] == 1
        assert spec["settings"]["visualization"] is False
        assert 0 <= int(spec["settings"]["decay"]) <= 6
        assert 0.04 <= float(spec["settings"]["truncation"]) <= 0.08
        if spec["region"] == "EUR":
            assert spec["settings"]["neutralization"] not in ("FAST", "SLOW_AND_FAST")

        for item in spec["items"]:
            rep = validator.validate(
                item["expression"],
                spec["settings"],
                queue_type=spec["queue_type"],
            )
            assert rep.valid, f"Failed {spec['batch_id']} -> {item['expression']}: {rep.errors}"
            all_ops.update(rep.operators_used)
            if item["source_side"] == "ADMIN_ORIGINAL":
                admin_cnt += 1
            elif item["source_side"] == "TOP100_2026Q4":
                top_cnt += 1

    assert admin_cnt == top_cnt == 168, f"50:50 imbalance: admin={admin_cnt}, top={top_cnt}"

    # Verify genuinely diverse, live-verified REGULAR Gold-81 operators are exercised!
    required_new_ops = {
        "quantile",
        "winsorize",
        "normalize",
        "signed_power",
        "scale",
        "group_neutralize",
        "group_std_dev",
        "group_scale",
        "ts_quantile",
        "ts_rank",
        "ts_av_diff",
        "ts_scale",
        "ts_ir",
        "last_diff_value",
        "ts_target_tvr_decay",
        "ts_target_tvr_hump",
        "ts_regression",
        "vector_neut",
        "max",
        "divide",
        "subtract",
        "bucket",
        "densify",
        "tail",
    }
    missing = required_new_ops - all_ops
    assert not missing, f"Missing expected diverse Gold-81 operators: {sorted(missing)}"
