def decay_linear_smoothing(field, d=10):
    """
    **线性衰减平滑**
    - **逻辑 (Logic):** 通过赋予近期观测值更大权重并对较旧观测值线性递减权重，来平滑波动较大的信号。
    - **模板 (Template):** `ts_decay_linear(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_decay_linear`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 10 或 20。通常包裹原始收益率或原始成交量，以创建稳定的趋势指标。
    """
    return "ts_decay_linear(%s, %d)" % (field, d)

def average_difference(field, d=20):
    """
    **时序平均差异**
    - **逻辑 (Logic):** 将当前值与滚动均值进行比较。正值表示交易在平均水平之上。
    - **模板 (Template):** `ts_av_diff(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_av_diff`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 20 或 60。
    """
    return "ts_av_diff(%s, %d)" % (field, d)

def momentum_step_counter(field, d=10):
    """
    **步数计数器 (时间推移)**
    - **逻辑 (Logic):** 主要用于回归中，以检测信号中的线性时间趋势。
    - **模板 (Template):** `ts_corr(<field>, ts_step({d}), {d})`
    - **使用算子 (Operators Used):** `ts_step`, `ts_corr` (或 `ts_regression`)
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 匹配回归窗口。
    """
    return "ts_corr(%s, ts_step(%d), %d)" % (field, d, d)

def price_extremes_timing(field, d=20):
    """
    **极端价格时机 (最大/最小值距离)**
    - **逻辑 (Logic):** 测量最大值或最小值发生在多少天前。近期的最大值（值为 0）意味着强烈的上升动量。
    - **模板 (Template):** `ts_arg_max(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_arg_max`, `ts_arg_min`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 20。
    """
    return "ts_arg_max(%s, %d)" % (field, d)

def robust_log_transformation(field):
    """
    **鲁棒性对数转换**
    - **逻辑 (Logic):** 将指数级数据（如市值或总资产）压缩到线性空间，处理符号以防止数学错误。
    - **模板 (Template):** `sign(<field>) * log(1 + abs(<field>))`
    - **使用算子 (Operators Used):** `sign`, `log`, `abs`
    - **参数建议 (Parameter Recommendations):**
      - 推荐用于未做边界处理的原始基本面数据。
    """
    return "sign(%s) * log(1 + abs(%s))" % (field, field)

def scaled_cumulative_product(field, d=5):
    """
    **缩放复利 (乘积与缩放)**
    - **逻辑 (Logic):** 计算滚动乘积（如复利收益）并将其缩放到标准的波动率或范围内。
    - **模板 (Template):** `ts_scale(ts_product(1 + <field>, {d}), 1)`
    - **使用算子 (Operators Used):** `ts_product`, `ts_scale`
    - **参数建议 (Parameter Recommendations):**
      - `<field>` 必须是百分比或收益率。
    """
    return "ts_scale(ts_product(1 + %s, %d), 1)" % (field, d)

def fundamental_backfill(field, d=60):
    """
    **数据完整性回填**
    - **逻辑 (Logic):** 用最后已知的值填补缺失的 NaN，这对稀疏的季度数据至关重要。
    - **模板 (Template):** `ts_backfill(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_backfill`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 60 (用于过渡一个缺失的季度)。
    """
    return "ts_backfill(%s, %d)" % (field, d)

def return_volatility_sqrt(field, d=20):
    """
    **平方根波动率衰减**
    - **逻辑 (Logic):** 使用平方根衰减高值，常用于方差或成交量。
    - **模板 (Template):** `sqrt(ts_mean(abs(ts_returns(<field>, 1)), {d}))`
    - **使用算子 (Operators Used):** `sqrt`, `ts_mean`, `ts_returns`, `abs`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 20。
    """
    return "sqrt(ts_mean(abs(ts_returns(%s, 1)), %d))" % (field, d)

def time_series_quantile_rank(field, d=60):
    """
    **时序分位数排名**
    - **逻辑 (Logic):** 将当前值与其自身的历史分布进行比较和排名。
    - **模板 (Template):** `ts_quantile(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_quantile`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 60 或 252 (1年)。
    """
    return "ts_quantile(%s, %d)" % (field, d)
