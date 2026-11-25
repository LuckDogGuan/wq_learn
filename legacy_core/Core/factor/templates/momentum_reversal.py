def momentum_20d(field):
    """
    **[20日动量]**
    - **逻辑 (Logic):** 将水平量级数据转换为过去20天的相对变化率。
    - **模板 (Template):** `(<field> - ts_delay(<field>, 20)) / ts_delay(<field>, 20)`
    - **使用算子 (Operators Used):** `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - `20` 可以根据目标频率更改为 60 或 120。
    """
    return "(%s - ts_delay(%s, 20)) / ts_delay(%s, 20)" % (field, field, field)

def short_term_reversal(field, d=5):
    """
    **[短期反转]**
    - **逻辑 (Logic):** 反转短期的价格或基本面变化方向。
    - **模板 (Template):** `-ts_delta(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_delta`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议默认值为 5。代表变化的回溯期。
    """
    return "-ts_delta(%s, %d)" % (field, d)

def price_volume_divergence(field, d=10):
    """
    **[量价背离]**
    - **逻辑 (Logic):** 衡量成交量和收益率之间的背离程度。同步运动可能代表拥挤的交易，而背离可能代表动能衰竭。
    - **模板 (Template):** `-ts_corr(rank(high), rank(<field>), {d})`
    - **使用算子 (Operators Used):** `ts_corr`, `rank`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 10. 可以用 5 或 20 进行测试。
    """
    return "-ts_corr(rank(high), rank(%s), %d)" % (field, d)

def double_difference_acceleration(field, d=5):
    """
    **[双重差分加速 (信息变化加速)]**
    - **逻辑 (Logic):** 双重差分消除了部分水平和趋势，用于观察信息变化的加速度。
    - **模板 (Template):** `-ts_delta(ts_delta(<field>, {d}), {d})`
    - **使用算子 (Operators Used):** `ts_delta`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议默认值为 5。对于季度基本面字段，考虑使用 63（1个季度）。
    """
    return "-ts_delta(ts_delta(%s, %d), %d)" % (field, d, d)

def overnight_gap_reversal(d=5):
    """
    **[隔夜跳空反转]**
    - **逻辑 (Logic):** 捕捉隔夜价格跳空后的流动性失衡和短期反转。
    - **模板 (Template):** `-ts_delta((open - ts_delay(close, 1)) / ts_delay(close, 1), {d})`
    - **使用算子 (Operators Used):** `ts_delta`, `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议默认值为 5。通常为 1、3 或 5。
    """
    return "-ts_delta((open - ts_delay(close, 1)) / ts_delay(close, 1), %d)" % d
