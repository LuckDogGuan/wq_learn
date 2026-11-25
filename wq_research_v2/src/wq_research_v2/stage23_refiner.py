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


def build_eur_model25_stage3_pc_crush_specs() -> list[dict[str, Any]]:
    """Stage-3 PC-Crushing Pack for EUR/TOP2500/model25 (2-Hour Audit #1 pivot).

    Live PC audit proved:
      - Simple INDUSTRY/MARKET val_mom + adv20 hits 0-FAIL Sh=2.49, 2Y=2.40, SC=0.37, BUT PC=0.946 (crowded).
      - Adding REVERSION_AND_MOMENTUM + country*industry (pwWXv5Kq) cut PC 0.946 -> 0.7948 (0-FAIL Sh=1.95, 2Y=2.20).
      - Adding REVERSION_AND_MOMENTUM + min(rank(val_mom), rank(op_eff)) (WjYqLeGo) cut PC -> 0.7815 (0-FAIL Sh=1.63, 2Y=2.28).
    This pack combines ALL FOUR PC-cutting levers to push PC from 0.7815 -> < 0.68 while preserving 0-FAIL POOL_S:
      1) Risk-factor neutralizations: STATISTICAL, SLOW_AND_FAST, CROWDING, FAST, REVERSION_AND_MOMENTUM
      2) Combining country*industry + dual-branch + signed_power(2/0.5) + ts_av_diff(126) + vector_neut(..., returns)
      3) Cross-dataset fusion with ultra-low-crowding EUR model238 SmartHoldings (aCnt=0..2, cov=96.27%!)
    """
    specs: list[dict[str, Any]] = []
    vm = "ts_backfill(value_momentum_region_percentile, 21)"
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    acc = "ts_backfill(mdl25_8v, 21)"
    noa = "ts_backfill(mdl25_bsv421_8v, 126)"
    ci = "group_cartesian_product(country, industry)"
    # Ultra-low-crowding EUR model238 SmartHoldings fields (live-verified cov=96.27%, aCnt=0..2!)
    sh_pref = "ts_backfill(regional_institutional_preference_rank_d1, 21)"
    sh_chg = "ts_backfill(regional_change_in_preference_rank_d1, 21)"
    sh_conc = "ts_backfill(regional_peer_investment_concentration_rank_d1, 21)"
    sh_fit = "ts_backfill(global_screening_factor_alignment_rank_d1, 21)"

    # Pack PC-A: Pure model25 + adv20 PC-crushers (combine country*industry + dual + signed_power + ts_av_diff + vector_neut)
    expr_defs_pca: list[tuple[str, str, str, str]] = [
        ("S3PC-ADM-01-vmoe-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({oe})), {ci}), 0)"),
        ("S3PC-ADM-02-vmoe-ci-sp2", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, signed_power(group_zscore(min(rank({vm}), rank({oe})), {ci}), 2), 0)"),
        ("S3PC-ADM-03-vm-avdiff126-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(ts_av_diff({vm}, 126), {ci}), 0)"),
        ("S3PC-ADM-04-vmoe-vneut-ret", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, vector_neut(group_zscore(min(rank({vm}), rank({oe})), {ci}), rank(ts_mean(returns, 22))), 0)"),
        ("S3PC-TOP-01-vm-ci-sp2", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, signed_power(group_zscore({vm}, {ci}), 2), 0)"),
        ("S3PC-TOP-02-vmav-oe-ci", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank(ts_av_diff({vm}, 126)), rank({oe})), {ci}), 0)"),
        ("S3PC-TOP-03-vm-acc-ci", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({acc})), {ci}), 0)"),
        ("S3PC-TOP-04-oe-noa-ci", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({oe}), rank({noa})), {ci}), 0)"),
    ]

    # Pack PC-B: Cross-dataset model25 x model238 SmartHoldings (aCnt=0..2!) low-PC fusion
    expr_defs_pcb: list[tuple[str, str, str, str]] = [
        ("S3PC-ADM-05-vm-shpref-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({sh_pref})), {ci}), 0)"),
        ("S3PC-ADM-06-vm-shchg-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank({sh_chg})), {ci}), 0)"),
        ("S3PC-ADM-07-oe-shpref-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({oe}), rank({sh_pref})), {ci}), 0)"),
        ("S3PC-ADM-08-vm-shconc-rev", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({vm}), rank(reverse({sh_conc}))), {ci}), 0)"),
        ("S3PC-TOP-05-vm-shfit-sp2", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, signed_power(group_zscore(min(rank({vm}), rank({sh_fit})), {ci}), 2), 0)"),
        ("S3PC-TOP-06-vm-vneut-shconc", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, vector_neut(group_zscore({vm}, {ci}), rank({sh_conc})), 0)"),
        ("S3PC-TOP-07-oe-shchg-ci", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({oe}), rank({sh_chg})), {ci}), 0)"),
        ("S3PC-TOP-08-vm-shpref-sp05", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.35, signed_power(group_zscore(min(rank({vm}), rank({sh_pref})), {ci}), 0.5), 0)"),
    ]

    pc_grid: list[tuple[str, str, int, float]] = [
        ("crd_d4_t06", "CROWDING", 4, 0.06),
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("stat_d4_t06", "STATISTICAL", 4, 0.06),
        ("stat_d6_t08", "STATISTICAL", 6, 0.08),
    ]

    for tag, neut, dec, trunc in pc_grid:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r2-EUR-M25PCA-{tag}",
                campaign_id="S3_EUR_M25_PC_CRUSH",
                hypothesis_id="HYP-S3-EUR-M25-PC-LT068-PURE",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "value_momentum_region_percentile",
                    }
                    for tid, side, auth, expr in expr_defs_pca
                ],
            )
        )
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r2-EUR-M25PCB-{tag}",
                campaign_id="S3_EUR_M25_PC_CRUSH",
                hypothesis_id="HYP-S3-EUR-M25-M238-PC-LT068",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "model25_x_model238",
                    }
                    for tid, side, auth, expr in expr_defs_pcb
                ],
            )
        )
    return specs


