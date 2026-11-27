"""Unit tests for the 6-Angle First-Principles PC-Breakout Laboratory (S3-r10-PCLAB)."""
from __future__ import annotations

from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.pc_breakout_lab import S3_ALPHA0_VERIFIED_FIELDS, build_pc_breakout_lab_s3r10_specs


def test_pc_breakout_lab_passes_all_static_gates_and_operator_diversity() -> None:
    specs = build_pc_breakout_lab_s3r10_specs()
    assert len(specs) == 140
    total_items = sum(len(s["items"]) for s in specs)
    assert total_items == 1120

    batch_ids = [s["batch_id"] for s in specs]
    assert len(batch_ids) == len(set(batch_ids)), "Duplicate batch_id in pc_breakout_lab!"
    assert any(b.startswith("S3-r33-ASI-MF120-Q5STR2-GATE-") for b in batch_ids), "Missing S3-r33 ASI MF120 Q5STR2 GATE!"
    assert any(b.startswith("S3-r33-EUR-OPEFF-SI6-ORTHO-") for b in batch_ids), "Missing S3-r33 EUR OPEFF SI6 ORTHO!"
    assert any(b.startswith("S3-r32-ASI-PSD-D59-FULL-") for b in batch_ids), "Missing S3-r32 ASI PSD D59 FULL!"
    assert any(b.startswith("S3-r32-ASI-ANL-PSD-GENTLE-") for b in batch_ids), "Missing S3-r32 ASI ANL PSD GENTLE!"
    assert any(b.startswith("S3-r31-EUR-M110-ZYX-FULL-") for b in batch_ids), "Missing S3-r31 EUR M110 ZYX FULL!"
    assert any(b.startswith("S3-r31-ASI-ANL120-RAW-FULL-") for b in batch_ids), "Missing S3-r31 ASI ANL120 RAW FULL!"
    assert any(b.startswith("S3-r30-ASI-ANL120-ORTHO-") for b in batch_ids), "Missing S3-r30 ASI ANL120 ORTHO!"
    assert any(b.startswith("S3-r29-ASI-ORTHO-M25-Q5-") for b in batch_ids), "Missing S3-r29 ASI ORTHO M25 Q5!"
    assert any(b.startswith("S3-r28-ASI-MF120-A1LQ-FIN-") for b in batch_ids), "Missing S3-r28 ASI MF120 A1LQ FIN!"
    assert any(b.startswith("S3-r27-ASI-MF120-INTERP-") for b in batch_ids), "Missing S3-r27 ASI MF120 INTERP!"
    assert any(b.startswith("S3-r27b-EUR-1YG-13BP-") for b in batch_ids), "Missing S3-r27b EUR 13bp!"
    assert any(b.startswith("S3-r26-ASI-MF120-LIQ50-N05-") for b in batch_ids), "Missing S3-r26 ASI MF120 LIQ50 N05!"
    assert any(b.startswith("S3-r26b-EUR-M238-ORTHO-") for b in batch_ids), "Missing S3-r26b EUR model238 ORTHO!"
    assert any(b.startswith("S3-r25-ASI-MF120-NEUT05-") for b in batch_ids), "Missing S3-r25 ASI MF120 NEUT05!"
    assert any(b.startswith("S3-r24-ASI-MF120-D22-LIQ-") for b in batch_ids), "Missing S3-r24 ASI MF120 D22+LIQ!"
    assert any(b.startswith("S3-r24b-ASI-MF120-D33-FREE-") for b in batch_ids), "Missing S3-r24b ASI MF120 D33 FREE!"
    assert any(b.startswith("S3-r23d-ASI-MF120-ROBUST-FREE-") for b in batch_ids), "Missing S3-r23d ASI MF120 ROBUST FREE!"
    assert any(b.startswith("S3-r23c-ASI-QTILE5-SUB-FREE-") for b in batch_ids), "Missing S3-r23c ASI QTILE5 SUB FREE!"
    assert any(b.startswith("S3-r23b-ASI-MF120-SUB-FREE-") for b in batch_ids), "Missing S3-r23b ASI MF120 SUB FREE!"
    assert any(b.startswith("S3-r23-ASI-MF120-ROBUST-") for b in batch_ids), "Missing S3-r23 ASI MF120 Robust Finisher!"
    assert any(b.startswith("S3-r22-ASI-MF120-FREE-") for b in batch_ids), "Missing S3-r22 ASI multifactor_return_pred FREE!"
    assert any(b.startswith("S3-r22-USA-MF120-FREE-") for b in batch_ids), "Missing S3-r22 USA multifactor_return_pred FREE!"
    assert any(b.startswith("S3-r21-ASI-GLBSEASON-FREE-") for b in batch_ids), "Missing S3-r21 ASI global_seasonal_model FREE!"
    assert any(b.startswith("S3-r20-USA-CNN-FREE-") for b in batch_ids), "Missing S3-r20 USA chart_cnn_alpha FREE!"
    assert any(b.startswith("S3-r20-EUR-1YG-HIGHMGN-") for b in batch_ids), "Missing S3-r20 EUR 1YG578aX High-Margin!"
    assert any(b.startswith("S3-r19-EUR-PC54-FIN-") for b in batch_ids), "Missing S3-r19 EUR PC=0.54 Finisher!"
    assert any(b.startswith("S3-r19-ASI-M25-FULL-") for b in batch_ids), "Missing S3-r19 ASI/model25 FULL!"
    assert any(b.startswith("S3-r18-EUR-M77M110-ORTHO-") for b in batch_ids), "Missing S3-r18 EUR model77 x model110!"
    assert any(b.startswith("S3-r18-EUR-SI6-TOFIX-") for b in batch_ids), "Missing S3-r18 EUR shortinterest6 TOFIX!"
    assert any(b.startswith("S3-r17-EUR-M238-ORTHO-") for b in batch_ids), "Missing S3-r17 EUR model238 orthogonal!"
    assert any(b.startswith("S3-r17-EUR-SI6-PROMO-") for b in batch_ids), "Missing S3-r17 EUR shortinterest6 promo!"
    assert any(b.startswith("S3-r17-ASI-M39-JPNFIX-") for b in batch_ids), "Missing S3-r17 ASI model39 JPN fix!"
    assert any(b.startswith("S3-r16-ASI-M39-FULL-") for b in batch_ids), "Missing S3-r16 ASI model39 FULL!"
    assert any(b.startswith("S3-r16-ASI-BEHAV-TOFIX-") for b in batch_ids), "Missing S3-r16 ASI behavioral TOFIX!"
    assert any(b.startswith("S3-r16-EUR-M110-LOWPC-") for b in batch_ids), "Missing S3-r16 EUR model110 Low-PC!"
    assert any(b.startswith("S3-r15-EUR-CLEAN4L-") for b in batch_ids), "Missing S3-r15 EUR Clean4L!"
    assert any(b.startswith("S3-r15-USA-CLEAN4L-") for b in batch_ids), "Missing S3-r15 USA Clean4L!"
    assert any(b.startswith("S3-r14-USA-E5M-1AX-") for b in batch_ids), "Missing S3-r14 Single-Axis E5mWLW0J Finisher!"
    assert any(b.startswith("S3-r13-USA-E5M-HIGHMGN-") for b in batch_ids), "Missing S3-r13 High-Margin Finisher!"

    validator = ExprValidator()
    all_ops: set[str] = set()
    admin_cnt = 0
    top_cnt = 0

    for spec in specs:
        assert spec["settings"]["delay"] == 1
        assert spec["settings"]["visualization"] is False
        assert 0 <= int(spec["settings"]["decay"]) <= 20
        assert 0.04 <= float(spec["settings"]["truncation"]) <= 0.08
        if spec["region"] in ("EUR", "USA"):
            assert spec["settings"]["neutralization"] not in ("FAST", "SLOW_AND_FAST")

        for item in spec["items"]:
            rep = validator.validate(
                item["expression"],
                spec["settings"],
                queue_type=spec["queue_type"],
                field_alpha_counts=S3_ALPHA0_VERIFIED_FIELDS if spec["queue_type"] == "UNUSED_ALPHA0" else None,
            )
            assert rep.valid, f"Failed {spec['batch_id']} -> {item['expression']}: {rep.errors}"
            all_ops.update(rep.operators_used)
            if item["source_side"] == "ADMIN_ORIGINAL":
                admin_cnt += 1
            elif item["source_side"] == "TOP100_2026Q4":
                top_cnt += 1

    assert admin_cnt == top_cnt == 560, f"50:50 imbalance: admin={admin_cnt}, top={top_cnt}"

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
