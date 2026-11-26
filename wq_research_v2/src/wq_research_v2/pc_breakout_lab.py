"""First-Principles Multi-Angle PC-Breakout Laboratory (S3-r10b-PCLAB, 100% Live Gold-81 Verified).

Breaks out of repetitive `group_rank(ts_decay_linear(min(...)))` templates by systematically
testing 6 orthogonal mathematical mechanisms to lower Prod Correlation (PC) while compressing
noise and amplifying payoff (Margin & Sharpe), strictly obeying:
  - D1-Only (delay == 1), RA-Primary (separated from PPA)
  - Decision #3 (NO +, *, add, multiply, trade_when)
  - Exact 81 live-verified REGULAR Gold operators (zero inaccessible ops like clamp/tanh/keep/group_median/vector_proj!)
  - 50:50 ADMIN_ORIGINAL : TOP100_2026Q4 source balance

Six First-Principles Angles (160 FULL = 112 USA + 48 EUR):
  Angle A (Dist Reshape): quantile(cauchy/gaussian), signed_power(0.5), normalize, tail(0.15/0.20/0.25)
  Angle B (Asymmetric/Robust): scale(longscale, shortscale), group_scale, group_neutralize / group_std_dev + winsorize
  Angle C (Time-Series/Event): ts_quantile(252), ts_rank(252), ts_av_diff(126), ts_scale(252), ts_ir(66),
                               last_diff_value(66), ts_target_tvr_decay(lambda_max=0.9), ts_target_tvr_hump
  Angle D (Geometric Ortho): ts_regression(rettype=0), vector_neut(adv20/cap/vol66/ret22) + tail/cauchy
  Angle E (Arithmetic/Cross-DS): max(rank,rank), divide(rank, subtract(2, rank)), subtract(rank, rank(reverse)),
                                 3-dataset nesting (model31 x model30 PC=0.676 x model28 FREE)
  Angle F (Dynamic Bucket & EUR): Wang Ge fundamental/credit bucket grouping + EUR/model25 & EUR/model77
                                  continuous liquidity tilt (no hard adv20 cliff!)
"""
from __future__ import annotations

from typing import Any


def _make_settings(
    region: str,
    universe: str,
    neutralization: str,
    *,
    decay: int,
    truncation: float,
    max_trade: str = "OFF",
) -> dict[str, Any]:
    return {
        "instrumentType": "EQUITY",
        "region": region,
        "universe": universe,
        "delay": 1,
        "decay": int(decay),
        "neutralization": neutralization,
        "truncation": float(truncation),
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "maxTrade": max_trade,
        "language": "FASTEXPR",
        "visualization": False,
    }


def _pack(
    *,
    batch_id: str,
    campaign_id: str,
    hypothesis_id: str,
    region: str,
    universe: str,
    dataset_id: str,
    settings: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "campaign_id": campaign_id,
        "hypothesis_id": hypothesis_id,
        "region": region,
        "universe": universe,
        "dataset_id": dataset_id,
        "queue_type": "NORMAL",
        "settings": settings,
        "items": items,
    }


def _build_items(
    exprs: list[tuple[str, str, str, str]],
    *,
    dataset_id: str,
    primary_field_id: str,
    tag_suffix: str,
) -> list[dict[str, Any]]:
    return [
        {
            "expression": expr,
            "template_id": f"{tid}_{tag_suffix}",
            "source_side": side,
            "author_id": auth,
            "dataset_id": dataset_id,
            "primary_field_id": primary_field_id,
        }
        for tid, side, auth, expr in exprs
    ]


