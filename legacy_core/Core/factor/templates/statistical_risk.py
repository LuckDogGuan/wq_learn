def historical_volatility_adjusted(field, d_vol=20):
    """
    **[波动率调整信号 (信息比率代理)]**
    - **逻辑 (Logic):** 通过历史波动率对原始时间序列均值进行调整，以评估信号的稳定性。类似于信息比率（Information Ratio）。
    - **模板 (Template):** `ts_ir(<field>, {d_vol})`
    - **使用算子 (Operators Used):** `ts_ir`
    - **参数建议 (Parameter Recommendations):**
      - `{d_vol}`: 建议使用 20 或 60。用于评估中短期的风险调整后强度。
    """
    return "ts_ir(%s, %d)" % (field, d_vol)

def rolling_kurtosis_risk(field, d=60):
    """
    **[尾部风险峰度检测器]**
    - **逻辑 (Logic):** 识别经历异常肥尾分布的资产，通常预示着即将发生的趋势反转或崩盘。
    - **模板 (Template):** `-ts_kurtosis(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_kurtosis`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议使用 60。需要较长的窗口来有意义地估计分布的四阶矩。
    """
    return "-ts_kurtosis(%s, %d)" % (field, d)

def extreme_value_reversion(field, d=20):
    """
    **[极值回归 (时间序列 Z-Score)]**
    - **逻辑 (Logic):** 当资产价格或基本面偏离其历史常态过远时，捕捉其均值回归。
    - **模板 (Template):** `-ts_zscore(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_zscore`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 短期价格回归建议使用 20，长期基本面价值回归建议使用 252。
    """
    return "-ts_zscore(%s, %d)" % (field, d)

def cumulative_volume_shock(field, d=5):
    """
    **[累积流量冲击]**
    - **逻辑 (Logic):** 汇总近期的成交量或流量，以检测机构的突然吸筹或派发。
    - **模板 (Template):** `ts_sum(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_sum`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议使用 5 或 10。
    """
    return "ts_sum(%s, %d)" % (field, d)

def max_difference_breakout(field, d=20):
    """
    **[最大差值突破]**
    - **逻辑 (Logic):** 测量窗口内的最大极端差值。如果差值很大，可能预示着突破趋势。
    - **模板 (Template):** `ts_max_diff(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_max_diff`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议使用 20 或 60 天。
    """
    return "ts_max_diff(%s, %d)" % (field, d)

def data_stability_check(field, d=60):
    """
    **[数据稳定性检查 (计算 NaN 数量)]**
    - **逻辑 (Logic):** 惩罚数据历史稀疏或不可靠的资产。
    - **模板 (Template):** `-ts_count_nans(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_count_nans`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 建议使用 60 或 120。通常在乘法运算中使用，将不可靠信号置为零。
    """
    return "-ts_count_nans(%s, %d)" % (field, d)
