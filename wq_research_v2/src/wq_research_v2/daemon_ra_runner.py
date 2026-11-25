"""Low-memory D1-Only RA Production Runner & Multi-Market Auto-Pivot Daemon for Guangzhou server (1.9 GiB RAM).

Strictly enforces:
- RA-Only D1 pipeline (PPA kept completely separate to avoid complexity/confusion)
- Delay = 1 hard lock, Decision #3 (NO add/multiply/trade_when), Gold 81 operator whitelist
- Prioritizes Tier-1 High-Base D1 winners (USA, ASI, EUR, GLB) + fresh high-multiplier markets
  (HKG, DEU/fnd6, CHN/analyst45, KOR/forum, GBR/other250, IND) with isolated per-region funnel exports
- Automatic POSITIVE-Sharpe dataset-level early stop: checks positive sharpe >= 0.80 / >= 1.25
  (immune to CHN short-borrow double-negative mirages where both +x and -x yield -2.0!)
- 8-item Multi-Sim packing, weighted slot concurrency (GLB=2 slots), SQLite WAL checkpoints,
  10m auth refresh + 10s reconnect, zero /submit calls
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
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date
from wq_research_v2.ra_evaluator import D1RAEvaluator
from wq_research_v2.sim_runner import SimRunner

# Default high-Base winner-first multi-market D1 exploration order (every region tracked independently!)
# Hourly Audit #1: USA & ASI price_signal_dl confirmed real symmetric alpha (8 & 5 positive POOL_B seeds!);
# CHN/other496, DEU/model264, DEU/analyst93, EUR/news_sentiment_dl, GBR/dl_riskfree_returns, KOR/behavioral, AMR/model239 demoted!
HIGH_BASE_MULTI_MARKET_ORDER: list[str] = [
    "USA", "ASI", "EUR", "GLB", "HKG", "DEU", "CHN", "KOR", "GBR", "IND"
]

# Verified clean D1 RA seed pools (ALL live-checked against cnhkmcp get_datafields on 2026-11-25).
CURATED_RA_D1_CAMPAIGNS: list[dict[str, Any]] = [
    # ==================== TIER 1: PROVEN HIGH-BASE WINNERS ====================
    {
        "campaign_id": "USA_PRICEDL_NORMVOL_FREE",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "price_signal_dl",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "CROWDING", "MARKET"],
        "fields": [
            "normalized_volume_indicator_1",
            "normalized_volume_indicator_2",
            "normalized_volume_indicator_3",
            "normalized_volume_indicator_5",
            "normalized_volume_indicator_6",
            "raw_volume_indicator_6",
            "raw_volume_indicator_3",
            "raw_volume_indicator_5",
        ],
    },
    {
        "campaign_id": "USA_PRICEDL_TREND_VOL_NORM",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "price_signal_dl",
        "queue_type": "NORMAL",
        "field_type": "CUSTOM_EXPRS",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "CROWDING", "MARKET"],
        "custom_base_exprs": [
            ("usa_rt0", "ts_backfill(raw_trend_indicator_0, 21)"),
            ("usa_rt1", "ts_backfill(raw_trend_indicator_1, 21)"),
            ("usa_rt2", "ts_backfill(raw_trend_indicator_2, 21)"),
            ("usa_rt3", "ts_backfill(raw_trend_indicator_3, 21)"),
            ("usa_rt4", "ts_backfill(raw_trend_indicator_4, 21)"),
            ("usa_rt5", "ts_backfill(raw_trend_indicator_5, 21)"),
            ("usa_rt6", "ts_backfill(raw_trend_indicator_6, 21)"),
            # Decision-#3 cross-subfamily dual-branch resonances (volume x trend, ATOM!)
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
    {
        "campaign_id": "ASI_PRICEDL_RA",
        "region": "ASI",
        "universe": "MINVOL1M",
        "dataset_id": "price_signal_dl",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "max_trade": "ON",
        "default_neut": "COUNTRY",
        "alt_neuts": ["SUBINDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "normalized_volume_indicator_2",
            "normalized_volume_indicator_0",
            "normalized_volume_indicator_1",
            "normalized_volume_indicator_5",
            "raw_trend_indicator_4",
            "normalized_trend_indicator_5",
            "normalized_trend_indicator_3",
            "normalized_trend_indicator_1",
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
        "default_neut": "COUNTRY",
        "alt_neuts": ["SUBINDUSTRY", "REVERSION_AND_MOMENTUM"],
        "custom_base_exprs": [
            # Pre-smoothed low-TO variants aiming to lift ASI Margin >= 15bp (like legd1PAN 15.28bp)
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
        "campaign_id": "EUR_PRICEDL_NORM",
        "region": "EUR",
        "universe": "TOP2500",
        "dataset_id": "price_signal_dl",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "COUNTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "SUBINDUSTRY"],
        "fields": [
            "raw_trend_indicator_0",
            "raw_trend_indicator_1",
            "raw_trend_indicator_2",
            "raw_trend_indicator_6",
            "raw_volume_indicator_2",
            "raw_volume_indicator_3",
            "normalized_trend_indicator_2",
            "normalized_trend_indicator_6",
        ],
    },
    {
        "campaign_id": "GLB_ANL10_2TO3",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "analyst10",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["COUNTRY", "SUBINDUSTRY"],
        "fields": [
            "anl10_entfy1_pred_surps_v1_6484",
            "anl10_entfy2_pred_surps_v1_6476",
            "anl10_fcffy1_pred_surps_v1_6437",
            "anl10_fcffy2_pred_surps_v1_6420",
            "anl10_grmfq2_pred_surps_v1_6235",
            "anl10_cpsfy2_pred_surps_v1_6286",
        ],
    },
    {
        "campaign_id": "GLB_FND44_2TO3",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "fundamental44",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["COUNTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "fnd44_fscore",
            "fnd44_yoon_wc_accruals",
            "fnd44_probability_restatement",
        ],
    },
    {
        "campaign_id": "USA_NEWSDL_FREE",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "news_sentiment_dl",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "CROWDING"],
        "fields": [
            "min_negative_word_sentiment_djnews",
            "min_negative_word_sentiment_inferess",
            "min_negative_word_sentiment_trna_us",
            "negative_word_sentiment_stddev_djnews",
            "negative_word_sentiment_stddev_inferess",
            "output_metric_1_djnews",
            "output_metric_1_inferess",
            "output_metric_1_trna_us",
        ],
    },
    {
        "campaign_id": "USA_OTH566_NORM",
        "region": "USA",
        "universe": "TOP3000",
        "dataset_id": "other566",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "CROWDING"],
        "fields": [
            "oth566_l3r20gasfmulti_prob_last_pattern",
            "oth566_l5r20gasfculr_prob_pattern",
            "five_bucket_return_rank_confidence_l3",
            "twenty_bucket_return_rank_confidence_l5",
            "oth566_l3r20gasf_prob",
        ],
    },
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
    # ==================== TIER 2: HIGH-MULTIPLIER / FRESH PROBES ====================
    {
        "campaign_id": "HKG_NEWSDL_FREE",
        "region": "HKG",
        "universe": "TOP800",
        "dataset_id": "news_sentiment_dl",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "max_trade": "ON",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
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
            ("fnd6_depr_capex", "divide(ts_backfill(fnd6_dpy, 126), abs(ts_backfill(fnd6_newq_ppentq, 126)))"),
            ("fnd6_eq_res", "divide(ts_backfill(fnd6_ewq_eqrtq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
        ],
    },
    {
        "campaign_id": "DEU_OTH250_FREE",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "other250",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "MARKET"],
        "fields": [
            "sales_position_rank",
            "oth250_item_review_count",
            "total_review_number",
            "oth250_item_display_price",
            "product_listed_price",
        ],
    },
    {
        "campaign_id": "CHN_ANL45_FREE",
        "region": "CHN",
        "universe": "TOP2000U",
        "dataset_id": "analyst45",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "risk_adjusted_performance_alpha",
            "risk_adjusted_return_treynor",
            "net_exposure_value",
            "relative_index_return_value_2",
            "mean_daily_relative_index_return_pct",
            "aggregate_return_percentage",
            "aggregate_return_excluding_fx",
            "mean_daily_return_pct",
            "aggregate_realized_unrealized_return",
            "realized_return_value",
            "riskless_investment_rate_2",
            "grouped_idea_quantity",
            "average_idea_age_period",
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
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "MARKET"],
        "fields": [
            "distinct_user_count_per_platform",
            "total_distinct_participants_count",
            "aggregate_comment_volume",
            "aggregate_buy_opinion_score",
            "aggregate_sell_opinion_score",
        ],
    },
    {
        "campaign_id": "GBR_OTH250_FREE",
        "region": "GBR",
        "universe": "TOP700",
        "dataset_id": "other250",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "MARKET"],
        "fields": [
            "oth250_rank",
            "oth250_item_rating",
            "total_review_number",
            "oth250_item_display_price",
            "product_listed_price",
        ],
    },
    {
        "campaign_id": "IND_AINEWS_NORM",
        "region": "IND",
        "universe": "TOP500",
        "dataset_id": "ai_news_scores",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "negative_score_median_value_4",
            "negative_score_median_value_5",
            "negative_score_minimum_value_4",
            "negative_score_maximum_value_2",
            "negative_score_minimum_value_2",
            "negative_sentiment_upper_estimate_2",
        ],
    },
]


# 8 clean 5:5 Stage-1/Stage-2 RA templates (4 ADMIN_ORIGINAL : 4 TOP100_2026Q4).
# Includes BOTH positive & negative twins of ts_zscore(ts_mean(x,5),66) and ts_rank(ts_decay_linear(x,10),66)
# plus proven USA/ASI winner group_rank(ts_decay_linear(x,10), subindustry) and signed_power tail booster.
# Strictly ZERO add/multiply/trade_when, ZERO decay > 252, ZERO lambda_max > 1.
TEMPLATE_SET_VER = "v3"
STAGE12_TEMPLATES_8: list[dict[str, str]] = [
    {"id": "RA-ADM-01-sub-grank-z66-pos", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry)"},
    {"id": "RA-ADM-02-rev-sub-grank-z66", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry))"},
    {"id": "RA-ADM-03-sub-grank-dec10", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "group_rank(ts_decay_linear({x}, 10), subindustry)"},
    {"id": "RA-ADM-04-rev-rank-m22", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(rank(ts_mean({x}, 22)))"},
    {"id": "RA-TOP-01-sub-tsrank66-pos", "side": "TOP100_2026Q4", "author": "LD22811", "fmt": "group_neutralize(ts_rank(ts_decay_linear({x}, 10), 66), subindustry)"},
    {"id": "RA-TOP-02-rev-sub-tsrank66", "side": "TOP100_2026Q4", "author": "LD22811", "fmt": "reverse(group_neutralize(ts_rank(ts_decay_linear({x}, 10), 66), subindustry))"},
    {"id": "RA-TOP-03-rev-sub-gz-m22", "side": "TOP100_2026Q4", "author": "SZ83096", "fmt": "reverse(group_zscore(ts_mean({x}, 22), subindustry))"},
    {"id": "RA-TOP-04-sp-sub-z66-pos", "side": "TOP100_2026Q4", "author": "ZS59763", "fmt": "signed_power(group_zscore(ts_zscore(ts_mean({x}, 5), 66), subindustry), 1.5)"},
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


def export_funnel_snapshot(ledger: LedgerStore, region: str) -> Path:
    """Persist non-destructive per-region tiered funnel snapshot so zero good alphas are ever lost."""
    from wq_research_v2.config_loader import DATA_DIR

    reg = region.upper()
    rows = [
        dict(r)
        for r in ledger._conn.execute(
            """
            SELECT task_id, batch_id, dataset_id, primary_field_id, template_id, source_side,
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
        "POOL_A_NEAR_SH135": [],
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
        elif sh >= 1.35:
            pools["POOL_A_NEAR_SH135"].append(r)
        elif sh > 0.80:
            pools["POOL_B_SEED_SH080"].append(r)
        elif sh < -1.20:
            pools["POOL_FLIP_SH_LT_NEG120"].append(r)

    out_path = DATA_DIR / "exports" / f"{reg.lower()}_ra_funnel_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "region": reg,
        "delay": 1,
        "total_completed": len(rows),
        "counts": {k: len(v) for k, v in pools.items()},
        "top_pool_s": pools["POOL_S_SH158_FIT1"][:50],
        "top_pool_a": pools["POOL_A_NEAR_SH135"][:50],
        "top_pool_b": pools["POOL_B_SEED_SH080"][:50],
        "top_pool_flip": pools["POOL_FLIP_SH_LT_NEG120"][:50],
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def run_ra_production_loop(
    *,
    regions: Optional[list[str]] = None,
    max_slots: int = 4,
    batch_size: int = 8,
    simulation_mode: str = "FULL",
    daily_target: int = 3000,
    max_batches: Optional[int] = None,
    sleep_between_batches_sec: float = 2.0,
    only_free_alpha0: bool = False,
    round_robin_waves: int = 1,
    early_stop_min_sims: int = 48,
    early_stop_min_pos_sharpe: float = 0.80,
) -> dict[str, Any]:
    """Run low-memory D1 RA production simulation loop with wave concurrency & positive-Sharpe auto early-stop."""
    ledger = LedgerStore()
    quota = QuotaTracker(ledger)
    auth = BrainAuthSession(quota_observer=quota.observe_response)
    bl = BlacklistRegistry(ledger)
    runner = SimRunner(auth, ledger, quota, blacklist_registry=bl, max_slots=max_slots, poll_interval_sec=4.0)
    evaluator = D1RAEvaluator()

    selected_campaigns = list(CURATED_RA_D1_CAMPAIGNS)
    if regions:
        ordered_regs = [r.strip().upper() for r in regions if r.strip()]
        reg_rank = {r: i for i, r in enumerate(ordered_regs)}
        selected_campaigns = [c for c in selected_campaigns if c["region"].upper() in reg_rank]
        selected_campaigns.sort(key=lambda c: reg_rank[c["region"].upper()])

    specs = build_ra_campaign_specs(campaigns=selected_campaigns)
    if only_free_alpha0:
        specs = [s for s in specs if s.get("queue_type") == "UNUSED_ALPHA0"]
    if round_robin_waves > 0:
        specs = interleave_specs_by_campaign_waves(specs, max_slots=max_slots, waves_per_turn=round_robin_waves)

    # Build alpha0 map for validation (handles both fields and custom_base_exprs)
    alpha0_map: dict[str, int] = {}
    for camp in CURATED_RA_D1_CAMPAIGNS:
        if camp["queue_type"] == "UNUSED_ALPHA0":
            for f in camp.get("fields") or []:
                alpha0_map[f] = 0
            for _, expr in camp.get("custom_base_exprs") or []:
                for tok in expr.replace("(", " ").replace(")", " ").replace(",", " ").split():
                    if tok.startswith(("oth496_", "raw_volume_indicator_", "normalized_volume_indicator_")):
                        alpha0_map[tok] = 0

    auth.authenticate()
    auth.start_background_monitors()
    batches_executed = 0
    total_completed = 0
    gate1_hits = 0
    gate3_hits = 0
    early_stopped_keys: set[tuple[str, str]] = set()

    print(
        f"[RA-DAEMON] Started D1-Only RA runner | regions={regions or 'HIGH_BASE_ALL'} | specs={len(specs)} | "
        f"slots={max_slots} | mode={simulation_mode} | daily_target={daily_target} | "
        f"rr_waves={round_robin_waves} | early_stop_sims={early_stop_min_sims}",
        flush=True,
    )

    try:
        idx = 0
        while idx < len(specs):
            est_day = current_est_platform_date()
            day_stats = ledger.compute_daily_summary(est_day)
            day_done = int(day_stats.get("full_valid_completed_count", 0)) + int(day_stats.get("quick_screened_count", 0))
            if day_done >= daily_target:
                print(f"[RA-DAEMON] Daily target reached ({day_done}/{daily_target}) on EST {est_day}; sleeping 300s.", flush=True)
                if max_batches is not None:
                    break
                time.sleep(300)
                continue

            if max_batches is not None and batches_executed >= max_batches:
                break

            first = specs[idx]
            reg = first["region"]
            ds = str(first.get("dataset_id") or "")
            ds_key = (reg.upper(), ds)

            if ds_key in early_stopped_keys:
                idx += 1
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
                idx += 1
                continue

            weight = runner.slot_weight_for_region(reg)
            wave_specs_cap = max(1, max_slots // weight)
            wave_tasks: list[dict[str, Any]] = []
            wave_batch_ids: list[str] = []

            while (
                idx < len(specs)
                and len(wave_batch_ids) < wave_specs_cap
                and specs[idx]["region"] == reg
                and str(specs[idx].get("dataset_id") or "") == ds
            ):
                spec = specs[idx]
                idx += 1
                bid, runnable, _ = runner.prepare_batch_tasks(
                    spec,
                    simulation_mode=simulation_mode,
                    field_alpha_counts=alpha0_map if spec["queue_type"] == "UNUSED_ALPHA0" else None,
                )
                if runnable:
                    wave_tasks.extend(runnable)
                    wave_batch_ids.append(bid)

            if not wave_tasks:
                continue

            wave_id = f"WAVE-{reg}-{ds[:10]}-{batches_executed + 1:04d}"
            t0 = time.monotonic()
            res = runner.run_prepared_tasks(wave_id, wave_tasks, batch_size=batch_size)
            elapsed = round(time.monotonic() - t0, 1)
            for bid in wave_batch_ids:
                ledger.update_batch_progress(bid, "DONE")

            batches_executed += len(wave_batch_ids)
            total_completed += res["completed"]

            placeholders = ",".join("?" for _ in wave_batch_ids)
            rows = ledger._conn.execute(
                f"SELECT task_id, alpha_id, dataset_id, sharpe, fitness, turnover, margin, returns, checks_json "
                f"FROM sim_tasks WHERE batch_id IN ({placeholders}) AND status IN ('COMPLETED_FULL','COMPLETED_QUICK')",
                tuple(wave_batch_ids),
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

            export_funnel_snapshot(ledger, reg)
            print(
                f"[RA-DAEMON] {wave_id} ({len(wave_batch_ids)}x{batch_size} in {elapsed}s): "
                f"done={res['completed']} unobs={res['unobserved']} | day_total={day_done + res['completed']}/{daily_target} "
                f"| gate1={gate1_hits} gate3={gate3_hits}",
                flush=True,
            )
            del rows, wave_tasks
            gc.collect()
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
        help="Comma-separated ordered region(s); default high-Base winners first",
    )
    p.add_argument("--slots", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--mode", default="FULL", choices=["FULL", "QUICK"])
    p.add_argument("--daily-target", type=int, default=3000)
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--only-free-alpha0", action="store_true")
    p.add_argument("--round-robin-waves", type=int, default=1, help="Waves per campaign before rotating to next market (0=sequential)")
    p.add_argument("--early-stop-sims", type=int, default=48, help="Min completed sims before auto-stopping a dead dataset (0=disable)")
    p.add_argument("--early-stop-sharpe", type=float, default=0.80, help="Min POSITIVE Sharpe threshold for early-stop hit detection")
    p.add_argument("--loop", action="store_true", help="Continuously loop across EST platform days")
    args = p.parse_args(argv)

    reg_list = [r.strip().upper() for r in str(args.region).split(",") if r.strip()]
    while True:
        res = run_ra_production_loop(
            regions=reg_list,
            max_slots=args.slots,
            batch_size=args.batch_size,
            simulation_mode=args.mode,
            daily_target=args.daily_target,
            max_batches=args.max_batches,
            only_free_alpha0=args.only_free_alpha0,
            round_robin_waves=args.round_robin_waves,
            early_stop_min_sims=args.early_stop_sims,
            early_stop_min_pos_sharpe=args.early_stop_sharpe,
        )
        print("[RA-DAEMON] Pass finished:", json.dumps(res), flush=True)
        if not args.loop or args.max_batches is not None:
            return 0
        time.sleep(300)


if __name__ == "__main__":
    raise SystemExit(main())
