"""Modular Stage-2 (target 1.3-1.4) & Stage-3 (target 1.6+, 0 FAIL) mild-parameter refiner.

Implements the user-approved graduated funnel:
- Stage 1 (Broad Screen): Sharpe >= 0.80 -> POOL_B
- Stage 2 (Mild Param & Structure Refinement): 0.80-1.25 -> 1.30-1.45+ (POOL_A)
    Mild axes: decay in {0, 2, 4, 6}, truncation in {0.04, 0.06, 0.08}, smoothing windows {5, 10, 15, 22},
    neutralization sweep, signed_power(x, 0.5/0.75/1.25), hump(x, hump=0.01), ATOM dual-branch min(rank, rank).
- Stage 3 (Targeted Bottleneck Rescue -> 1.60+, 0 FAIL -> POOL_S):
    * EUR/model25 monsters (legq0aml Sh=3.16, 6XG8EML5 Sh=2.66, np6JW77q Sh=1.85, kq87KjPK Sh=1.70)
      ONLY failed LOW_SUB_UNIVERSE_SHARPE -> rescue via nested group_cartesian_product(country, industry/subindustry),
      EUR/TOP1200 & EUR/TOP800, mild decay {0, 2, 4, 6}, truncation {0.04, 0.06, 0.08}, signed_power(x, 0.5/0.75),
      and ATOM dual-branch min(rank(val_mom), rank(op_eff)).
    * ASI/price_signal_dl seeds (3qGbRKo6 Sh=1.21, 2Y=1.66) -> rescue LOW_ASI_JPN_SHARPE & ROBUST via
      group_cartesian_product(country, industry), group_neutralize(..., country), decay {2, 4, 6}, maxTrade=ON.
    * USA/price_signal_dl seeds (N1K03xae Sh=1.10, 2Y=1.84; gJrAY2bM 2Y=1.99, Mgn=33.4bp) -> mild param ladder to 1.3-1.4+.
    * DEU/fundamental6 seeds (ROA Sh=0.90-1.05, Mgn=46-59bp) -> mild param ladder + ROA x GP/CF dual-branch to 1.3-1.4+.

Strictly enforces D1-Only (delay=1), Decision #3 (NO add/multiply/trade_when), Gold 81 whitelist, 5:5 side balance.
"""
from __future__ import annotations

from typing import Any

REFINER_VER = "r1"


def _make_settings(
    region: str,
    universe: str,
    neutralization: str,
    *,
    decay: int = 0,
    truncation: float = 0.04,
    max_trade: str = "OFF",
) -> dict[str, Any]:
    return {
        "region": region,
        "universe": universe,
        "delay": 1,
        "neutralization": neutralization,
        "decay": int(decay),
        "truncation": float(truncation),
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "ON",
        "maxTrade": max_trade,
        "visualization": False,
    }


def _pack_items_into_spec(
    *,
    batch_id: str,
    campaign_id: str,
    hypothesis_id: str,
    region: str,
    universe: str,
    dataset_id: str,
    queue_type: str,
    settings: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "campaign_id": campaign_id,
        "hypothesis_id": hypothesis_id,
        "queue_type": queue_type,
        "source_side": "MIXED_4_4",
        "region": region,
        "universe": universe,
        "dataset_id": dataset_id,
        "settings": settings,
        "items": items,
    }