def build_usa_pricedl_stage3_rescue_specs() -> list[dict[str, Any]]:
    """Stage-3 Rescue for USA/TOP3000/price_signal_dl POOL_A breakthroughs (2-Hour Audit #1).

    Live breakthroughs:
      - xAl6rxYw: Sh=1.51, 2Y=2.89, Fit=0.69, TO=25.4%, Mgn=4.22bp, PC=0.7490 (ONLY 0.049 from <0.70!)
      - gJrAXo2J: Sh=1.49, 2Y=2.65, Fit=0.74, TO=19.1%, Mgn=4.90bp, PC=0.7576
      - xAl6VmEw: Sh=1.43, 2Y=2.33, Fit=0.64, TO=22.9%, Mgn=3.99bp
    Targets simultaneously:
      1) Cut TO 25% -> 7-12% (ts_mean 10/15/22 + mild decay {2,4,6} + hump) -> Fitness 0.7 -> >1.0 & Margin 4bp -> >10bp
      2) Fix Sub-Universe Sharpe via adv20 large-cap gating (if_else(rank(adv20) > 0.35, ...))
      3) Crush PC from 0.749 -> <0.65 via STATISTICAL / SLOW_AND_FAST / CROWDING / signed_power(2/0.5) / model238 fusion!
    """
    specs: list[dict[str, Any]] = []
    t1 = "ts_backfill(raw_trend_indicator_1, 21)"
    t4 = "ts_backfill(raw_trend_indicator_4, 21)"
    v6 = "ts_backfill(raw_volume_indicator_6, 21)"
    # Ultra-low-crowding USA model238 SmartHoldings (cov=96.74%, aCnt=1..2) for PC-crushing cross-fusion
    us_sh = "ts_backfill(regional_institutional_preference_rank, 21)"
    us_chg = "ts_backfill(regional_change_in_preference_rank, 21)"

    dual_v6_t1 = f"min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({t1}, 10)))"
    dual_v6_t4 = f"min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({t4}, 10)))"

    usa_s3_exprs: list[tuple[str, str, str, str]] = [
        ("S3US-ADM-01-t1-m15-z66-adv", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_rank(ts_zscore(ts_mean({t1}, 15), 66), subindustry), 0)"),
        ("S3US-ADM-02-t1-m22-z126-adv", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_rank(ts_zscore(ts_mean({t1}, 22), 126), subindustry), 0)"),
        ("S3US-ADM-03-dual-v6t1-m15-adv", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_rank(ts_zscore(ts_mean({dual_v6_t1}, 15), 66), subindustry), 0)"),
        ("S3US-ADM-04-dual-v6t4-m15-adv", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_rank(ts_zscore(ts_mean({dual_v6_t4}, 15), 66), subindustry), 0)"),
        ("S3US-TOP-01-t1-m15-sp2-adv", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, signed_power(group_zscore(ts_zscore(ts_mean({t1}, 15), 66), subindustry), 2), 0)"),
        ("S3US-TOP-02-v6t1-hump-adv", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.35, hump(group_rank(ts_zscore(ts_mean({dual_v6_t1}, 10), 66), subindustry), hump=0.01), 0)"),
        ("S3US-TOP-03-t1-x-shpref-adv", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, group_rank(min(rank(ts_zscore(ts_mean({t1}, 15), 66)), rank({us_sh})), subindustry), 0)"),
        ("S3US-TOP-04-v6t1-x-shchg-adv", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.35, group_rank(min(rank(ts_zscore(ts_mean({dual_v6_t1}, 15), 66)), rank({us_chg})), subindustry), 0)"),
    ]

    usa_grid: list[tuple[str, str, int, float]] = [
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("ram_d6_t06", "REVERSION_AND_MOMENTUM", 6, 0.06),
        ("stat_d4_t06", "STATISTICAL", 4, 0.06),
        ("snf_d4_t06", "SLOW_AND_FAST", 4, 0.06),
        ("crd_d4_t06", "CROWDING", 4, 0.06),
        ("sub_d6_t08", "SUBINDUSTRY", 6, 0.08),
    ]

    for tag, neut, dec, trunc in usa_grid:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r2-USA-PSD-{tag}",
                campaign_id="S3_USA_PSD_RESCUE",
                hypothesis_id="HYP-S3-USA-PSD-160-PC-LT068",
                region="USA",
                universe="TOP3000",
                dataset_id="price_signal_dl",
                queue_type="NORMAL",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "price_signal_dl",
                        "primary_field_id": "raw_trend_indicator_1",
                    }
                    for tid, side, auth, expr in usa_s3_exprs
                ],
            )
        )
    return specs


