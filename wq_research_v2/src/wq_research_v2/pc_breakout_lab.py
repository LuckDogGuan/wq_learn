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
    queue_type: str = "NORMAL",
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "campaign_id": campaign_id,
        "hypothesis_id": hypothesis_id,
        "region": region,
        "universe": universe,
        "dataset_id": dataset_id,
        "queue_type": queue_type,
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


def build_usa_stat_3ds_pc_finisher_s3r12_specs() -> list[dict[str, Any]]:
    """S3-r12 Laser-Focused Post-95-OS Orthogonal Useful Finisher (6 USA batches = 48 FULL).

    Directly capitalizes on S3-r11's verified monotonic breakthrough against live 95-OS pool:
      - blxZz93p (model31 x model30 eps1, STATISTICAL d=5): 95-OS SC=0.4111, PC=0.7348, Sh=1.65, 2Y=2.02, Fit=0.96!
        (d=3->d=5 moved Fit 0.90->0.96, PC 0.7444->0.7348, SC 0.4182->0.4111, Margin 5.80->6.81bp simultaneously!)
      - qM5rGXZv (model31 x model28 FREE dtd, STATISTICAL d=5): 95-OS SC=0.3913, PC=0.7593, Sh=1.67, 2Y=2.49, Fit=0.98!
    Combines 3-dataset nesting (model31 x model30 x model28 FREE), longer 22d/33d post-min smoothing + hump(0.01) +
    ts_target_tvr_decay + divide() synergy + signed_power(1.5) + industry grouping + d={5,6} to push Fit 0.96->1.10+,
    Margin 6.8->10+bp, and PC 0.7348 -> < 0.68 at 95-OS SC < 0.42!
    """
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    eps1 = "ts_backfill(star_eps_surprise_prediction_fq1, 21)"
    eps2 = "ts_backfill(star_eps_surprise_prediction_fq2, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"
    ret22 = "rank(ts_mean(returns, 22))"

    m31_m30_d22 = f"ts_decay_linear(min(rank({at_pq}), rank({eps1})), 22)"
    m31_m30_d33 = f"ts_decay_linear(min(rank({at_pq}), rank({eps1})), 33)"
    m31_m30_m28 = f"ts_decay_linear(min(rank({at_pq}), min(rank({eps1}), rank({dtd}))), 22)"
    m31_m30_div = f"ts_decay_linear(divide(rank({at_pq}), subtract(2, rank({eps1}))), 22)"
    m31_m30_e2 = f"ts_decay_linear(min(rank({at_pq}), rank({eps2})), 22)"
    m31_m30_dtd_div = f"ts_decay_linear(divide(rank(min(rank({at_pq}), rank({eps1}))), subtract(2, rank({dtd}))), 22)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC12-S1-3ds-m31m30m28-vret", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank({m31_m30_m28}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC12-S2-3ds-div-dtd-vret", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank({m31_m30_dtd_div}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC12-S3-m31m30-d22-hump", "ADMIN_ORIGINAL", "WL13229", f"hump(tail(vector_neut(group_rank({m31_m30_d22}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0), hump=0.01)"),
        ("PC12-S4-m31m30-d33-vret", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank({m31_m30_d33}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC12-S5-m31m30-div-vret", "TOP100_2026Q4", "SZ83096", f"tail(vector_neut(group_rank({m31_m30_div}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC12-S6-m31m30-sp15-vret", "TOP100_2026Q4", "SZ83096", f"signed_power(vector_neut(group_rank({m31_m30_d22}, subindustry), {ret22}), 1.5)"),
        ("PC12-S7-m31m30-ind-vret", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut(group_rank({m31_m30_d22}, industry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC12-S8-m31m30-tvrdec", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(tail(vector_neut(group_rank({m31_m30_e2}, subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0), lambda_min=0, lambda_max=0.9, target_tvr=0.06)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("stat_d5_t08", "STATISTICAL", 5, 0.08),
        ("stat_d6_t08", "STATISTICAL", 6, 0.08),
        ("stat_d6_t06", "STATISTICAL", 6, 0.06),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r12-USA-STAT3DS-{tag}",
                campaign_id="S3_PCLAB_USA_STAT_3DS_FINISHER",
                hypothesis_id="HYP-PC12-POST95OS-ORTHO-USEFUL96",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_prior_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_usa_e5m_highmgn_s3r13_specs() -> list[dict[str, Any]]:
    """S3-r13 High-Margin Upgrade for Orthogonal 3-Dataset USA Useful Champion E5mWLW0J (Sh=1.83, SC=0.344, Mgn=7.99bp).

    E5mWLW0J passed official /check 0-FAIL with ultra-low 95-OS SC=0.3443 and PC=0.7531 PASS (Sh=1.83),
    but daily 22d-return vector_neut raised turnover to 11.5% (Margin=7.99bp).
    To strictly honor the user's Margin-First preference (higher Margin = better), this 32-FULL pack
    replaces fast 22d return neutralization with slower 66d/126d returns, longer 33d/44d post-min decay,
    hump(0.01), ts_target_tvr_decay(target_tvr=0.05), and higher-Margin ass_tvr_prior_y/last_qtr variants
    to lift Margin 7.99bp -> 12-18bp+ while preserving SC < 0.42 and Sh >= 1.75!
    """
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    at_lq = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    at_py = "ts_backfill(mdl31_ab1_ass_tvr_prior_y, 21)"
    eps1 = "ts_backfill(star_eps_surprise_prediction_fq1, 21)"
    eps2 = "ts_backfill(star_eps_surprise_prediction_fq2, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"

    core_pq = f"min(rank({at_pq}), min(rank({eps1}), rank({dtd})))"
    core_lq = f"min(rank({at_lq}), min(rank({eps1}), rank({dtd})))"
    core_py = f"min(rank({at_py}), min(rank({eps1}), rank({dtd})))"
    core_e2 = f"min(rank({at_pq}), min(rank({eps2}), rank({dtd})))"

    ret22 = "rank(ts_mean(returns, 22))"
    ret66 = "rank(ts_mean(returns, 66))"
    ret126 = "rank(ts_mean(returns, 126))"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC13-M1-e5m-ret66", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC13-M2-e5m-ret126", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret126}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC13-M3-e5m-d33-ret66", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 33), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC13-M4-e5m-hump01", "ADMIN_ORIGINAL", "WL13229", f"hump(tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0), hump=0.01)"),
        ("PC13-M5-e5m-tvr05", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0), lambda_min=0, lambda_max=0.9, target_tvr=0.05)"),
        ("PC13-M6-e5m-atpy-ret66", "TOP100_2026Q4", "SZ83096", f"tail(vector_neut(group_rank(ts_decay_linear({core_py}, 22), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC13-M7-e5m-atlq-d44", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut(group_rank(ts_decay_linear({core_lq}, 44), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC13-M8-e5m-eps2-ret66", "TOP100_2026Q4", "LD22811", f"tail(vector_neut(group_rank(ts_decay_linear({core_e2}, 33), subindustry), {ret66}), lower=-0.25, upper=0.25, newval=0)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("stat_d5_t08", "STATISTICAL", 5, 0.08),
        ("stat_d6_t08", "STATISTICAL", 6, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r13-USA-E5M-HIGHMGN-{tag}",
                campaign_id="S3_PCLAB_USA_E5M_HIGHMGN",
                hypothesis_id="HYP-PC13-E5MWLW0J-MARGIN-15BP-ORTHO",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_prior_qtr", tag_suffix=tag),
            )
        )
    return specs


def build_usa_e5m_1ax_margin_s3r14_specs() -> list[dict[str, Any]]:
    """S3-r14 Strict Single-Variable Controlled-Variable Attribution on E5mWLW0J (16 FULL = 2 batches).

    Follows AGENTS.md Section 3 & OPTIMIZATION_LEDGER.json (EFF-05 & INEFF-01):
      - S3-r13 changed 3 axes at once (last_qtr + d44 + ret66 -> pwWrLpaV 9.56bp, 2Y=2.63, Fit=0.95)
        and proved ret22->ret66 alone dropped Sharpe 1.83->1.58 while hump outside tail(newval=0) crashed 0.83.
      - Here we FREEZE E5mWLW0J's core (ass_tvr_prior_qtr x eps1 x dtd, d22, ret22, tail[-0.25,0.25,0], STATISTICAL)
        and vary STRICTLY ONE variable per expression (ZERO hump outside tail!).
    """
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    at_lq = "ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)"
    eps1 = "ts_backfill(star_eps_surprise_prediction_fq1, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"

    core_pq = f"min(rank({at_pq}), min(rank({eps1}), rank({dtd})))"
    core_lq = f"min(rank({at_lq}), min(rank({eps1}), rank({dtd})))"

    ret22 = "rank(ts_mean(returns, 22))"
    ret33 = "rank(ts_mean(returns, 33))"
    ret44 = "rank(ts_mean(returns, 44))"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC14-1AX-d33-only", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 33), subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC14-1AX-d44-only", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 44), subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC14-1AX-ret33-only", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret33}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC14-1AX-ret44-only", "ADMIN_ORIGINAL", "WL13229", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret44}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC14-1AX-atlq-only", "TOP100_2026Q4", "SZ83096", f"tail(vector_neut(group_rank(ts_decay_linear({core_lq}, 22), subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0)"),
        ("PC14-1AX-tail30-only", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret22}), lower=-0.3, upper=0.3, newval=0)"),
        ("PC14-1AX-tail20-only", "TOP100_2026Q4", "ZS59763", f"tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret22}), lower=-0.2, upper=0.2, newval=0)"),
        ("PC14-1AX-tvr08-only", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(tail(vector_neut(group_rank(ts_decay_linear({core_pq}, 22), subindustry), {ret22}), lower=-0.25, upper=0.25, newval=0), lambda_min=0, lambda_max=0.9, target_tvr=0.08)"),
    ]

    specs: list[dict[str, Any]] = []
    for tag, neut, dec, trunc in [
        ("stat_d6_t08", "STATISTICAL", 6, 0.08),
        ("stat_d4_t08", "STATISTICAL", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r14-USA-E5M-1AX-{tag}",
                campaign_id="S3_PCLAB_USA_E5M_1AX",
                hypothesis_id="HYP-PC14-E5M-STRICT-SINGLE-AXIS-MARGIN",
                region="USA",
                universe="TOP3000",
                dataset_id="model31",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(exprs, dataset_id="model31", primary_field_id="mdl31_ab1_ass_tvr_prior_qtr", tag_suffix=tag),
            )
        )
    return specs




def build_clean_lowpc_controlled_s3r15_specs() -> list[dict[str, Any]]:
    """S3-r15 Clean <=4-Layer Controlled-Variable (decay in {0, 5, 20}) Low-PC Rescue & Day-2 Seed Upgrade (64 FULL = 8 batches).

    Strictly implements user directives (2026-11-26 16:04):
      1) E5mWLW0J (PC=0.7531 >= 0.70, 7-layer over-nested) is conservatively shelved to SC_PASS (no further optimization).
      2) Focuses ONLY on clean <=4-layer expressions targeting true PC < 0.70 + high Margin:
         - Pack A (EUR/TOP2500, 32 FULL across decay in {0, 5, 20}):
           * Rescues near-threshold 0-FAIL SC_PASS soft targets np6RxVz3 (15.10bp, Sh=2.10, PC=0.720) &
             MPgRMMJ8 (13.09bp, Sh=1.95, PC=0.713) via Wang Ge L6 tail(0.25, 0.75, 0.5) & shortinterest6 cross-DS;
           * Upgrades today's new 29.34bp/22.33bp EUR/model77 finstmtrank (YPlGvEqv Sh=1.89, legbW5xN Sh=1.97,
             only fail = LOW_SUB_UNIVERSE_SHARPE) x EUR/shortinterest6 (1YGQzpGR Sh=1.47, 2Y=1.91).
         - Pack B (USA/TOP3000, 32 FULL across decay in {0, 5, 20}):
           * Combines today's fresh Alphas=0 FREE winners from USA/analyst_revision_horizons
             (O06EnNqJ Sh=1.30/2Y=1.78, A1LMJpeg Sh=1.28, vRY3j0VG Sh=1.28, LL8An92n Sh=1.24/2Y=1.83)
             with high-Margin USA/model39 (1YGQd20M 30.0bp) & USA/model31 (ass_tvr_prior_qtr 19.95bp)
             in clean 3-4 layer structures.
    """
    specs: list[dict[str, Any]] = []

    # --- Pack A: EUR/TOP2500 Clean <=4-Layer Controlled-Variable (decay in {0, 5, 20}) ---
    vm = "ts_backfill(value_momentum_region_percentile, 21)"
    acc25 = "ts_backfill(mdl25_8v, 21)"
    finst = "reverse(ts_backfill(mdl177_qvm_finstmtrank_qvaeur_alt, 21))"
    finst_m22 = "reverse(ts_mean(ts_backfill(mdl177_qvm_finstmtrank_qvaeur_alt, 21), 22))"
    si_ind = "ts_backfill(star_hold_industry_rank, 21)"
    si_glb = "ts_backfill(star_hold_global_screening_rank, 21)"
    ci = "group_cartesian_product(country, industry)"

    eur_exprs: list[tuple[str, str, str, str]] = [
        ("PC15-E1-np6-tail25", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, tail(group_rank(min(rank({vm}), rank({acc25})), {ci}), lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC15-E2-finst-m22-gate35", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore({finst_m22}, {ci}), 0)"),
        ("PC15-E3-finst-siind-ci", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_rank(min(rank({finst}), rank({si_ind})), {ci}), 0)"),
        ("PC15-E4-finst-siglb-ci", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.35, group_rank(min(rank({finst}), rank({si_glb})), {ci}), 0)"),
        ("PC15-E5-finst-siind-tail25", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, tail(group_rank(min(rank({finst}), rank({si_ind})), {ci}), lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC15-E6-finst-m22-liqtilt", "TOP100_2026Q4", "SZ83096", f"divide(subtract(group_rank({finst_m22}, {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC15-E7-finst-siind-tilt", "TOP100_2026Q4", "SZ83096", f"divide(subtract(group_rank(min(rank({finst}), rank({si_ind})), {ci}), 0.5), subtract(1.5, rank(adv20)))"),
        ("PC15-E8-vm-siind-tail25", "TOP100_2026Q4", "JR23144", f"if_else(rank(adv20) > 0.4, tail(group_rank(min(rank({vm}), rank({si_ind})), {ci}), lower=0.25, upper=0.75, newval=0.5), 0)"),
    ]

    for tag, neut, dec, trunc in [
        ("ram_d0_t06", "REVERSION_AND_MOMENTUM", 0, 0.06),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
        ("crd_d20_t08", "CROWDING", 20, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r15-EUR-CLEAN4L-{tag}",
                campaign_id="S3_PCLAB_EUR_CLEAN4L",
                hypothesis_id="HYP-PC15-EUR-FINST-SI6-DECAY-0-5-20",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_exprs, dataset_id="model77", primary_field_id="mdl177_qvm_finstmtrank_qvaeur_alt", tag_suffix=tag),
            )
        )

    # --- Pack B: USA/TOP3000 Clean <=4-Layer Controlled-Variable (decay in {0, 5, 20}) ---
    rev_l = "ts_zscore(ts_mean(ts_backfill(mean_revisioncluster_revision_pct_quarterly_eps_long, 21), 5), 66)"
    rev_s = "ts_zscore(ts_mean(ts_backfill(mean_revisioncluster_revision_pct_quarterly_eps_short, 21), 5), 66)"
    ebit_low = "ts_decay_linear(ts_backfill(analyst_count_lowering_next_year_ebitda_14d_long_2, 21), 10)"
    upg_7d = "ts_decay_linear(ts_backfill(analyst_recommendation_upgrades_7d_medium, 21), 10)"
    m39_lt = "ts_backfill(long_term_price_momentum_score_3, 21)"
    m39_reg = "ts_backfill(regional_price_momentum_percentile, 21)"
    at_pq = "ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)"
    dtd = "ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)"

    usa_exprs: list[tuple[str, str, str, str]] = [
        ("PC15-U1-revl-ebit-d22", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({rev_l}), rank({ebit_low})), 22), subindustry)"),
        ("PC15-U2-revl-upg7-d22", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({rev_l}), rank({upg_7d})), 22), subindustry)"),
        ("PC15-U3-revl-dtd-free", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({rev_l}), rank({dtd})), 22), subindustry)"),
        ("PC15-U4-ebit-dtd-free", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({ebit_low}), rank({dtd})), 22), subindustry)"),
        ("PC15-U5-revl-atpq-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({at_pq}), rank({rev_l})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC15-U6-ebit-atpq-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({at_pq}), rank({ebit_low})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC15-U7-m39lt-atpq-d22", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear(min(rank({at_pq}), rank({m39_lt})), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC15-U8-m39reg-revl-d22", "TOP100_2026Q4", "JR23144", f"group_rank(ts_decay_linear(min(rank({m39_reg}), rank({rev_s})), 22), subindustry)"),
    ]

    for tag, neut, dec, trunc in [
        ("sub_d0_t04", "SUBINDUSTRY", 0, 0.04),
        ("ram_d0_t06", "REVERSION_AND_MOMENTUM", 0, 0.06),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
        ("crd_d20_t08", "CROWDING", 20, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r15-USA-CLEAN4L-{tag}",
                campaign_id="S3_PCLAB_USA_CLEAN4L",
                hypothesis_id="HYP-PC15-USA-ANLREV-M39-DECAY-0-5-20",
                region="USA",
                universe="TOP3000",
                dataset_id="analyst_revision_horizons",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(usa_exprs, dataset_id="analyst_revision_horizons", primary_field_id="mean_revisioncluster_revision_pct_quarterly_eps_long", tag_suffix=tag),
            )
        )

    return specs


def build_asi_eur_s3r16_controlled_specs() -> list[dict[str, Any]]:
    """S3-r16 Multi-Region Stage-3 FULL Controlled-Variable Strike (12 batches = 96 FULL: 72 ASI + 24 EUR).

    Triggered by 3-hour Audit #2 (2026-11-26 20:12 CST):
      - Pack A (32 FULL, ASI/MINVOL1M/model39): 11/104 QUICK winners hit Sh=1.61..2.35, Fit=1.04..1.91,
        Margin=12.65..35.56bp, nonPASS=[]! Since P0Pdk9Gq (TO=5.6%), akRqpR1v (TO=5.6%), zqA1lpRG (TO=2.9%)
        have TO < 8% (SKIP_LOW_TURNOVER), we confirm them in FULL mode at decay=0 & decay=5 across
        COUNTRY/SUBINDUSTRY/SLOW/RAM + country*industry + Wang Ge tail25 + signed_power(1.5) for low PC & high Margin!
      - Pack B (24 FULL, ASI/MINVOL1M/behavioral_signals): Direct execution of Universal High-Turnover Reduction
        on N1K9mOG7 (Sh=1.60, TO=35.8%) & xAlg8npq (Sh=1.49, TO=91.9%) using decay in {0, 5, 20},
        pre-rank ts_mean/ts_decay_linear, and ts_target_tvr_decay(lambda_max=0.9, target_tvr=0.12) (NO hump on ASI!).
      - Pack C (16 FULL, ASI/MINVOL1M/price_signal_dl): Confirms d59AaaMg (Sh=1.74, 2Y=2.56, Fit=1.00) &
        58GoJJmX (Sh=1.63, 2Y=2.59) in FULL mode with gentle smoothing to lift Margin 6.6bp -> 15bp+.
      - Pack D (24 FULL, EUR/TOP2500/model110): Pivots away from crowded mdl110_value (vRY3kp13 PC=0.8664)
        to low-crowding mdl110_alternative/tree/price_momentum_reversal/quality + dual-branch & tail25/signed_power!
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"

    # --- Pack A (32 FULL): ASI/MINVOL1M/model39 (SKIP_LOW_TURNOVER -> preserve 21-36bp Margin!) ---
    ind_vm = "ts_backfill(industry_value_momentum_rank_float, 21)"
    reg_vm = "ts_backfill(region_value_momentum_rank, 21)"
    mid_pm = "ts_backfill(mid_term_price_momentum_score_2, 21)"

    asi_m39_exprs: list[tuple[str, str, str, str]] = [
        ("PC16-A1-indvm-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({ind_vm}, 10), subindustry)"),
        ("PC16-A2-regvm-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({reg_vm}, 10), subindustry)"),
        ("PC16-A3-indvm-m22-sub", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_mean({ind_vm}, 22), subindustry)"),
        ("PC16-A4-indvm-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({ind_vm}, 10), {ci})"),
        ("PC16-A5-indvm-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({ind_vm}, 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-A6-regvm-tail25-ci", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({reg_vm}, 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-A7-indvm-sp15-ind", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore({ind_vm}, industry), 1.5)"),
        ("PC16-A8-vm-pm-dual-ci", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank({ind_vm}), rank({mid_pm})), 10), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("sub_d0_t08", "SUBINDUSTRY", 0, 0.08),
        ("slow_d0_t08", "SLOW", 0, 0.08),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r16-ASI-M39-FULL-{tag}",
                campaign_id="S3_ASI_M39_FULL_CHAMPION",
                hypothesis_id="HYP-S3R16-ASI-M39-0OS-USEFUL",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="model39",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_m39_exprs, dataset_id="model39", primary_field_id="industry_value_momentum_rank_float", tag_suffix=tag),
            )
        )

    # --- Pack B (24 FULL): ASI/MINVOL1M/behavioral_signals (REDUCE_HIGH_TURNOVER: TO 35.8%-91.9% -> <18%) ---
    streak = "ts_backfill(vec_avg(consecutive_return_streak_length), 21)"
    salience = "ts_backfill(vec_avg(salience_weighted_return_score), 21)"
    ext_ret = "ts_backfill(vec_avg(extreme_daily_return_indicator), 21)"

    asi_behav_exprs: list[tuple[str, str, str, str]] = [
        ("PC16-B1-strk-m10-z66", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({streak}, 10), 66), subindustry)"),
        ("PC16-B2-strk-m22-z66", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_zscore(ts_mean({streak}, 22), 66), subindustry)"),
        ("PC16-B3-strk-d22-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({streak}, 22), {ci})"),
        ("PC16-B4-strk-m22-cty", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_mean({streak}, 22), country)"),
        ("PC16-B5-strk-tvr12", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(group_rank(ts_zscore(ts_mean({streak}, 5), 66), subindustry), lambda_min=0, lambda_max=0.9, target_tvr=0.12)"),
        ("PC16-B6-strk-postd22", "TOP100_2026Q4", "ZS59763", f"group_rank(ts_decay_linear(ts_zscore(ts_mean({streak}, 5), 66), 22), {ci})"),
        ("PC16-B7-strk-sal-d22", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank(ts_mean({streak}, 10)), rank(ts_mean({salience}, 10))), 22), {ci})"),
        ("PC16-B8-strk-ext-d22", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank(ts_mean({streak}, 10)), rank(ts_mean({ext_ret}, 10))), 22), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d5_t08", "COUNTRY", 5, 0.08),
        ("cty_d20_t08", "COUNTRY", 20, 0.08),
        ("slow_d5_t08", "SLOW", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r16-ASI-BEHAV-TOFIX-{tag}",
                campaign_id="S3_ASI_BEHAV_TO_REDUCTION",
                hypothesis_id="HYP-S3R16-ASI-BEHAV-HIGHTO-RESCUE",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="behavioral_signals",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_behav_exprs, dataset_id="behavioral_signals", primary_field_id="consecutive_return_streak_length", tag_suffix=tag),
            )
        )

    # --- Pack C (16 FULL): ASI/MINVOL1M/price_signal_dl (Confirm d59AaaMg Sh=1.74 in FULL + lift Margin) ---
    nv1 = "ts_backfill(normalized_volume_indicator_1, 21)"
    nv2 = "ts_backfill(normalized_volume_indicator_2, 21)"
    rt4 = "ts_backfill(raw_trend_indicator_4, 21)"
    dual_nv = f"min(rank(ts_decay_linear({nv1}, 10)), rank(ts_decay_linear({nv2}, 10)))"

    asi_psd_exprs: list[tuple[str, str, str, str]] = [
        ("PC16-C1-nv2-d10-ci", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({nv2}, 10), {ci})"),
        ("PC16-C2-nv2-d22-ci", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({nv2}, 22), {ci})"),
        ("PC16-C3-dualnv-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({dual_nv}, 15), {ci})"),
        ("PC16-C4-dualnv-d22-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({dual_nv}, 22), subindustry)"),
        ("PC16-C5-nv2-tail25-ci", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({nv2}, 15), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-C6-dualnv-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({dual_nv}, 15), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-C7-nv2-tvr10", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(group_rank(ts_decay_linear({nv2}, 10), {ci}), lambda_min=0, lambda_max=0.9, target_tvr=0.10)"),
        ("PC16-C8-nv2-rt4-d22", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank({nv2}), rank({rt4})), 22), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
        ("cty_d10_t08", "COUNTRY", 10, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r16-ASI-PSD-FULL-{tag}",
                campaign_id="S3_ASI_PSD_FULL_CONFIRM",
                hypothesis_id="HYP-S3R16-ASI-PSD-174-MARGIN15BP",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="price_signal_dl",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_psd_exprs, dataset_id="price_signal_dl", primary_field_id="normalized_volume_indicator_2", tag_suffix=tag),
            )
        )

    # --- Pack D (24 FULL): EUR/TOP2500/model110 Low-PC Multi-Field & Nonlinear Tail (bypass crowded mdl110_value) ---
    m_alt = "ts_backfill(mdl110_alternative, 21)"
    m_tree = "ts_backfill(mdl110_tree, 21)"
    m_pmr = "ts_backfill(mdl110_price_momentum_reversal, 21)"
    m_qual = "ts_backfill(mdl110_quality, 21)"
    m_val = "ts_backfill(mdl110_value, 21)"

    eur_m110_exprs: list[tuple[str, str, str, str]] = [
        ("PC16-D1-alt-tree-ci", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({m_alt}), rank({m_tree})), 10), {ci})"),
        ("PC16-D2-val-alt-ci", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear(min(rank({m_val}), rank({m_alt})), 10), {ci})"),
        ("PC16-D3-val-tree-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({m_val}), rank({m_tree})), 10), {ci})"),
        ("PC16-D4-qual-alt-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({m_qual}), rank({m_alt})), 10), {ci})"),
        ("PC16-D5-val-alt-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({m_val}), rank({m_alt})), 15), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-D6-val-pmr-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({m_val}), rank({m_pmr})), 15), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC16-D7-val-qual-sp15", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(min(rank({m_val}), rank({m_qual})), {ci}), 1.5)"),
        ("PC16-D8-tree-pmr-ci", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank({m_tree}), rank({m_pmr})), 10), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d0_t06", "REVERSION_AND_MOMENTUM", 0, 0.06),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r16-EUR-M110-LOWPC-{tag}",
                campaign_id="S3_EUR_M110_LOWPC",
                hypothesis_id="HYP-S3R16-EUR-M110-BYPASS-VAL-PC086",
                region="EUR",
                universe="TOP2500",
                dataset_id="model110",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_m110_exprs, dataset_id="model110", primary_field_id="mdl110_alternative", tag_suffix=tag),
            )
        )

    return specs


def build_eur_asi_s3r17_orthogonal_specs() -> list[dict[str, Any]]:
    """S3-r17 Orthogonal EUR Useful Strike & ASI COUNTRY-JPN Controlled-Variable Rescue (8 batches = 64 FULL).

    Triggered by 2-hour Audit #10 (2026-11-26 21:00 CST):
      - Pack A (24 FULL, EUR/TOP2500/model238): Rescues orthogonal seed 78GbxbA1 (Sh=1.73, 2Y=2.21, Fit=0.99,
        corr=0.205 vs EUR Useful RR5QjWYz, proven PC=0.608 < 0.70!) via EFF-03 adv20 gate + country*industry
        + post-min decay(10/15/22) + tail25 across RAM d={4,6} & CROWDING d=5 (clean <=4 layers).
      - Pack B (16 FULL, EUR/TOP2500/shortinterest6): Promotes 1YGQzpGR (Sh=1.47, 2Y=1.91) & P0PdGrlJ
        (Sh=1.37, 2Y=1.84) with adv20 gate + country*industry + cross-DS model238 orthogonal branch.
      - Pack C (24 FULL, ASI/MINVOL1M/model39): Controlled-variable COUNTRY neutralization decay ladder
        (d in {0, 5, 15}) + country-equalized ranking (group_rank(..., country) / country*industry / winsorize)
        to diagnose & rescue LOW_ASI_JPN_SHARPE (0.01..0.35 -> >=1.00) & LOW_ROBUST_UNIVERSE_SHARPE after
        fixing the ASI:2 stall_timeout=240s bug (now ASI:1 + stall_timeout=360s).
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"
    cs = "group_cartesian_product(country, sector)"

    # --- Pack A (24 FULL): EUR/TOP2500/model238 (Orthogonal corr=0.205, PC=0.608!) ---
    pref = "ts_backfill(regional_change_in_preference_rank_d1, 21)"
    align = "ts_backfill(global_screening_factor_alignment_rank_d1, 21)"
    crel = "ts_backfill(country_relative_investment_rank_d1, 21)"
    si_ind = "ts_backfill(star_hold_industry_rank, 21)"

    eur_m238_exprs: list[tuple[str, str, str, str]] = [
        ("PC17-A1-pref-align-adv35-d10", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(ts_decay_linear(min(rank({pref}), rank({align})), 10), {ci}), 0)"),
        ("PC17-A2-pref-align-adv40-d10", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({pref}), rank({align})), 10), {ci}), 0)"),
        ("PC17-A3-pref-align-adv40-d22", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({pref}), rank({align})), 22), {ci}), 0)"),
        ("PC17-A4-pref-crel-adv40-d15", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({pref}), rank({crel})), 15), {ci}), 0)"),
        ("PC17-A5-pref-align-tail25", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.4, tail(group_rank(ts_decay_linear(min(rank({pref}), rank({align})), 15), {ci}), lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC17-A6-pref-align-adv45-d15", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.45, group_zscore(ts_decay_linear(min(rank({pref}), rank({align})), 15), {ci}), 0)"),
        ("PC17-A7-pref-siind-adv40-d15", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({pref}), rank({si_ind})), 15), {ci}), 0)"),
        ("PC17-A8-pref-align-sp15-adv40", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore(ts_decay_linear(min(rank({pref}), rank({align})), 10), {ci}), 1.5), 0)"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("ram_d6_t08", "REVERSION_AND_MOMENTUM", 6, 0.08),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r17-EUR-M238-ORTHO-{tag}",
                campaign_id="S3_EUR_M238_ORTHO_USEFUL",
                hypothesis_id="HYP-S3R17-EUR-M238-PC061-SUBUNI-FIX",
                region="EUR",
                universe="TOP2500",
                dataset_id="model238",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_m238_exprs, dataset_id="model238", primary_field_id="regional_change_in_preference_rank_d1", tag_suffix=tag),
            )
        )

    # --- Pack B (16 FULL): EUR/TOP2500/shortinterest6 Stage-3 Promotion ---
    si_glb = "ts_backfill(star_hold_global_screening_rank, 21)"
    si_reg = "ts_backfill(star_hold_region_owner_rank, 21)"

    eur_si6_exprs: list[tuple[str, str, str, str]] = [
        ("PC17-B1-siind-adv35-d10", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.35, group_zscore(ts_decay_linear({si_ind}, 10), {ci}), 0)"),
        ("PC17-B2-siind-adv40-d22", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear({si_ind}, 22), {ci}), 0)"),
        ("PC17-B3-siind-siglb-adv40-d15", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({si_ind}), rank({si_glb})), 15), {ci}), 0)"),
        ("PC17-B4-siind-sireg-adv40-d15", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({si_ind}), rank({si_reg})), 15), {ci}), 0)"),
        ("PC17-B5-siind-siglb-tail25", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.4, tail(group_rank(ts_decay_linear(min(rank({si_ind}), rank({si_glb})), 15), {ci}), lower=0.25, upper=0.75, newval=0.5), 0)"),
        ("PC17-B6-siglb-pref-adv40-d15", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({si_glb}), rank({pref})), 15), {ci}), 0)"),
        ("PC17-B7-siind-align-adv40-d15", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.4, group_zscore(ts_decay_linear(min(rank({si_ind}), rank({align})), 15), {ci}), 0)"),
        ("PC17-B8-siind-siglb-sp15", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.4, signed_power(group_zscore(ts_decay_linear(min(rank({si_ind}), rank({si_glb})), 10), {ci}), 1.5), 0)"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d5_t08", "CROWDING", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r17-EUR-SI6-PROMO-{tag}",
                campaign_id="S3_EUR_SI6_PROMO",
                hypothesis_id="HYP-S3R17-EUR-SI6-147-TO-165",
                region="EUR",
                universe="TOP2500",
                dataset_id="shortinterest6",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_si6_exprs, dataset_id="shortinterest6", primary_field_id="star_hold_industry_rank", tag_suffix=tag),
            )
        )

    # --- Pack C (24 FULL): ASI/MINVOL1M/model39 COUNTRY + Japan-Equalized Rescue ---
    ind_vm = "ts_backfill(industry_value_momentum_rank_float, 21)"
    reg_vm = "ts_backfill(region_value_momentum_rank, 21)"
    asi_m39_jpn_exprs: list[tuple[str, str, str, str]] = [
        ("PC17-C1-indvm-d10-cty", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({ind_vm}, 10), country)"),
        ("PC17-C2-regvm-d10-cty", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({reg_vm}, 10), country)"),
        ("PC17-C3-indvm-d10-cs", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_decay_linear({ind_vm}, 10), {cs})"),
        ("PC17-C4-regvm-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({reg_vm}, 10), {ci})"),
        ("PC17-C5-indvm-win3-ci", "TOP100_2026Q4", "JX79797", f"winsorize(group_zscore(ts_decay_linear({ind_vm}, 10), {ci}), std=3)"),
        ("PC17-C6-regvm-tail25-cs", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({reg_vm}, 10), {cs}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC17-C7-indvm-m22-cty", "TOP100_2026Q4", "SZ83096", f"group_zscore(ts_mean({ind_vm}, 22), country)"),
        ("PC17-C8-indvm-sp05-ci", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore(ts_decay_linear({ind_vm}, 10), {ci}), 0.5)"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d5_t08", "COUNTRY", 5, 0.08),
        ("cty_d15_t08", "COUNTRY", 15, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r17-ASI-M39-JPNFIX-{tag}",
                campaign_id="S3_ASI_M39_COUNTRY_JPNFIX",
                hypothesis_id="HYP-S3R17-ASI-M39-COUNTRY-DECAY-JPN-ROBUST",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="model39",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_m39_jpn_exprs, dataset_id="model39", primary_field_id="industry_value_momentum_rank_float", tag_suffix=tag),
            )
        )

    return specs


