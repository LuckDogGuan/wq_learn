"""Offline unit tests for low-memory RA-Only D1 production campaign builder."""
from __future__ import annotations

from wq_research_v2.daemon_ra_runner import CURATED_RA_D1_CAMPAIGNS, build_ra_campaign_specs
from wq_research_v2.expr_validator import ExprValidator


def test_all_curated_ra_d1_campaign_specs_pass_static_validator() -> None:
    specs = build_ra_campaign_specs(include_dual_branch=True, include_alt_neut=True)
    assert len(specs) > 100

    # Build alpha0 field map for UNUSED_ALPHA0 specs
    alpha0_map: dict[str, int] = {}
    for camp in CURATED_RA_D1_CAMPAIGNS:
        if camp["queue_type"] == "UNUSED_ALPHA0":
            for f in camp.get("fields") or []:
                alpha0_map[f] = 0
            for _, expr in camp.get("custom_base_exprs") or []:
                for tok in expr.replace("(", " ").replace(")", " ").replace(",", " ").split():
                    if tok.startswith("oth496_"):
                        alpha0_map[tok] = 0

    validator = ExprValidator()
    total_exprs = 0
    admin_cnt = 0
    top_cnt = 0
    for spec in specs:
        assert spec["settings"]["delay"] == 1
        assert spec["settings"]["visualization"] is False
        for item in spec["items"]:
            rep = validator.validate(
                item["expression"],
                spec["settings"],
                queue_type=spec["queue_type"],
                field_alpha_counts=alpha0_map if spec["queue_type"] == "UNUSED_ALPHA0" else None,
            )
            assert rep.valid, f"Failed {spec['batch_id']} -> {item['expression']}: {rep.errors}"
            total_exprs += 1
            if item["source_side"] == "ADMIN_ORIGINAL":
                admin_cnt += 1
            elif item["source_side"] == "TOP100_2026Q4":
                top_cnt += 1

    assert total_exprs >= 1200
    # Verify exact 50/50 split!
    assert admin_cnt == top_cnt


def test_daily_summary_keys_and_funnel_export(tmp_path) -> None:
    from wq_research_v2.ledger_store import LedgerStore
    from wq_research_v2.quota_tracker import current_est_platform_date

    ledger = LedgerStore(tmp_path / "test_ledger.db")
    try:
        stats = ledger.compute_daily_summary(current_est_platform_date())
        assert "full_valid_completed_count" in stats
        assert "quick_screened_count" in stats
    finally:
        ledger.close()