def build_usa_pc_angle_ab_dist_specs() -> list[dict[str, Any]]:
    """Pack 1 (24 FULL): Angles A & B — Nonlinear Distribution Reshape, Asymmetric Scale & Winsorized Group-Neutralized Std."""
    at = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    acc = "ts_backfill(mdl31_ab1_acc_prior_qtr, 21)"
    core = f"ts_decay_linear(min(rank({at}), rank({acc})), 22)"
    gr = f"group_rank({core}, subindustry)"
    gz = f"group_zscore({core}, subindustry)"

    exprs: list[tuple[str, str, str, str]] = [
        # Angle A: Heavy-tail amplification, Gaussian probit & tail concentration (100% live Gold-81!)
        ("PC10B-A1-cauchy-win", "ADMIN_ORIGINAL", "WL13229", f'winsorize(quantile({gr}, driver="cauchy", sigma=1.0), std=3)'),
        ("PC10B-A2-tail20-80", "ADMIN_ORIGINAL", "WL13229", f"tail({gr}, lower=0.2, upper=0.8, newval=0.5)"),
        ("PC10B-A3-tail15-85", "ADMIN_ORIGINAL", "WL13229", f"tail({gr}, lower=0.15, upper=0.85, newval=0.5)"),
        ("PC10B-A4-gauss-win", "ADMIN_ORIGINAL", "WL13229", f'winsorize(quantile({gr}, driver="gaussian", sigma=1.0), std=3)'),
        ("PC10B-A5-sp05-gz", "TOP100_2026Q4", "SZ83096", f"signed_power({gz}, 0.5)"),
        ("PC10B-A6-norm-tail20", "TOP100_2026Q4", "SZ83096", f"normalize(tail({gr}, lower=0.2, upper=0.8, newval=0.5), useStd=true, limit=0.0)"),
        # Angle B: Asymmetric long/short scaling & Group-neutralized std standardization
        ("PC10B-B1-asym-short", "TOP100_2026Q4", "ZS59763", f"scale(subtract({gr}, 0.5), scale=1, longscale=0.6, shortscale=1.4)"),
        ("PC10B-B2-gneut-std", "TOP100_2026Q4", "JX79797", f"winsorize(divide(group_neutralize({core}, subindustry), group_std_dev({core}, subindustry)), std=3)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10b-USA-PC-DIST-{tag}",
                campaign_id="S3_PCLAB_USA_DIST",
                hypothesis_id="HYP-PCLAB-AB-NONLINEAR-ASYM-GOLD81",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_last_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_usa_pc_angle_c_time_specs() -> list[dict[str, Any]]:
    """Pack 2 (24 FULL): Angle C — Time-Series Self-Comparison, `last_diff_value` Event Isolation, Adaptive TVR Control."""
    at = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    acc = "ts_backfill(mdl31_ab1_acc_prior_qtr, 21)"
    base_min = f"min(rank({at}), rank({acc}))"
    core = f"ts_decay_linear({base_min}, 22)"
    gr = f"group_rank({core}, subindustry)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC10B-C1-tsq252", "ADMIN_ORIGINAL", "WL13229", f'group_rank(min(rank(ts_quantile({at}, 252, driver="gaussian")), rank(ts_quantile({acc}, 252, driver="gaussian"))), subindustry)'),
        ("PC10B-C2-tsrank252", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank(ts_rank({at}, 252)), rank(ts_rank({acc}, 252))), 22), subindustry)"),
        ("PC10B-C3-tsavdiff126", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank(ts_av_diff({at}, 126)), rank(ts_av_diff({acc}, 126))), 22), subindustry)"),
        ("PC10B-C4-lastdiff66", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank(last_diff_value({at}, 66)), rank(last_diff_value({acc}, 66))), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10B-C5-tsscale252", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank(ts_scale({at}, 252)), rank(ts_scale({acc}, 252))), 22), subindustry)"),
        ("PC10B-C6-tsir66", "TOP100_2026Q4", "ZS59763", f"group_rank(min(rank(ts_ir({at}, 66)), rank(ts_ir({acc}, 66))), subindustry)"),
        ("PC10B-C7-tvr-decay", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(tail({gr}, lower=0.25, upper=0.75, newval=0.5), lambda_min=0, lambda_max=0.9, target_tvr=0.04)"),
        ("PC10B-C8-tvr-hump", "TOP100_2026Q4", "LW67640", f"ts_target_tvr_hump(tail({gr}, lower=0.25, upper=0.75, newval=0.5), lambda_min=0, lambda_max=0.9, target_tvr=0.04)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("ram_d2_t06", "REVERSION_AND_MOMENTUM", 2, 0.06),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("stat_d3_t06", "STATISTICAL", 3, 0.06),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10b-USA-PC-TIME-{tag}",
                campaign_id="S3_PCLAB_USA_TIME",
                hypothesis_id="HYP-PCLAB-C-TIMESERIES-EVENT-TVR",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_last_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_usa_pc_angle_d_ortho_specs() -> list[dict[str, Any]]:
    """Pack 3 (32 FULL): Angle D — Geometric Orthogonalization (`ts_regression`, `vector_neut` vs ret/adv20/cap/vol66) + STATISTICAL Useful #2."""
    at_lq = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    acc_pq = "ts_backfill(mdl31_ab1_acc_prior_qtr, 21)"
    core = f"ts_decay_linear(min(rank({at_lq}), rank({acc_pq})), 22)"
    gr = f"group_rank({core}, subindustry)"
    gr_pq = f"group_rank(ts_decay_linear({at_pq}, 10), subindustry)"

    exprs: list[tuple[str, str, str, str]] = [
        # Direct strike on orthogonal STATISTICAL cluster (1YGbjW96/qM5r0dxj corr=0.52 vs e71w5Qrl!)
        ("PC10B-D1-vret-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut({gr}, rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"),
        ("PC10B-D2-vret-pq-tail", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut({gr_pq}, rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"),
        ("PC10B-D3-vret-cauchy", "ADMIN_ORIGINAL", "WL13229", f'winsorize(quantile(vector_neut({gr}, rank(ts_mean(returns, 22))), driver="cauchy", sigma=1.0), std=3)'),
        ("PC10B-D4-tsreg-ret126", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_regression({core}, ts_mean(returns, 22), 126, lag=0, rettype=0), subindustry)"),
        ("PC10B-D5-tsreg-vol126", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_regression({core}, ts_std_dev(returns, 22), 126, lag=0, rettype=0), subindustry)"),
        ("PC10B-D6-vneut-adv20", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut({gr}, rank(adv20)), lower=-0.2, upper=0.2, newval=0)"),
        ("PC10B-D7-vneut-cap", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut({gr}, rank(cap)), lower=-0.25, upper=0.25, newval=0)"),
        ("PC10B-D8-vneut-vol66", "TOP100_2026Q4", "LD22811", f"tail(vector_neut({gr}, rank(ts_std_dev(returns, 66))), lower=-0.25, upper=0.25, newval=0)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("stat_d3_t06", "STATISTICAL", 3, 0.06),
        ("stat_d5_t08", "STATISTICAL", 5, 0.08),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10b-USA-PC-ORTHO-{tag}",
                campaign_id="S3_PCLAB_USA_ORTHO",
                hypothesis_id="HYP-PCLAB-D-ORTHO-REGRESSION-USEFUL2",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_last_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_usa_pc_angle_ef_nest_specs() -> list[dict[str, Any]]:
    """Pack 4 (32 FULL): Angles E & F — Already completed 8/8 clean on S3-r10-USA-PC-NEST-* (kept for ledger dedup)."""
    at = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    acc = "ts_backfill(mdl31_ab1_acc_prior_qtr, 21)"
    erq = "ts_backfill(mdl31_ab1_erq_raw_prior_qtr, 21)"
    eps1 = "ts_backfill(star_eps_surprise_prediction_fq1, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"
    pd_pct = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_pd_pct, 21)"
    core = f"ts_decay_linear(min(rank({at}), rank({acc})), 22)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC10-E1-max-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(max(rank({at}), rank({acc})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10-E2-div-synergy", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(divide(rank({at}), subtract(2, rank({acc}))), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10-E3-sub-rev-sum", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(subtract(rank({at}), rank(reverse({acc}))), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10-E4-3ds-m31-m30", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank({core}), rank({eps1})), 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10-E5-3ds-m31-m28", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear(divide(rank({core}), subtract(2, rank({dtd}))), 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10-E6-gscale-3ds", "TOP100_2026Q4", "JR23144", f"group_scale(ts_decay_linear(min(rank({at}), min(rank({acc}), rank({eps1}))), 22), subindustry)"),
        ("PC10-F1-bkt-erq-sec", "TOP100_2026Q4", "ZS59763", f'tail(group_rank({core}, densify(group_cartesian_product(sector, bucket(rank({erq}), range="0,1,0.2")))), lower=0.25, upper=0.75, newval=0.5)'),
        ("PC10-F2-bkt-m28pd", "TOP100_2026Q4", "ZS59763", f'tail(group_rank({core}, densify(group_cartesian_product(sector, bucket(rank({pd_pct}), range="0,1,0.2")))), lower=0.25, upper=0.75, newval=0.5)'),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("stat_d3_t06", "STATISTICAL", 3, 0.06),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10-USA-PC-NEST-{tag}",
                campaign_id="S3_PCLAB_USA_NEST",
                hypothesis_id="HYP-PCLAB-EF-CROSSDS-BUCKET-COMBINATORS",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_last_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_eur_pc_m25_breakout_specs() -> list[dict[str, Any]]:
    """Pack 5 (24 FULL): EUR/TOP2500/model25 PC-Breakout (L6 tail25/20 + cauchy + non-val_mom OpEff x model77, 100% Gold-81)."""
    vm = "ts_backfill(value_momentum_region_percentile, 21)"
    acc = "ts_backfill(mdl25_8v, 21)"
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    emm = "reverse(ts_backfill(mdl177_emm_fc_rev3y2_alt, 21))"
    ci = "group_cartesian_product(country, industry)"

    vm_acc_gr = f"group_rank(min(rank({vm}), rank({acc})), {ci})"
    oe_emm_gr = f"group_rank(min(rank({oe}), rank({emm})), {ci})"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC10B-E25-1-tail25", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, tail({vm_acc_gr}, lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC10B-E25-2-cauchy", "ADMIN_ORIGINAL", "WL13229", f'if_else(rank(adv20) > 0.4, winsorize(quantile({vm_acc_gr}, driver="cauchy", sigma=1.0), std=3), 0)'),
        ("PC10B-E25-3-tail20", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, tail({vm_acc_gr}, lower=0.2, upper=0.8, newval=0.5), 0)"),
        ("PC10B-E25-4-oe-emm-tail", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, tail({oe_emm_gr}, lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC10B-E25-5-oe-emm-div", "TOP100_2026Q4", "SZ83096", f"divide(subtract(group_rank(min(rank({oe}), rank({emm})), {ci}), 0.5), subtract(1.6, rank(adv20)))"),
        ("PC10B-E25-6-oe-tsq252", "TOP100_2026Q4", "ZS59763", f'if_else(rank(adv20) > 0.35, group_zscore(ts_quantile({oe}, 252, driver="gaussian"), {ci}), 0)'),
        ("PC10B-E25-7-asym-vm", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.4, scale(subtract({vm_acc_gr}, 0.5), scale=1, longscale=1.4, shortscale=0.6), 0)"),
        ("PC10B-E25-8-tvr-hump", "TOP100_2026Q4", "LW67640", f"ts_target_tvr_hump(if_else(rank(adv20) > 0.4, tail({vm_acc_gr}, lower=0.25, upper=0.75, newval=0.5), 0), lambda_min=0, lambda_max=0.9, target_tvr=0.05)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10b-EUR-PC-M25-{tag}",
                campaign_id="S3_PCLAB_EUR_M25",
                hypothesis_id="HYP-PCLAB-EUR-M25-NONLINEAR-ORTHO",
                region="EUR",
                universe="TOP2500",
                dataset_id="model25",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model25", primary_field_id="operating_efficiency_component_percentile", tag_suffix=tag),
            )
        )
    return specs


def build_eur_pc_m77_breakout_specs() -> list[dict[str, Any]]:
    """Pack 6 (24 FULL): EUR/TOP2500/model77 Continuous Liquidity Tilt + Non-Standard PC-Breakout (100% Gold-81)."""
    dvm = "reverse(ts_backfill(mdl177_qvm_dvm_qvaeur_alt, 21))"
    est = "reverse(ts_backfill(mdl177_qvm_estrevrank_qmaeur_alt, 21))"
    emm = "reverse(ts_backfill(mdl177_emm_fc_rev3y2_alt, 21))"
    ci = "group_cartesian_product(country, industry)"
    cty_liq = 'densify(group_cartesian_product(country, bucket(rank(adv20), range="0,1,0.2")))'

    dvm_emm = f"min(rank({dvm}), rank({emm}))"
    est_emm = f"min(rank({est}), rank({emm}))"

    exprs: list[tuple[str, str, str, str]] = [
        # Continuous liquidity tilt: amplifies TOP1200/800 without zeroing out mid-caps!
        ("PC10B-E77-1-dvm-liqtilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({dvm}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC10B-E77-2-est-liqtilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({est}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC10B-E77-3-dvm-emm-tilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({dvm_emm}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC10B-E77-4-est-emm-tail", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(tail(group_rank({est_emm}, {ci}), lower=0.25, upper=0.75, newval=0.5), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC10B-E77-5-cty-liqbkt", "TOP100_2026Q4", "ZS59763", f"tail(group_rank({dvm_emm}, {cty_liq}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC10B-E77-6-cauchy-tilt", "TOP100_2026Q4", "SZ83096", f'divide(winsorize(quantile(group_rank({dvm_emm}, {ci}), driver="cauchy", sigma=1.0), std=3), subtract(1.5, rank(adv20)))'),
        ("PC10B-E77-7-tsq252-tilt", "TOP100_2026Q4", "JX79797", f'divide(subtract(group_rank(ts_quantile({dvm}, 252, driver="gaussian"), {ci}), 0.5), subtract(1.5, rank(adv20)))'),
        ("PC10B-E77-8-gnz-tilt", "TOP100_2026Q4", "JX79797", f"divide(winsorize(divide(group_neutralize({dvm_emm}, {ci}), group_std_dev({dvm_emm}, {ci})), std=3), subtract(1.5, rank(adv20)))"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r10b-EUR-PC-M77-{tag}",
                campaign_id="S3_PCLAB_EUR_M77",
                hypothesis_id="HYP-PCLAB-EUR-M77-LIQTILT-ORTHO-USEFUL2",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model77", primary_field_id="mdl177_qvm_dvm_qvaeur_alt", tag_suffix=tag),
            )
        )
    return specs


def build_ortho_pc_breakout_s3r11_specs() -> list[dict[str, Any]]:
    """S3-r11 Post-e71w5Qrl-OS Orthogonal PC-Breakout Strike (12 batches = 96 FULL: 64 USA + 32 Fast EUR).

    Directly applies S3-r10b 6-angle quantitative proof (after e71w5Qrl entered live OS/Prod!):
      1) S3-r10b proved any single-dataset RAM tweak of ass_tvr_last_qtr x acc_prior_qtr now collides at
         PC == corr(e71w5Qrl) = 0.84-0.87.
      2) Three mechanisms BROKE e71w5Qrl & PC:
         - Cross-dataset model31 x model30 (N1KmLbEg): PC=0.6654 < 0.70, corr(e71)=0.6655 < 0.68, 2Y=2.82!
         - STATISTICAL + tail(vector_neut(..., returns)) (1YGbl1EQ/legO522N): 0-FAIL, corr(e71)=0.440!
         - divide(rank(A), subtract(2, rank(B))) & quantile(cauchy): cut corr by -0.120 vs linear decay!
      3) EUR-M25/M77 stalls traced to ts_quantile(252), quantile(cauchy) & ts_target_tvr_hump(if_else) on EUR ->
         removed for fast, zero-stall EUR continuous liquidity tilt!
    """
    specs: list[dict[str, Any]] = []

    # --- USA Pack A (32 FULL): 100% ZERO ass_tvr_last_qtr/prior_qtr (fully detached from e71w5Qrl!) ---
    eps1 = "ts_backfill(star_eps_surprise_prediction_fq1, 21)"
    eps2 = "ts_backfill(star_eps_surprise_prediction_fq2, 21)"
    epsy2 = "ts_backfill(star_eps_surprise_prediction_fy2, 21)"
    acc_pq = "ts_backfill(mdl31_ab1_acc_prior_qtr, 21)"
    roe_t4 = "ts_backfill(mdl31_ab1_roe_pct_t4q, 21)"
    gm_lq = "ts_backfill(mdl31_ab1_gm_pct_last_qtr, 21)"
    excl_c1 = "ts_backfill(mdl31_ab1_exclusions_chg_1_qtr, 21)"
    avol = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_asset_volatility_pct, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"
    trd1 = "ts_zscore(ts_mean(ts_backfill(raw_trend_indicator_1, 21), 5), 66)"
    vol6 = "ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10)"

    usa_detach_exprs: list[tuple[str, str, str, str]] = [
        ("PC11-U1-eps1-acc-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank({eps1}), rank({acc_pq})), 15), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-U2-eps1-roe-div", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(divide(rank({eps1}), subtract(2, rank({roe_t4}))), 15), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-U3-eps1-eps2-cauchy", "ADMIN_ORIGINAL", "WL13229", f'winsorize(quantile(group_rank(ts_decay_linear(min(rank({eps1}), rank({eps2})), 10), subindustry), driver="cauchy", sigma=1.0), std=3)'),
        ("PC11-U4-eps1-dtd-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank({eps1}), rank({dtd})), 15), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-U5-eps1-trd1-sub", "TOP100_2026Q4", "SZ83096", f"group_rank(subtract(rank(ts_decay_linear({eps1}, 10)), rank(reverse({trd1}))), subindustry)"),
        ("PC11-U6-eps2-vol6-tail", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(min(rank(ts_decay_linear({eps2}, 10)), rank({vol6})), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-U7-acc-gm-avol", "TOP100_2026Q4", "JX79797", f"tail(vector_neut(group_rank(ts_decay_linear(min(rank({acc_pq}), rank({gm_lq})), 22), subindustry), rank({avol})), lower=-0.25, upper=0.25, newval=0)"),
        ("PC11-U8-epsy2-excl-vret", "TOP100_2026Q4", "LD22811", f"tail(vector_neut(group_rank(ts_decay_linear(min(rank({epsy2}), rank({excl_c1})), 10), subindustry), rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"),
    ]

    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("stat_d3_t06", "STATISTICAL", 3, 0.06),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r11-USA-DETACH-{tag}",
                campaign_id="S3_PCLAB_USA_DETACH",
                hypothesis_id="HYP-PC11-ZERO-ASSTVR-ORTHO-USEFUL2",
                region="USA",
                universe="TOP3000",
                dataset_id="model30",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(usa_detach_exprs, dataset_id="model30", primary_field_id="star_eps_surprise_prediction_fq1", tag_suffix=tag),
            )
        )

    # --- USA Pack B (32 FULL): Upgrade Proven PC=0.6654 (model31 x model30) & corr=0.44 (STATISTICAL+vret)! ---
    at_lq = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    at_py = "ts_backfill(mdl31_ab1_ass_tvr_prior_y, 21)"

    usa_cross_exprs: list[tuple[str, str, str, str]] = [
        ("PC11-X1-atpq-eps1-d22", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({at_pq}), rank({eps1})), 22), subindustry)"),
        ("PC11-X2-atpq-eps1-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank({at_pq}), rank({eps1})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-X3-atlq-eps1-hump", "ADMIN_ORIGINAL", "WL13229", f"hump(group_rank(ts_decay_linear(min(rank({at_lq}), rank({eps1})), 22), subindustry), hump=0.01)"),
        ("PC11-X4-atpy-eps1-tail25", "ADMIN_ORIGINAL", "WL13229", f"tail(group_rank(ts_decay_linear(min(rank({at_py}), rank({eps1})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-X5-atpq-eps1-div", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear(divide(rank({at_pq}), subtract(2, rank({eps1}))), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-X6-atpq-eps2-tail", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear(min(rank({at_pq}), rank({eps2})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC11-X7-atpq-eps1-vret", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut(group_rank(ts_decay_linear(min(rank({at_pq}), rank({eps1})), 15), subindustry), rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"),
        ("PC11-X8-atpq-dtd-vret", "TOP100_2026Q4", "LD22811", f"tail(vector_neut(group_rank(ts_decay_linear(min(rank({at_pq}), rank({dtd})), 15), subindustry), rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)"),
    ]

    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("stat_d3_t06", "STATISTICAL", 3, 0.06),
        ("stat_d5_t08", "STATISTICAL", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r11-USA-CROSS-{tag}",
                campaign_id="S3_PCLAB_USA_CROSS_M31M30",
                hypothesis_id="HYP-PC11-M31XM30-PC065-FIT105",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(usa_cross_exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_prior_qtr", tag_suffix=tag),
            )
        )

    # --- EUR Pack C (32 FULL): Fast, Zero-Stall Continuous Liquidity Tilt (NO ts_quantile / cauchy / tvr_hump!) ---
    dvm = "reverse(ts_backfill(mdl177_qvm_dvm_qvaeur_alt, 21))"
    est = "reverse(ts_backfill(mdl177_qvm_estrevrank_qmaeur_alt, 21))"
    emm = "reverse(ts_backfill(mdl177_emm_fc_rev3y2_alt, 21))"
    ev = "reverse(ts_backfill(mdl177_qvm_ev_qvaeur_alt, 21))"
    oe = "ts_backfill(operating_efficiency_component_percentile, 21)"
    ci = "group_cartesian_product(country, industry)"

    dvm_emm = f"min(rank({dvm}), rank({emm}))"
    est_emm = f"min(rank({est}), rank({emm}))"
    oe_emm = f"min(rank({oe}), rank({emm}))"

    eur_fast_exprs: list[tuple[str, str, str, str]] = [
        ("PC11-E1-dvm-liqtilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({dvm}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E2-est-liqtilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({est}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E3-dvm-emm-tilt", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(group_rank({dvm_emm}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E4-dvm-emm-tail", "ADMIN_ORIGINAL", "WL13229", f"divide(subtract(tail(group_rank({dvm_emm}, {ci}), lower=0.25, upper=0.75, newval=0.5), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E5-est-emm-tail", "TOP100_2026Q4", "SZ83096", f"divide(subtract(tail(group_rank({est_emm}, {ci}), lower=0.25, upper=0.75, newval=0.5), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E6-oe-emm-tilt", "TOP100_2026Q4", "SZ83096", f"divide(subtract(tail(group_rank({oe_emm}, {ci}), lower=0.25, upper=0.75, newval=0.5), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E7-ev-emm-sp15", "TOP100_2026Q4", "ZS59763", f"divide(signed_power(subtract(group_rank(min(rank({ev}), rank({emm})), {ci}), 0.5), 1.5), subtract(1.5, rank(adv20)))"),
        ("PC11-E8-dvm-asym-tilt", "TOP100_2026Q4", "LD22811", f"divide(scale(subtract(group_rank({dvm_emm}, {ci}), 0.5), scale=1, longscale=1.4, shortscale=0.6), subtract(1.5, rank(adv20)))"),
    ]

    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r11-EUR-FASTTILT-{tag}",
                campaign_id="S3_PCLAB_EUR_FAST_LIQTILT",
                hypothesis_id="HYP-PC11-EUR-FAST-LIQTILT-USEFUL2",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_fast_exprs, dataset_id="model77", primary_field_id="mdl177_qvm_dvm_qvaeur_alt", tag_suffix=tag),
            )
        )

    return specs


def build_pc_breakout_lab_s3r10_specs() -> list[dict[str, Any]]:
    """Return ordered S3-r11 Post-OS Orthogonal Breakout (96 FULL) + S3-r10b 6-Angle Lab (160 FULL)."""
    return (
        build_ortho_pc_breakout_s3r11_specs()
        + build_usa_pc_angle_ab_dist_specs()
        + build_usa_pc_angle_c_time_specs()
        + build_usa_pc_angle_d_ortho_specs()
        + build_usa_pc_angle_ef_nest_specs()
        + build_eur_pc_m25_breakout_specs()
        + build_eur_pc_m77_breakout_specs()
    )