def build_eur_pc_pass_finisher_s3r3_specs() -> list[dict[str, Any]]:
    """Stage-3 r3 Finisher for ALREADY PC_PASS (<0.68) + SC_PASS (<0.30) EUR/model25 monsters!

    Live verified PC_PASS near-miss alphas (literally 0.01-0.02 from ALL-GREEN Useful!):
      - RR53xm10 (val_mom x mdl25_8v accruals, CROWDING d=4): Sh=1.76, 2Y=2.37, Fit=1.05, SC=0.269, PC=0.6599, ONLY sub=0.90/0.91!
      - vRYqEZja (val_mom x mdl25_8v accruals, RAM d=4): Sh=1.71, 2Y=2.33, sub=PASS, lad=PASS, SC=0.296, PC=0.6688, ONLY Fit=0.98/1.00!
      - pwWX2xNb (signed_power(val_mom, 2), RAM d=4): Sh=2.04, 2Y=2.86, Fit=1.47, SC=0.256, PC=0.6806, ONLY sub=1.05/1.06!
      - vRYqEALz (signed_power(val_mom, 2), STAT d=6): Sh=2.24, 2Y=2.71, Fit=1.40, SC=0.204, PC=0.6218, ONLY sub=0.93/1.16!
      - gJrA5OlJ (vector_neut(val_mom, m238_conc), STAT d=4): Sh=2.21, 2Y=2.83, Fit=1.26, SC=0.203, PC=0.6433, ONLY sub=0.90/1.15!
      - 1YG98OpJ (val_mom x op_eff, RAM d=4): Sh=1.62, 2Y=2.06, sub=PASS, lad=PASS, SC=0.325, PC=0.6727, ONLY Fit=0.91/1.00!
    Micro-sweeps adv20 gate {0.40, 0.45, 0.50} + mild decay {3, 4, 5, 6} + truncation {0.06, 0.08}
    on fast CROWDING & REVERSION_AND_MOMENTUM (and 1 safe STATISTICAL batch) -> instant ALL-GREEN Useful!
    """
    specs: list[dict[str, Any]] = []
    vm = "ts_backfill(value_momentum_region_percentile, 21)"
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    acc = "ts_backfill(mdl25_8v, 21)"
    sh_conc = "ts_backfill(regional_peer_investment_concentration_rank_d1, 21)"
    ci = "group_cartesian_product(country, industry)"

    fin_exprs: list[tuple[str, str, str, str]] = [
        ("S3FIN-ADM-01-acc-adv40", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({vm}), rank({acc})), {ci}), 0)"),
        ("S3FIN-ADM-02-acc-adv45", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.45, group_zscore(min(rank({vm}), rank({acc})), {ci}), 0)"),
        ("S3FIN-ADM-03-acc-adv50", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.5, group_zscore(min(rank({vm}), rank({acc})), {ci}), 0)"),
        ("S3FIN-ADM-04-acc-m5-adv40", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(ts_mean(min(rank({vm}), rank({acc})), 5), {ci}), 0)"),
        ("S3FIN-TOP-01-sp2-adv40", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore({vm}, {ci}), 2), 0)"),
        ("S3FIN-TOP-02-sp2-adv45", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.45, signed_power(group_zscore({vm}, {ci}), 2), 0)"),
        ("S3FIN-TOP-03-sp2-adv50", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.5, signed_power(group_zscore({vm}, {ci}), 2), 0)"),
        ("S3FIN-TOP-04-vneut-adv45", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.45, vector_neut(group_zscore({vm}, {ci}), rank({sh_conc})), 0)"),
    ]

    fin_exprs_b: list[tuple[str, str, str, str]] = [
        ("S3FIN-ADM-05-vmoe-adv40", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({vm}), rank({oe})), {ci}), 0)"),
        ("S3FIN-ADM-06-vmoe-adv45", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.45, group_zscore(min(rank({vm}), rank({oe})), {ci}), 0)"),
        ("S3FIN-ADM-07-vmoe-m5-adv35", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(ts_mean(min(rank({vm}), rank({oe})), 5), {ci}), 0)"),
        ("S3FIN-ADM-08-acc-m10-adv35", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(ts_mean(min(rank({vm}), rank({acc})), 10), {ci}), 0)"),
        ("S3FIN-TOP-05-sp2-adv55", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.55, signed_power(group_zscore({vm}, {ci}), 2), 0)"),
        ("S3FIN-TOP-06-vneut-adv50", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.5, vector_neut(group_zscore({vm}, {ci}), rank({sh_conc})), 0)"),
        ("S3FIN-TOP-07-vmoe-ret-adv45", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.45, vector_neut(group_zscore(min(rank({vm}), rank({oe})), {ci}), rank(ts_mean(returns, 22))), 0)"),
        ("S3FIN-TOP-08-acc-sp15-adv40", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore(min(rank({vm}), rank({acc})), {ci}), 1.5), 0)"),
    ]

    fin_grid: list[tuple[str, str, int, float]] = [
        ("crd_d4_t06", "CROWDING", 4, 0.06),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
        ("ram_d5_t06", "REVERSION_AND_MOMENTUM", 5, 0.06),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d3_t06", "CROWDING", 3, 0.06),
        ("stat_d5_t08", "STATISTICAL", 5, 0.08),
    ]

    for tag, neut, dec, trunc in fin_grid:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r3b-EUR-FINA-{tag}",
                campaign_id="S3_EUR_PC_PASS_FINISHER",
                hypothesis_id="HYP-S3-EUR-FIN-0FAIL-PC-LT068",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "value_momentum_region_percentile",
                    }
                    for tid, side, auth, expr in fin_exprs
                ],
            )
        )
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r3b-EUR-FINB-{tag}",
                campaign_id="S3_EUR_PC_PASS_FINISHER",
                hypothesis_id="HYP-S3-EUR-FINB-0FAIL-PC-LT068",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "value_momentum_region_percentile",
                    }
                    for tid, side, auth, expr in fin_exprs_b
                ],
            )
        )
    return specs