def build_eur_s3r18_ortho_strike_specs() -> list[dict[str, Any]]:
    """S3-r18 EUR Ultra-Orthogonal Complementary Strike (97-OS SC=0.12..0.33, 6 batches = 48 FULL).

    Triggered by 2-hour Audit #11 (2026-11-26 22:55 CST) after user submitted E5mWLW0J + Jj88vq2e -> 97/100 OS:
      - Pack A (32 FULL, EUR/TOP2500/model77 x model110): Pairs high-2Y/high-Margin model77
        (zqApnwdR dvm_ttmgfp_alt 20.3bp Sh=2.05/2Y=2.21/Sub=0.90/1.07 SC=0.336; GrQJ50gP 23.6bp 2Y=2.52)
        with large-cap Sub-Uni strong ultra-orthogonal model110 & emm
        (P0P95bbx mdl110_analyst_sentiment Sh=2.30/Sub=1.16/1.20 SC=0.123!; RR5W58Qg mdl110_score Sh=2.02 Sub PASS!;
        78G9RNAZ emm_fc_epsrm_alt Sh=1.90/Sub=0.90/0.99 SC=0.149!).
        Strictly aligns reverse() on negative model77 branches and avoids heavy adv20>0.40 cuts (INEFF-09).
      - Pack B (16 FULL, EUR/TOP2500/shortinterest6): Universal High-Turnover Reduction (TO 28.9% -> 8-15%)
        on 1YGE0pEz (Sh=1.80, 2Y=1.61, SC=0.216) & VkMJ5KqY (Sh=1.76, 2Y=1.68) & XgN6M3gl (Sh=1.58, 2Y=2.02)
        with ZERO heavy adv20 gate (uses ts_decay_linear, ts_mean, ts_target_tvr_decay, hump, cross-DS model77/110).
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"

    # --- Pack A (32 FULL): EUR/TOP2500 model77 x model110 Complementary Orthogonal Fusion ---
    dvm_gfp = "reverse(ts_backfill(mdl177_dvm_ttmgfp_alt, 21))"
    dvm_gfp_m22 = "reverse(ts_mean(ts_backfill(mdl177_dvm_ttmgfp_alt, 21), 22))"
    emm_eps = "reverse(ts_backfill(mdl177_emm_fc_epsrm_alt, 21))"
    anl_sent = "ts_backfill(mdl110_analyst_sentiment, 21)"
    m110_sc = "ts_backfill(mdl110_score, 21)"

    eur_m77_m110_exprs: list[tuple[str, str, str, str]] = [
        ("PC18-A1-dvm-anlsent-ci", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank({dvm_gfp}), rank({anl_sent})), {ci})"),
        ("PC18-A2-dvmm22-anlsent-ci", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank({dvm_gfp_m22}), rank({anl_sent})), {ci})"),
        ("PC18-A3-dvm-m110sc-ci", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(min(rank({dvm_gfp}), rank({m110_sc})), {ci})"),
        ("PC18-A4-dvm-emmeps-ci", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(min(rank({dvm_gfp}), rank({emm_eps})), {ci})"),
        ("PC18-A5-dvm-anlsent-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({dvm_gfp}), rank({anl_sent})), 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC18-A6-dvm-m110sc-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({dvm_gfp}), rank({m110_sc})), 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC18-A7-dvm-anlsent-adv25", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.25, group_zscore(min(rank({dvm_gfp}), rank({anl_sent})), {ci}), 0)"),
        ("PC18-A8-dvm-emmeps-sp15", "TOP100_2026Q4", "LD22811", f"signed_power(group_zscore(min(rank({dvm_gfp}), rank({emm_eps})), {ci}), 1.5)"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d0_t06", "REVERSION_AND_MOMENTUM", 0, 0.06),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r18-EUR-M77M110-ORTHO-{tag}",
                campaign_id="S3_EUR_M77_M110_ORTHO",
                hypothesis_id="HYP-S3R18-EUR-M77-2Y25-X-M110-SUBPASS-SC012",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_m77_m110_exprs, dataset_id="model77", primary_field_id="mdl177_dvm_ttmgfp_alt", tag_suffix=tag),
            )
        )

    # --- Pack B (16 FULL): EUR/TOP2500/shortinterest6 Universal High-TO Reduction (ZERO adv20 hard cut!) ---
    sh_gchg = "ts_backfill(star_hold_global_change_rank, 21)"
    sh_rchg = "ts_backfill(star_hold_region_change_rank, 21)"
    sh_rrnk = "ts_backfill(star_hold_region_rank, 21)"

    eur_si6_tofix_exprs: list[tuple[str, str, str, str]] = [
        ("PC18-B1-gchg-d10-ci", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_decay_linear({sh_gchg}, 10), {ci})"),
        ("PC18-B2-rchg-d10-ci", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_decay_linear({sh_rchg}, 10), {ci})"),
        ("PC18-B3-gchg-m22-ind", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_mean({sh_gchg}, 22), industry)"),
        ("PC18-B4-rrnk-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_decay_linear({sh_rrnk}, 10), {ci})"),
        ("PC18-B5-gchg-tvr12", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(group_zscore({sh_gchg}, {ci}), lambda_min=0, lambda_max=0.9, target_tvr=0.12)"),
        ("PC18-B6-gchg-hump01", "TOP100_2026Q4", "ZS59763", f"hump(group_zscore(ts_decay_linear({sh_gchg}, 5), {ci}), hump=0.01)"),
        ("PC18-B7-gchg-dvm-ci", "TOP100_2026Q4", "SZ83096", f"group_zscore(ts_decay_linear(min(rank({sh_gchg}), rank({dvm_gfp})), 10), {ci})"),
        ("PC18-B8-rrnk-anlsent-ci", "TOP100_2026Q4", "LD22811", f"group_zscore(ts_decay_linear(min(rank({sh_rrnk}), rank({anl_sent})), 10), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r18-EUR-SI6-TOFIX-{tag}",
                campaign_id="S3_EUR_SI6_HIGHTO_FIX",
                hypothesis_id="HYP-S3R18-EUR-SI6-TO28-TO-12-NO-ADV20CUT",
                region="EUR",
                universe="TOP2500",
                dataset_id="shortinterest6",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_si6_tofix_exprs, dataset_id="shortinterest6", primary_field_id="star_hold_global_change_rank", tag_suffix=tag),
            )
        )

    return specs


def build_asi_eur_s3r19_breakout_specs() -> list[dict[str, Any]]:
    """S3-r19 High-Probability Useful Finisher: EUR PC=0.54 Ultra-Ortho + ASI/model25 51bp FULL Confirm (7 batches = 56 FULL).

    Triggered by 2-hour Audit #12 (2026-11-27 00:52 CST):
      - Pack A (32 FULL, EUR/TOP2500/model77 x model110): S3-r18 recon proved 3qGWQAeX (Sh=2.32, Sub=1.19/1.21,
        2Y=1.51) has 97-OS SC=0.2660 & PC=0.5419 (0 collisions!), and MPgAMxbM (Sh=1.95, 11.4bp, 2Y=2.05 PASS!)
        has SC=0.2593 & PC=0.5643 (0 collisions!). With 0.15 of free PC headroom, we close the tiny 0.02 Sub-Uni
        & 0.07 2Y gap via 3-way complementary fusion (dvm x emm x anl_sent/score) + gentle adv20>{0.15,0.20,0.25,0.35}
        + post-min decay(10) across RAM d={0,2,5} & SUBINDUSTRY d=4!
      - Pack B (24 FULL, ASI/MINVOL1M/model25): First-wave QUICK monster 78GVVzjx (ev_to_ebitda_relative_score,
        aCnt=1, 51.63bp, Sh=1.91, 2Y=2.62, Fit=1.29, TO=2.2%, SC=0.000!) promoted immediately to FULL mode
        (maxTrade=ON, TO<8% -> SKIP_LOW_TURNOVER) across COUNTRY/SUBINDUSTRY/CROWDING to verify LOW_ASI_JPN_SHARPE
        & LOW_ROBUST_UNIVERSE_SHARPE!
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"

    # --- Pack A (32 FULL): EUR/TOP2500 PC=0.54-0.56 Useful Finisher ---
    dvm_gfp = "reverse(ts_backfill(mdl177_dvm_ttmgfp_alt, 21))"
    dvm_qvm = "reverse(ts_backfill(mdl177_qvm_dvm_qvaeur_alt, 21))"
    emm_eps = "reverse(ts_backfill(mdl177_emm_fc_epsrm_alt, 21))"
    anl_sent = "ts_backfill(mdl110_analyst_sentiment, 21)"
    m110_sc = "ts_backfill(mdl110_score, 21)"

    eur_fin_exprs: list[tuple[str, str, str, str]] = [
        ("PC19-E1-3way-dvm-emm-anlsent", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank({dvm_gfp}), min(rank({emm_eps}), rank({anl_sent}))), {ci})"),
        ("PC19-E2-3way-dvm-emm-m110sc", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(min(rank({dvm_gfp}), min(rank({emm_eps}), rank({m110_sc}))), {ci})"),
        ("PC19-E3-dvm-emm-adv25", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.25, group_zscore(min(rank({dvm_gfp}), rank({emm_eps})), {ci}), 0)"),
        ("PC19-E4-dvm-emm-adv35", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.35, group_zscore(min(rank({dvm_gfp}), rank({emm_eps})), {ci}), 0)"),
        ("PC19-E5-3way-adv20", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.2, group_zscore(min(rank({dvm_gfp}), min(rank({emm_eps}), rank({anl_sent}))), {ci}), 0)"),
        ("PC19-E6-dvm-anlsent-adv15", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.15, group_zscore(min(rank({dvm_gfp}), rank({anl_sent})), {ci}), 0)"),
        ("PC19-E7-qvmdvm-anlsent-adv20", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.2, group_zscore(min(rank({dvm_qvm}), rank({anl_sent})), {ci}), 0)"),
        ("PC19-E8-dvm-emm-d10-adv25", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.25, group_zscore(ts_decay_linear(min(rank({dvm_gfp}), rank({emm_eps})), 10), {ci}), 0)"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d0_t06", "REVERSION_AND_MOMENTUM", 0, 0.06),
        ("ram_d2_t08", "REVERSION_AND_MOMENTUM", 2, 0.08),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
        ("sub_d4_t08", "SUBINDUSTRY", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r19-EUR-PC54-FIN-{tag}",
                campaign_id="S3_EUR_PC54_USEFUL_FINISHER",
                hypothesis_id="HYP-S3R19-EUR-3QGW-PC054-CLOSE-002-SUB-007-2Y",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_fin_exprs, dataset_id="model77", primary_field_id="mdl177_dvm_ttmgfp_alt", tag_suffix=tag),
            )
        )

    # --- Pack B (24 FULL): ASI/MINVOL1M/model25 ev_to_ebitda_relative_score 51.63bp FULL Confirmation ---
    ev_ebitda = "ts_backfill(ev_to_ebitda_relative_score, 21)"
    ev_sales = "ts_backfill(ev_to_sales_relative_score, 21)"
    eps_10y = "ts_backfill(forward_10yr_eps_cagr, 21)"
    cred_ind = "ts_backfill(industry_credit_risk_percentile, 21)"

    asi_m25_exprs: list[tuple[str, str, str, str]] = [
        ("PC19-A1-evebitda-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({ev_ebitda}, 10), subindustry)"),
        ("PC19-A2-evebitda-ind", "ADMIN_ORIGINAL", "WL13229", f"group_zscore({ev_ebitda}, industry)"),
        ("PC19-A3-evebitda-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({ev_ebitda}, 10), {ci})"),
        ("PC19-A4-evebitda-d10-cty", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({ev_ebitda}, 10), country)"),
        ("PC19-A5-evebitda-tail25-ci", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({ev_ebitda}, 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC19-A6-evebitda-sp15-ind", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore({ev_ebitda}, industry), 1.5)"),
        ("PC19-A7-evebitda-evsales-ci", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank({ev_ebitda}), rank({ev_sales})), 10), {ci})"),
        ("PC19-A8-evebitda-eps10y-cred", "TOP100_2026Q4", "JR23144", f"group_rank(ts_decay_linear(min(rank({ev_ebitda}), min(rank({eps_10y}), rank({cred_ind}))), 10), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("sub_d0_t08", "SUBINDUSTRY", 0, 0.08),
        ("crd_d2_t08", "CROWDING", 2, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r19-ASI-M25-FULL-{tag}",
                campaign_id="S3_ASI_M25_51BP_FULL_CONFIRM",
                hypothesis_id="HYP-S3R19-ASI-M25-EVEBITDA-51BP-JPN-CHECK",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="model25",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_m25_exprs, dataset_id="model25", primary_field_id="ev_to_ebitda_relative_score", tag_suffix=tag),
            )
        )

    return specs


