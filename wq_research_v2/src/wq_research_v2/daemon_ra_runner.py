"""Low-memory D1-Only RA Production Runner & Multi-Market Auto-Pivot Daemon for Guangzhou server (1.9 GiB RAM).

Strictly enforces:
- RA-Only D1 pipeline (PPA kept completely separate to avoid complexity/confusion)
- Delay = 1 hard lock, Decision #3 (NO add/multiply/trade_when), Gold 81 operator whitelist
- Hourly Audit #2 Pivot (v4):
  * Upgrades STAGE12_TEMPLATES_8 to 4 pure symmetric pairs (both + and - for 1-op raw industry zscore,
    10d decay subindustry rank, 22d smoothed subindustry zscore, and 66d ts_zscore subindustry rank)
    so neither fundamental level signals (ROA/model25/option) nor TS-change signals miss their sign!
  * Shifts firepower to Tier-1 High-Base institutional heavyweights:
    EUR/model25 (value/momentum/efficiency percentiles, 0 OS),
    USA/option_horizon_decomp (Alphas=0 Put/Call OI & Vol ratios + IV term spreads, 0 OS),
    GLB/model239 + sentiment26 + analyst15 (WDS blue-ocean + 2->3 quick-win),
    ASI/price_signal_dl (8 positive POOL_B seeds), USA/price_signal_dl (10 positive POOL_B seeds),
    DEU/fundamental6 (ROA |Sh|=1.05, 59.8bp Margin), HKG/news_sentiment_dl (+0.95), KOR/equity_forum_data (+0.76).
  * Cuts dead/0-hit directions (CHN/analyst45, DEU/other250, GBR/other250, IND/ai_news_scores).
- Automatic POSITIVE-Sharpe dataset-level early stop (immune to CHN borrow-cost double-negative mirage).
- 8-item Multi-Sim packing, weighted slot concurrency (GLB=2 slots), SQLite WAL checkpoints, zero /submit calls.
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.auth_session import BrainAuthSession
from wq_research_v2.batch_audit_logger import build_batch_audit_report, render_batch_audit_markdown
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date
from wq_research_v2.ra_evaluator import D1RAEvaluator
from wq_research_v2.seed_pruner import PruningConfig, prune_similar_seeds
from wq_research_v2.sim_runner import SimRunner
from wq_research_v2.stage23_refiner import build_all_stage23_refiner_specs

# Default high-Base institutional-alpha-first D1 exploration order (every region tracked independently!)
HIGH_BASE_MULTI_MARKET_ORDER: list[str] = [
    "EUR", "USA", "GLB", "ASI", "DEU", "HKG", "KOR"
]

# Verified clean D1 RA seed pools (ALL live-checked against cnhkmcp get_datafields on 2026-11-25).
CURATED_RA_D1_CAMPAIGNS: list[dict[str, Any]] = [
    # ==================== TIER 1: HIGH-BASE INSTITUTIONAL HEAVYWEIGHTS ====================
    {
        "campaign_id": "EUR_M25_PCT_NORM",
        "region": "EUR",
        "universe": "TOP2500",
        "dataset_id": "model25",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "INDUSTRY",
        "alt_neuts": ["SUBINDUSTRY", "COUNTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "value_momentum_region_percentile",
            "operating_efficiency_component_percentile",
            "exclusions_component_percentile",
            "regional_momentum_percentile",
            "mid_term_momentum_percentile",
            "long_term_momentum_percentile",
            "global_momentum_percentile",
            "mdl25_pcv421_81v",
        ],
    },
    {
        "campaign_id": "EUR_M238_SMARTHOLDINGS_NORM",
        "region": "EUR",
        "universe": "TOP2500",
        "dataset_id": "model238",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "CROWDING",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "COUNTRY", "SUBINDUSTRY"],
        "fields": [
            "regional_peer_investment_concentration_rank_d1",
            "global_screening_factor_alignment_rank_d1",
            "regional_change_in_preference_rank_d1",
            "regional_institutional_preference_rank_d1",
            "global_peer_investment_concentration_rank_d1",
            "global_change_in_preference_rank_d1",
            "country_relative_investment_rank_d1",
            "regional_screening_factor_alignment_rank_d1",
        ],
    },
    {
        "campaign_id": "EUR_M77_CAPIQ_NORM",
        "region": "EUR",
        "universe": "TOP2500",
        "dataset_id": "model77",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["CROWDING", "COUNTRY", "SUBINDUSTRY"],
        "fields": [
            "mdl177_pmm_actrtn24m_2",
            "mdl177_pmm_p50_200ratio_2",
            "mdl177_pmm_indrelrtn5d_2",
            "mdl177_pmm_slope52wp_alt",
            "mdl177_dvm_past_alt",
            "mdl177_emm_fc_rev3y2_alt",
            "mdl177_emm_fc_stdevfy1epsp_alt",
            "mdl177_qvm_ev_qvaeur_alt",
        ],
    },
    {
        "campaign_id": "EUR_OTH455_N2V_NORM",
        "region": "EUR",
        "universe": "TOP2500",
        "dataset_id": "other455",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["CROWDING", "COUNTRY", "SUBINDUSTRY"],
        "fields": [
            "oth455_competitor_n2v_p10_q200_w2_pca_fact1_value",
            "oth455_competitor_n2v_p10_q200_w3_pca_fact1_value",
            "oth455_competitor_n2v_p10_q200_w3_pca_fact2_value",
            "oth455_competitor_n2v_p10_q200_w1_pca_fact3_value",
            "oth455_competitor_n2v_p10_q200_w2_pca_fact3_value",
            "oth455_competitor_n2v_p10_q200_w3_pca_fact3_value",
            "oth455_competitor_n2v_p10_q200_w1_pca_fact2_value",
            "oth455_competitor_n2v_p10_q200_w2_pca_fact2_value",
        ],
    },
    # EUR_AIEQ_ALPHA_VEC_NORM retired at 2-Hour Audit #3 (72% Sim ERROR/stall rate, 0/24 hits, max=0.68).
    {
        "campaign_id": "USA_OTH580_ETF_FREE",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "other580",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["CROWDING", "SUBINDUSTRY", "INDUSTRY"],
        "fields": [
            "change_sqrt_weighted_count",
            "change_cubed_sum_5d",
            "change_log_weighted_cubed_sum_2",
            "change_sqrt_weighted_cubed_sum",
            "change_sqrt_weighted_simple_sum",
            "change_cubed_sum",
            "change_log_weighted_squared_sum",
            "change_log_weighted_sum",
        ],
    },
    {
        "campaign_id": "USA_PVTECH_MATRIX_NORM",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "pv_tech_indicators",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["CROWDING", "SUBINDUSTRY", "INDUSTRY"],
        "fields": [
            "price_change_index",
            "price_change_intensity",
            "price_fluctuation_index",
            "price_fluctuation_score",
            "price_movement_index",
            "price_movement_score",
            "price_reversal_index",
            "price_trend_factor",
        ],
    },
    # USA_M68_DREAM_VEC_NORM (56 FULL, max=0.82, 2Y=0.27) & USA_FWDBETA_VEC_NORM (120 FULL, max=0.99, 0>=1.25)
    # retired at 2-Hour Audit #3 in favor of pure-MATRIX USA_OTH580_ETF_FREE (Alphas=0) & USA_PVTECH_MATRIX_NORM (val=6.0).
    {
        "campaign_id": "GLB_M239_SHORT_NORM",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "model239",
        "queue_type": "NORMAL",
        "field_type": "VECTOR",
        "default_neut": "COUNTRY",
        "alt_neuts": ["SUBINDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "mdl239_combo_loanrate2",
            "mdl239_combo_tickets",
            "mdl239_combo_crossdeltaactivity",
            "mdl239_combo_deltacrossdelta",
            "mdl239_combo_utilisation_x_rate",
            "mdl239_combo_ltdelta",
            "mdl239_combo_deltarate",
            "mdl239_combo_deltaactivity",
        ],
    },
    {
        "campaign_id": "GLB_SNT26_NORM",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "sentiment26",
        "queue_type": "NORMAL",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["COUNTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "snt26_top25pctranking_41",
            "snt26_top75pctranking_44",
            "snt26_top10pctranking_29",
            "snt26_top50pctranking_42",
            "snt26_top50pctrankingavg_37",
            "snt26_topranking_33",
            "snt26_avgranking_40",
        ],
    },
    {
        "campaign_id": "GLB_ANL15_2TO3",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "analyst15",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["INDUSTRY", "COUNTRY"],
        "fields": [
            "anl15_gr_cal_fy1_3m_chg",
            "anl15_gr_18_m_3m_chg",
            "anl15_gr_cal_fy2_3m_chg",
            "anl15_gr_cal_fy1_mean",
        ],
    },
    {
        "campaign_id": "ASI_PRICEDL_DUAL_LOWTO",
        "region": "ASI",
        "universe": "MINVOL1M",
        "dataset_id": "price_signal_dl",
        "queue_type": "NORMAL",
        "field_type": "CUSTOM_EXPRS",
        "max_trade": "ON",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["SUBINDUSTRY", "COUNTRY"],
        "custom_base_exprs": [
            ("asi_nv2_m22", "ts_mean(ts_backfill(normalized_volume_indicator_2, 21), 22)"),
            ("asi_nv0_m22", "ts_mean(ts_backfill(normalized_volume_indicator_0, 21), 22)"),
            ("asi_nv1_m22", "ts_mean(ts_backfill(normalized_volume_indicator_1, 21), 22)"),
            ("asi_rt4_m22", "ts_mean(ts_backfill(raw_trend_indicator_4, 21), 22)"),
            (
                "asi_dual_nv2_rt4",
                "min(rank(ts_decay_linear(ts_backfill(normalized_volume_indicator_2, 21), 10)), rank(ts_decay_linear(ts_backfill(raw_trend_indicator_4, 21), 10)))",
            ),
            (
                "asi_dual_nv2_nt5",
                "min(rank(ts_decay_linear(ts_backfill(normalized_volume_indicator_2, 21), 10)), rank(ts_decay_linear(ts_backfill(normalized_trend_indicator_5, 21), 10)))",
            ),
            (
                "asi_dual_nv0_nt3",
                "min(rank(ts_decay_linear(ts_backfill(normalized_volume_indicator_0, 21), 10)), rank(ts_decay_linear(ts_backfill(normalized_trend_indicator_3, 21), 10)))",
            ),
        ],
    },
    {
        "campaign_id": "USA_PRICEDL_TREND_VOL_NORM",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "price_signal_dl",
        "queue_type": "NORMAL",
        "field_type": "CUSTOM_EXPRS",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["CROWDING", "MARKET"],
        "custom_base_exprs": [
            ("usa_v6_raw", "ts_backfill(raw_volume_indicator_6, 21)"),
            ("usa_rt6_raw", "ts_backfill(raw_trend_indicator_6, 21)"),
            ("usa_rt1_raw", "ts_backfill(raw_trend_indicator_1, 21)"),
            ("usa_rt4_raw", "ts_backfill(raw_trend_indicator_4, 21)"),
            (
                "usa_dual_v6_t6",
                "min(rank(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10)), rank(ts_decay_linear(ts_backfill(raw_trend_indicator_6, 21), 10)))",
            ),
            (
                "usa_dual_v6_t4",
                "min(rank(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10)), rank(ts_decay_linear(ts_backfill(raw_trend_indicator_4, 21), 10)))",
            ),
            (
                "usa_dual_v6_t1",
                "min(rank(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10)), rank(ts_decay_linear(ts_backfill(raw_trend_indicator_1, 21), 10)))",
            ),
            (
                "usa_dual_nv2_t6",
                "min(rank(ts_decay_linear(ts_backfill(normalized_volume_indicator_2, 21), 10)), rank(ts_decay_linear(ts_backfill(raw_trend_indicator_6, 21), 10)))",
            ),
        ],
    },
    # EUR_PRICEDL_NORM retired at 2-Hour Audit #1 (148 FULL completed, 0 >= 1.25, max=1.22, max_fit=0.36).
    # Replaced by EUR_M238_SMARTHOLDINGS_NORM (aCnt=0..3, cov=96.27%) + S3_EUR_M25_PC_CRUSH.
    {
        "campaign_id": "ASI_BEHAV_RA",
        "region": "ASI",
        "universe": "MINVOL1M",
        "dataset_id": "behavioral_signals",
        "queue_type": "NORMAL",
        "field_type": "VECTOR",
        "max_trade": "ON",
        "default_neut": "COUNTRY",
        "alt_neuts": ["SUBINDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "extreme_daily_return_indicator",
            "salience_weighted_return_score",
            "price_path_curvature_measure",
            "visual_price_path_shape_score",
            "chronological_return_sequence_correlation",
            "consecutive_return_streak_length",
        ],
    },
    # ==================== TIER 2: HIGH-MULTIPLIER / PROVEN SEED MARKETS ====================
    {
        "campaign_id": "DEU_FND6_RATIOS",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "fundamental6",
        "queue_type": "NORMAL",
        "field_type": "CUSTOM_EXPRS",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "custom_base_exprs": [
            ("fnd6_roa", "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_roe", "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_ewq_teqq, 126)))"),
            ("fnd6_cash_at", "divide(ts_backfill(fnd6_newq_cheq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_gp_at", "divide(ts_backfill(fnd6_gpsa, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_cf_at", "divide(ts_backfill(fnd6_chechy, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_rev_at", "divide(ts_backfill(fnd6_revty, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_lev", "divide(ts_backfill(fnd6_ewq_lltq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_intan", "divide(ts_backfill(fnd6_ewq_intanq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            (
                "fnd6_dual_roa_gp",
                "min(rank(divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))), rank(divide(ts_backfill(fnd6_gpsa, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))))",
            ),
            (
                "fnd6_dual_roa_cf",
                "min(rank(divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))), rank(divide(ts_backfill(fnd6_chechy, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))))",
            ),
        ],
    },
    {
        "campaign_id": "HKG_NEWSDL_FREE",
        "region": "HKG",
        "universe": "TOP800",
        "dataset_id": "news_sentiment_dl",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "max_trade": "ON",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["INDUSTRY", "SUBINDUSTRY"],
        "fields": [
            "min_positive_word_sentiment_inferess",
            "positive_word_sentiment_entropy_inferess",
            "positive_word_sentiment_stddev_inferess",
            "text_complexity_score_inferess",
            "sentence_count_inferess",
            "avg_words_per_sentence_inferess",
        ],
    },
    {
        "campaign_id": "KOR_FORUM_NORM",
        "region": "KOR",
        "universe": "TOP600",
        "dataset_id": "equity_forum_data",
        "queue_type": "NORMAL",
        "field_type": "VECTOR",
        "max_trade": "ON",
        "default_neut": "INDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "SUBINDUSTRY"],
        "fields": [
            "distinct_user_count_per_platform",
            "total_distinct_participants_count",
            "aggregate_comment_volume",
            "aggregate_buy_opinion_score",
            "aggregate_sell_opinion_score",
        ],
    },
]


# 8 clean 5:5 Stage-1/Stage-2 RA templates (4 ADMIN_ORIGINAL : 4 TOP100_2026Q4).
# v4: 4 pure symmetric (+/-) pairs covering:
#   1) 1-op zero-smoothing industry zscore (Guangzhou historical Sh=3.26/Fit=2.77 champion!)
#   2) 22d smoothed subindustry zscore (captures fundamental ROA +1.05/59.8bp & low-TO options!)
#   3) 10d decay subindustry rank (captures USA +1.10/2Y 1.85 & ASI +1.13/2Y 1.40!)
#   4) 66d ts_zscore subindustry rank (captures momentum/change signals!)
# Strictly ZERO add/multiply/trade_when, ZERO decay > 252, ZERO lambda_max > 1.
TEMPLATE_SET_VER = "v4"
STAGE12_TEMPLATES_8: list[dict[str, str]] = [
    {"id": "RA-ADM-01-sub-gz-m22-pos", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "group_zscore(ts_mean({x}, 22), subindustry)"},
    {"id": "RA-ADM-02-rev-sub-gz-m22", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(group_zscore(ts_mean({x}, 22), subindustry))"},
    {"id": "RA-ADM-03-sub-grank-dec10-pos", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "group_rank(ts_decay_linear({x}, 10), subindustry)"},
    {"id": "RA-ADM-04-rev-sub-grank-dec10", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(group_rank(ts_decay_linear({x}, 10), subindustry))"},
    {"id": "RA-TOP-01-sub-grank-z66-pos", "side": "TOP100_2026Q4", "author": "SZ83096", "fmt": "group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry)"},
    {"id": "RA-TOP-02-rev-sub-grank-z66", "side": "TOP100_2026Q4", "author": "SZ83096", "fmt": "reverse(group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry))"},
    {"id": "RA-TOP-03-ind-gz-raw-pos", "side": "TOP100_2026Q4", "author": "LD22811", "fmt": "group_zscore({x}, industry)"},
    {"id": "RA-TOP-04-rev-ind-gz-raw", "side": "TOP100_2026Q4", "author": "LD22811", "fmt": "reverse(group_zscore({x}, industry))"},
]


def _wrap_field(field_id: str, field_type: str, backfill_days: int = 21) -> str:
    if field_type == "VECTOR":
        return f"ts_backfill(vec_avg({field_id}), {backfill_days})"
    return f"ts_backfill({field_id}, {backfill_days})"


def build_ra_campaign_specs(
    *,
    campaigns: Optional[list[dict[str, Any]]] = None,
    include_dual_branch: bool = True,
    include_alt_neut: bool = True,
) -> list[dict[str, Any]]:
    """Build deterministic, 5:5 balanced, Decision-#3 compliant D1 RA specs (8 tasks per batch)."""
    camp_list = campaigns or CURATED_RA_D1_CAMPAIGNS
    specs: list[dict[str, Any]] = []

    for camp in camp_list:
        cid = camp["campaign_id"]
        reg = camp["region"]
        uni = camp["universe"]
        ds = camp["dataset_id"]
        qtype = camp["queue_type"]
        ftype = camp["field_type"]
        max_trade = camp.get("max_trade", "OFF")
        neuts = [camp["default_neut"]] + (camp.get("alt_neuts") or [] if include_alt_neut else [])

        if ftype == "CUSTOM_EXPRS":
            base_list = camp.get("custom_base_exprs") or []
            for neut in neuts:
                for c_idx, (name, base_expr) in enumerate(base_list):
                    items = [
                        {
                            "expression": t["fmt"].format(x=base_expr),
                            "template_id": f"{t['id']}_{neut}",
                            "source_side": t["side"],
                            "author_id": t["author"],
                            "dataset_id": ds,
                            "primary_field_id": name,
                        }
                        for t in STAGE12_TEMPLATES_8
                    ]
                    specs.append({
                        "batch_id": f"RA-{TEMPLATE_SET_VER}-{cid}-{c_idx:02d}-{name}-{neut}",
                        "campaign_id": cid,
                        "hypothesis_id": f"HYP-{cid}",
                        "queue_type": qtype,
                        "source_side": "MIXED_4_4",
                        "region": reg,
                        "universe": uni,
                        "dataset_id": ds,
                        "settings": {
                            "region": reg, "universe": uni, "delay": 1,
                            "neutralization": neut, "decay": 0, "truncation": 0.04,
                            "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                            "maxTrade": max_trade, "visualization": False,
                        },
                        "items": items,
                    })
            continue

        fields = camp.get("fields") or []
        for neut in neuts:
            for f_idx, fid in enumerate(fields):
                wrapped = _wrap_field(fid, ftype)
                items = [
                    {
                        "expression": t["fmt"].format(x=wrapped),
                        "template_id": f"{t['id']}_{neut}",
                        "source_side": t["side"],
                        "author_id": t["author"],
                        "dataset_id": ds,
                        "primary_field_id": fid,
                    }
                    for t in STAGE12_TEMPLATES_8
                ]
                specs.append({
                    "batch_id": f"RA-{TEMPLATE_SET_VER}-{cid}-{f_idx:02d}-{fid[-16:]}-{neut}",
                    "campaign_id": cid,
                    "hypothesis_id": f"HYP-{cid}",
                    "queue_type": qtype,
                    "source_side": "MIXED_4_4",
                    "region": reg,
                    "universe": uni,
                    "dataset_id": ds,
                    "settings": {
                        "region": reg, "universe": uni, "delay": 1,
                        "neutralization": neut, "decay": 0, "truncation": 0.04,
                        "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                        "maxTrade": max_trade, "visualization": False,
                    },
                    "items": items,
                })

            # Decision #3 canonical dual-branch pairs (same dataset -> keeps ATOM!)
            if include_dual_branch and len(fields) >= 2:
                pair_items = []
                for f1, f2 in list(itertools.combinations(fields[:8], 2))[:8]:
                    w1 = _wrap_field(f1, ftype)
                    w2 = _wrap_field(f2, ftype)
                    expr_a = f"ts_decay_linear({w1}, 10)"
                    expr_b = f"ts_decay_linear({w2}, 10)"
                    pair_items.append({
                        "expression": f"group_rank(min(rank({expr_a}), rank({expr_b})), subindustry)",
                        "template_id": f"RA-DUAL-GRANK-MIN-{neut}",
                        "source_side": "ADMIN_ORIGINAL",
                        "author_id": "WL13229",
                        "dataset_id": ds,
                        "primary_field_id": f1,
                    })
                    pair_items.append({
                        "expression": f"reverse(group_rank(min(rank({expr_a}), rank({expr_b})), subindustry))",
                        "template_id": f"RA-DUAL-REV-GRANK-MIN-{neut}",
                        "source_side": "TOP100_2026Q4",
                        "author_id": "SZ83096",
                        "dataset_id": ds,
                        "primary_field_id": f1,
                    })
                for chunk_i in range(0, len(pair_items), 8):
                    sub = pair_items[chunk_i : chunk_i + 8]
                    if len(sub) >= 2:
                        specs.append({
                            "batch_id": f"RA-{TEMPLATE_SET_VER}-{cid}-DUAL-{neut}-{chunk_i//8:02d}",
                            "campaign_id": cid,
                            "hypothesis_id": f"HYP-{cid}-DUAL",
                            "queue_type": qtype,
                            "source_side": "MIXED_4_4",
                            "region": reg,
                            "universe": uni,
                            "dataset_id": ds,
                            "settings": {
                                "region": reg, "universe": uni, "delay": 1,
                                "neutralization": neut, "decay": 0, "truncation": 0.04,
                                "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                                "maxTrade": max_trade, "visualization": False,
                            },
                            "items": sub,
                        })

    return specs


