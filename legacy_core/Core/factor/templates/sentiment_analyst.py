def unstructured_news_sentiment(field, d=20):
    """
    **[非结构化新闻情绪趋势]**
    - **逻辑 (Logic):** 评估短期新闻情绪相比其1个月基线是否高度积极。使用简单的移动平均线进行判断。
    - **模板 (Template):** `ts_mean(<field>, 5) > ts_mean(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_mean`
    - **参数建议 (Parameter Recommendations):**
      - `<field>`: 通常使用 `nws20_ssc` 或 `rp_css_business`。
    """
    return "ts_mean(%s, 5) > ts_mean(%s, %d)" % (field, field, d)

def analyst_estimate_revision(field):
    """
    **[分析师预期修正信号]**
    - **逻辑 (Logic):** 识别分析师大幅上调预期的情况，表明存在积极的基本面动能。
    - **模板 (Template):** `group_rank(ts_delta(<field>, 20), sector)`
    - **使用算子 (Operators Used):** `group_rank`, `ts_delta`
    - **参数建议 (Parameter Recommendations):**
      - `<field>`: 通常使用分析师情绪模型因子，如 `mdl110_analyst_sentiment`。
    """
    return "group_rank(ts_delta(%s, 20), sector)" % field

def forum_sentiment_divergence(sentiment_field, price_field):
    """
    **[散户论坛情绪背离]**
    - **逻辑 (Logic):** (特别适用于中国/韩国市场) 检测散户论坛情绪与实际价格动能的背离。如果论坛情绪极度看涨但价格在下跌，可能是一个逆向卖出信号。
    - **模板 (Template):** `-ts_corr(rank(<sentiment_field>), rank(<price_field>), 10)`
    - **使用算子 (Operators Used):** `correlation`, `rank`
    - **参数建议 (Parameter Recommendations):**
      - `<sentiment_field>`: 例如 `oth111_xueqiunaturaldaybasicdivisionstat_senti_conform`。
    """
    return "-ts_corr(rank(%s), rank(%s), 10)" % (sentiment_field, price_field)
