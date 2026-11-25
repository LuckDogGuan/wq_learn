"""
虎哥模版实证及其改进效果评价
Author: 论坛大佬 LR93609 (虎哥模板系列)
Link: https://support.worldquantbrain.com/hc/en-us/community/posts/33768594280343
"""

def huge_series_1_cross_sectional_residual(field_a, field_b):
    # WQB不支持 regression_neut，用 group_neutralize 替代
    # 或者直接跳过，这里先返回 None 或随便一个合法的，我们不在 batch 里调它
    return f"group_neutralize({field_a}, industry)"


def huge_series_2_timeseries_residual_stddev(field_a, field_b, d=500):
    """
    系列 2 改进 1 (时序残差标准差)
    释义: 把 rettype 从 0 改成 6，由残差改为残差的标准差。
          把因子从“解释后的残差”升级为“解释可靠性的直接度量”，更易于做风险打分或稳健性筛选。
    """
    return (
        f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), "
        f"{d}, lag=0, rettype=6)"
    )


def huge_series_2_timeseries_beta_lagged(field_a, field_b, d=500, lag=5):
    """
    系列 2 改进 2 (时序滞后 Beta预测)
    释义: 用 B lag 天前的标准化值预测 A 今天的标准化值，返回回归斜率 β。
    """
    return (
        f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), "
        f"{d}, lag={lag}, rettype=2)"
    )


def huge_series_3_beta_stability(field_a, field_b, d=500):
    """
    系列 3 改进版 (Beta 稳定性倒数)
    释义: 用过去 d 天内 A 与同期 B 的 z-score 回归得到的 β 序列，
          再取它在过去 d 天的波动率的倒数——β 越稳定，因子值越大。
    """
    beta_expr = f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, 0, 2)"
    return f"1 / ts_std_dev({beta_expr}, {d})"


def huge_series_4_beta_sharpe(field_a, field_b, d=500):
    """
    系列 4 改进 1 (Beta 的夏普化信号)
    释义: 用过去 d 天的 β 序列的「均值 / 标准差」直接算出「β 的夏普化信号」，
          数值越大说明 A 对 B 的敏感度既强又稳。
    """
    beta_expr = f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, 0, 2)"
    return f"{beta_expr} / ts_std_dev({beta_expr}, {d})"


def huge_series_4_beta_tstat_newey_west(field_a, field_b, d=500):
    """
    系列 4 改进 2 (经异方差-自相关修正的 Beta t-stat)
    释义: 分母换成 rettype=8 返回的 β 的 Newey-West 标准误，得到统计显著性更可靠的信号。
    """
    beta_expr = f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, 0, 2)"
    se_expr = f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, 0, 8)"
    return f"{beta_expr} / {se_expr}"


def huge_series_5_time_trend_residual(field_a, d=500):
    """
    系列 5 (剥离时间趋势残差)
    释义: 返回残差序列（A 中无法被时间趋势解释的部分）。
          若 A 有强烈的时间趋势，残差序列会围绕 0 随机波动；若趋势弱，残差序列会接近原始 zscore。
    """
    # ts_step(1) 在 FASTEXPR 是 ts_step(1)，不需要额外处理
    return f"ts_regression(ts_zscore({field_a}, {d}), ts_step(1), {d}, 0, 6)"