# Live-verified alphaCount==0 fields used in UNUSED_ALPHA0 Stage-3 FULL batches (2026-11-27).
S3_ALPHA0_VERIFIED_FIELDS: dict[str, int] = {
    "img30d_return_tercile_confidence0_zackbatch": 0,
    "img30d_return_tercile_confidence2_zackbatch": 0,
    "img30d_return_quartile_confidence0_zackbatch": 0,
    "analyst_regime_120d_return_quantile5_prob0": 0,
    "analyst_monthquarter_120d_return_quantile5_score3": 0,
    "analyst_monthquarter_60d_return_quantile5_score1": 0,
    "analyst_60d_return_quantile5_prob3": 0,
    "analyst_regime_60d_return_quantile5_score2": 0,
    "short_term_regime2_60d_single_quantile_pred": 0,
    "analyst_120d_single_quantile_pred": 0,
    "short_term_60d_qtile5_class_pred": 0,
    "long_term_quantile1_r60_pred": 0,
    "long_term_quantile5_r60_pred": 0,
    "long_term_seasonal_quantile1_r120_pred": 0,
    "long_term_regime2_quantile1_r120_pred": 0,
    "short_hedge3_60d_single_quantile_pred": 0,
}


def build_s3r23d_asi_mf120_robust_free_specs() -> list[dict[str, Any]]:
    """S3-r23d (24 FULL, 100% UNUSED_ALPHA0 FREE): ASI/MINVOL1M/multifactor_return_pred Robust>=90% + JPN>=1.00 Finisher!

    Triggered by 2-hour Audit #17 (2026-11-27 10:48 CST) after S3-r23b (16/16 FULL) & S3-r23c (16/16 FULL):
      - Controlled Attribution across 56 ASI/multifactor_return_pred FULL sims:
        1) `MPgwVVRL` (COUNTRY d=2, d10 + tail25, subindustry): Sh=2.58, 2Y=2.63, Fit=1.65, JPN=1.05 PASS, rob=0.884 (2.05/2.32).
        2) `88GA2dqz` / `2rGEeez6` (COUNTRY d=6/d=2, d15 + tail25, subindustry): lengthening decay 10d->15d + d=6
           lifted rob_ratio from 0.884 -> 0.916 (2.08/2.27), rret to 0.917 (0.0411/0.0448), Margin to 11.34bp
           (Sh=2.52, 2Y=2.53, Fit=1.59), missing JPN by only 0.01-0.02 (0.99/1.00 & 0.98/1.00)!
        3) `vRY0o3g3` / `1YGv2QvX` (COUNTRY d=6, anl120 x st_r2, subindustry): 14.41bp / 13.97bp, Sh=2.34-2.35,
           Fit=1.64-1.71, JPN=1.13 / 1.04 PASS!
        4) `MPgw26wL` (S3-r23c COUNTRY d=0, qtile5 x st_r2 + tail25, subindustry): Sh=2.44, 2Y=2.60, Fit=1.53, JPN=1.03 PASS!
        5) `9qGo72A1` (S3-r22 CROWDING d=2, bare d10 subindustry): rob_ratio=0.964 (1.85/1.92 — only 0.07 short!)
           AND JPN=1.02 PASS!
      - Combines d12/d15/d22 linear smoothing + Wang Ge L6 `tail(0.25, 0.75, 0.5)` + `anl120`/`qtile5` dual-branch
        across `CROWDING d=6` (to push 9qGo72A1's 0.964 rob_ratio over 1.00 while crushing PC<0.70),
        `REVERSION_AND_MOMENTUM d=4` (EFF-11's -0.190 PC crusher, first time on ASI MF120 FULL),
        and `COUNTRY d=12 tr=0.06` (continuing monotonic d=0->2->6->12 Margin & Robust climb).
    """
    specs: list[dict[str, Any]] = []
    st_r2 = "ts_backfill(short_term_regime2_60d_single_quantile_pred, 21)"
    anl_120 = "ts_backfill(analyst_120d_single_quantile_pred, 21)"
    st_q5 = "ts_backfill(short_term_60d_qtile5_class_pred, 21)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC23D-A1-str2-d12-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_r2}, 12), subindustry)"),
        ("PC23D-A2-str2-d22-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_r2}, 22), subindustry)"),
        ("PC23D-A3-anl-str2-d15-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 15), subindustry)"),
        ("PC23D-A4-q5-str2-d15-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({st_q5}), rank({st_r2})), 15), subindustry)"),
        ("PC23D-A5-str2-d12-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_r2}, 12), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23D-A6-str2-d22-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_r2}, 22), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23D-A7-anl-str2-d12-tail25", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 12), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23D-A8-q5-str2-d12-tail25", "TOP100_2026Q4", "LD22811", f"tail(group_rank(ts_decay_linear(min(rank({st_q5}), rank({st_r2})), 12), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
    ]
    for tag, neut, dec, trunc in [
        ("crd_d6_t08", "CROWDING", 6, 0.08),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("cty_d12_t06", "COUNTRY", 12, 0.06),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r23d-ASI-MF120-ROBUST-FREE-{tag}",
                campaign_id="S3_ASI_MF120_ROBUST_FREE_FULL",
                hypothesis_id="HYP-S3R23D-ASI-9QGO72A1-88GA2DQZ-ROBUST96-JPN-PASS-FREE",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="multifactor_return_pred",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(exprs, dataset_id="multifactor_return_pred", primary_field_id="short_term_regime2_60d_single_quantile_pred", tag_suffix=tag),
            )
        )
    return specs