def build_usa_pricedl_single_axis_s3r3_specs() -> list[dict[str, Any]]:
    """Stage-3 r3 STRICT SINGLE-AXIS refinement around USA/TOP3000/price_signal_dl winners.

    Postmortem fix from S3-r2-USA-PSD (which changed window + adv20 + decay simultaneously and dropped 1.51 -> 0.77):
    Keep xAl6rxYw (Sh=1.51, 2Y=2.89, PC=0.749) & gJrAXo2J (Sh=1.49, 2Y=2.65, PC=0.758) intact WITHOUT hard adv20 cutoff,
    and sweep ONE mild axis at a time (decay {1,2,3} | window {5,8,10} | hump {0.005,0.01} | signed_power {0.5,1.5}).
    """
    specs: list[dict[str, Any]] = []
    t1 = "ts_backfill(raw_trend_indicator_1, 21)"
    t4 = "ts_backfill(raw_trend_indicator_4, 21)"
    v6 = "ts_backfill(raw_volume_indicator_6, 21)"
    dual_v6_t1 = f"min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({t1}, 10)))"
    dual_v6_t4 = f"min(rank(ts_decay_linear({v6}, 10)), rank(ts_decay_linear({t4}, 10)))"

    single_axis_exprs: list[tuple[str, str, str, str]] = [
        ("S3U1-ADM-01-t1-m5-base", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({t1}, 5), 66), subindustry)"),
        ("S3U1-ADM-02-t1-m8-z66", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({t1}, 8), 66), subindustry)"),
        ("S3U1-ADM-03-t1-m10-z66", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({t1}, 10), 66), subindustry)"),
        ("S3U1-ADM-04-v6t1-m5-base", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({dual_v6_t1}, 5), 66), subindustry)"),
        ("S3U1-TOP-01-t1-hump005", "TOP100_2026Q4", "SZ83096", f"hump(group_rank(ts_zscore(ts_mean({t1}, 5), 66), subindustry), hump=0.005)"),
        ("S3U1-TOP-02-t1-sp15", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_zscore(ts_mean({t1}, 5), 66), subindustry), 1.5)"),
        ("S3U1-TOP-03-v6t1-hump01", "TOP100_2026Q4", "ZS59763", f"hump(group_rank(ts_zscore(ts_mean({dual_v6_t1}, 5), 66), subindustry), hump=0.01)"),
        ("S3U1-TOP-04-v6t4-sp05", "TOP100_2026Q4", "LD22811", f"signed_power(group_zscore(ts_zscore(ts_mean({dual_v6_t4}, 5), 66), subindustry), 0.5)"),
    ]

    for tag, neut, dec, trunc in [
        ("ram_d1_t04", "REVERSION_AND_MOMENTUM", 1, 0.04),
        ("ram_d2_t06", "REVERSION_AND_MOMENTUM", 2, 0.06),
        ("ram_d3_t06", "REVERSION_AND_MOMENTUM", 3, 0.06),
        ("crd_d2_t06", "CROWDING", 2, 0.06),
        ("sub_d2_t06", "SUBINDUSTRY", 2, 0.06),
    ]:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r3b-USA-1AX-{tag}",
                campaign_id="S3_USA_PSD_SINGLE_AXIS",
                hypothesis_id="HYP-S3-USA-PSD-1AX-160-PC-LT068",
                region="USA",
                universe="TOP3000",
                dataset_id="price_signal_dl",
                queue_type="NORMAL",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "price_signal_dl",
                        "primary_field_id": "raw_trend_indicator_1",
                    }
                    for tid, side, auth, expr in single_axis_exprs
                ],
            )
        )
    return specs


