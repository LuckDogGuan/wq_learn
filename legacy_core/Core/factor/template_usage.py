"""模板候选注册、筛选和使用记录。

模板名字只表示研究方向，不保证 Sharpe。性能状态只使用相同研究范围内、
状态为 COMPLETE 的可观测结果；PENDING、语法错误和权限错误均不算失败。
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import inspect
import json
import re
import threading
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from Core.data.runtime_paths import (
    TEMPLATE_USAGE_V2_EVENTS_PATH,
    TEMPLATE_USAGE_V2_SUMMARY_PATH,
    TEMPLATE_USAGE_V5_EVENTS_PATH,
    TEMPLATE_USAGE_V5_SUMMARY_PATH,
)
from Core.factor.filter.expression_checker import verify_alpha_expression
from Core.factor.templates.admin_distributed import ADMIN_SOURCES, semantic_pair, operator_count
from Core.factor.templates.forum_verified import load_verified_catalog


_WRITE_LOCK = threading.Lock()
_EVENT_CACHE = {}
_FINAL_STATUSES = {
    "COMPLETE", "FAILED", "CANCELLED", "PENDING", "RESULTS_UNOBSERVED",
    "LOCAL_REJECTED", "LIVE_REJECTED", "FIELD_REJECTED",
    "DEFERRED_SINGLETON", "DEFERRED_INCOMPLETE_BATCH", "CACHE_HIT",
    "BLOCKED_INCOMPLETE_BATCH", "BLOCKED_INCOMPLETE_TEMPLATE_BATCH",
    "BLOCKED_INCOMPLETE_MARGIN_BATCH", "AGGREGATED_REJECTED",
    "PENDING_CATEGORY", "PENDING_CATEGORY_CONFLICT",
}
_NON_PERFORMANCE_STATUSES = {
    "PENDING", "RESULTS_UNOBSERVED", "CANCELLED", "LOCAL_REJECTED", "LIVE_REJECTED",
    "FIELD_REJECTED", "DEFERRED_SINGLETON", "DEFERRED_INCOMPLETE_BATCH",
    "BLOCKED_INCOMPLETE_BATCH", "BLOCKED_INCOMPLETE_TEMPLATE_BATCH",
    "PENDING_CATEGORY", "PENDING_CATEGORY_CONFLICT",
}
_FORBIDDEN_OPERATORS = {"add", "multiply", "trade_when"}
_CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
TEMPLATE_LEARNING_VERSION = "region-category-stage0-branches-v6"
_LEGACY_SCOPE_FIELDS = ("region", "universe", "delay", "dataset_id", "field_type")
_SCOPE_FIELDS = ("region", "category")
_LOOKBACK_VALUES = (5, 10, 22, 66, 120, 252)
_DECAY_VALUES = (2, 5, 10)
_DELAY_VALUES = (1, 2)
_GROUP_VALUES = ("sector", "industry", "subindustry")
_ROLE_TARGETS = {
    "SIGNAL_BUILD": ("sharpe", "fitness", "sharpe_2y", "margin"),
    "STABILITY_CONTROL": ("sharpe_2y", "turnover", "sc", "stability"),
    "FINAL_REPAIR": ("sharpe", "fitness", "sharpe_2y", "margin", "turnover", "sc", "pc"),
    "MARGIN_REPAIR": ("sharpe", "fitness", "sharpe_2y", "margin", "turnover"),
}


def _entry(template_id, module, function, family, *, tier=1, kind="field",
           params=None, condition=None, enabled=True, note="", stages=None,
           role_by_stage=None, template_class="STATISTICAL_CONTROL",
           supported_categories=(), economic_hypothesis="",
           semantic_requirements=(), input_mode="FIELD",
           horizon_days=(), economic_thesis_id="", class_by_stage=None):
    if stages is None:
        stages = (2, 3) if kind == "expression" else (1,)
    role_by_stage = dict(role_by_stage or {})
    for stage in stages:
        role_by_stage.setdefault(
            int(stage),
            "SIGNAL_BUILD" if int(stage) == 1
            else "STABILITY_CONTROL" if int(stage) == 2
            else "FINAL_REPAIR",
        )
    return {
        "template_id": template_id,
        "module": module,
        "function": function,
        "family": family,
        "tier": tier,
        "kind": kind,
        "params": params or {},
        "condition": condition,
        "enabled": enabled,
        "note": note,
        "stages": tuple(int(stage) for stage in stages),
        "role_by_stage": role_by_stage,
        "template_class": template_class,
        "supported_categories": tuple(str(value).upper() for value in supported_categories),
        "economic_hypothesis": economic_hypothesis,
        "semantic_requirements": tuple(semantic_requirements),
        "input_mode": input_mode,
        "horizon_days": tuple(horizon_days),
        "economic_thesis_id": economic_thesis_id or template_id,
        "class_by_stage": dict(class_by_stage or {}),
    }


# 首轮每个模板只使用一个代表参数，避免模板 × 参数的笛卡尔积。
# 5/10=短期，22=约一月，66=约一季，120/252=中长期。
_VERIFIED_FORUM_ENTRIES = tuple({
    **_entry(
        item["template_id"], item["template_module"], item["template_function"],
        item.get("family") or item["template_id"], kind="field",
        params=item["template_params"], condition="matrix_fields",
        stages=(1, 2, 3), template_class="STATISTICAL_CONTROL",
        note="本地合规通过；收益UNVALIDATED，MATRIX字段替换后重新核对权限、语法和复杂度",
    ),
    "source_kind": "ADMIN_DISTRIBUTED" if item.get("source_section") == "BODY" and (
        item.get("source_relation") in {"ADMIN_AUTHORED", "ADMIN_POSTED"}
        or item.get("source_author") in {"WL13229", "KH94146"}
    ) else "COMMUNITY_REFERENCED",
    "source_post_id": item.get("source_post_id"), "source_url": item.get("source_url"),
    "source_relation": item.get("source_relation"), "source_section": item.get("source_section"),
    "source_author": item.get("source_author"), "source_line": item.get("source_line"),
    "catalog_status": item["status"], "validation_status": "UNVALIDATED",
} for item in load_verified_catalog())
TEMPLATE_CANDIDATES = (
    *_VERIFIED_FORUM_ENTRIES,
    *tuple({
        **_entry(
            f"admin.{function}", "Core.factor.templates.admin_distributed", function,
            f"admin_{function}", kind=kind, params=params, condition=condition,
            stages=(1,), template_class="ECONOMIC_SIGNAL",
            supported_categories=categories, semantic_requirements=tags,
            economic_hypothesis=hypothesis,
            input_mode="SAME_DATASET_PAIR" if kind == "binary" else "FIELD",
        ),
        "source_kind": "ADMIN_DISTRIBUTED", "source_post_id": ADMIN_SOURCES[function],
        "source_url": f"https://support.worldquantbrain.com/hc/zh-cn/community/posts/{ADMIN_SOURCES[function]}",
        "validation_status": "UNVALIDATED",
        "enabled": function != "peg_relative_value",
        "note": "PEG含非正值保护后总算子>=6；隔离保存，暂不轮动" if function == "peg_relative_value" else "管理员分发/译介；收益待验证",
    } for function, kind, params, condition, categories, tags, hypothesis in (
        ("profit_to_size", "binary", {"d": 66}, "admin_profit_size", ("FUNDAMENTAL", "ANALYST"), ("fundamental",), "盈利/规模比率的历史改善反映经营效率。"),
        ("net_sentiment", "binary", {"d": 22}, "admin_sentiment_pair", ("SENTIMENT", "NEWS", "ANALYST"), (), "正负情绪净差异反映观点变化。"),
        ("term_structure", "binary", {"group": "industry"}, "admin_term_pair", ("ANALYST", "MODEL"), (), "同指标不同预测期限的差异反映预期增长。"),
        ("dupont_difference", "binary", {"d": 66, "group": "industry"}, "admin_dupont_pair", ("FUNDAMENTAL",), ("fundamental",), "ROE与利润率变化的差异区分杠杆和经营改善。"),
        ("peg_relative_value", "binary", {"group": "industry"}, "admin_peg_pair", ("FUNDAMENTAL", "ANALYST", "MODEL"), (), "正盈利和正增长下的相对PEG衡量估值。"),
        ("group_residual", "field", {"d": 252, "backfill": 63, "group": "sector"}, None, ("FUNDAMENTAL", "ANALYST", "MODEL", "SENTIMENT", "NEWS", "OTHER"), ("information_signal",), "单数据集等权改编：剔除同行可解释部分，保留公司特异信息。"),
        ("group_beta", "binary", {"d": 252, "group": "sector"}, "admin_beta_pair", ("FUNDAMENTAL", "ANALYST", "MODEL", "OTHER"), ("information_signal",), "单数据集等权改编：语义相关量之间的组内信息传导敏感度。"),
    )),
    # Stage 0 是 Stage 1 的简单经济信号来源，不是额外的流程阶段。
    _entry(
        "stage0.cross_sectional_rank", "Core.factor.templates.stage_0_basic",
        "stage0_cross_sectional_rank", "stage0_relative_strength", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OPTIONS", "MACRO", "EVENT", "OTHER"),
        economic_hypothesis="同一时点的截面相对位置比原始量纲更接近可比较的定价信号。",
        semantic_requirements=("information_signal",), input_mode="FIELD",
        economic_thesis_id="stage0_cross_sectional_strength",
    ),
    _entry(
        "stage0.time_series_rank", "Core.factor.templates.stage_0_basic",
        "stage0_time_series_rank", "stage0_historical_position", params={"d": 22},
        stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OPTIONS", "MACRO", "EVENT", "OTHER"),
        economic_hypothesis="指标相对自身历史的位置可以识别新信息或异常状态。",
        semantic_requirements=("information_signal",), input_mode="FIELD",
        horizon_days=(5, 10, 22, 66, 120, 252), economic_thesis_id="stage0_historical_position",
    ),
    _entry(
        "stage0.financial_ratio", "Core.factor.templates.stage_0_basic",
        "stage0_financial_ratio", "stage0_fundamental_ratio", kind="binary",
        condition="fundamental_pair", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("FUNDAMENTAL", "ANALYST"),
        economic_hypothesis="同源基本面比率可以消除规模效应并表达盈利或估值效率。",
        semantic_requirements=("fundamental",), input_mode="SAME_DATASET_PAIR",
        economic_thesis_id="stage0_fundamental_ratio",
    ),
    _entry(
        "stage0.yoy_growth", "Core.factor.templates.stage_0_basic",
        "stage0_yoy_growth", "stage0_growth", params={"d": 252},
        condition="fundamental_or_analyst", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("FUNDAMENTAL", "ANALYST", "MODEL"),
        economic_hypothesis="年度边际变化比静态水平更直接反映基本面或预期改善。",
        semantic_requirements=("information_signal",), input_mode="FIELD",
        horizon_days=(66, 120, 252), economic_thesis_id="stage0_growth",
    ),
    _entry(
        "stage0.pricing_bias", "Core.factor.templates.stage_0_basic",
        "stage0_pricing_bias", "stage0_price_reversion", params={"d": 10},
        condition="price_like", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("PV", "IMBALANCE", "OTHER"),
        economic_hypothesis="价格偏离近期中枢后可能出现短期均值回归。",
        semantic_requirements=("price_volume",), input_mode="FIELD",
        horizon_days=(5, 10, 22), economic_thesis_id="stage0_price_reversion",
    ),
    _entry(
        "stage0.volume_shock", "Core.factor.templates.stage_0_basic",
        "stage0_volume_shock", "stage0_liquidity_shock", params={"d": 22},
        condition="volume_like", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("PV", "IMBALANCE", "OTHER"),
        economic_hypothesis="成交或订单流相对历史中枢的异常反映流动性冲击。",
        semantic_requirements=("price_volume",), input_mode="FIELD",
        horizon_days=(5, 10, 22, 66), economic_thesis_id="stage0_liquidity_shock",
    ),
    _entry(
        "stage0.model_zscore", "Core.factor.templates.stage_0_basic",
        "stage0_model_zscore", "stage0_model_extreme", params={"d": 120},
        condition="model_or_sentiment", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("MODEL", "NEWS", "SENTIMENT", "OTHER"),
        economic_hypothesis="模型或情绪得分相对自身历史的异常程度代表新的定价冲击。",
        semantic_requirements=("information_signal",), input_mode="FIELD",
        horizon_days=(22, 66, 120, 252), economic_thesis_id="stage0_model_extreme",
    ),
    _entry(
        "stage0.options_put_call", "Core.factor.templates.stage_0_alternative",
        "stage0_options_put_call_ratio", "stage0_options_sentiment", kind="binary",
        condition="put_call_pair", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("OPTIONS", "OPTION", "OTHER"),
        economic_hypothesis="同源Put与Call活动之比反映期权市场的方向性风险偏好。",
        semantic_requirements=("options",), input_mode="SAME_DATASET_PAIR",
        economic_thesis_id="stage0_put_call_sentiment",
    ),
    _entry(
        "stage0.options_skew", "Core.factor.templates.stage_0_alternative",
        "stage0_options_volatility_skew", "stage0_options_skew", kind="binary",
        condition="call_put_vol_pair", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("OPTIONS", "OPTION", "OTHER"),
        economic_hypothesis="Call与Put隐含波动率差异反映尾部风险定价偏好。",
        semantic_requirements=("options",), input_mode="SAME_DATASET_PAIR",
        economic_thesis_id="stage0_options_skew",
    ),
    _entry(
        "stage0.macro_shock", "Core.factor.templates.stage_0_alternative",
        "stage0_macro_shock", "stage0_macro_state", params={"d": 66},
        condition="macro_like", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("MACRO", "OTHER"),
        economic_hypothesis="宏观指标偏离中期中枢可以代理系统性状态变化。",
        semantic_requirements=("macro",), input_mode="FIELD",
        horizon_days=(22, 66, 120, 252), economic_thesis_id="stage0_macro_state",
    ),
    _entry(
        "stage0.event_frequency", "Core.factor.templates.stage_0_alternative",
        "stage0_event_frequency", "stage0_event_density", params={"d": 22},
        condition="event_like", stages=(1,), template_class="ECONOMIC_SIGNAL",
        supported_categories=("EVENT", "INSIDERS", "OTHER"),
        economic_hypothesis="近期公司事件发生密度可以刻画行为或信息冲击的持续性。",
        semantic_requirements=(), input_mode="FIELD",
        horizon_days=(10, 22, 66), economic_thesis_id="stage0_event_density",
    ),
    # 经济含义明确的低复杂度信号。相同表达式函数可以服务多个 Category，
    # 但每个注册项的假设和语义证据彼此独立。
    _entry(
        "economic.information_change", "Core.factor.templates.economic_signals",
        "information_change", "economic_change", params={"d": 22},
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OTHER"),
        economic_hypothesis="新信息会逐步进入价格，字段变化方向可预测后续收益。",
        semantic_requirements=("information_signal",), input_mode="SOURCE_EXPRESSION",
        horizon_days=(5, 10, 22, 66, 120, 252), economic_thesis_id="information_change",
    ),
    _entry(
        "economic.information_acceleration", "Core.factor.templates.economic_signals",
        "information_acceleration", "economic_acceleration", params={"d": 22},
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "NEWS", "SENTIMENT", "FUNDAMENTAL"),
        economic_hypothesis="信息修正加速比稳定水平包含更多边际信息。",
        semantic_requirements=("information_signal",), input_mode="SOURCE_EXPRESSION", horizon_days=(10, 22, 66, 120),
        economic_thesis_id="information_acceleration",
    ),
    _entry(
        "economic.persistence", "Core.factor.templates.economic_signals",
        "persistent_signal", "economic_persistence", params={"d": 66},
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL"),
        economic_hypothesis="持续出现的基本面、持仓、订单流或观点比一次性噪声更可靠。",
        semantic_requirements=("information_signal",), input_mode="SOURCE_EXPRESSION", horizon_days=(10, 22, 66, 120, 252),
        economic_thesis_id="signal_persistence",
    ),
    _entry(
        "economic.historical_surprise", "Core.factor.templates.economic_signals",
        "historical_surprise", "economic_surprise", params={"d": 66},
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "NEWS", "SENTIMENT", "FUNDAMENTAL"),
        economic_hypothesis="相对自身历史的异常变化代表新的经济冲击。",
        semantic_requirements=("information_signal",), input_mode="SOURCE_EXPRESSION", horizon_days=(22, 66, 120, 252),
        economic_thesis_id="historical_surprise",
    ),
    _entry(
        "economic.cross_sectional_strength", "Core.factor.templates.economic_signals",
        "cross_sectional_strength", "economic_relative_strength",
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OTHER"),
        economic_hypothesis="同一时点公司间相对强弱比原始量纲更能反映定价差异。",
        semantic_requirements=("information_signal",), input_mode="SOURCE_EXPRESSION", economic_thesis_id="cross_sectional_strength",
    ),
    _entry(
        "economic.short_reversal", "Core.factor.templates.economic_signals",
        "short_horizon_reversal", "economic_reversal", params={"d": 5},
        kind="expression", stages=(1,),
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("IMBALANCE", "PV", "NEWS", "SENTIMENT", "OTHER"),
        economic_hypothesis="短期订单流、价格或极端情绪压力会部分反转。",
        semantic_requirements=("short_reversal_signal",), input_mode="SOURCE_EXPRESSION", horizon_days=(5, 10, 22),
        economic_thesis_id="short_horizon_reversal",
    ),
    # 动量、反转和截面模板。
    _entry("momentum.momentum_20d", "Core.factor.templates.momentum_reversal", "momentum_20d", "momentum"),
    _entry("momentum.short_reversal", "Core.factor.templates.momentum_reversal", "short_term_reversal", "reversal", params={"d": 5}),
    _entry("momentum.acceleration", "Core.factor.templates.momentum_reversal", "double_difference_acceleration", "momentum", params={"d": 22}),
    _entry("momentum.price_volume_divergence", "Core.factor.templates.momentum_reversal", "price_volume_divergence", "correlation", params={"d": 10}, condition="needs_high"),
    _entry("momentum.overnight_gap", "Core.factor.templates.momentum_reversal", "overnight_gap_reversal", "reversal", params={"d": 5}, kind="fixed", condition="needs_open_close"),
    _entry("fundamental.group_zscore", "Core.factor.templates.fundamentals", "zscore_normalization", "cross_sectional", params={"group": "subindustry"}, stages=(2,)),
    _entry("fundamental.rank_difference", "Core.factor.templates.fundamentals", "rank_difference", "cross_sectional", kind="binary"),
    _entry("fundamental.trend", "Core.factor.templates.fundamentals", "fundamental_trend", "fundamental", params={"d": 66}),
    _entry("cross.group_rank", "Core.factor.templates.cross_sectional", "cross_sectional_group_rank", "cross_sectional", params={"group": "subindustry"}, stages=(2,)),
    _entry("cross.quantile_zscore", "Core.factor.templates.cross_sectional", "cross_sectional_quantile_zscore", "cross_sectional", stages=(2,)),
    _entry("cross.robust_normalize", "Core.factor.templates.cross_sectional", "robust_normalization", "cross_sectional", stages=(2,)),
    _entry("cross.inverse", "Core.factor.templates.cross_sectional", "cross_sectional_inverse_value", "cross_sectional"),
    _entry(
        "cross.densify", "Core.factor.templates.cross_sectional",
        "density_compression", "cross_sectional", kind="category",
        note="平台要求 Group/Category 单位；不得用于 MATRIX/VECTOR 数值字段",
    ),

    # 常用时序和风险模板。
    _entry("advanced.decay_linear", "Core.factor.templates.advanced_ops", "decay_linear_smoothing", "smoothing", params={"d": 10}, stages=(2,)),
    _entry("advanced.average_difference", "Core.factor.templates.advanced_ops", "average_difference", "mean_reversion", params={"d": 22}),
    _entry("advanced.step_counter", "Core.factor.templates.advanced_ops", "momentum_step_counter", "trend", params={"d": 22}),
    _entry("advanced.extreme_timing", "Core.factor.templates.advanced_ops", "price_extremes_timing", "timing", params={"d": 22}),
    _entry("advanced.robust_log", "Core.factor.templates.advanced_ops", "robust_log_transformation", "transform"),
    _entry("advanced.cumulative_product", "Core.factor.templates.advanced_ops", "scaled_cumulative_product", "returns", params={"d": 5}, condition="returns_like"),
    _entry("advanced.backfill", "Core.factor.templates.advanced_ops", "fundamental_backfill", "coverage", params={"d": 66}, stages=(2,)),
    _entry("advanced.volatility_sqrt", "Core.factor.templates.advanced_ops", "return_volatility_sqrt", "risk", params={"d": 22}, condition="returns_like", stages=(2,)),
    _entry("advanced.ts_quantile", "Core.factor.templates.advanced_ops", "time_series_quantile_rank", "distribution", params={"d": 66}),
    _entry("risk.ts_ir", "Core.factor.templates.statistical_risk", "historical_volatility_adjusted", "risk", params={"d_vol": 22}, stages=(2,)),
    _entry("risk.kurtosis", "Core.factor.templates.statistical_risk", "rolling_kurtosis_risk", "risk", params={"d": 66}, stages=(2,)),
    _entry("risk.extreme_reversion", "Core.factor.templates.statistical_risk", "extreme_value_reversion", "reversal", params={"d": 22}, stages=(2,)),
    _entry("risk.cumulative_shock", "Core.factor.templates.statistical_risk", "cumulative_volume_shock", "flow", params={"d": 5}, stages=(2,)),
    _entry("risk.max_difference", "Core.factor.templates.statistical_risk", "max_difference_breakout", "breakout", params={"d": 22}, stages=(2,)),
    _entry("risk.nan_stability", "Core.factor.templates.statistical_risk", "data_stability_check", "coverage", params={"d": 66}, stages=(2,)),

    # 字段语义匹配时才运行。
    _entry("sentiment.news", "Core.factor.templates.sentiment_analyst", "unstructured_news_sentiment", "sentiment", params={"d": 22}, condition="news_like"),
    _entry("sentiment.analyst_revision", "Core.factor.templates.sentiment_analyst", "analyst_estimate_revision", "analyst", condition="analyst_like"),
    _entry("sentiment.forum_divergence", "Core.factor.templates.sentiment_analyst", "forum_sentiment_divergence", "sentiment", kind="binary", condition="sentiment_like"),

    # 虎哥 Series 2：仅作为同数据集、双 MATRIX、语义相关字段的 Margin Challenger。
    _entry(
        "hu_ge.series2_residual_stddev", "Core.factor.assembly.hu_ge_series",
        "huge_series_2_timeseries_residual_stddev", "hu_ge_relation",
        params={"d": 120}, condition="hu_ge_pair", kind="binary",
        stages=(1, 2, 3),
        role_by_stage={1: "MARGIN_REPAIR", 2: "MARGIN_REPAIR", 3: "MARGIN_REPAIR"},
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OTHER"),
        economic_hypothesis="两个同源经济量之间无法相互解释的波动可能包含独立定价信息。",
        semantic_requirements=("information_signal",), input_mode="SAME_DATASET_PAIR",
        horizon_days=(120, 252), economic_thesis_id="hu_ge_series2_relation",
    ),
    _entry(
        "hu_ge.series2_beta_lagged", "Core.factor.assembly.hu_ge_series",
        "huge_series_2_timeseries_beta_lagged", "hu_ge_relation",
        params={"d": 120, "lag": 5}, condition="hu_ge_pair", kind="binary",
        stages=(1, 2, 3),
        role_by_stage={1: "MARGIN_REPAIR", 2: "MARGIN_REPAIR", 3: "MARGIN_REPAIR"},
        template_class="ECONOMIC_SIGNAL",
        supported_categories=("ANALYST", "MODEL", "INSTITUTIONS", "INSIDERS", "IMBALANCE", "PV", "NEWS", "SENTIMENT", "FUNDAMENTAL", "OTHER"),
        economic_hypothesis="一个经济量的滞后变化对另一个经济量的敏感度可反映信息传导。",
        semantic_requirements=("information_signal",), input_mode="SAME_DATASET_PAIR",
        horizon_days=(120, 252), economic_thesis_id="hu_ge_series2_relation",
    ),

    # 虎哥 60 天模板：先广测一元，再在同数据集双字段上测试二元。
    *tuple(_entry(f"tiger.unary_{i}", "Core.factor.assembly.sixty_days_matrix", name, "tiger_unary", tier=2, params=params)
           for i, (name, params) in enumerate((
               ("unary_0_slope", {"d": 252}),
               ("unary_1_growth_rate_acceleration", {"d1": 66, "d2": 252}),
               ("unary_2_growth_rate", {"d": 66}),
               ("unary_3_autoregressive_slope", {"d1": 66, "d2": 252}),
               ("unary_4_squared_momentum", {"d1": 22, "d2": 66}),
               ("unary_5_decay_weighted_momentum", {"d1": 22, "d2": 66}),
               ("unary_6_rank_reversal", {"d": 66}),
               ("unary_7_log_smoothing", {"d": 66}),
               ("unary_8_sign_preserved_power", {"d": 66}),
               ("unary_9_differential_cascade", {"d1": 22, "d2": 66}),
           ))),
    *tuple(_entry(f"tiger.binary_{i}", "Core.factor.assembly.sixty_days_matrix", name, "tiger_binary", tier=2, kind="binary", params=params)
           for i, (name, params) in enumerate((
               ("binary_0_regression_residual", {"d": 252}),
               ("binary_1_regression_beta", {"d": 252}),
               ("binary_2_regression_residual_stddev", {"d": 252}),
               ("binary_3_raw_regression_beta_short", {"d": 120}),
               ("binary_4_raw_regression_beta_long", {"d": 252}),
               ("binary_5_log_regression_neut", {}),
               ("binary_6_vector_neut", {}),
           ))),

    # 已有表达式的轻量后处理；不会直接当成原始字段模板。
    _entry("post.decay", "Core.factor.templates.risk_and_correlation", "optimize_turnover_with_decay", "postprocess", tier=3, kind="expression", params={"d": 5}, class_by_stage={3: "RISK_REPAIR"}),
    _entry("post.group_neutralize", "Core.factor.templates.risk_and_correlation", "optimize_weight_concentration_neutralize", "postprocess", tier=3, kind="expression", params={"group": "subindustry"}, class_by_stage={3: "RISK_REPAIR"}),
    _entry("post.rank", "Core.factor.templates.risk_and_correlation", "optimize_weight_concentration_rank", "postprocess", tier=3, kind="expression", class_by_stage={3: "RISK_REPAIR"}),
    _entry("post.delay", "Core.factor.templates.risk_and_correlation", "reduce_correlation_by_delay_signal", "postprocess", tier=3, kind="expression", params={"days": 1}, class_by_stage={3: "RISK_REPAIR"}),
    # pc_control 是结构/集中度重塑，不把函数名当作 Production Correlation 保证。
    _entry("structure.pc_rank", "Core.factor.templates.pc_control", "pc_control_rank", "structure_reshape", tier=3, kind="raw_vector", params={"d1": 252, "scale": 5}, condition="vector_only", stages=(3,), template_class="RISK_REPAIR"),
    _entry("structure.pc_zscore", "Core.factor.templates.pc_control", "pc_control_zscore", "structure_reshape", tier=3, kind="raw_vector", params={"d1": 252, "scale": 5}, condition="vector_only", stages=(3,), template_class="RISK_REPAIR"),
    _entry("structure.pc_ts_rank", "Core.factor.templates.pc_control", "pc_control_ts_rank", "structure_reshape", tier=3, kind="raw_vector", params={"d1": 252, "scale": 5, "rank_d": 66}, condition="vector_only", stages=(3,), template_class="RISK_REPAIR"),
    _entry("structure.exchange_sector", "Core.factor.templates.pc_control", "pc_control_exchange_sector_grouping", "structure_reshape", tier=3, kind="raw_vector", params={"d1": 252, "scale": 5}, condition="vector_only", stages=(3,), template_class="RISK_REPAIR"),
)


# 批次 6～7 的操作符形态。它们使用当前字段而不是盲目替换任意 AST 参数。
OPERATOR_SHAPES = (
    ("shape.rank", "cross_sectional", "rank({field})"),
    ("shape.zscore", "cross_sectional", "zscore({field})"),
    ("shape.signed_rank", "cross_sectional", "signed_power(rank({field}), 1.5)"),
    ("shape.reverse", "reversal", "reverse({field})"),
    ("shape.ts_rank", "distribution", "ts_rank({field}, 66)"),
    ("shape.ts_zscore", "distribution", "ts_zscore({field}, 66)"),
    ("shape.ts_mean", "smoothing", "ts_mean({field}, 22)"),
    ("shape.ts_delta", "momentum", "ts_delta({field}, 22)"),
    ("shape.ts_decay", "smoothing", "ts_decay_linear({field}, 10)"),
    ("shape.ts_av_diff", "mean_reversion", "ts_av_diff({field}, 22)"),
    ("shape.ts_ir", "risk", "ts_ir({field}, 22)"),
    ("shape.ts_quantile", "distribution", "ts_quantile({field}, 66)"),
    ("shape.group_rank", "cross_sectional", "group_rank({field}, subindustry)"),
    ("shape.group_zscore", "cross_sectional", "group_zscore({field}, subindustry)"),
    ("shape.group_neutralize", "cross_sectional", "group_neutralize({field}, subindustry)"),
    ("shape.base_reverse", "postprocess", "reverse({expression})"),
    # 与上面的单层模板不同，以下形态用于补足第二阶段的结构广度。
    ("shape.rank_ts_zscore22", "distribution", "rank(ts_zscore({field}, 22))"),
    ("shape.zscore_rank", "cross_sectional", "zscore(rank({field}))"),
    ("shape.signed_rank_half", "cross_sectional", "signed_power(rank({field}), 0.5)"),
    ("shape.signed_rank_square", "cross_sectional", "signed_power(rank({field}), 2.0)"),
    ("shape.reverse_ts_rank22", "reversal", "reverse(ts_rank({field}, 22))"),
    ("shape.group_rank_delta", "momentum", "group_rank(ts_delta({field}, 22), industry)"),
    ("shape.ts_std_dev", "risk", "ts_std_dev({field}, 22)"),
    ("shape.ts_arg_min", "timing", "ts_arg_min({field}, 22)"),
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _scope_key(record):
    fields = _SCOPE_FIELDS if record.get("template_learning_version") else _LEGACY_SCOPE_FIELDS
    return tuple(str(record.get(name, "")) for name in fields)


def _normalized_expression(expression):
    return re.sub(r"\s+", "", expression or "")


def _introduced_operators(expression, inherited_expression=""):
    candidate = Counter(name.lower() for name in _CALL_PATTERN.findall(expression or ""))
    inherited = Counter(
        name.lower() for name in _CALL_PATTERN.findall(inherited_expression or "")
    )
    return candidate - inherited


def resolve_template_category(primary_tower=None, field_categories=()):
    """主塔是权威来源；字段 Category 仅回退并负责发现冲突。"""
    tower_category = ""
    if primary_tower:
        tower_category = str(primary_tower).strip().replace("\\", "/").split("/")[-1].upper()
    categories = set()
    for value in field_categories:
        if isinstance(value, dict):
            value = value.get("id") or value.get("name") or value.get("value")
        normalized = str(value or "").strip().upper()
        if normalized:
            categories.add(normalized)
    if tower_category and categories and tower_category not in categories:
        return {
            "category": "UNKNOWN", "category_source": "CONFLICT",
            "status": "PENDING_CATEGORY_CONFLICT",
        }
    if tower_category:
        return {"category": tower_category, "category_source": "PRIMARY_TOWER", "status": "OK"}
    if len(categories) == 1:
        return {
            "category": next(iter(categories)), "category_source": "FIELD_METADATA",
            "status": "OK",
        }
    return {
        "category": "UNKNOWN",
        "category_source": "CONFLICT" if len(categories) > 1 else "MISSING",
        "status": "PENDING_CATEGORY_CONFLICT" if len(categories) > 1 else "PENDING_CATEGORY",
    }


def _variant_params(entry):
    """生成各参数轴的相邻点；单个候选只改变一轴，不做笛卡尔积。"""
    params = dict(entry.get("params") or {})
    variants = [params]
    for name, value in params.items():
        choices = (
            _GROUP_VALUES if name == "group" else
            _DELAY_VALUES if name == "days" else
            _DECAY_VALUES if name == "d" and (
                entry.get("template_id") in {"post.decay", "advanced.decay_linear"}
            ) else
            _LOOKBACK_VALUES if name in {"d", "d1", "d2", "rank_d", "vol_d", "d_vol"} else ()
        )
        if name in {"d", "d1", "d2", "rank_d", "vol_d", "d_vol"} and entry.get("horizon_days"):
            choices = tuple(choice for choice in choices if choice in entry["horizon_days"])
        if not choices:
            continue
        if value in choices:
            index = choices.index(value)
            neighbor_indexes = [index - 1, index + 1]
        else:
            neighbor_indexes = list(range(len(choices)))
        for index in neighbor_indexes:
            if 0 <= index < len(choices):
                variant = dict(params)
                variant[name] = choices[index]
                if variant not in variants:
                    variants.append(variant)
    return variants


def _variant_id(template_version, params):
    payload = json.dumps(params or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{template_version}|{payload}".encode("utf-8")).hexdigest()[:16]


def _entry_for_stage(entry, stage, params=None):
    stage = max(1, min(3, int(stage or 1)))
    if stage not in entry.get("stages", (1,)):
        return None
    role = entry.get("role_by_stage", {}).get(stage)
    if not role:
        return None
    value = {**entry, "params": dict(params if params is not None else entry.get("params") or {})}
    value["stage"] = stage
    value["role"] = role
    value["target_metrics"] = _ROLE_TARGETS[role]
    value["template_class"] = entry.get("class_by_stage", {}).get(
        stage, entry.get("template_class", "STATISTICAL_CONTROL")
    )
    return value


def _source_hash(func):
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        source = f"{func.__module__}.{func.__name__}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def _operators(expression):
    return _CALL_PATTERN.findall(expression or "")


def _condition_matches(condition, fields):
    if condition == "matrix_fields":
        return bool(fields) and all(str(field.get("type", "")).upper() == "MATRIX" for field in fields)
    if condition and condition.startswith("admin_"):
        return semantic_pair(fields, condition) is not None
    ids = {str(field.get("id", "")).lower() for field in fields}
    joined = " ".join(ids)
    if not condition:
        return True
    if condition == "needs_high":
        return "high" in ids
    if condition == "needs_open_close":
        return {"open", "close"}.issubset(ids)
    if condition == "returns_like":
        return any(token in joined for token in ("return", "ret_", "pct", "yield"))
    if condition == "news_like":
        return any(token in joined for token in ("news", "nws", "headline"))
    if condition == "analyst_like":
        return any(token in joined for token in ("analyst", "anl", "estimate", "est_"))
    if condition == "sentiment_like":
        return any(token in joined for token in ("sent", "senti", "forum", "news", "nws"))
    if condition == "vector_only":
        return any(str(field.get("type", "")).upper() == "VECTOR" for field in fields)
    if condition == "hu_ge_pair":
        if len(fields) != 2:
            return False
        if any(str(field.get("type", "")).upper() != "MATRIX" for field in fields):
            return False
        datasets = {str(field.get("dataset_id") or "UNKNOWN") for field in fields}
        if len(datasets) != 1 or "UNKNOWN" in datasets:
            return False
        shared_tags = _field_semantic_tags([fields[0]]) & _field_semantic_tags([fields[1]])
        return bool(shared_tags - {"information_signal"})
    tags = _field_semantic_tags(fields)
    joined_text = " ".join(
        str(field.get(name) or "").lower()
        for field in fields for name in ("id", "name", "description")
    )
    if condition == "fundamental_pair":
        return len(fields) == 2 and "fundamental" in tags
    if condition == "fundamental_or_analyst":
        return bool(tags & {"fundamental", "analyst", "model"})
    if condition == "price_like":
        return any(token in joined_text for token in ("price", "close", "vwap", "open"))
    if condition == "volume_like":
        return any(token in joined_text for token in ("volume", "turnover", "flow", "imbalance"))
    if condition == "model_or_sentiment":
        return bool(tags & {"model", "sentiment"})
    if condition == "put_call_pair":
        return len(fields) == 2 and "put" in joined_text and "call" in joined_text
    if condition == "call_put_vol_pair":
        return (
            len(fields) == 2 and "put" in joined_text and "call" in joined_text
            and any(token in joined_text for token in ("vol", "volatility", "iv"))
        )
    if condition == "macro_like":
        return "macro" in tags
    if condition == "event_like":
        return bool(tags & {"event", "insider"})
    return False


_SEMANTIC_WORDS = {
    "analyst": ("analyst", "estimate", "est_", "revision", "recommend", "target"),
    "model": ("model", "score", "signal", "factor", "prediction"),
    "institution": ("institution", "holding", "ownership", "fund_flow", "position"),
    "insider": ("insider", "transaction", "buy", "sell", "net_purchase"),
    "imbalance": ("imbalance", "order", "flow", "bid", "ask", "volume"),
    "price_volume": ("price", "close", "open", "return", "volume", "turnover", "vwap"),
    "sentiment": ("sentiment", "news", "headline", "forum", "opinion", "buzz"),
    "fundamental": ("fundamental", "value", "growth", "earn", "revenue", "sales", "asset", "cash", "margin", "quality"),
    "technical": ("technical", "price", "return", "volume", "volatility", "momentum"),
    "options": ("option", "put", "call", "implied_vol", "open_interest"),
    "macro": ("macro", "inflation", "interest", "yield", "fx", "currency", "gdp"),
    "event": ("event", "announcement", "buyback", "merger", "acquisition", "corporate_action"),
}


def _field_semantic_tags(fields):
    """从可审计元数据提取保守语义标签；不推断收益方向。"""
    text = " ".join(
        str(field.get(name) or "").lower()
        for field in fields
        for name in ("id", "name", "description", "dataset_id", "category")
    )
    tags = {tag for tag, words in _SEMANTIC_WORDS.items() if any(word in text for word in words)}
    if tags:
        tags.add("information_signal")
    if tags & {"imbalance", "price_volume", "sentiment", "technical"}:
        tags.add("short_reversal_signal")
    return tags


def _economic_match(entry, category, fields):
    if entry.get("template_class") != "ECONOMIC_SIGNAL":
        return False, (), "非经济信号模板"
    supported = set(entry.get("supported_categories") or ())
    if supported and category not in supported:
        return False, (), f"Category {category} 不在模板白名单"
    tags = _field_semantic_tags(fields)
    requirements = set(entry.get("semantic_requirements") or ())
    if requirements and not requirements.issubset(tags):
        return False, tuple(sorted(tags)), "字段语义证据不足"
    if category == "OTHER" and not tags.intersection({
        "technical", "price_volume", "fundamental", "model", "sentiment",
        "options", "macro", "event", "insider",
    }):
        return False, tuple(sorted(tags)), "OTHER 未识别 technical/return/value 等语义"
    return True, tuple(sorted(tags)), ""


def _usable_fields(context):
    fields = []
    for value in context.get("fields", []):
        field = value if isinstance(value, dict) else {"id": str(value)}
        field_type = str(field.get("type", "UNKNOWN")).upper()
        if field_type in {"GROUP", "CATEGORY"}:
            continue
        field = dict(field)
        field["expression"] = (
            f"vec_avg({field['id']})" if field_type == "VECTOR" else field["id"]
        )
        fields.append(field)
    return fields


def _category_fields(context):
    """只接受平台元数据明确标记的分类字段，绝不按字段名猜类型。"""
    fields = []
    for value in context.get("fields", []):
        field = value if isinstance(value, dict) else {"id": str(value)}
        if str(field.get("type", "UNKNOWN")).upper() not in {"GROUP", "CATEGORY"}:
            continue
        field = dict(field)
        field["expression"] = field["id"]
        fields.append(field)
    return fields


def _same_dataset_pair(fields):
    for index, first in enumerate(fields):
        for second in fields[index + 1:]:
            left = first.get("dataset_id")
            right = second.get("dataset_id")
            if left and right and left != right:
                continue
            return first, second
    return None


def _ordered_semantic_pair(fields, condition):
    if condition and condition.startswith("admin_"):
        return semantic_pair(fields, condition)
    pair = _same_dataset_pair(fields)
    if not pair or condition not in {"put_call_pair", "call_put_vol_pair"}:
        return pair
    first, second = pair
    first_text = " ".join(str(first.get(name) or "").lower() for name in ("id", "name", "description"))
    second_text = " ".join(str(second.get(name) or "").lower() for name in ("id", "name", "description"))
    if condition == "put_call_pair":
        return (first, second) if "put" in first_text and "call" in second_text else (second, first)
    return (first, second) if "call" in first_text and "put" in second_text else (second, first)


def _make_candidate(entry, context, fields):
    module = importlib.import_module(entry["module"])
    func = getattr(module, entry["function"])
    params = dict(entry["params"])
    kind = entry["kind"]
    primary = fields[0] if fields else None
    pair = _ordered_semantic_pair(fields, entry.get("condition"))

    if kind == "fixed":
        expression = func(**params)
        used_fields = fields[:2]
    elif kind == "binary":
        if not pair:
            raise ValueError("需要两个同数据集的兼容字段")
        expression = func(pair[0]["expression"], pair[1]["expression"], **params)
        used_fields = list(pair)
    elif kind == "expression":
        base = context.get("expression")
        if not base:
            raise ValueError("缺少源表达式")
        expression = func(base, **params)
        used_fields = fields[:2]
    elif kind == "raw_vector":
        primary = next(
            (field for field in fields if str(field.get("type", "")).upper() == "VECTOR"),
            None,
        )
        if not primary:
            raise ValueError("需要 VECTOR 字段")
        expression = func(primary["id"], **params)
        used_fields = [primary]
    else:
        if not primary:
            raise ValueError("没有可用数值字段")
        expression = func(primary["expression"], **params)
        used_fields = [primary]

    operators = _operators(expression)
    inherited_expression = context.get("expression", "") if kind == "expression" else ""
    introduced = _introduced_operators(expression, inherited_expression)
    introduced_names = set(introduced)
    allowed = {str(name).lower() for name in (context.get("allowed_operators") or ())}
    unauthorized = sorted(introduced_names - allowed)
    reason = ""
    if introduced_names & _FORBIDDEN_OPERATORS:
        reason = "新变换引入项目禁用操作符"
    elif sum(int(value) for value in introduced.values()) >= 6:
        reason = "新引入操作符数量 >= 6"
    elif context.get("allowed_operators") is None:
        reason = "实时算子权限不可观察"
    elif unauthorized:
        reason = f"当前账户无权限操作符: {', '.join(unauthorized)}"

    validation = verify_alpha_expression(expression)
    if entry.get("source_kind") == "ADMIN_DISTRIBUTED" or entry.get("catalog_status") == "LOCAL_PASS_UNVALIDATED":
        datasets = {field.get("dataset_id") for field in used_fields}
        if len(datasets) != 1 or next(iter(datasets)) in {None, "", "UNKNOWN"}:
            reason = "管理员模板需要可核实的单数据集字段"
        elif operator_count(expression) >= 6:
            reason = "管理员模板总操作符调用数 >=6"
    if not validation.get("valid"):
        reason = "; ".join(str(item) for item in validation.get("errors", [])) or "本地语法检查失败"

    normalized = _normalized_expression(expression)
    template_version = _source_hash(func)
    return {
        **entry,
        "candidate_origin": "FORMAL_TEMPLATE",
        "expression": expression,
        "expression_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
        "template_version": template_version,
        "variant_id": _variant_id(template_version, params),
        "resolved_params": params,
        "operators": operators,
        "fields": [field.get("id") for field in used_fields],
        "field_type": "+".join(sorted({str(field.get("type", "UNKNOWN")) for field in used_fields})),
        "dataset_id": "+".join(sorted({str(field.get("dataset_id", "UNKNOWN")) for field in used_fields})),
        "local_validation": validation,
        "eligible": not reason,
        "reason": reason,
    }


def _shape_candidates(context, fields):
    if not fields:
        return []
    field = fields[0]["expression"]
    base = context.get("expression", field)
    candidates = []
    stage = max(1, min(3, int(context.get("stage") or 1)))
    if stage > 2:
        return []
    role = "SIGNAL_BUILD" if stage == 1 else "STABILITY_CONTROL"
    for template_id, family, pattern in OPERATOR_SHAPES:
        expression = pattern.format(field=field, expression=base)
        operators = _operators(expression)
        validation = verify_alpha_expression(expression)
        inherited_expression = base if "{expression}" in pattern else ""
        introduced = _introduced_operators(expression, inherited_expression)
        introduced_names = set(introduced)
        allowed = {str(name).lower() for name in (context.get("allowed_operators") or ())}
        unauthorized = sorted(introduced_names - allowed)
        reason = ""
        if introduced_names & _FORBIDDEN_OPERATORS:
            reason = "新变换引入项目禁用操作符"
        elif sum(int(value) for value in introduced.values()) >= 6:
            reason = "新引入操作符数量 >= 6"
        elif context.get("allowed_operators") is None:
            reason = "实时算子权限不可观察"
        elif unauthorized:
            reason = f"当前账户无权限操作符: {', '.join(unauthorized)}"
        elif not validation.get("valid"):
            reason = "; ".join(str(item) for item in validation.get("errors", []))
        normalized = _normalized_expression(expression)
        candidates.append({
            "template_id": template_id,
            "module": __name__,
            "function": template_id.split(".")[-1],
            "family": family,
            "tier": 2,
            "kind": "shape",
            "params": {},
            "condition": None,
            "enabled": True,
            "note": "操作符形态探索",
            "expression": expression,
            "expression_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
            "template_version": "builtin-v1",
            "variant_id": _variant_id("builtin-v1", {}),
            "resolved_params": {},
            "stage": stage,
            "role": role,
            "target_metrics": _ROLE_TARGETS[role],
            "operators": operators,
            "fields": [fields[0].get("id")],
            "field_type": str(fields[0].get("type", "UNKNOWN")),
            "dataset_id": str(fields[0].get("dataset_id", "UNKNOWN")),
            "local_validation": validation,
            "eligible": not reason,
            "reason": reason,
            "candidate_origin": "FORMAL_TEMPLATE",
            "template_class": "STATISTICAL_CONTROL",
            "supported_categories": (),
            "economic_hypothesis": "",
            "semantic_requirements": (),
            "semantic_match_evidence": (),
            "economic_match": False,
            "economic_thesis_id": template_id,
        })
    return candidates


def load_template_usage(path=TEMPLATE_USAGE_V5_EVENTS_PATH):
    """增量读取 JSONL；同一进程只解析新增部分。"""
    path = Path(path)
    if not path.exists():
        return []
    cache_key = str(path.resolve())
    size = path.stat().st_size
    cached = _EVENT_CACHE.get(cache_key)
    if not cached or size < cached["offset"]:
        cached = {"offset": 0, "events": []}
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(cached["offset"])
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                cached["events"].append(value)
        cached["offset"] = handle.tell()
    _EVENT_CACHE[cache_key] = cached
    return list(cached["events"])


def _latest_events(events):
    latest = {}
    for event in events:
        key = event.get("candidate_key") or "|".join((
            str(event.get("run_id", "")), str(event.get("template_id", "")),
            str(event.get("expression_hash", "")), str(event.get("decay", "")),
        ))
        latest[key] = event
    return list(latest.values())


def _explicit_overfit_failure(record):
    """只认可明确失败证据；检查缺失或PENDING不算过拟合。"""
    if not isinstance(record, dict):
        return False
    for key in ("overfit_status", "robust_status", "strict_overfit_status"):
        if str(record.get(key, "")).upper() in {"FAIL", "FAILED", "OVERFIT_FAIL"}:
            return True
    checks = record.get("checks") or record.get("platform_checks") or []
    if isinstance(checks, dict):
        checks = [{"name": key, "result": value} for key, value in checks.items()]
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            name = str(check.get("name", "")).upper()
            result = str(check.get("result") or check.get("status") or "").upper()
            if ("OVERFIT" in name or "ROBUST" in name) and result in {"FAIL", "FAILED"}:
                return True
    return False


def summarize_template_usage(scope=None, path=TEMPLATE_USAGE_V5_EVENTS_PATH,
                             summary_path=TEMPLATE_USAGE_V5_SUMMARY_PATH):
    """v4 按 Region×Category×Stage×版本×参数汇总正式模板结果。"""
    events = _latest_events(load_template_usage(path))
    if scope:
        if scope.get("template_learning_version"):
            events = [
                event for event in events
                if event.get("template_learning_version") == scope["template_learning_version"]
                and str(event.get("region", "")) == str(scope.get("region", ""))
                and str(event.get("category", "")) == str(scope.get("category", ""))
                and (
                    scope.get("stage") is None
                    or int(event.get("stage") or 0) == int(scope.get("stage") or 0)
                )
            ]
        else:
            wanted = _scope_key(scope)
            events = [event for event in events if _scope_key(event) == wanted]

    grouped = defaultdict(list)
    for event in events:
        is_v2 = bool(event.get("template_learning_version"))
        key = (
            is_v2, _scope_key(event), int(event.get("stage") or 0) if is_v2 else 0,
            event.get("template_id", "UNKNOWN"),
            event.get("template_version", "LEGACY") if is_v2 else "LEGACY",
            event.get("variant_id", "LEGACY") if is_v2 else "LEGACY",
        )
        grouped[key].append(event)

    rows = []
    for (is_v2, scope_key, stage, template_id, template_version, variant_id), items in grouped.items():
        complete = [
            item for item in items
            if item.get("status") in {"COMPLETE", "CACHE_HIT"}
            and (
                not is_v2
                or item.get("candidate_origin") == "FORMAL_TEMPLATE"
                and item.get("baseline_metrics_complete") is True
                and item.get("result_metrics_complete") is True
            )
        ]
        improved = [
            item for item in complete
            if (
                item.get("margin_effective_improvement") is True
                if item.get("repair_goal") == "MARGIN"
                else item.get("gate_improved") is True
                and item.get("retained_previous_gates") is not False
            )
        ]
        hard_passed = [item for item in complete if item.get("hard_pass")]
        pending = [item for item in items if item.get("status") in _NON_PERFORMANCE_STATUSES]
        deltas = [float(item.get("score_delta", 0) or 0) for item in complete]
        gate_deltas = [
            float(item.get("gate_deficit_delta", 0) or 0) for item in complete
            if item.get("gate_deficit_delta") is not None
        ]
        target_improvements = [
            float(item.get("target_improvement_value")) for item in complete
            if item.get("target_improvement_value") is not None
        ]
        manually_disabled = any(item.get("template_state") == "MANUAL_DISABLED" for item in items)
        source_ids = {str(item.get("source_alpha_id") or "") for item in complete}
        source_ids.discard("")
        improved_sources = {str(item.get("source_alpha_id") or "") for item in improved}
        improved_sources.discard("")
        median_gate_delta = median(gate_deltas) if gate_deltas else ""
        median_target_improvement = median(target_improvements) if target_improvements else ""
        improvement_rate = len(improved) / len(complete) if complete else 0.0
        margin_effect_deltas = [
            float(item.get("margin_bp_delta")) for item in complete
            if item.get("repair_goal") == "MARGIN"
            and item.get("margin_bp_delta") is not None
        ]
        median_effect = (
            median(margin_effect_deltas) if margin_effect_deltas
            else median_target_improvement
        )
        retained_count = sum(
            (
                item.get("non_margin_gates_retained") is True
                if item.get("repair_goal") == "MARGIN"
                else item.get("retained_previous_gates") is True
            )
            for item in complete
        )
        retained_rate = retained_count / len(complete) if complete else 0.0
        recheck_recovered = any(
            item.get("template_state") == "LOW_PRIORITY"
            and int(item.get("low_recheck_cycle") or 0) > 0
            and item.get("gate_improved") is True
            and item.get("retained_previous_gates") is True
            for item in complete
        )
        overfit_failed = any(_explicit_overfit_failure(item) for item in items)
        if overfit_failed:
            state = "DISABLED_SCOPE"
        elif not is_v2:
            if manually_disabled:
                state = "MANUAL_DISABLED"
            elif improved or hard_passed:
                state = "PROMISING"
            elif len(complete) >= 8:
                state = "DISABLED_SCOPE"
            elif len(complete) >= 3:
                state = "LOW_PRIORITY"
            else:
                state = "ACTIVE"
        elif manually_disabled:
            state = "MANUAL_DISABLED"
        elif recheck_recovered:
            state = "PROBATION"
        elif (
            len(complete) >= 8 and len(source_ids) >= 3
            and improvement_rate >= 0.25
            and retained_rate >= 0.75
            and isinstance(median_effect, (int, float))
            and median_effect > 0
        ):
            state = "CHAMPION"
        elif len(improved_sources) >= 2:
            state = "PROMISING"
        elif len(complete) >= 16 and len(source_ids) >= 5 and not improved:
            state = "DISABLED_SCOPE"
        elif len(complete) >= 8 and (
            improvement_rate < 0.125
            or isinstance(median_effect, (int, float)) and median_effect < 0
        ):
            state = "LOW_PRIORITY"
        else:
            state = "PROBATION"
        row = {
            **dict(zip(_SCOPE_FIELDS if is_v2 else _LEGACY_SCOPE_FIELDS, scope_key)),
            "template_id": template_id,
            "template_state": state,
            "disabled_reason": "OVERFIT_OR_ROBUST_FAIL" if overfit_failed else "",
            "complete_count": len(complete),
            "improved_count": len(improved),
            "hard_pass_count": len(hard_passed),
            "pending_count": len(pending),
            "median_score_delta": median(deltas) if deltas else "",
            "median_gate_deficit_delta": median_gate_delta,
            "median_target_improvement": median_target_improvement,
            "last_used_at": max((item.get("timestamp", "") for item in items), default=""),
        }
        if is_v2:
            margin_deltas = [
                float(item.get("margin_bp_delta")) for item in complete
                if item.get("margin_bp_delta") is not None
            ]
            row.update({
                "template_learning_version": items[-1].get("template_learning_version"),
                "stage": stage,
                "template_role": items[-1].get("template_role") or items[-1].get("role"),
                "template_version": template_version,
                "variant_id": variant_id,
                "resolved_params": json.dumps(
                    items[-1].get("resolved_params") or {}, ensure_ascii=False, sort_keys=True,
                ),
                "unique_source_count": len(source_ids),
                "improved_source_count": len(improved_sources),
                "improvement_rate": improvement_rate,
                "retained_gate_count": retained_count,
                "retained_gate_rate": retained_rate,
                "template_class": items[-1].get("template_class"),
                "economic_hypothesis": items[-1].get("economic_hypothesis"),
                "repair_goal": items[-1].get("repair_goal"),
                "margin_cross_count": sum(
                    item.get("margin_threshold_crossed") is True for item in complete
                ),
                "median_margin_bp_delta": median(margin_deltas) if margin_deltas else "",
                "turnover_invalid_count": sum(
                    item.get("turnover_retained") is False for item in complete
                ),
            })
        rows.append(row)

    rows.sort(key=lambda row: (
        {"CHAMPION": 0, "PROMISING": 1, "PROBATION": 2, "ACTIVE": 2,
         "LOW_PRIORITY": 3, "DISABLED_SCOPE": 4}.get(row["template_state"], 5),
        -row["improved_count"], -row["hard_pass_count"],
        -(row["median_gate_deficit_delta"]
          if isinstance(row["median_gate_deficit_delta"], float) else -9999),
        row["template_id"],
    ))
    if summary_path:
        summary_path = Path(summary_path)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        is_v2_summary = any(row.get("template_learning_version") for row in rows)
        fieldnames = (
            ["template_learning_version", "region", "category", "stage", "template_role",
             "template_id", "template_version", "variant_id", "resolved_params",
             "template_state", "complete_count", "unique_source_count",
             "improved_count", "improved_source_count", "improvement_rate",
             "retained_gate_count", "retained_gate_rate", "hard_pass_count", "pending_count",
             "template_class", "economic_hypothesis",
             "repair_goal", "margin_cross_count", "median_margin_bp_delta",
             "turnover_invalid_count",
             "median_score_delta", "median_gate_deficit_delta",
             "median_target_improvement", "last_used_at"]
            if is_v2_summary else list(_LEGACY_SCOPE_FIELDS) + [
                "template_id", "template_state", "complete_count", "improved_count",
                "hard_pass_count", "pending_count", "median_score_delta", "last_used_at",
                "median_gate_deficit_delta", "median_target_improvement",
            ]
        )
        fieldnames.append("disabled_reason")
        with summary_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return rows


def record_template_usage(record, path=TEMPLATE_USAGE_V5_EVENTS_PATH,
                          summary_path=TEMPLATE_USAGE_V5_SUMMARY_PATH,
                          refresh_summary=True):
    """追加一条事件并刷新汇总；不覆盖历史。"""
    events = record_template_usage_batch(
        [record], path, summary_path, refresh_summary=refresh_summary
    )
    return events[0] if events else None


def record_template_usage_batch(records, path=TEMPLATE_USAGE_V5_EVENTS_PATH,
                                summary_path=TEMPLATE_USAGE_V5_SUMMARY_PATH,
                                refresh_summary=True):
    """批量追加事件并只刷新一次汇总；全部事件校验通过后才写入。"""
    events = []
    for record in records:
        event = dict(record)
        event.setdefault("timestamp", _now())
        event.setdefault("status", "PENDING")
        if event["status"] not in _FINAL_STATUSES | {"GENERATED", "SUBMITTED"}:
            raise ValueError(f"未知模板状态: {event['status']}")
        if event.get("candidate_origin") != "FORMAL_TEMPLATE":
            continue
        if event.get("status") not in {"COMPLETE", "AGGREGATED_REJECTED"}:
            continue
        events.append(event)
    if not events:
        return []

    path = Path(path)
    with _WRITE_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing_keys = {_compact_event_key(event) for event in load_template_usage(path)}
        deduplicated = []
        for event in events:
            event_key = _compact_event_key(event)
            if event_key in existing_keys:
                continue
            existing_keys.add(event_key)
            deduplicated.append(event)
        events = deduplicated
        if not events:
            return []
        with path.open("a", encoding="utf-8") as handle:
            handle.writelines(
                json.dumps(event, ensure_ascii=False, default=str) + "\n"
                for event in events
            )
        if refresh_summary:
            summarize_template_usage(path=path, summary_path=summary_path)
    return events


def _compact_event_key(event):
    """Stable result identity so restart/recovery does not grow the v5 ledger."""
    explicit = event.get("candidate_key")
    if explicit:
        return f"candidate:{explicit}:{event.get('status')}"
    parts = (
        event.get("template_learning_version"), event.get("source_alpha_id"),
        event.get("formal_batch_id") or event.get("run_id"), event.get("template_id"),
        event.get("template_version"), event.get("variant_id"), event.get("stage"),
        event.get("expression_hash") or event.get("expression"), event.get("status"),
        event.get("rejection_reason") or event.get("reason"),
    )
    payload = json.dumps(parts, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _low_recheck_context(context, events):
    scoped = [
        event for event in events
        if event.get("template_learning_version") == TEMPLATE_LEARNING_VERSION
        and str(event.get("region")) == str(context.get("region"))
        and str(event.get("category")) == str(context.get("category"))
        and int(event.get("stage") or 0) == int(context.get("stage") or 0)
        and event.get("candidate_origin") == "FORMAL_TEMPLATE"
    ]
    parent_ids = {
        str(event.get("formal_batch_id") or event.get("run_id") or "")
        for event in scoped if event.get("status") in {"GENERATED", "COMPLETE", "CACHE_HIT"}
    }
    parent_ids.discard("")
    cycle = len(parent_ids) // 20
    rechecked = {
        (event.get("template_id"), event.get("template_version"), event.get("variant_id"))
        for event in scoped
        if int(event.get("low_recheck_cycle") or 0) >= cycle and cycle > 0
    }
    return cycle, rechecked


def _legacy_cooldown_keys(context, path=TEMPLATE_USAGE_V2_SUMMARY_PATH):
    """v2 只提供初始冷却名单，不迁移任何正负表现样本。"""
    path = Path(path)
    if not path.exists():
        return set()
    keys = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if (
                    str(row.get("region")) != str(context.get("region"))
                    or str(row.get("category")) != str(context.get("category"))
                    or int(row.get("stage") or 0) != int(context.get("stage") or 0)
                    or int(float(row.get("complete_count") or 0)) < 8
                    or int(float(row.get("unique_source_count") or 0)) < 5
                    or int(float(row.get("improved_count") or 0)) != 0
                ):
                    continue
                delta = row.get("median_gate_deficit_delta")
                if delta in {None, ""} or float(delta) >= 0:
                    continue
                keys.add((row.get("template_id"), row.get("template_version"), row.get("variant_id")))
    except (OSError, ValueError, csv.Error):
        return set()
    return keys


def select_template_candidates(context, limit=64, include_rejected=False):
    """按阶段角色及 Region×Category 当前版本证据选择候选。"""
    if limit < 1:
        return []
    fields = _usable_fields(context)
    category_fields = _category_fields(context)
    is_v2 = context.get("template_learning_version") == TEMPLATE_LEARNING_VERSION
    stage = max(1, min(3, int(context.get("stage") or 1)))
    desired_role = context.get("template_role")
    summary_rows = summarize_template_usage(
        scope=context,
        path=context.get("usage_path", TEMPLATE_USAGE_V5_EVENTS_PATH),
        summary_path=None,
    )
    usage_events = load_template_usage(context.get("usage_path", TEMPLATE_USAGE_V5_EVENTS_PATH))
    low_cycle, rechecked_low = _low_recheck_context(context, usage_events)
    # 用实际尝试轮动；PENDING 只算调用次数，不算性能失败。
    scoped_events = [event for event in _latest_events(usage_events)
                     if event.get("template_learning_version") == context.get("template_learning_version")
                     and all(str(event.get(key, "")) == str(context.get(key, "")) for key in _SCOPE_FIELDS)
                     and int(event.get("stage") or 0) == stage]
    attempts = Counter(event.get("template_id") for event in scoped_events)
    # v4 的 Margin 目标与旧版评分口径不同，旧账本只读留档，不继承冷却状态。
    legacy_cooldown = set()
    summaries = {
        (
            row.get("template_id"), row.get("template_version", "LEGACY"),
            row.get("variant_id", "LEGACY"),
        ): row for row in summary_rows
    }
    built = []
    for entry in TEMPLATE_CANDIDATES:
        # 爬山显式启用管理员优先；其他调用方保持原候选行为。
        if (entry.get("source_kind") == "ADMIN_DISTRIBUTED" or entry.get("catalog_status")) and not context.get("prefer_admin_templates"):
            continue
        variants = _variant_params(entry) if is_v2 else [dict(entry.get("params") or {})]
        for params in variants:
            staged_entry = _entry_for_stage(entry, stage, params) if is_v2 else {
                **entry, "params": params, "stage": stage,
                "role": "SIGNAL_BUILD", "target_metrics": _ROLE_TARGETS["SIGNAL_BUILD"],
            }
            if staged_entry is None:
                continue
            if desired_role and staged_entry.get("role") != desired_role:
                continue
            economic_match, semantic_tags, semantic_reason = _economic_match(
                staged_entry, str(context.get("category") or "UNKNOWN").upper(), fields
            )
            catalog_probe = context.get("prefer_catalog_templates") and staged_entry.get("catalog_status") == "LOCAL_PASS_UNVALIDATED"
            if is_v2 and stage == 1 and not economic_match and not catalog_probe:
                if include_rejected:
                    built.append({
                        **staged_entry, "eligible": False,
                        "reason": semantic_reason or "Stage 1 只允许经济语义匹配模板",
                        "semantic_match_evidence": semantic_tags,
                    })
                continue
            candidate_fields = category_fields if staged_entry.get("kind") == "category" else fields
            if not candidate_fields or not _condition_matches(staged_entry["condition"], candidate_fields):
                if include_rejected:
                    built.append({
                        **staged_entry, "eligible": False,
                        "reason": "字段语义或固定字段条件不满足",
                    })
                continue
            try:
                candidate = _make_candidate(staged_entry, context, candidate_fields)
            except Exception as exc:
                candidate = {**staged_entry, "eligible": False, "reason": str(exc)}
            row = summaries.get((
                candidate.get("template_id"), candidate.get("template_version", "LEGACY"),
                candidate.get("variant_id", "LEGACY"),
            ), {})
            state = row.get("template_state", "PROBATION" if is_v2 else "ACTIVE")
            candidate_key = (
                candidate.get("template_id"), candidate.get("template_version"),
                candidate.get("variant_id"),
            )
            if not row and candidate_key in legacy_cooldown:
                state = "LOW_PRIORITY"
            excluded_states = {"DISABLED_SCOPE", "MANUAL_DISABLED"}
            if context.get("prefer_admin_templates"):
                # 本轮用户明确禁止差模板复检；LOW不能作为挑战或补位重入。
                excluded_states.add("LOW_PRIORITY")
            if not staged_entry["enabled"] or state in excluded_states:
                continue
            candidate["template_state"] = state
            candidate["economic_match"] = economic_match
            candidate["semantic_match_evidence"] = semantic_tags
            candidate["template_complete_count"] = int(row.get("complete_count") or 0)
            candidate["template_attempt_count"] = (
                attempts[candidate.get("template_id")] if context.get("prefer_admin_templates") else 0
            )
            candidate["selection_bucket"] = (
                "GOOD" if state in {"CHAMPION", "PROMISING"}
                else "PROBATION" if row
                else "CHALLENGER"
            )
            low_key = candidate_key
            candidate["low_recheck_cycle"] = low_cycle
            candidate["low_recheck_due"] = (
                state == "LOW_PRIORITY" and low_cycle > 0 and low_key not in rechecked_low
            )
            built.append(candidate)

    if not desired_role or desired_role == (
        "SIGNAL_BUILD" if stage == 1 else "STABILITY_CONTROL"
    ):
        # 操作符形态没有独立经济假设，Stage 1 不再把它们当正式模板。
        if stage > 1 or not is_v2:
            built.extend(_shape_candidates(context, fields))
    # 管理员目录可与既有优胜模板同式；先排性能状态再去重，避免新目录遮蔽CHAMPION。
    if context.get("prefer_admin_templates"):
        from Core.factor.templates.disabled_templates import blocked_reason
        # 对所有候选（含形态补位）拦截，不能借新ID、版本或补位绕过日志停用。
        for candidate in built:
            reason = blocked_reason(candidate, {**context, "stage": stage})
            if reason:
                candidate.update(eligible=False, reason=reason, template_state="DISABLED_SCOPE")
        priorities = {"CHAMPION": 0, "PROMISING": 1, "PROBATION": 2, "ACTIVE": 2, "LOW_PRIORITY": 3}
        built.sort(key=lambda candidate: (
            0 if context.get("prefer_catalog_templates") and candidate.get("catalog_status") == "LOCAL_PASS_UNVALIDATED" else 1,
            priorities.get(candidate.get("template_state", "ACTIVE"), 3),
            1 if candidate.get("kind") == "shape" else 0,
            candidate.get("template_attempt_count", 0),
            0 if candidate.get("source_kind") == "ADMIN_DISTRIBUTED" else 1,
            candidate.get("tier", 9), candidate.get("template_id", ""),
        ))
    seen = set()
    eligible = []
    rejected = []
    for candidate in built:
        expression_hash = candidate.get("expression_hash")
        # rank(zscore(x)) 等排序等价式依靠标准表达式和模板 ID 保留单一代表；
        # 已经完全相同的表达式无条件去重。
        if candidate.get("eligible") and expression_hash not in seen:
            seen.add(expression_hash)
            eligible.append(candidate)
        elif include_rejected:
            rejected.append(candidate)

    state_order = {
        "CHAMPION": 0, "PROMISING": 1, "PROBATION": 2,
        "ACTIVE": 2, "LOW_PRIORITY": 3,
    }
    eligible.sort(key=lambda candidate: (
        0 if context.get("prefer_catalog_templates") and candidate.get("catalog_status") == "LOCAL_PASS_UNVALIDATED" else 1,
        state_order.get(candidate.get("template_state", "ACTIVE"), 3),
        1 if candidate.get("kind") == "shape" else 0,
        candidate.get("template_attempt_count", 0),
        0 if candidate.get("source_kind") == "ADMIN_DISTRIBUTED" else 1,
        candidate.get("tier", 9),
        candidate.get("template_id", ""),
    ))
    shapes = [item for item in eligible if item.get("kind") == "shape"]
    ordinary = [item for item in eligible if item.get("kind") != "shape"]
    shape_limit = min(16, len(shapes), limit)
    selected = ordinary[:max(0, limit - shape_limit)] + shapes[:shape_limit]
    return (selected, rejected) if include_rejected else selected


def compose_template_batch(candidates, size=8):
    """4 个语义/缺口匹配 + 2 个优胜 + 2 个挑战；LOW 只按期复检。"""
    unique = []
    seen = set()
    for candidate in candidates:
        key = candidate.get("expression_hash")
        if not key or key in seen or not candidate.get("eligible"):
            continue
        seen.add(key)
        unique.append(candidate)
    usable = [
        item for item in unique
        if item.get("template_state") not in {"LOW_PRIORITY", "DISABLED_SCOPE"}
    ]
    matched_pool = [
        item for item in usable
        if item.get("economic_match")
        or item.get("template_class") in {"STATISTICAL_CONTROL", "RISK_REPAIR"}
    ]
    # 四条主方向优先覆盖不同经济假设，参数邻点留给 Challenger。
    matched = []
    theses = set()
    for item in matched_pool:
        thesis = item.get("economic_thesis_id") or item.get("template_id")
        if thesis in theses:
            continue
        theses.add(thesis)
        matched.append(item)
        if len(matched) == 4:
            break
    if len(matched) < 4:
        matched.extend(item for item in matched_pool if item not in matched)
        matched = matched[:4]
    good = [item for item in usable if item.get("template_state") in {"CHAMPION", "PROMISING"}]
    probation = [
        item for item in usable
        if item.get("selection_bucket") == "PROBATION"
        or item.get("template_state") == "ACTIVE"
    ]
    challengers = [
        item for item in usable
        if item.get("selection_bucket") == "CHALLENGER"
    ]
    due_low = [
        item for item in unique
        if item.get("template_state") == "LOW_PRIORITY" and item.get("low_recheck_due")
    ][:1]
    selected = matched[:4]
    selected.extend([item for item in good if item not in selected][:2])
    challenge_slots = 2
    challenge_pool = [item for item in challengers if item not in selected]
    selected.extend(challenge_pool[:challenge_slots - len(due_low)])
    selected.extend(item for item in due_low if item not in selected)
    # 只能用合法经济/同角色 PROBATION 补位；普通 LOW 永不补位。
    selected.extend(item for item in probation if item not in selected)
    selected.extend(item for item in usable if item not in selected)
    return selected[:size] if len(selected) >= size else []


def compose_stage1_template_batch(candidates, size=8):
    """4 Stage0 + 2 经济信号 + 1 范围优胜 + 1 Challenger。"""
    usable = []
    seen = set()
    for item in candidates:
        key = item.get("expression_hash")
        if (
            not key or key in seen or not item.get("eligible")
            or item.get("template_state") in {"LOW_PRIORITY", "DISABLED_SCOPE"}
        ):
            continue
        seen.add(key)
        usable.append(item)

    selected = []

    def extend(pool, limit, distinct_thesis=False):
        theses = {
            item.get("economic_thesis_id") or item.get("template_id")
            for item in selected
        }
        added = 0
        for item in pool:
            if item in selected:
                continue
            thesis = item.get("economic_thesis_id") or item.get("template_id")
            if distinct_thesis and thesis in theses:
                continue
            selected.append(item)
            theses.add(thesis)
            added += 1
            if added >= limit:
                break

    stage0 = [item for item in usable if str(item.get("template_id", "")).startswith("stage0.")]
    economic = [
        item for item in usable
        if item.get("template_class") == "ECONOMIC_SIGNAL" and item not in stage0
    ]
    good = [item for item in usable if item.get("template_state") in {"CHAMPION", "PROMISING"}]
    challengers = [item for item in usable if item.get("selection_bucket") == "CHALLENGER"]
    extend(stage0, 4, distinct_thesis=True)
    extend(economic, 2, distinct_thesis=True)
    extend(good, 1)
    extend(challengers, 1)
    extend(stage0 + economic + usable, size - len(selected))
    return selected[:size] if len(selected) >= size else []


__all__ = [
    "TEMPLATE_CANDIDATES", "OPERATOR_SHAPES", "record_template_usage",
    "record_template_usage_batch",
    "load_template_usage", "summarize_template_usage", "select_template_candidates",
    "resolve_template_category", "compose_template_batch", "compose_stage1_template_batch",
    "TEMPLATE_LEARNING_VERSION",
]