def build_s3r23c_asi_qtile5_sub_free_specs() -> list[dict[str, Any]]:
    """S3-r23c (16 FULL, 100% UNUSED_ALPHA0 FREE): ASI/MINVOL1M/multifactor_return_pred qtile5_class_pred subindustry/sector Finisher!

    Triggered by 2026-11-27 09:44 CST audit:
      - Fresh sibling field `short_term_60d_qtile5_class_pred` just hit vRY06mzQ (Sh=2.01, 2Y=2.56, Fit=1.25,
        TO=13.55%, FAIL=[], CROWDING d=0) on `subindustry` (never yet tested on `subindustry`/`sector` under
        COUNTRY in FULL mode!).
      - Pairs `qtile5_class_pred` standalone & in single-dataset ATOM dual-branch with `st_r2` / `anl_120`
        using `subindustry` / `sector` + Wang Ge L6 `tail(0.25, 0.75, 0.5)` across COUNTRY d={0, 4} (maxTrade=ON).
      - Runs IMMEDIATELY in Phase-2 (`queue_type='UNUSED_ALPHA0'`, ZERO normal quota cost!).
    """
    specs: list[dict[str, Any]] = []
    st_q5 = "ts_backfill(short_term_60d_qtile5_class_pred, 21)"
    st_r2 = "ts_backfill(short_term_regime2_60d_single_quantile_pred, 21)"
    anl_120 = "ts_backfill(analyst_120d_single_quantile_pred, 21)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC23C-A1-q5-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_q5}, 10), subindustry)"),
        ("PC23C-A2-q5-d15-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_q5}, 15), subindustry)"),
        ("PC23C-A3-q5-d10-sec", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({st_q5}, 10), sector)"),
        ("PC23C-A4-q5-str2-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({st_q5}), rank({st_r2})), 10), subindustry)"),
        ("PC23C-A5-q5-tail25-sub", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_q5}, 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23C-A6-q5-tail25-sec", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_q5}, 10), sector), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23C-A7-q5-anl120-sub", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank({st_q5}), rank({anl_120})), 10), subindustry)"),
        ("PC23C-A8-q5-str2-tail25", "TOP100_2026Q4", "LD22811", f"tail(group_rank(ts_decay_linear(min(rank({st_q5}), rank({st_r2})), 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d4_t08", "COUNTRY", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r23c-ASI-QTILE5-SUB-FREE-{tag}",
                campaign_id="S3_ASI_QTILE5_SUB_ALPHA0_FULL",
                hypothesis_id="HYP-S3R23C-ASI-VRY06MZQ-QTILE5-SUB-SEC-FREE-FULL",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="multifactor_return_pred",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(exprs, dataset_id="multifactor_return_pred", primary_field_id="short_term_60d_qtile5_class_pred", tag_suffix=tag),
            )
        )
    return specs