def build_eur_model238_stage3_finisher_specs() -> list[dict[str, Any]]:
    """Stage-3 r4 ORTHOGONAL Finisher for EUR/TOP2500/model238 (SmartHoldings, ZERO model25 overlap!).

    Audit #2 verified breakthrough:
      - xAl8adOn (country_relative_investment_rank_d1, CROWDING d=0):
        Sh=1.58, 2Y=1.95, Local SC=0.2836, pairwise corr(RR5QjWYz)=0.2957 (COMPLETELY ORTHOGONAL!),
        ONLY failing LOW_FITNESS(0.77, TO=17.95%) and LOW_SUB_UNIVERSE_SHARPE(0.13)!
      - kq87w6vO (global_screening_factor_alignment x regional_change_in_preference):
        Sh=1.50, PC=0.6349 (ALREADY PC_PASS!).
    Applies our proven EUR Stage-3 blueprint (adv20 gate + mild decay {2,4,6} + truncation {0.06,0.08} +
    light 3d/5d smoothing + same-dataset model238 dual branches) to mint our #2 orthogonal EUR Useful winner!
    """
    specs: list[dict[str, Any]] = []
    cri = "ts_backfill(country_relative_investment_rank_d1, 21)"
    gfa = "ts_backfill(global_screening_factor_alignment_rank_d1, 21)"
    rcp = "ts_backfill(regional_change_in_preference_rank_d1, 21)"
    rpic = "ts_backfill(regional_peer_investment_concentration_rank_d1, 21)"
    rip = "ts_backfill(regional_institutional_preference_rank_d1, 21)"
    ci = "group_cartesian_product(country, industry)"

    m238_exprs: list[tuple[str, str, str, str]] = [
        ("S3M238-ADM-01-cri-adv35-ind", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore({cri}, industry), 0)"),
        ("S3M238-ADM-02-cri-adv45-ind", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.45, group_zscore({cri}, industry), 0)"),
        ("S3M238-ADM-03-cri-d5-adv40-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear({cri}, 5), {ci}), 0)"),
        ("S3M238-ADM-04-cri-gfa-adv40", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({cri}), rank({gfa})), {ci}), 0)"),
        ("S3M238-TOP-01-cri-rcp-adv40", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({cri}), rank({rcp})), {ci}), 0)"),
        ("S3M238-TOP-02-cri-sp15-adv40", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore({cri}, {ci}), 1.5), 0)"),
        ("S3M238-TOP-03-gfa-rcp-adv35", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, group_rank(min(rank(ts_decay_linear({gfa}, 5)), rank(ts_decay_linear({rcp}, 5))), subindustry), 0)"),
        ("S3M238-TOP-04-cri-rip-adv45", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.45, group_zscore(min(rank({cri}), rank({rip})), industry), 0)"),
    ]

    m238_grid: list[tuple[str, str, int, float]] = [
        ("crd_d3_t06", "CROWDING", 3, 0.06),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("ind_d4_t06", "INDUSTRY", 4, 0.06),
        ("cty_d4_t06", "COUNTRY", 4, 0.06),
    ]
    for tag, neut, dec, trunc in m238_grid:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r4-EUR-M238-{tag}",
                campaign_id="S3_EUR_M238_ORTHOGONAL",
                hypothesis_id="HYP-S3-EUR-M238-ORTHO-USEFUL",
                region="EUR",
                universe="TOP2500",
                dataset_id="model238",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model238",
                        "primary_field_id": "country_relative_investment_rank_d1",
                    }
                    for tid, side, auth, expr in m238_exprs
                ],
            )
        )
    return specs