def interleave_specs_by_campaign_waves(
    specs: list[dict[str, Any]],
    *,
    max_slots: int = 4,
    waves_per_turn: int = 1,
) -> list[dict[str, Any]]:
    """Round-robin interleave specs by Region -> Campaign in wave-sized slices."""
    if waves_per_turn <= 0:
        return list(specs)

    by_reg_camps: dict[str, deque[deque[dict[str, Any]]]] = {}
    camp_map: dict[tuple[str, str], deque[dict[str, Any]]] = {}
    reg_order: list[str] = []

    for s in specs:
        reg = str(s["region"]).upper()
        cid = str(s.get("campaign_id") or f"{reg}_{s['dataset_id']}")
        if reg not in by_reg_camps:
            by_reg_camps[reg] = deque()
            reg_order.append(reg)
        key = (reg, cid)
        if key not in camp_map:
            q: deque[dict[str, Any]] = deque()
            camp_map[key] = q
            by_reg_camps[reg].append(q)
        camp_map[key].append(s)

    out: list[dict[str, Any]] = []
    active_regs = deque(reg_order)
    while active_regs:
        reg = active_regs.popleft()
        camp_queues = by_reg_camps[reg]
        while camp_queues and not camp_queues[0]:
            camp_queues.popleft()
        if not camp_queues:
            continue
        q = camp_queues.popleft()
        weight = 2 if reg == "GLB" else 1
        slice_len = max(1, max_slots // weight) * waves_per_turn
        for _ in range(slice_len):
            if q:
                out.append(q.popleft())
        if q:
            camp_queues.append(q)
        if camp_queues:
            active_regs.append(reg)
    return out


def should_early_stop_dataset(
    ledger: LedgerStore,
    *,
    region: str,
    dataset_id: str,
    min_completed: int = 48,
    min_pos_sharpe: float = 0.80,
    min_hit_rate: float = 0.02,
    strong_pos_sharpe: float = 1.25,
) -> tuple[bool, dict[str, Any]]:
    """Check SQLite POSITIVE-Sharpe performance for (region, dataset_id) to auto-stop dead directions.

    Strictly checks positive Sharpe (not ABS(sharpe)) because high short-borrow-cost regions like CHN
    produce negative Sharpe (-1.5..-2.5) on BOTH +x and -x for zero-alpha noise signals!
    """
    row = ledger._conn.execute(
        """
        SELECT
            COUNT(*) AS completed,
            SUM(CASE WHEN COALESCE(sharpe, -999.0) >= ? THEN 1 ELSE 0 END) AS pos_hits_08,
            SUM(CASE WHEN COALESCE(sharpe, -999.0) >= ? THEN 1 ELSE 0 END) AS pos_hits_strong,
            MAX(sharpe) AS max_pos_sh
        FROM sim_tasks
        WHERE region = ? AND dataset_id = ? AND status IN ('COMPLETED_FULL', 'COMPLETED_QUICK')
        """,
        (min_pos_sharpe, strong_pos_sharpe, region.upper(), dataset_id),
    ).fetchone()
    completed = int(row["completed"] or 0)
    pos_hits_08 = int(row["pos_hits_08"] or 0)
    pos_hits_strong = int(row["pos_hits_strong"] or 0)
    max_pos_sh = round(float(row["max_pos_sh"]), 3) if row["max_pos_sh"] is not None else None
    hit_rate = (pos_hits_08 / completed) if completed > 0 else 0.0
    stats = {
        "completed": completed,
        "hits_08": pos_hits_08,
        "hits_strong": pos_hits_strong,
        "max_pos_sh": max_pos_sh,
        "hit_rate": round(hit_rate, 4),
    }
    if min_completed > 0 and completed >= min_completed and pos_hits_strong == 0 and hit_rate < min_hit_rate:
        return True, stats
    return False, stats


def export_funnel_snapshot(
    ledger: LedgerStore,
    region: str,
    *,
    pruning_config: PruningConfig = PruningConfig(),
) -> Path:
    """Persist non-destructive per-region tiered funnel snapshot + pruned Stage-2/3 seed queue."""
    from wq_research_v2.config_loader import DATA_DIR

    reg = region.upper()
    rows = [
        dict(r)
        for r in ledger._conn.execute(
            """
            SELECT task_id, batch_id, region, dataset_id, primary_field_id, template_id, source_side,
                   alpha_id, expression, sharpe, fitness, turnover, margin, returns, sharpe_2y, status
            FROM sim_tasks
            WHERE region=? AND status IN ('COMPLETED_FULL','COMPLETED_QUICK')
            ORDER BY sharpe DESC
            """,
            (reg,),
        ).fetchall()
    ]
    pools: dict[str, list[dict[str, Any]]] = {
        "POOL_S_SH158_FIT1": [],
        "POOL_A_NEAR_SH125": [],
        "POOL_B_SEED_SH080": [],
        "POOL_FLIP_SH_LT_NEG120": [],
    }
    for r in rows:
        sh = r.get("sharpe")
        fit = r.get("fitness")
        if sh is None:
            continue
        if sh > 1.58 and (fit or 0) > 1.0:
            pools["POOL_S_SH158_FIT1"].append(r)
        elif sh >= 1.25:
            pools["POOL_A_NEAR_SH125"].append(r)
        elif sh > 0.80:
            pools["POOL_B_SEED_SH080"].append(r)
        elif sh < -1.20:
            pools["POOL_FLIP_SH_LT_NEG120"].append(r)

    pruned_s, dropped_s = prune_similar_seeds(pools["POOL_S_SH158_FIT1"], config=pruning_config)
    pruned_a, dropped_a = prune_similar_seeds(pools["POOL_A_NEAR_SH125"], config=pruning_config)
    pruned_b, dropped_b = prune_similar_seeds(pools["POOL_B_SEED_SH080"], config=pruning_config)

    out_path = DATA_DIR / "exports" / f"{reg.lower()}_ra_funnel_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "region": reg,
        "delay": 1,
        "total_completed": len(rows),
        "counts": {k: len(v) for k, v in pools.items()},
        "pruning_config": {
            "jaccard_max": pruning_config.jaccard_max,
            "max_per_field": pruning_config.max_per_field,
            "max_per_dataset": pruning_config.max_per_dataset,
        },
        "pruned_counts": {
            "POOL_S_PRUNED": len(pruned_s),
            "POOL_A_PRUNED": len(pruned_a),
            "POOL_B_PRUNED": len(pruned_b),
            "total_similar_pruned": len(dropped_s) + len(dropped_a) + len(dropped_b),
        },
        "top_pool_s": pruned_s[:50],
        "top_pool_a": pruned_a[:50],
        "top_pool_b": pruned_b[:50],
        "top_pool_flip": pools["POOL_FLIP_SH_LT_NEG120"][:50],
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        audit_rep = build_batch_audit_report(ledger.db_path)
        (DATA_DIR / "exports" / "batch_audit_latest.json").write_text(
            json.dumps(audit_rep, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (DATA_DIR / "exports" / "batch_audit_latest.md").write_text(
            render_batch_audit_markdown(audit_rep), encoding="utf-8"
        )
    except Exception:
        pass
    return out_path


def parse_region_caps(spec_str: Optional[str]) -> dict[str, int]:
    """Parse CLI `--region-caps EUR:1,USA:3` into `{region: max_slots}`."""
    caps: dict[str, int] = {}
    if not spec_str:
        return caps
    for part in str(spec_str).split(","):
        part = part.strip()
        if ":" not in part:
            continue
        reg, val = part.split(":", 1)
        reg_u = reg.strip().upper()
        try:
            n = int(val.strip())
        except ValueError:
            continue
        if reg_u and n > 0:
            caps[reg_u] = n
    return caps


def run_ra_production_loop(
    *,
    regions: Optional[list[str]] = None,
    max_slots: int = 4,
    max_per_region: int = 2,
    region_caps: Optional[dict[str, int]] = None,
    post_stagger_sec: float = 2.0,
    batch_size: int = 8,
    simulation_mode: str = "FULL",
    daily_target: int = 4500,
    max_batches: Optional[int] = None,
    sleep_between_batches_sec: float = 1.0,
    only_free_alpha0: bool = False,
    round_robin_waves: int = 1,
    early_stop_min_sims: int = 48,
    early_stop_min_pos_sharpe: float = 0.80,
    include_stage23_refiner: bool = True,
    pruning_config: PruningConfig = PruningConfig(),
) -> dict[str, Any]:
    """Run low-memory D1 RA continuous rolling multi-region pipeline (zero wave barrier, 2-4 concurrent threads)."""
    ledger = LedgerStore()
    quota = QuotaTracker(ledger)
    auth = BrainAuthSession(quota_observer=quota.observe_response)
    bl = BlacklistRegistry(ledger)
    clean_region_caps = {str(k).upper(): int(v) for k, v in (region_caps or {}).items() if int(v) > 0}
    runner = SimRunner(
        auth,
        ledger,
        quota,
        blacklist_registry=bl,
        max_slots=max_slots,
        max_per_region=max_per_region,
        region_caps=clean_region_caps,
        post_stagger_sec=post_stagger_sec,
        max_post_429_retries=4,
        poll_interval_sec=4.0,
        poll_timeout_sec=720.0,
        stall_timeout_sec=240.0,
    )
    evaluator = D1RAEvaluator()

    selected_campaigns = list(CURATED_RA_D1_CAMPAIGNS)
    ordered_regs = [r.strip().upper() for r in regions if r.strip()] if regions else list(HIGH_BASE_MULTI_MARKET_ORDER)
    reg_rank = {r: i for i, r in enumerate(ordered_regs)}
    if regions:
        selected_campaigns = [c for c in selected_campaigns if c["region"].upper() in reg_rank]
        selected_campaigns.sort(key=lambda c: reg_rank[c["region"].upper()])

    stage1_specs = build_ra_campaign_specs(campaigns=selected_campaigns)
    refiner_specs: list[dict[str, Any]] = []
    if include_stage23_refiner:
        refiner_specs = [
            s for s in build_all_stage23_refiner_specs()
            if (not regions) or (str(s["region"]).upper() in reg_rank)
        ]

    # Put Stage-2/3 targeted refinement specs FIRST so proven winners climb 1.0->1.3-1.4->1.6+ immediately!
    specs = refiner_specs + stage1_specs
    if only_free_alpha0:
        specs = [s for s in specs if s.get("queue_type") == "UNUSED_ALPHA0"]
    if round_robin_waves > 0:
        specs = interleave_specs_by_campaign_waves(specs, max_slots=max_slots, waves_per_turn=round_robin_waves)

    # Build alpha0 map for validation (handles fields, custom_base_exprs, and Stage-2/3 free refiner specs)
    alpha0_map: dict[str, int] = {
        "raw_volume_indicator_6": 0,
        "raw_volume_indicator_3": 0,
        "raw_volume_indicator_5": 0,
        "normalized_volume_indicator_2": 0,
    }
    for camp in CURATED_RA_D1_CAMPAIGNS:
        if camp["queue_type"] == "UNUSED_ALPHA0":
            for f in camp.get("fields") or []:
                alpha0_map[f] = 0
            for _, expr in camp.get("custom_base_exprs") or []:
                for tok in expr.replace("(", " ").replace(")", " ").replace(",", " ").split():
                    if tok.startswith((
                        "oth496_",
                        "raw_volume_indicator_",
                        "normalized_volume_indicator_",
                        "put_call_",
                        "implied_volatility_",
                    )):
                        alpha0_map[tok] = 0

    auth.authenticate()
    auth.start_background_monitors()
    batches_executed = 0
    total_completed = 0
    gate1_hits = 0
    gate3_hits = 0
    early_stopped_keys: set[tuple[str, str]] = set()

    print(
        f"[RA-DAEMON] Started Continuous Rolling D1-Only RA runner | regions={regions or 'HIGH_BASE_ALL'} | specs={len(specs)} | "
        f"slots={max_slots} (max_per_region={max_per_region}, region_caps={clean_region_caps or 'default'}) | "
        f"batch={batch_size} | stagger={post_stagger_sec}s | mode={simulation_mode} | daily_target={daily_target} | early_stop_sims={early_stop_min_sims}",
        flush=True,
    )

    try:
        # Interleave batches proportionally to per-region caps (e.g. 1 EUR : 3 USA) so continuous pool
        # keeps all 4 threads saturated with zero idle slots and zero EUR compute-node thrashing!
        by_reg_q: dict[str, deque[dict[str, Any]]] = {}
        reg_cycle: list[str] = []
        for s in specs:
            r = str(s["region"]).upper()
            if r not in by_reg_q:
                by_reg_q[r] = deque()
                reg_cycle.append(r)
            by_reg_q[r].append(s)

        interleaved_specs: list[dict[str, Any]] = []
        active_r = deque(reg_cycle)
        while active_r:
            r = active_r.popleft()
            take_n = max(1, int(clean_region_caps.get(r, max_per_region)))
            for _ in range(take_n):
                if by_reg_q[r]:
                    interleaved_specs.append(by_reg_q[r].popleft())
            if by_reg_q[r]:
                active_r.append(r)

        # Process in rolling super-windows of 16 specs (up to 128 alphas) so early-stop & daily-target
        # stay responsive while eliminating wave barriers completely!
        window_size = max(8, max_slots * 4)
        idx = 0
        while idx < len(interleaved_specs):
            est_day = current_est_platform_date()
            day_stats = ledger.compute_daily_summary(est_day)
            day_done = int(day_stats.get("full_valid_completed_count", 0)) + int(day_stats.get("quick_screened_count", 0))
            last_rem = quota.last_snapshot.remaining_val if (quota.last_snapshot and quota.last_snapshot.endpoint == "/simulations") else None
            if day_done >= daily_target or (last_rem is not None and last_rem <= 80):
                print(
                    f"[RA-DAEMON] Daily target/safety cap reached (day_done={day_done}/{daily_target}, "
                    f"api_rem={last_rem}) on EST {est_day}; sleeping 300s.",
                    flush=True,
                )
                if max_batches is not None:
                    break
                time.sleep(300)
                continue

            if max_batches is not None and batches_executed >= max_batches:
                break

            prepared_window: list[dict[str, Any]] = []
            while idx < len(interleaved_specs) and len(prepared_window) < window_size:
                if max_batches is not None and (batches_executed + len(prepared_window)) >= max_batches:
                    break
                spec = interleaved_specs[idx]
                idx += 1
                reg = str(spec["region"]).upper()
                ds = str(spec.get("dataset_id") or "")
                ds_key = (reg, ds)
                if ds_key in early_stopped_keys:
                    continue
                stop_now, ds_stats = should_early_stop_dataset(
                    ledger,
                    region=reg,
                    dataset_id=ds,
                    min_completed=early_stop_min_sims,
                    min_pos_sharpe=early_stop_min_pos_sharpe,
                )
                if stop_now:
                    early_stopped_keys.add(ds_key)
                    print(
                        f"[EARLY-STOP] Demoting weak direction {reg}/{ds}: "
                        f"completed={ds_stats['completed']} pos_hits(sh>={early_stop_min_pos_sharpe})={ds_stats['hits_08']} "
                        f"max_pos_sh={ds_stats['max_pos_sh']} -> pivoting to next dataset/market!",
                        flush=True,
                    )
                    continue
                bid, runnable, _ = runner.prepare_batch_tasks(
                    spec,
                    simulation_mode=simulation_mode,
                    field_alpha_counts=alpha0_map if spec["queue_type"] == "UNUSED_ALPHA0" else None,
                )
                if runnable:
                    prepared_window.append({"batch_id": bid, "region": reg, "dataset_id": ds, "tasks": runnable})

            if not prepared_window:
                continue

            completed_in_win = 0
            touched_regions: set[str] = set()

            def _should_stop_now() -> bool:
                if max_batches is not None and batches_executed >= max_batches:
                    return True
                rem_snap = quota.last_snapshot
                if rem_snap and rem_snap.endpoint == "/simulations" and rem_snap.remaining_val is not None and rem_snap.remaining_val <= 80:
                    return True
                return (day_done + completed_in_win) >= daily_target

            def _on_done(bid: str, reg: str, n_items: int, res: dict[str, int], elapsed: float) -> None:
                nonlocal batches_executed, total_completed, gate1_hits, gate3_hits, completed_in_win
                batches_executed += 1
                total_completed += res["completed"]
                completed_in_win += res["completed"]
                touched_regions.add(reg)
                rows = ledger._conn.execute(
                    "SELECT task_id, alpha_id, dataset_id, sharpe, fitness, turnover, margin, returns, checks_json "
                    "FROM sim_tasks WHERE batch_id=? AND status IN ('COMPLETED_FULL','COMPLETED_QUICK')",
                    (bid,),
                ).fetchall()
                for r in rows:
                    checks = json.loads(r["checks_json"]) if r["checks_json"] else []
                    ev = evaluator.evaluate(
                        str(r["alpha_id"] or r["task_id"]),
                        region=reg,
                        delay=1,
                        sharpe=r["sharpe"],
                        fitness=r["fitness"],
                        turnover=r["turnover"],
                        margin=r["margin"],
                        returns=r["returns"],
                        is_checks=checks,
                    )
                    if ev.gate_status in ("GATE3_TIER1_PASS", "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"):
                        gate3_hits += 1
                        print(
                            f"  [POOL_S GATE3_PASS!] {reg}/{r['dataset_id']} alpha={r['alpha_id']} "
                            f"Sh={r['sharpe']} Fit={r['fitness']} M={ev.margin_bp}bp",
                            flush=True,
                        )
                    elif ev.gate_status in ("GATE2_IMPROVING", "GATE1_POOL_SH08"):
                        gate1_hits += 1
                        print(
                            f"  [POOL_A/B SEED] {reg}/{r['dataset_id']} alpha={r['alpha_id']} "
                            f"Sh={r['sharpe']} Fit={r['fitness']} M={ev.margin_bp}bp",
                            flush=True,
                        )
                rem_val = quota.last_snapshot.remaining_val if (quota.last_snapshot and quota.last_snapshot.endpoint == "/simulations") else "?"
                print(
                    f"[RA-ROLL] {bid} ({reg} x{n_items} in {elapsed}s): done={res['completed']} unobs={res['unobserved']} | "
                    f"day_est={day_done + completed_in_win}/{daily_target} api_rem={rem_val} | g1={gate1_hits} g3={gate3_hits}",
                    flush=True,
                )
                if batches_executed % 4 == 0:
                    export_funnel_snapshot(ledger, reg, pruning_config=pruning_config)

            runner.run_continuous_rolling_batches(
                prepared_window,
                batch_size=batch_size,
                should_stop=_should_stop_now,
                on_batch_complete=_on_done,
            )
            for tr in sorted(touched_regions):
                export_funnel_snapshot(ledger, tr, pruning_config=pruning_config)
            gc.collect()
            if sleep_between_batches_sec > 0:
                time.sleep(sleep_between_batches_sec)

        return {
            "batches_executed": batches_executed,
            "total_completed": total_completed,
            "gate1_hits": gate1_hits,
            "gate3_hits": gate3_hits,
            "early_stopped": sorted(f"{r}/{d}" for r, d in early_stopped_keys),
        }
    finally:
        auth.close()
        ledger.close()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Low-memory D1-Only RA multi-market production daemon")
    p.add_argument(
        "--region",
        default=",".join(HIGH_BASE_MULTI_MARKET_ORDER),
        help="Comma-separated ordered region(s); default high-Base institutional heavyweights first",
    )
    p.add_argument("--slots", type=int, default=4, help="Global concurrent multi-sim threads (2-4 recommended; max 8)")
    p.add_argument("--max-per-region", type=int, default=2, help="Default max concurrent multi-sim threads per region")
    p.add_argument("--region-caps", default="", help="Optional per-region slot overrides, e.g. EUR:1,USA:3")
    p.add_argument("--post-stagger", type=float, default=2.0, help="Min seconds between POST /simulations across threads to prevent burst 429")
    p.add_argument("--batch-size", type=int, default=8, help="Children per multi-sim (Gold max=8)")
    p.add_argument("--mode", default="FULL", choices=["FULL", "QUICK"])
    p.add_argument("--daily-target", type=int, default=4500)
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--only-free-alpha0", action="store_true")
    p.add_argument("--round-robin-waves", type=int, default=1, help="Waves per campaign before rotating to next market (0=sequential)")
    p.add_argument("--early-stop-sims", type=int, default=48, help="Min completed sims before auto-stopping a dead dataset (0=disable)")
    p.add_argument("--early-stop-sharpe", type=float, default=0.80, help="Min POSITIVE Sharpe threshold for early-stop hit detection")
    p.add_argument("--prune-jaccard", type=float, default=0.78, help="Max token Jaccard similarity before pruning redundant seeds")
    p.add_argument("--prune-max-per-field", type=int, default=2, help="Max promoted seeds kept per (region, dataset, field)")
    p.add_argument("--prune-max-per-dataset", type=int, default=6, help="Max promoted seeds kept per (region, dataset)")
    p.add_argument("--loop", action="store_true", help="Continuously loop across EST platform days")
    args = p.parse_args(argv)

    reg_list = [r.strip().upper() for r in str(args.region).split(",") if r.strip()]
    reg_caps = parse_region_caps(args.region_caps)
    p_cfg = PruningConfig(
        jaccard_max=args.prune_jaccard,
        max_per_field=args.prune_max_per_field,
        max_per_dataset=args.prune_max_per_dataset,
    )
    while True:
        res = run_ra_production_loop(
            regions=reg_list,
            max_slots=args.slots,
            max_per_region=args.max_per_region,
            region_caps=reg_caps,
            post_stagger_sec=args.post_stagger,
            batch_size=args.batch_size,
            simulation_mode=args.mode,
            daily_target=args.daily_target,
            max_batches=args.max_batches,
            only_free_alpha0=args.only_free_alpha0,
            round_robin_waves=args.round_robin_waves,
            early_stop_min_sims=args.early_stop_sims,
            early_stop_min_pos_sharpe=args.early_stop_sharpe,
            pruning_config=p_cfg,
        )
        print("[RA-DAEMON] Pass finished:", json.dumps(res), flush=True)
        if not args.loop or args.max_batches is not None:
            return 0
        time.sleep(300)


if __name__ == "__main__":
    raise SystemExit(main())