def build_s3r23b_asi_mf120_sub_free_specs() -> list[dict[str, Any]]:
    """S3-r23b (24 FULL, 100% UNUSED_ALPHA0 FREE): ASI/MINVOL1M/multifactor_return_pred subindustry/sector Robust & PC<0.70 Finisher!

    Key S3-r22 attribution:
      - On ASI/MINVOL1M under COUNTRY neutralization, `subindustry` (A1L67JZg: Sh=2.62, 2Y=2.71, Fit=1.61,
        JPN=PASS, PC=0.7084, Robust=2.10/2.36=89.0%) crushed `country*industry` (78GOnqEQ: Sh=2.33, JPN=0.83 FAIL)
        because country*industry slices Asia into ~700 tiny buckets!
      - In S3-r22, `tail25` and `anl120 x st_r2` (A1L631kY, QUICK Sh=2.35/2Y=2.30) were only tested on
        `country*industry`, NEVER on `subindustry` or broader `sector` in FULL mode!
      - Runs IMMEDIATELY in Phase-2 (queue_type='UNUSED_ALPHA0', ZERO quota cost!) across COUNTRY d={0,2,6} (maxTrade=ON).
    """
    specs: list[dict[str, Any]] = []
    st_r2 = "ts_backfill(short_term_regime2_60d_single_quantile_pred, 21)"
    anl_120 = "ts_backfill(analyst_120d_single_quantile_pred, 21)"
    sh3_60 = "ts_backfill(short_hedge3_60d_single_quantile_pred, 21)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC23B-A1-str2-d15-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_r2}, 15), subindustry)"),
        ("PC23B-A2-str2-d10-sec", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_r2}, 10), sector)"),
        ("PC23B-A3-str2-d15-sec", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({st_r2}, 15), sector)"),
        ("PC23B-A4-anl120-str2-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 10), subindustry)"),
        ("PC23B-A5-str2-tail25-sub", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_r2}, 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23B-A6-str2-d15-tail25-sub", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_r2}, 15), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23B-A7-str2-tail25-sec", "TOP100_2026Q4", "SZ83096", f"tail(group_rank(ts_decay_linear({st_r2}, 10), sector), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC23B-A8-anl-str2-tail25-sub", "TOP100_2026Q4", "LD22811", f"tail(group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d2_t08", "COUNTRY", 2, 0.08),
        ("cty_d6_t08", "COUNTRY", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r23b-ASI-MF120-SUB-FREE-{tag}",
                campaign_id="S3_ASI_MF120_SUB_ALPHA0_FULL",
                hypothesis_id="HYP-S3R23B-ASI-A1L67JZG-SUB-SEC-TAIL25-FREE-FULL",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="multifactor_return_pred",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(exprs, dataset_id="multifactor_return_pred", primary_field_id="short_term_regime2_60d_single_quantile_pred", tag_suffix=tag),
            )
        )
    return specs


