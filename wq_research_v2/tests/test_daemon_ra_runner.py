"""Offline unit tests for low-memory RA-Only D1 multi-market campaign builder & auto early-stop."""
from __future__ import annotations

from wq_research_v2.daemon_ra_runner import (
    CURATED_RA_D1_CAMPAIGNS,
    HIGH_BASE_MULTI_MARKET_ORDER,
    build_ra_campaign_specs,
    interleave_specs_by_campaign_waves,
    should_early_stop_dataset,
)
from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import current_est_platform_date


def test_all_curated_ra_d1_campaign_specs_pass_static_validator() -> None:
    specs = build_ra_campaign_specs(include_dual_branch=True, include_alt_neut=True)
    assert len(specs) > 250

    covered_regions = {s["region"] for s in specs}
    assert set(HIGH_BASE_MULTI_MARKET_ORDER).issubset(covered_regions)

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
        if spec["region"] in ("ASI", "HKG", "KOR"):
            assert spec["settings"]["maxTrade"] == "ON"
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

    assert total_exprs >= 2500
    assert admin_cnt == top_cnt


def test_country_neutralization_blocked_on_single_country_regions() -> None:
    validator = ExprValidator()
    for reg, uni in [("USA", "TOP3000"), ("CHN", "TOP2000U"), ("DEU", "TOP500"), ("HKG", "TOP800")]:
        rep = validator.validate(
            "rank(ts_mean(close, 22))",
            {"region": reg, "universe": uni, "delay": 1, "neutralization": "COUNTRY", "visualization": False},
        )
        assert not rep.valid
        assert any("Invalid neutralization 'COUNTRY'" in e for e in rep.errors)

    for reg, uni in [("EUR", "TOP2500"), ("GLB", "TOP3000"), ("ASI", "MINVOL1M"), ("AMR", "TOP600")]:
        rep = validator.validate(
            "rank(ts_mean(close, 22))",
            {"region": reg, "universe": uni, "delay": 1, "neutralization": "COUNTRY", "visualization": False},
        )
        assert rep.valid, rep.errors


def test_round_robin_interleave_preserves_all_specs_and_rotates_markets() -> None:
    specs = build_ra_campaign_specs(include_dual_branch=False, include_alt_neut=False)
    rr = interleave_specs_by_campaign_waves(specs, max_slots=4, waves_per_turn=1)
    assert len(rr) == len(specs)
    # First 18 specs (EUR 4 + USA 4 + GLB 2 + ASI 4 + CHN 4) must already hit all 5 Tier-1 High-Base markets!
    early_regions = {s["region"] for s in rr[:18]}
    assert {"EUR", "USA", "GLB", "ASI", "CHN"}.issubset(early_regions)


def test_auto_early_stop_demotes_weak_dataset_but_keeps_strong_dataset(tmp_path) -> None:
    ledger = LedgerStore(tmp_path / "early_stop.db")
    try:
        est = current_est_platform_date()
        ledger.create_batch(
            "B-WEAK", hypothesis_id="H1", queue_type="UNUSED_ALPHA0", source_side="MIXED_4_4",
            region="DEU", universe="TOP500", delay=1, simulation_mode="FULL", slots_required=1,
        )
        for i in range(50):
            tid = f"T-WEAK-{i}"
            ledger.upsert_sim_task({
                "task_id": tid,
                "batch_id": "B-WEAK",
                "payload_fingerprint": f"fp-w-{i}",
                "canonical_dedup_key": f"dk-w-{i}",
                "source_side": "ADMIN_ORIGINAL",
                "queue_type": "UNUSED_ALPHA0",
                "region": "DEU",
                "universe": "TOP500",
                "delay": 1,
                "dataset_id": "model264",
                "primary_field_id": "f1",
                "simulation_mode": "FULL",
                "expression": f"rank(f_{i})",
                "settings_json": '{"region":"DEU","delay":1}',
                "status": "SUBMITTED",
                "est_platform_date": est,
            })
            ledger.mark_task_completed(
                tid, simulation_mode="FULL", alpha_id=f"A{i}",
                sharpe=0.45, fitness=0.25, turnover=0.10, margin=0.0012,
            )

        stop_weak, stats_weak = should_early_stop_dataset(ledger, region="DEU", dataset_id="model264", min_completed=48)
        assert stop_weak is True
        assert stats_weak["completed"] == 50
        assert stats_weak["hits_08"] == 0

        # Add one strong hit -> must NOT early stop
        ledger.mark_task_completed(
            "T-WEAK-0", simulation_mode="FULL", alpha_id="A0",
            sharpe=1.45, fitness=0.95, turnover=0.10, margin=0.0015,
        )
        stop_strong, stats_strong = should_early_stop_dataset(ledger, region="DEU", dataset_id="model264", min_completed=48)
        assert stop_strong is False
        assert stats_strong["hits_strong"] == 1
    finally:
        ledger.close()


def test_daily_summary_keys_and_funnel_export(tmp_path) -> None:
    ledger = LedgerStore(tmp_path / "test_ledger.db")
    try:
        stats = ledger.compute_daily_summary(current_est_platform_date())
        assert "full_valid_completed_count" in stats
        assert "quick_screened_count" in stats
    finally:
        ledger.close()
