"""Stage 0 Basic Signals Templates

本模块提供了基于纯经济学逻辑和0阶思路的最基础因子构建模板。
0阶信号是后续高级模板的种子，旨在通过简单的逻辑运算（如消除量纲、比率构造）提取有经济学意义的特征。
不要直接填入无意义的表达式，参数位应严格对应各 Data Category (Fundamental, Pricing, Analyst, Model) 下相关的原始字段。
"""

def stage0_cross_sectional_rank(field):
    """
    **0阶：截面相对强弱 (Cross-Sectional Rank)**
    - **逻辑 (Logic):** 对任意具有良好截面分布的数据提取其相对位置，去除极端值和绝对量纲。
    - **模板 (Template):** `rank(<field>)`
    - **使用算子 (Operators Used):** `rank`
    - **参数建议 (Parameter Recommendations):**
      - `<field>`: 任意原始字段，如市盈率、特定分析师得分、模型打分等。
    """
    return "rank(%s)" % (field)

def stage0_time_series_rank(field, d=20):
    """
    **0阶：时序相对位置 (Time-Series Rank)**
    - **逻辑 (Logic):** 衡量某个指标在其自身近期历史（特定时间窗口）中的相对高低。
    - **模板 (Template):** `ts_rank(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_rank`
    - **参数建议 (Parameter Recommendations):**
      - `<field>`: 任何时序波动的字段，如价格、情绪得分。
      - `{d}`: 窗口期，通常为 20 (一个月) 或 63 (一个季度)。
    """
    return "ts_rank(%s, %d)" % (field, d)

def stage0_financial_ratio(field_numerator, field_denominator):
    """
    **0阶：财务比率构造 (Fundamental Ratio / Valuation)**
    - **逻辑 (Logic):** 通过除法计算比率以消除规模效应。例如计算 ROA、毛利率、E/P、负债率等。
    - **模板 (Template):** `<field_numerator> / <field_denominator>`
    - **使用算子 (Operators Used):** 无 (基础除法)
    - **参数建议 (Parameter Recommendations):**
      - `<field_numerator>`: 分子字段。例如 `net_income`（净利润）、`gross_profit`（毛利）。
      - `<field_denominator>`: 分母字段。例如 `total_assets`（总资产）、`market_cap`（市值）、`sales_revenue`（营业收入）。
    """
    return "%s / %s" % (field_numerator, field_denominator)

def stage0_yoy_growth(field, d=252):
    """
    **0阶：同比/环比增速 (Growth / Marginal Change)**
    - **逻辑 (Logic):** 衡量基本面数据或预期的边际改善幅度。
    - **模板 (Template):** `(<field> - ts_delay(<field>, {d})) / ts_delay(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - `<field>`: 基本面字段，如营业收入、净利润；或分析师预期字段。
      - `{d}`: 252 (年度同比) 或 63 (季度环比)。
    """
    return "(%s - ts_delay(%s, %d)) / ts_delay(%s, %d)" % (field, field, d, field, d)

def stage0_pricing_bias(price_field, d=20):
    """
    **0阶：量价乖离率 / 短期反转 (Price Mean Reversion)**
    - **逻辑 (Logic):** 衡量当前价格偏离其近期均值的程度。可用于构建短期反转信号。
    - **模板 (Template):** `<price_field> / ts_mean(<price_field>, {d}) - 1`
    - **使用算子 (Operators Used):** `ts_mean`
    - **参数建议 (Parameter Recommendations):**
      - `<price_field>`: 价格字段，通常为 `close` 或 `vwap`。
      - `{d}`: 窗口期，通常为 10 到 20。
    """
    return "%s / ts_mean(%s, %d) - 1" % (price_field, price_field, d)

def stage0_volume_shock(vol_field, d=20):
    """
    **0阶：相对成交量异动 (Volume Shock / Liquidity Anomaly)**
    - **逻辑 (Logic):** 衡量近期成交量相较于历史均值的突然放大或萎缩。
    - **模板 (Template):** `<vol_field> / ts_mean(<vol_field>, {d})`
    - **使用算子 (Operators Used):** `ts_mean`
    - **参数建议 (Parameter Recommendations):**
      - `<vol_field>`: 成交量字段，如 `volume`。
      - `{d}`: 历史均值窗口期，通常为 20。
    """
    return "%s / ts_mean(%s, %d)" % (vol_field, vol_field, d)

def stage0_analyst_surprise(actual_field, estimate_field, scale_field):
    """
    **0阶：预期差与盈余意外 (Analyst Earnings Surprise)**
    - **逻辑 (Logic):** 衡量实际公布的数据与分析师预期之间的差额，并用股价或资产规模进行缩放。
    - **模板 (Template):** `(<actual_field> - <estimate_field>) / <scale_field>`
    - **使用算子 (Operators Used):** 无 (基础四则运算)
    - **参数建议 (Parameter Recommendations):**
      - `<actual_field>`: 实际发布值，如 `actual_eps`。
      - `<estimate_field>`: 分析师预测值，如 `analyst_eps_estimate`。
      - `<scale_field>`: 缩放因子，通常为 `close`（收盘价） 或 `total_assets`（总资产）。
    """
    return "(%s - %s) / %s" % (actual_field, estimate_field, scale_field)

def stage0_model_zscore(model_score_field, d=252):
    """
    **0阶：模型得分或情绪极值 (Model/Sentiment Z-Score)**
    - **逻辑 (Logic):** 针对第三方 AI/ML 模型输出得分或新闻情绪得分，进一步提取其偏离历史均值的程度。
    - **模板 (Template):** `ts_zscore(<model_score_field>, {d})`
    - **使用算子 (Operators Used):** `ts_zscore`
    - **参数建议 (Parameter Recommendations):**
      - `<model_score_field>`: 模型预测分 (如 `ai_alpha_forecast`) 或情绪得分 (如 `news_sentiment_score`)。
      - `{d}`: 窗口期，如 252 (一年) 或 63 (一个季度)。
    """
    return "ts_zscore(%s, %d)" % (model_score_field, d)