def build_eur_model25_opeff_orthogonal_s3r4_specs() -> list[dict[str, Any]]:
    """Stage-3 r4 NON-val_mom EUR/model25 high-Margin orthogonal pack (operating_efficiency / exclusions / accruals).

    Audit #2 proved all val_mom variants correlate 0.707-0.999 with Useful winner RR5QjWYz (14.10bp).
    Pure operating_efficiency_component_percentile already hit np6JW77q (Sh=1.85, 2Y=1.79, Fit=1.25, Mgn=40.73bp)
    and kq87KjPK (Sh=1.70, 2Y=1.85, Mgn=52.92bp) WITHOUT value_momentum -> high Margin + low corr vs RR5QjWYz!
    """
    specs: list[dict[str, Any]] = []
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    excl = "ts_backfill(exclusions_component_percentile, 21)"
    acc = "ts_backfill(mdl25_8v, 21)"
    noa = "ts_backfill(mdl25_bsv421_8v, 126)"
    cri = "ts_backfill(country_relative_investment_rank_d1, 21)"
    ci = "group_cartesian_product(country, industry)"

    opeff_exprs: list[tuple[str, str, str, str]] = [
        ("S3OE-ADM-01-oe-adv40-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore({oe}, {ci}), 0)"),
        ("S3OE-ADM-02-oe-adv45-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.45, group_zscore({oe}, {ci}), 0)"),
        ("S3OE-ADM-03-oe-acc-adv40-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({oe}), rank({acc})), {ci}), 0)"),
        ("S3OE-ADM-04-oe-noa-adv40-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({oe}), rank({noa})), {ci}), 0)"),
        ("S3OE-TOP-01-oe-sp2-adv40-ci", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore({oe}, {ci}), 2), 0)"),
        ("S3OE-TOP-02-oe-excl-adv40-ci", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({oe}), rank({excl})), {ci}), 0)"),
        ("S3OE-TOP-03-oe-cri-adv40-ci", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.4, group_zscore(min(rank({oe}), rank({cri})), {ci}), 0)"),
        ("S3OE-TOP-04-oe-vret-adv40-ci", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.4, vector_neut(group_zscore({oe}, {ci}), rank(ts_mean(returns, 22))), 0)"),
    ]

    for tag, neut, dec, trunc in [
        ("crd_d4_t06", "CROWDING", 4, 0.06),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
        ("ram_d4_t06", "REVERSION_AND_MOMENTUM", 4, 0.06),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
    ]:
        specs.append(
            _pack_items_into_spec(
                batch_id=f"S3-r4-EUR-OPEFF-{tag}",
                campaign_id="S3_EUR_M25_OPEFF_ORTHO",
                hypothesis_id="HYP-S3-EUR-OPEFF-HIGHMGN-ORTHO",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=[
                    {
                        "expression": expr,
                        "template_id": f"{tid}_{neut}_d{dec}",
                        "source_side": side,
                        "author_id": auth,
                        "dataset_id": "model25",
                        "primary_field_id": "operating_efficiency_component_percentile",
                    }
                    for tid, side, auth, expr in opeff_exprs
                ],
            )
        )
    return specs


def build_all_stage23_refiner_specs() -> list[dict[str, Any]]:
    """Return ordered Stage-3 r4 Orthogonal Winners -> r3 Finishers -> r2 PC-Crush -> r1b Sub-Uni -> Stage-2."""
    return (
        build_eur_model238_stage3_finisher_specs()
        + build_eur_model25_opeff_orthogonal_s3r4_specs()
        + build_eur_pc_pass_finisher_s3r3_specs()
        + build_usa_pricedl_single_axis_s3r3_specs()
        + build_eur_model25_stage3_pc_crush_specs()
        + build_eur_model25_stage3_subuniverse_rescue_specs()
        + build_stage2_mild_param_ladder_specs()
    )