def build_s3r23_asi_mf120_robust_specs() -> list[dict[str, Any]]:
    """S3-r23 (24 FULL, NORMAL): ASI/MINVOL1M/multifactor_return_pred ROBUST_UNIVERSE & PC<0.70 Finisher!

    Triggered by 2-hour Audit #16 (2026-11-27 08:51 CST):
      HISTORIC ASI BREAKTHROUGH in S3-r22-ASI-MF120-FREE (24/24 FULL):
        - First time EVER passing LOW_ASI_JPN_SHARPE >= 1.00 on ASI FULL (5 alphas PASSED JPN!):
          * A1L67JZg (COUNTRY d=0, st_r2_60d subindustry): Sh=2.62, 2Y=2.71, Fit=1.61, JPN=PASS,
            ASI SC=0.000, remote PC=0.7084 (ge070=3 ONLY! 0.0084 above 0.70!) — ONLY failed
            LOW_ROBUST_UNIVERSE_SHARPE (2.10/2.36 = 89.0% vs 90%!) & ROBUST_RETURNS (0.0376/0.0425)!
          * 9qGo72A1 (CROWDING d=2): JPN=PASS, Robust=1.85/1.92, PC=0.8136 -> proves COUNTRY cuts PC -0.105!
          * N1KMRVqg (COUNTRY d=4, anl120 x st_r2): 11.81bp, Sh=2.06, Fit=1.35, JPN=PASS, PC=0.7325!
      Lock COUNTRY d={0,2,4} (maxTrade=ON) and apply EFF-03 liquidity gating (adv20>{0.2,0.3,0.4} / cap>0.25)
      + Wang Ge L6 tail(0.25,0.75,0.5) (EFF-02) to simultaneously lift Robust Ratio 89%->95%+ PASS AND
      crush PC 0.7084 -> <0.68, minting ASI's FIRST-EVER Useful (0 OS -> SC=0.000)!
    """
    specs: list[dict[str, Any]] = []
    st_r2 = "ts_backfill(short_term_regime2_60d_single_quantile_pred, 21)"
    anl_120 = "ts_backfill(analyst_120d_single_quantile_pred, 21)"
    base_d10 = f"group_rank(ts_decay_linear({st_r2}, 10), subindustry)"
    base_tail = f"tail({base_d10}, lower=0.25, upper=0.75, newval=0.5)"
    base_m22 = f"group_zscore(ts_mean({st_r2}, 22), subindustry)"
    base_dual = f"group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 10), subindustry)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC23-A1-str2-adv20", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.2, {base_d10}, 0)"),
        ("PC23-A2-str2-adv30", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.3, {base_d10}, 0)"),
        ("PC23-A3-str2-adv40", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.4, {base_d10}, 0)"),
        ("PC23-A4-str2-cap25", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(cap) > 0.25, {base_d10}, 0)"),
        ("PC23-A5-str2-adv25-tail25", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.25, {base_tail}, 0)"),
        ("PC23-A6-str2-adv35-tail25", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.35, {base_tail}, 0)"),
        ("PC23-A7-str2-m22-adv30", "TOP100_2026Q4", "SZ83096", f"if_else(rank(adv20) > 0.3, {base_m22}, 0)"),
        ("PC23-A8-anl120-str2-adv30", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.3, {base_dual}, 0)"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d2_t08", "COUNTRY", 2, 0.08),
        ("cty_d4_t08", "COUNTRY", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r23-ASI-MF120-ROBUST-{tag}",
                campaign_id="S3_ASI_MF120_ROBUST_USEFUL",
                hypothesis_id="HYP-S3R23-ASI-A1L67JZG-PC0708-LIQGATE-ROBUST-PASS",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="multifactor_return_pred",
                queue_type="NORMAL",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(exprs, dataset_id="multifactor_return_pred", primary_field_id="short_term_regime2_60d_single_quantile_pred", tag_suffix=tag),
            )
        )
    return specs


