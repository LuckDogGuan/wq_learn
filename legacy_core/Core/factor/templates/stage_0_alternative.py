"""Stage 0 Alternative & Other Signals Templates

本模块针对 WorldQuant Brain 的其他几类非传统或非基本面的 Data Categories：
Macro（宏观）、Options（期权）、News/Sentiment（新闻与情绪）、Event/Corporate（事件与公司行为）。
这些数据集的0阶逻辑往往偏向于：情绪扩散、波动率偏度、宏观中枢偏移。
"""

def stage0_options_put_call_ratio(put_field, call_field):
    """
    **0阶：期权认沽认购比 (Options Put/Call Ratio)**
    - **逻辑 (Logic):** 衡量市场看空与看多情绪的比例。P/C Ratio 极度升高通常意味着市场极度恐慌（可能见底反转）。
    - **模板 (Template):** `<put_field> / <call_field>`
    - **使用算子 (Operators Used):** 无
    - **参数建议 (Parameter Recommendations):**
      - `<put_field>`: 认沽期权成交量或持仓量 (如 `put_volume`, `put_open_interest`)
      - `<call_field>`: 认购期权成交量或持仓量 (如 `call_volume`, `call_open_interest`)
    """
    return "%s / %s" % (put_field, call_field)

def stage0_options_volatility_skew(call_vol_field, put_vol_field):
    """
    **0阶：期权波动率偏度 (Options Volatility Skew)**
    - **逻辑 (Logic):** 比较 Call 和 Put 的隐含波动率差异，反映资金在期权端对尾部风险的定价偏好。
    - **模板 (Template):** `(<call_vol_field> - <put_vol_field>) / <call_vol_field>`
    - **使用算子 (Operators Used):** 无
    - **参数建议 (Parameter Recommendations):**
      - `<call_vol_field>`: 认购期权隐含波动率 (如 `call_implied_vol`)
      - `<put_vol_field>`: 认沽期权隐含波动率 (如 `put_implied_vol`)
    """
    return "(%s - %s) / %s" % (call_vol_field, put_vol_field, call_vol_field)

def stage0_sentiment_polarity(pos_sentiment_field, neg_sentiment_field):
    """
    **0阶：情绪多空比 / 情感极性 (News/Event Sentiment Polarity)**
    - **逻辑 (Logic):** 结合 NLP 技术解析财报会议或新闻中的积极/消极词汇数量，从而构建该实体的纯净情绪指标。
    - **模板 (Template):** `<pos_sentiment_field> / (<pos_sentiment_field> + <neg_sentiment_field> + 1)`
    - **使用算子 (Operators Used):** 无 (+1 是为了防止分母为0)
    - **参数建议 (Parameter Recommendations):**
      - 黄金顾问推荐用法：例如 `oth384_presentation_posnum` (正面词频) 和 `oth384_presentation_negnum` (负面词频)。
    """
    return "%s / (%s + %s + 1)" % (pos_sentiment_field, pos_sentiment_field, neg_sentiment_field)

def stage0_macro_shock(macro_field, d=60):
    """
    **0阶：宏观中枢偏离 (Macro Shock / State Deviation)**
    - **逻辑 (Logic):** 宏观数据（如利率、通胀、汇率）通常用于定义大盘状态，但用其近期偏离均值的比例，可作为系统性风险升温的代理信号。
    - **模板 (Template):** `<macro_field> / ts_mean(<macro_field>, {d}) - 1`
    - **使用算子 (Operators Used):** `ts_mean`
    - **参数建议 (Parameter Recommendations):**
      - `<macro_field>`: 宏观字段，如外汇率、国债收益率。
      - `{d}`: 通常较长，如 60 (一季度) 或 252 (一年)。
    """
    return "%s / ts_mean(%s, %d) - 1" % (macro_field, macro_field, d)

def stage0_event_frequency(event_flag_field, d=20):
    """
    **0阶：事件密集度 (Event/Corporate Action Frequency)**
    - **逻辑 (Logic):** 对于布尔型或频次型事件（如某类高管变动、股票回购公告），计算近期发生的频次密度。
    - **模板 (Template):** `ts_sum(<event_flag_field>, {d})`
    - **使用算子 (Operators Used):** `ts_sum`
    - **参数建议 (Parameter Recommendations):**
      - `<event_flag_field>`: 发生标记字段 (0或1)，如 Insider Trading、Share Buyback、M&A 标记。
      - `{d}`: 窗口期，如 20 或 60。
    """
    return "ts_sum(%s, %d)" % (event_flag_field, d)