def build_eur_model25_stage3_subuniverse_rescue_specs() -> list[dict[str, Any]]:
    """Stage-3 rescue for EUR/TOP2500/model25 (Sh=1.70..3.16, 2Y=1.79..2.27, Mgn=23..60bp, ONLY fail=LOW_SUB_UNIVERSE_SHARPE).

    Empirical Wave #1 lesson: EUR/TOP1200 alone dropped Sharpe 3.16->1.26, whereas EUR/TOP2500 keeps full 3.16
    and already gets Sub-Uni=1.29. Therefore STAY on EUR/TOP2500 and rescue Sub-Universe via:
      - ATOM size-bucket normalization & large-cap gating using model25's own Total Assets (mdl25_bsv421_5v)
      - Nested country x industry/subindustry grouping + mild decay {0,2,4,6} & truncation {0.04,0.06,0.08}
      - Mild signed_power(0.5/0.75) + ATOM dual-branch min(rank(val_mom), rank(op_eff/exclusions))
    """
    specs: list[dict[str, Any]] = []
    vm = "ts_backfill(value_momentum_region_percentile, 21)"
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    ex = "ts_backfill(exclusions_component_percentile, 21)"
    rm = "ts_backfill(regional_momentum_percentile, 21)"
    # model25 Total Assets (live-verified cov=62.8%, dCov=1.0) -> keeps 100% single-dataset ATOM!
    m25_at = "ts_backfill(mdl25_bsv421_5v, 126)"

    # Pack A: Pure ATOM EUR/TOP2500 Sub-Universe rescue (size-gated + nested country*industry + dual-branch)
    expr_defs_a: list[tuple[str, str, str, str]] = [
        ("S3-ADM-01-atom-gate30-vm", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank({m25_at}) > 0.3, group_zscore({vm}, industry), 0)"),
        ("S3-ADM-02-atom-gate45-vm", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank({m25_at}) > 0.45, group_zscore({vm}, industry), 0)"),
        ("S3-ADM-03-atom-bkt-vm", "ADMIN_ORIGINAL", "WL13229", f"group_zscore({vm}, bucket(rank({m25_at}), range=\"0.2,1,0.2\"))"),
        ("S3-ADM-04-ci-vm-m10", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_mean({vm}, 10), group_cartesian_product(country, industry))"),
        ("S3-TOP-01-sp05-vm-ind", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore({vm}, industry), 0.5)"),
        ("S3-TOP-02-atom-gate35-vm-m22", "TOP100_2026Q4", "SZ83096", f"if_else(rank({m25_at}) > 0.35, group_zscore(ts_mean({vm}, 22), subindustry), 0)"),
        ("S3-TOP-03-dual-vm-oe-gate30", "TOP100_2026Q4", "ZS59763", f"if_else(rank({m25_at}) > 0.3, group_zscore(min(rank({vm}), rank({oe})), industry), 0)"),
        ("S3-TOP-04-dual-vm-ex-ci", "TOP100_2026Q4", "ZS59763", f"group_zscore(min(rank({vm}), rank({ex})), group_cartesian_product(country, industry))"),
    ]

    # Pack B: PV1 adv20 / cap liquidity-bucket & large-cap gate + op_eff combinations on EUR/TOP2500
    expr_defs_b: list[tuple[str, str, str, str]] = [
        ("S3-ADM-05-adv-gate35-vm", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore({vm}, industry), 0)"),
        ("S3-ADM-06-adv-gate50-vm", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.5, group_zscore({vm}, industry), 0)"),
        ("S3-ADM-07-adv-bkt-vm", "ADMIN_ORIGINAL", "WL13229", f"group_zscore({vm}, bucket(rank(adv20), range=\"0.2,1,0.2\"))"),
        ("S3-ADM-08-adv-gate35-oe", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore({oe}, industry), 0)"),
        ("S3-TOP-05-adv-gate40-vm-m22", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, group_zscore(ts_mean({vm}, 22), subindustry), 0)"),
        ("S3-TOP-06-adv-gate35-dual-vmoe", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({oe})), industry), 0)"),
        ("S3-TOP-07-adv-gate35-vm-ci", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, group_zscore({vm}, group_cartesian_product(country, industry)), 0)"),
        ("S3-TOP-08-adv-gate35-vm-rm", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({rm})), industry), 0)"),
    ]

    setting_grid: list[tuple[str, str, int, float]] = [
        ("u2500_ind_d0_t04", "INDUSTRY", 0, 0.04),
        ("u2500_sub_d2_t06", "SUBINDUSTRY", 2, 0.06),
        ("u2500_cty_d2_t06", "COUNTRY", 2, 0.06),
        ("u2500_ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("u2500_mkt_d4_t08", "MARKET", 4, 0.08),
        ("u2500_ind_d6_t06", "INDUSTRY", 6, 0.06),
    ]

    for tag, neut, dec, trunc in setting_grid:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-{REFINER_VER}b-EUR-M25A-{tag}",
                campaign_id="S3_EUR_M25_SUBRESCUE",
                hypothesis_id="HYP-S3-EUR-M25-TOP2500-ATOM-SUBRESCUE",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_TOP2500_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "value_momentum_region_percentile",
                    }
                    for tid, side, auth, expr in expr_defs_a
                ],
            )
        )
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-{REFINER_VER}b-EUR-M25B-{tag}",
                campaign_id="S3_EUR_M25_SUBRESCUE",
                hypothesis_id="HYP-S3-EUR-M25-TOP2500-ADV-SUBRESCUE",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_TOP2500_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "value_momentum_region_percentile",
                    }
                    for tid, side, auth, expr in expr_defs_b
                ],
            )
        )
    return specs


