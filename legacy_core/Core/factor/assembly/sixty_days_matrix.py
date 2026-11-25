"""
模版群助我60天点亮60个塔Alpha Template
Author: 论坛大佬 LR93609
Link: https://support.worldquantbrain.com/hc/en-us/community/posts/35253150989719
"""

# ==============================================================================
# 一元模版 (Unary) - 模版层面尽量不要有重复，从模版底层降低self-corr
# ==============================================================================

def unary_0_slope(field, d=500):
    """斜率: 时间序列线性的增长强度"""
    return f"ts_regression(ts_zscore({field}, {d}), ts_step(1), {d}, rettype=2)"

def unary_1_growth_rate_acceleration(field, d1=252, d2=252):
    """增长率的增长率: 差分之比后再差分"""
    return f"ts_delta(ts_delta({field}, {d1}) / ts_delay({field}, {d1}), {d2})"

def unary_2_growth_rate(field, d=252):
    """增长率: 最原始的一阶差分百分比变动"""
    return f"ts_delta({field}, {d}) / ts_delay({field}, {d})"

def unary_3_autoregressive_slope(field, d1=252, d2=500):
    """自回归斜率: 中期动量与长期动量之间的敏感度回归"""
    return f"ts_regression(ts_delta({field}, {d1}), ts_delta({field}, {d2}), {d2}, rettype=2)"

def unary_4_squared_momentum(field, d1=252, d2=500):
    """平方动量: 对变化量的二次方进行均值平滑，突显极大异动"""
    return f"ts_mean(signed_power(ts_delta({field}, {d1}), 2), {d2})"

def unary_5_decay_weighted_momentum(field, d1=252, d2=500):
    """衰减加权动量: 离当前越近的变化赋予越高的权重"""
    return f"ts_decay_linear(ts_delta({field}, {d1}), {d2})"

def unary_6_rank_reversal(field, d=500):
    """排名反转: 时序排名取反，做均值回归"""
    return f"reverse(ts_rank(ts_zscore({field}, {d}), {d}))"

def unary_7_log_smoothing(field, d=500):
    """对数平滑: 绝对值的对数放缩，抹平数据极差差异"""
    return f"log(abs(ts_delta({field}, {d})) + 0.000001)"

def unary_8_sign_preserved_power(field, d=500):
    """符号保留幂: 将变化量做平方放大，但保留原始正负号方向"""
    return f"signed_power(ts_delta({field}, {d}), 2)"

def unary_9_differential_cascade(field, d1=252, d2=500):
    """差分层叠: 对短期变化量求中长期的二次差分"""
    return f"ts_delta(ts_delta({field}, {d1}), {d2})"


# ==============================================================================
# 二元模版 (Binary) - 降self-corr
# ==============================================================================

def binary_0_regression_residual(field_a, field_b, d=500):
    """线性回归残差 (默认rettype=0)"""
    return f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d})"

def binary_1_regression_beta(field_a, field_b, d=500):
    """线性回归斜率 Beta (rettype=2)"""
    return f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, rettype=2)"

def binary_2_regression_residual_stddev(field_a, field_b, d=500):
    """回归残差的标准差 (rettype=6)"""
    return f"ts_regression(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}, rettype=6)"

def binary_3_raw_regression_beta_short(field_a, field_b, d=252):
    """短期原生回归 Beta"""
    return f"ts_regression({field_a}, {field_b}, {d}, rettype=2)"

def binary_4_raw_regression_beta_long(field_a, field_b, d=500):
    """长期原生回归 Beta"""
    return f"ts_regression({field_a}, {field_b}, {d}, rettype=2)"

def binary_5_log_regression_neut(field_a, field_b):
    """截面对数回归中性化: A在B方向的截面残差"""
    A_log = f"sign({field_a}) * log(abs({field_a}) + 1)"
    B_log = f"sign({field_b}) * log(abs({field_b}) + 1)"
    return f"regression_neut({A_log}, {B_log})"

def binary_6_vector_neut(field_a, field_b):
    """截面向量中性化: 正交剔除同向暴露"""
    return f"vector_neut({field_a}, {field_b})"


# ==============================================================================
# 三元模版 (Ternary) - 去self-corr，盈利模式极其丰富
# ==============================================================================

def ternary_0_joint_neutralization(field_a, field_b, field_c):
    """联合中性化: a 在 b 和 c 上的向量正交"""
    return f"vector_neut(vector_neut({field_a}, {field_b}), {field_c})"

def ternary_1_layered_regression_residual(field_a, field_b, field_c):
    """分层回归残差: 先对 b 做截面中性化，再对 c 做中性化"""
    return f"regression_neut(regression_neut({field_a}, {field_b}), {field_c})"

def ternary_3_correlation_with_weight(field_a, field_b, field_c, d=252):
    """三变量时序相关性: a 与 b 的相关性，用 c 作权重或方向调节"""
    return f"ts_corr(ts_zscore({field_a}, {d}), ts_zscore({field_b}, {d}), {d}) * {field_c}"

def ternary_4_dynamic_ranking_timing(field_a, field_b, field_c, weight_field="1", d=500):
    """动态排序择时: a 在 b（分类）中的排序做 ts_rank，并乘以 c（打分）"""
    return f"ts_rank(group_mean({field_a}, {weight_field}, {field_b}), {d}) * {field_c}"

def ternary_5_triple_interaction(field_a, field_b, field_c, d=500):
    """三重交互项: 非线性放大（相乘）"""
    return f"ts_zscore({field_a}, {d}) * ts_zscore({field_b}, {d}) * ts_zscore({field_c}, {d})"

def ternary_6_conditional_switch(field_a, field_b, field_c, d=500):
    """条件切换: c 强势时用 a，弱势时用 b"""
    return f"if_else({field_c} > ts_mean({field_c}, {d}), {field_a}, {field_b})"