def build_s3r22_mf120_free_specs() -> list[dict[str, Any]]:
    """S3-r22 (48 FULL, 100% UNUSED_ALPHA0 FREE): ASI/multifactor_return_pred 2.87/3.07 FULL + USA/multifactor_return_pred FULL!

    Triggered by 2-hour Audit #15 (2026-11-27 06:51 CST):
      - Pack A (24 FULL, ASI/MINVOL1M/multifactor_return_pred, maxTrade=ON, ZERO quota cost!):
        Wave 1 (only 96 QUICK) erupted with FOUR 0-FAIL QUICK monsters (0 OS -> SC=0.000!):
          * N1KMgZao (short_term_regime2_60d_single_quantile_pred d10): Sh=2.87, 2Y=3.07, Fit=1.93, TO=12.6%, 9.02bp!
          * A1L631kY (analyst_120d x short_term_regime2_60d): Sh=2.35, 2Y=2.30, Fit=1.58, 9.09bp!
          * rK0kJx58 (short_term_regime2_60d m22): Sh=2.15, 2Y=1.87, Fit=1.23, TO=6.9%, 11.81bp!
          * WjYkXgEZ (short_term_60d_qtile5_class_pred d10): Sh=2.12, 2Y=2.77, Fit=1.25!
        Immediately promote to FULL across COUNTRY d={0,4} & CROWDING d=2 to verify LOW_ASI_JPN_SHARPE &
        ROBUST_UNIVERSE and push Margin to 12-20bp with country*industry & 3-way consensus!
      - Pack B (24 FULL, USA/TOP3000/multifactor_return_pred, ZERO quota cost!):
        Wave 1 (208 QUICK) yielded 46 S1 / 15 S2 / 1 S3 (RR5X05Yj Sh=1.59; QPWeEOXQ 1.48/2Y=1.69;
        qM5beOvK 1.44/2Y=1.99; blxp7x2r d10 held Sh=1.41 while slashing TO 41%->12.9%!).
        Apply controlled High-TO smoothing + complementary q1_r60 x q5_r60 x seasonal_r120 fusion across
        SUBINDUSTRY/CROWDING/RAM d=4 to push Fitness>=1.05, 2Y>=1.80, Margin>=8bp!
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"

    # --- Pack A (24 FULL, UNUSED_ALPHA0 FREE): ASI/MINVOL1M/multifactor_return_pred ---
    st_r2 = "ts_backfill(short_term_regime2_60d_single_quantile_pred, 21)"
    anl_120 = "ts_backfill(analyst_120d_single_quantile_pred, 21)"
    st_q5 = "ts_backfill(short_term_60d_qtile5_class_pred, 21)"

    asi_exprs: list[tuple[str, str, str, str]] = [
        ("PC22-A1-str2-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({st_r2}, 10), subindustry)"),
        ("PC22-A2-str2-m22-sub", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_mean({st_r2}, 22), subindustry)"),
        ("PC22-A3-str2-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({st_r2}, 10), {ci})"),
        ("PC22-A4-str2-d10-cty", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({st_r2}, 10), country)"),
        ("PC22-A5-str2-tail25-ci", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear({st_r2}, 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC22-A6-anl120-str2-ci", "TOP100_2026Q4", "ZS59763", f"group_rank(ts_decay_linear(min(rank({anl_120}), rank({st_r2})), 10), {ci})"),
        ("PC22-A7-str2-q5-m22-ci", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_mean(min(rank({st_r2}), rank({st_q5})), 22), {ci})"),
        ("PC22-A8-3way-str2-q5-anl", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank({st_r2}), min(rank({st_q5}), rank({anl_120}))), 10), {ci})"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d4_t08", "COUNTRY", 4, 0.08),
        ("crd_d2_t08", "CROWDING", 2, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r22-ASI-MF120-FREE-{tag}",
                campaign_id="S3_ASI_MF120_ALPHA0_FULL",
                hypothesis_id="HYP-S3R22-ASI-MF120-SH287-2Y307-JPN-FULL-CONFIRM",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="multifactor_return_pred",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(asi_exprs, dataset_id="multifactor_return_pred", primary_field_id="short_term_regime2_60d_single_quantile_pred", tag_suffix=tag),
            )
        )

    # --- Pack B (24 FULL, UNUSED_ALPHA0 FREE): USA/TOP3000/multifactor_return_pred ---
    q1_60 = "ts_backfill(long_term_quantile1_r60_pred, 21)"
    q5_60 = "ts_backfill(long_term_quantile5_r60_pred, 21)"
    s1_120 = "ts_backfill(long_term_seasonal_quantile1_r120_pred, 21)"
    r1_120 = "ts_backfill(long_term_regime2_quantile1_r120_pred, 21)"

    usa_exprs: list[tuple[str, str, str, str]] = [
        ("PC22-U1-q1-d5-ind", "ADMIN_ORIGINAL", "WL13229", f"group_zscore(ts_decay_linear({q1_60}, 5), industry)"),
        ("PC22-U2-q1-d10-sub", "ADMIN_ORIGINAL", "WL13229", f"group_rank(ts_decay_linear({q1_60}, 10), subindustry)"),
        ("PC22-U3-q5-d10-sub", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear({q5_60}, 10), subindustry)"),
        ("PC22-U4-q1-q5-d10", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_decay_linear(min(rank({q1_60}), rank({q5_60})), 10), subindustry)"),
        ("PC22-U5-q1-q5-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank({q1_60}), rank({q5_60})), 10), subindustry), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC22-U6-q1-tvr15", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(group_zscore({q1_60}, industry), lambda_min=0, lambda_max=0.9, target_tvr=0.15)"),
        ("PC22-U7-3way-q1-q5-s1", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank({q1_60}), min(rank({q5_60}), rank({s1_120}))), 10), subindustry)"),
        ("PC22-U8-3way-q1-q5-r1", "TOP100_2026Q4", "LD22811", f"group_rank(ts_decay_linear(min(rank({q1_60}), min(rank({q5_60}), rank({r1_120}))), 10), subindustry)"),
    ]
    for tag, neut, dec, trunc in [
        ("sub_d4_t08", "SUBINDUSTRY", 4, 0.08),
        ("crd_d4_t08", "CROWDING", 4, 0.08),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r22-USA-MF120-FREE-{tag}",
                campaign_id="S3_USA_MF120_ALPHA0_FULL",
                hypothesis_id="HYP-S3R22-USA-MF120-SH159-2Y217-SMOOTH-FREE",
                region="USA",
                universe="TOP3000",
                dataset_id="multifactor_return_pred",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(usa_exprs, dataset_id="multifactor_return_pred", primary_field_id="long_term_quantile1_r60_pred", tag_suffix=tag),
            )
        )

    return specs


def build_s3r21_asi_glbseason_free_specs() -> list[dict[str, Any]]:
    """S3-r21 (24 FULL, UNUSED_ALPHA0 FREE): ASI/MINVOL1M/global_seasonal_model FULL JPN + 2Y Finisher.

    Triggered by 2-hour Audit #14 (2026-11-27 04:51 CST):
      ASI/global_seasonal_model (100% Alphas=0 FREE, cov=1.000, dateCov=1.000, 0 OS -> SC=0.000!)
      exploded on Wave 1 (272 QUICK -> 89 S1 / 39 S2 / 12 S3 >= 1.58):
        - rK0kmNY1 (rev regime_120d_prob0): Sh=1.80
        - wpN6V2Kl (rev gneut d10): 16.13bp, Sh=1.67, Fit=1.19
        - blx30mzK / kq8R5WdK (m22): 32.62-37.76bp, Sh=1.60-1.65, Fit=1.15-1.19, TO=3.7%
        - LL8eeG2n / 3qGddp2O (monthquarter_120d_score3): Sh=1.57-1.64, 2Y=1.50-1.58, 21.76bp
      Immediately promotes to FULL (maxTrade=ON, ZERO quota cost!) across COUNTRY d={0,4} & CROWDING d=2
      to verify LOW_ASI_JPN_SHARPE & ROBUST_UNIVERSE while fusing 120d/60d horizons to lift 2Y >= 1.65!
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"
    p0 = "ts_backfill(analyst_regime_120d_return_quantile5_prob0, 21)"
    mq120 = "ts_backfill(analyst_monthquarter_120d_return_quantile5_score3, 21)"
    mq60 = "ts_backfill(analyst_monthquarter_60d_return_quantile5_score1, 21)"
    p3 = "ts_backfill(analyst_60d_return_quantile5_prob3, 21)"
    s2 = "ts_backfill(analyst_regime_60d_return_quantile5_score2, 21)"

    exprs: list[tuple[str, str, str, str]] = [
        ("PC21-A1-p0-d10-gneut-sub", "ADMIN_ORIGINAL", "WL13229", f"reverse(group_neutralize(ts_decay_linear({p0}, 10), subindustry))"),
        ("PC21-A2-p0-m22-ci", "ADMIN_ORIGINAL", "WL13229", f"reverse(group_zscore(ts_mean({p0}, 22), {ci}))"),
        ("PC21-A3-mq120-m22-sec", "ADMIN_ORIGINAL", "KH94146", f"group_rank(ts_mean({mq120}, 22), sector)"),
        ("PC21-A4-p0-mq120-d10-ci", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_decay_linear(min(rank(reverse({p0})), rank({mq120})), 10), {ci})"),
        ("PC21-A5-p0-mq120-m22-ci", "TOP100_2026Q4", "ZS59763", f"group_rank(ts_mean(min(rank(reverse({p0})), rank({mq120})), 22), {ci})"),
        ("PC21-A6-p0-mq120-tail25", "TOP100_2026Q4", "ZS59763", f"tail(group_rank(ts_decay_linear(min(rank(reverse({p0})), rank({mq120})), 10), {ci}), lower=0.25, upper=0.75, newval=0.5)"),
        ("PC21-A7-3way-p0-mq120-p3", "TOP100_2026Q4", "SZ83096", f"group_rank(ts_decay_linear(min(rank(reverse({p0})), min(rank({mq120}), rank({p3}))), 10), {ci})"),
        ("PC21-A8-mq60-s2-cty", "TOP100_2026Q4", "LD22811", f"group_rank(ts_mean(min(rank({mq60}), rank({s2})), 22), country)"),
    ]
    for tag, neut, dec, trunc in [
        ("cty_d0_t08", "COUNTRY", 0, 0.08),
        ("cty_d4_t08", "COUNTRY", 4, 0.08),
        ("crd_d2_t08", "CROWDING", 2, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r21-ASI-GLBSEASON-FREE-{tag}",
                campaign_id="S3_ASI_GLBSEASON_ALPHA0_FULL",
                hypothesis_id="HYP-S3R21-ASI-GLBSEASON-ALPHA0-37BP-JPN-2Y-FINISHER",
                region="ASI",
                universe="MINVOL1M",
                dataset_id="global_seasonal_model",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("ASI", "MINVOL1M", neut, decay=dec, truncation=trunc, max_trade="ON"),
                items=_build_items(exprs, dataset_id="global_seasonal_model", primary_field_id="analyst_regime_120d_return_quantile5_prob0", tag_suffix=tag),
            )
        )
    return specs