def build_stage2_mild_param_ladder_specs() -> list[dict[str, Any]]:
    """Stage-2 mild parameter & structure ladder targeting 1.30-1.45+ (POOL_A) on live POOL_B winners."""
    specs: list[dict[str, Any]] = []

    # 1) USA / TOP3000 / price_signal_dl (Alphas=0 FREE! Live seeds: Sh=1.10, 2Y=1.99, Mgn=33.4bp)
    v6 = "ts_backfill(raw_volume_indicator_6, 21)"
    v3 = "ts_backfill(raw_volume_indicator_3, 21)"
    v5 = "ts_backfill(raw_volume_indicator_5, 21)"
    nv2 = "ts_backfill(normalized_volume_indicator_2, 21)"
    usa_exprs: list[tuple[str, str, str, str]] = [
        ("S2-ADM-01-v6-d15", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({v6}, 15), subindustry)"),
        ("S2-ADM-02-v6-d30", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({v6}, 30), subindustry)"),
        ("S2-ADM-03-v6-gz-d10", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_decay_linear({v6}, 10), subindustry)"),
        ("S2-ADM-04-dual-v6-v3", "ADMIN_ORIGINAL", "WL13229", f"group_rank(min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({v3}, 10))), subindustry)"),
        ("S2-TOP-01-sp075-v6", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_decay_linear({v6}, 10), subindustry), 0.75)"),
        ("S2-TOP-02-sp125-v6", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_decay_linear({v6}, 15), subindustry), 1.25)"),
        ("S2-TOP-03-dual-v6-nv2", "TOP100_2026Q4", "ZS59763", f"group_rank(min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({nv2}, 10))), subindustry)"),
        ("S2-TOP-04-hump-v6-v5", "TOP100_2026Q4", "ZS59763", f"hump(group_rank(min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({v5}, 10))), subindustry), hump=0.01)"),
    ]
    for tag, neut, dec, trunc in [
        ("sub_d2_t04", "SUBINDUSTRY", 2, 0.04),
        ("sub_d4_t06", "SUBINDUSTRY", 4, 0.06),
        ("ind_d2_t06", "INDUSTRY", 2, 0.06),
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("crd_d4_t04", "CROWDING", 4, 0.04),
        ("mkt_d6_t06", "MARKET", 6, 0.06),
    ]:
        items = [
            {
                "expression": expr,
                "template_id": f"{tid}_{neut}_d{dec}",
                "source_side": side,
                "author_id": auth,
                "dataset_id": "price_signal_dl",
                "primary_field_id": "raw_volume_indicator_6",
            }
            for tid, side, auth, expr in usa_exprs
        ]
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S2-{REFINER_VER}-USA-PSD-{tag}",
                campaign_id="S2_USA_PRICEDL_MILD",
                hypothesis_id="HYP-S2-USA-PSD-130-145",
                region="USA",
                universe="TOP3000",
                dataset_id="price_signal_dl",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=items,
            )
        )

    # 2) ASI / MINVOL1M / price_signal_dl (Live seeds: 3qGbRKo6 Sh=1.21, 2Y=1.66 -> fix JPN & Robust + climb 1.3-1.5!)
    anv1 = "ts_backfill(normalized_volume_indicator_1, 21)"
    anv2 = "ts_backfill(normalized_volume_indicator_2, 21)"
    art4 = "ts_backfill(raw_trend_indicator_4, 21)"
    asi_exprs: list[tuple[str, str, str, str]] = [
        ("S2-ADM-01-nv1-ci-z66", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({anv1}, 22), 66), group_cartesian_product(country, industry))"),
        ("S2-ADM-02-nv2-ci-dec10", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({anv2}, 10), group_cartesian_product(country, industry))"),
        ("S2-ADM-03-nv1-cs-dec15", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(ts_mean({anv1}, 10), 15), group_cartesian_product(country, subindustry))"),
        ("S2-ADM-04-dual-nv1-nv2", "ADMIN_ORIGINAL", "WL13229", f"group_rank(min(rank(ts_decay_linear({anv1}, 10)), rank(ts_decay_linear({anv2}, 10))), group_cartesian_product(country, industry))"),
        ("S2-TOP-01-sp075-nv2-ci", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_mean({anv2}, 22), group_cartesian_product(country, industry)), 0.75)"),
        ("S2-TOP-02-ctyneut-nv1", "TOP100_2026Q4", "SZ83096", f"group_neutralize(group_rank(ts_zscore(ts_mean({anv1}, 10), 66), subindustry), country)"),
        ("S2-TOP-03-dual-nv2-rt4", "TOP100_2026Q4", "ZS59763", f"group_rank(min(rank(ts_mean({anv2}, 22)), rank(ts_mean({art4}, 22))), group_cartesian_product(country, industry))"),
        ("S2-TOP-04-ctyneut-nv2", "TOP100_2026Q4", "LD22811", f"group_neutralize(group_rank(ts_decay_linear(ts_mean({anv2}, 15), 10), subindustry), country)"),
    ]
    for tag, uni, neut, dec, trunc in [
        ("mv1m_cty_d2_t04", "MINVOL1M", "COUNTRY", 2, 0.04),
        ("mv1m_cty_d6_t06", "MINVOL1M", "COUNTRY", 6, 0.06),
        ("mv1m_ram_d4_t04", "MINVOL1M", "REVERSION_AND_MOMENTUM", 4, 0.04),
        ("mv1m_sub_d4_t06", "MINVOL1M", "SUBINDUSTRY", 4, 0.06),
        ("t500_cty_d4_t06", "TOP500", "COUNTRY", 4, 0.06),
    ]:
        items = [
            {
                "expression": expr,
                "template_id": f"{tid}_{uni}_{neut}_d{dec}",
                "source_side": side,
                "author_id": auth,
                "dataset_id": "price_signal_dl",
                "primary_field_id": "normalized_volume_indicator_1",
            }
            for tid, side, auth, expr in asi_exprs
        ]
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S2-{REFINER_VER}-ASI-PSD-{tag}",
                campaign_id="S2_ASI_PRICEDL_MILD",
                hypothesis_id="HYP-S2-ASI-PSD-JPN-RESCUE",
                region="ASI",
                universe=uni,
                dataset_id="price_signal_dl",
                queue_type="NORMAL",
                settings=_make_settings("ASI", uni, neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=items,
            )
        )

    # 3) DEU / TOP500 / fundamental6 (Live seeds: Sh=0.90-1.05, Mgn=43-59.8bp! 1.8x blank pyramid)
    roa = "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"
    roe = "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_ewq_teqq, 126)))"
    gp = "divide(ts_backfill(fnd6_gpsa, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"
    cf = "divide(ts_backfill(fnd6_chechy, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"
    deu_exprs: list[tuple[str, str, str, str]] = [
        ("S2-ADM-01-roa-rank-m22", "ADMIN_ORIGINAL", "WL13229", f"rank(ts_mean({roa}, 22))"),
        ("S2-ADM-02-roa-ind-gz", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_mean({roa}, 22), industry)"),
        ("S2-ADM-03-dual-roa-gp", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank(ts_mean({roa}, 22)), rank(ts_mean({gp}, 22))), industry)"),
        ("S2-ADM-04-dual-roa-cf", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank(ts_mean({roa}, 22)), rank(ts_mean({cf}, 22))), subindustry)"),
        ("S2-TOP-01-sp075-roa", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_mean({roa}, 22), industry), 0.75)"),
        ("S2-TOP-02-sp125-roa-gp", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(min(rank({roa}), rank({gp})), subindustry), 1.25)"),
        ("S2-TOP-03-dual-roe-cf", "TOP100_2026Q4", "ZS59763", f"group_rank(min(rank(ts_mean({roe}, 22)), rank(ts_mean({cf}, 22))), industry)"),
        ("S2-TOP-04-roa-tsrank126", "TOP100_2026Q4", "LD22811", f"group_zscore(min(rank({roa}), rank(ts_rank({roa}, 126))), industry)"),
    ]
    for tag, neut, dec, trunc in [
        ("sub_d0_t04", "SUBINDUSTRY", 0, 0.04),
        ("ind_d2_t06", "INDUSTRY", 2, 0.06),
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("mkt_d4_t06", "MARKET", 4, 0.06),
    ]:
        items = [
            {
                "expression": expr,
                "template_id": f"{tid}_{neut}_d{dec}",
                "source_side": side,
                "author_id": auth,
                "dataset_id": "fundamental6",
                "primary_field_id": "fnd6_roa",
            }
            for tid, side, auth, expr in deu_exprs
        ]
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S2-{REFINER_VER}-DEU-FND6-{tag}",
                campaign_id="S2_DEU_FND6_MILD",
                hypothesis_id="HYP-S2-DEU-FND6-130-145",
                region="DEU",
                universe="TOP500",
                dataset_id="fundamental6",
                queue_type="NORMAL",
                settings=_make_settings("DEU", "TOP500", neut, decay=dec, truncation=trunc),
                items=items,
            )
        )

    return specs


def build_all_stage23_refiner_specs() -> list[dict[str, Any]]:
    """Return ordered Stage-3 Sub-Universe Rescue specs followed by Stage-2 Mild Param Ladder specs."""
    return build_eur_model25_stage3_subuniverse_rescue_specs() + build_stage2_mild_param_ladder_specs()