def build_s3r20_free_and_eur_margin_specs() -> list[dict[str, Any]]:
    """S3-r20: Phase-2 FREE USA/chart_cnn_alpha High-TO FULL Rescue (32 FULL) + EUR 1YG578aX High-Margin RAM Upgrade (16 FULL).

    Triggered by 2-hour Audit #13 (2026-11-27 02:56 CST):
      - Pack A (32 FULL, UNUSED_ALPHA0 FREE — runs immediately in Phase-2 at ZERO quota cost!):
        USA/chart_cnn_alpha exploded on Wave 1 with rK0mNeX8 (Sh=1.45, 2Y=2.74, TO=51.9%),
        RR5LemNg (Sh=1.36, 2Y=2.72, TO=51.4%), MPgAe0wa (Sh=1.33, 2Y=2.48, TO=56.4%) — ALL 3 fields
        live-verified alphaCount=0, cov=0.9964! Applies Universal High-TO Reduction Ladder
        (ts_decay_linear 5/10, ts_mean 5/10, ts_target_tvr_decay 0.15, hump 0.01, complementary CNN consensus).
      - Pack B (16 FULL, NORMAL — runs after Phase-2 / EST reset):
        1YG578aX (EUR/TOP2500/model77 x model110, RAM d=0) passed ALL official /check items 0-FAIL
        (Sh=2.39, 2Y=2.25, Fit=1.46, SC=0.260, PC=0.590, 0 collisions, Useful tagged!). Its SUBINDUSTRY
        sibling O06vZ7md hit 16.12bp but PC=0.779 (142 collisions!), proving RAM is the essential PC crusher.
        Meanwhile wpNVlEP1 (RAM d=5) already hit 11.09bp (Sh=2.20, 2Y=2.20, Fit=1.31) missing Sub-Uni by ONLY 0.04!
        Stay strictly on RAM d={3,5} with ultra-gentle adv20>{0.08,0.10,0.12} + post-min d5/d10 to push Margin 7.44->11-13bp!
    """
    specs: list[dict[str, Any]] = []
    ci = "group_cartesian_product(country, industry)"

    # --- Pack A (32 FULL, UNUSED_ALPHA0 FREE): USA/TOP3000/chart_cnn_alpha Universal High-TO Reduction ---
    t0 = "ts_backfill(img30d_return_tercile_confidence0_zackbatch, 21)"
    t2 = "ts_backfill(img30d_return_tercile_confidence2_zackbatch, 21)"
    q0 = "ts_backfill(img30d_return_quartile_confidence0_zackbatch, 21)"

    usa_cnn_exprs: list[tuple[str, str, str, str]] = [
        ("PC20-C1-t0-d5-ind", "ADMIN_ORIGINAL", "WL13229", f"reverse(group_zscore(ts_decay_linear({t0}, 5), industry))"),
        ("PC20-C2-t0-d10-ind", "ADMIN_ORIGINAL", "WL13229", f"reverse(group_zscore(ts_decay_linear({t0}, 10), industry))"),
        ("PC20-C3-t0-m5-ind", "ADMIN_ORIGINAL", "KH94146", f"reverse(group_zscore(ts_mean({t0}, 5), industry))"),
        ("PC20-C4-t0-m10-sub", "ADMIN_ORIGINAL", "KH94146", f"reverse(group_zscore(ts_mean({t0}, 10), subindustry))"),
        ("PC20-C5-t0-tvr15", "TOP100_2026Q4", "JX79797", f"ts_target_tvr_decay(reverse(group_zscore({t0}, industry)), lambda_min=0, lambda_max=0.9, target_tvr=0.15)"),
        ("PC20-C6-t0-hump01", "TOP100_2026Q4", "ZS59763", f"hump(reverse(group_zscore(ts_decay_linear({t0}, 5), industry)), hump=0.01)"),
        ("PC20-C7-t0-t2-d10", "TOP100_2026Q4", "SZ83096", f"group_zscore(ts_decay_linear(min(rank(reverse({t0})), rank({t2})), 10), subindustry)"),
        ("PC20-C8-t0-q0-d10", "TOP100_2026Q4", "LD22811", f"group_zscore(ts_decay_linear(min(rank(reverse({t0})), rank(reverse({q0}))), 10), subindustry)"),
    ]
    for tag, neut, dec, trunc in [
        ("sub_d4_t06", "SUBINDUSTRY", 4, 0.06),
        ("sub_d8_t08", "SUBINDUSTRY", 8, 0.08),
        ("ram_d4_t08", "REVERSION_AND_MOMENTUM", 4, 0.08),
        ("crd_d6_t08", "CROWDING", 6, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r20-USA-CNN-FREE-{tag}",
                campaign_id="S3_USA_CNN_ALPHA0_TOFIX",
                hypothesis_id="HYP-S3R20-USA-CHARTCNN-ALPHA0-2Y274-TO52-TO-15",
                region="USA",
                universe="TOP3000",
                dataset_id="chart_cnn_alpha",
                queue_type="UNUSED_ALPHA0",
                settings=_make_settings("USA", "TOP3000", neut, decay=dec, truncation=trunc),
                items=_build_items(usa_cnn_exprs, dataset_id="chart_cnn_alpha", primary_field_id="img30d_return_tercile_confidence0_zackbatch", tag_suffix=tag),
            )
        )

    # --- Pack B (16 FULL, NORMAL): EUR/TOP2500 1YG578aX (PC=0.590 Useful) RAM High-Margin Upgrade (7.44->11-13bp) ---
    dvm_gfp = "reverse(ts_backfill(mdl177_dvm_ttmgfp_alt, 21))"
    emm_eps = "reverse(ts_backfill(mdl177_emm_fc_epsrm_alt, 21))"
    m110_sc = "ts_backfill(mdl110_score, 21)"
    anl_sent = "ts_backfill(mdl110_analyst_sentiment, 21)"
    core_sc = f"min(rank({dvm_gfp}), min(rank({emm_eps}), rank({m110_sc})))"
    core_as = f"min(rank({dvm_gfp}), min(rank({emm_eps}), rank({anl_sent})))"

    eur_mgn_exprs: list[tuple[str, str, str, str]] = [
        ("PC20-E1-sc-adv08", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.08, group_zscore({core_sc}, {ci}), 0)"),
        ("PC20-E2-sc-adv10", "ADMIN_ORIGINAL", "WL13229", f"if_else(rank(adv20) > 0.1, group_zscore({core_sc}, {ci}), 0)"),
        ("PC20-E3-sc-adv12", "ADMIN_ORIGINAL", "KH94146", f"if_else(rank(adv20) > 0.12, group_zscore({core_sc}, {ci}), 0)"),
        ("PC20-E4-sc-postd5", "ADMIN_ORIGINAL", "KH94146", f"group_zscore(ts_decay_linear({core_sc}, 5), {ci})"),
        ("PC20-E5-sc-postd10", "TOP100_2026Q4", "ZS59763", f"group_zscore(ts_decay_linear({core_sc}, 10), {ci})"),
        ("PC20-E6-sc-d5-adv10", "TOP100_2026Q4", "ZS59763", f"if_else(rank(adv20) > 0.1, group_zscore(ts_decay_linear({core_sc}, 5), {ci}), 0)"),
        ("PC20-E7-sc-sp125", "TOP100_2026Q4", "SZ83096", f"signed_power(group_zscore({core_sc}, {ci}), 1.25)"),
        ("PC20-E8-as-adv10", "TOP100_2026Q4", "LD22811", f"if_else(rank(adv20) > 0.1, group_zscore({core_as}, {ci}), 0)"),
    ]
    for tag, neut, dec, trunc in [
        ("ram_d3_t08", "REVERSION_AND_MOMENTUM", 3, 0.08),
        ("ram_d5_t08", "REVERSION_AND_MOMENTUM", 5, 0.08),
    ]:
        specs.append(
            _pack(
                batch_id=f"S3-r20-EUR-1YG-HIGHMGN-{tag}",
                campaign_id="S3_EUR_1YG_RAM_HIGHMGN",
                hypothesis_id="HYP-S3R20-EUR-1YG578AX-RAM-KEEP-PC059-LIFT-11BP",
                region="EUR",
                universe="TOP2500",
                dataset_id="model77",
                queue_type="NORMAL",
                settings=_make_settings("EUR", "TOP2500", neut, decay=dec, truncation=trunc),
                items=_build_items(eur_mgn_exprs, dataset_id="model77", primary_field_id="mdl177_dvm_ttmgfp_alt", tag_suffix=tag),
            )
        )

    return specs


def build_pc_breakout_lab_s3r10_specs() -> list[dict[str, Any]]:
    """Return ordered S3-r23d (24 FULL FREE) -> S3-r23b (24 FULL FREE) -> S3-r23c (16 FULL FREE) -> S3-r23 (24 FULL) -> ..."""
    return (
        build_s3r23d_asi_mf120_robust_free_specs()
        + build_s3r23b_asi_mf120_sub_free_specs()
        + build_s3r23c_asi_qtile5_sub_free_specs()
        + build_s3r23_asi_mf120_robust_specs()
        + build_s3r22_mf120_free_specs()
        + build_s3r21_asi_glbseason_free_specs()
        + build_s3r20_free_and_eur_margin_specs()
        + build_asi_eur_s3r19_breakout_specs()
        + build_eur_s3r18_ortho_strike_specs()
        + build_eur_asi_s3r17_orthogonal_specs()
        + build_asi_eur_s3r16_controlled_specs()
        + build_clean_lowpc_controlled_s3r15_specs()
        + build_usa_e5m_1ax_margin_s3r14_specs()
        + build_usa_e5m_highmgn_s3r13_specs()
        + build_usa_stat_3ds_pc_finisher_s3r12_specs()
        + build_ortho_pc_breakout_s3r11_specs()
        + build_usa_pc_angle_ab_dist_specs()
        + build_usa_pc_angle_c_time_specs()
        + build_usa_pc_angle_d_ortho_specs()
        + build_usa_pc_angle_ef_nest_specs()
        + build_eur_pc_m25_breakout_specs()
        + build_eur_pc_m77_breakout_specs()
    )
