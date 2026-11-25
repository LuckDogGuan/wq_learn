"""
WorldQuant Brain 风险与相关性优化模板 (Risk & Correlation Optimization Templates)
用于解决 Alpha 测试时的风险项失败：
1. Turnover & Concentrated Weight (换手率过高过低、头寸过度集中)
2. Correlation (自相关性与生产因子相关性过高)

核心策略：
- 线性平滑降换手 (Decay)
- 截面中性化打散聚集头寸 (Group Neutralize)
- 延时与扫频去相关
"""

def optimize_turnover_with_decay(expression: str, d: int = 5) -> str:
    """
    **[平滑降换手 (Decay)]**
    - **逻辑 (Logic):** 引入线性衰减 (Decay) 对历史信号进行平滑，避免每天信号剧烈反转导致的高换手率。
    - **模板 (Template):** `ts_decay_linear(<alpha>, {d})`
    - **使用算子 (Operators Used):** `ts_decay_linear`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
      - `d`: 平滑天数，推荐 2 到 10 天。
    """
    return "ts_decay_linear(%s, %d)" % (expression, d)


def optimize_weight_concentration_neutralize(expression: str, group: str = "industry") -> str:
    """
    **[集中度优化（中性化分散法）]**
    - **逻辑 (Logic):** 通过中性化打散头寸分布，解决权重过度集中在个别股票或行业的问题。将信号在特定分类内进行去均值处理，实现横截面分散。
    - **模板 (Template):** `group_neutralize(<alpha>, <group>)`
    - **使用算子 (Operators Used):** `group_neutralize`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
      - `group`: 中性化分组类别，如 "industry", "subindustry", "sector" 等。
    """
    return "group_neutralize(%s, %s)" % (expression, group)


def optimize_weight_concentration_rank(expression: str) -> str:
    """
    **[集中度优化（Rank 映射）]**
    - **逻辑 (Logic):** 将原始信号截面映射至 [0,1] 均匀分布，强制切断原始极端因子值带来的超额头寸分配，根除长尾极值集中。
    - **模板 (Template):** `rank(<alpha>)`
    - **使用算子 (Operators Used):** `rank`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
    """
    return "rank(%s)" % expression


def reduce_correlation_by_decay_sweep(expression: str, d: int) -> str:
    """
    **[自相关优化 (Decay扫频)]**
    - **逻辑 (Logic):** 自相关过高通常因为信号迟钝。可以通过对短周期信号增加不同周期的 Decay 进行扫频，寻找相关性盲区。
    - **模板 (Template):** `ts_decay_linear(<alpha>, {d})`
    - **使用算子 (Operators Used):** `ts_decay_linear`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
      - `d`: 扫频天数。通过测试不同天数寻找低相关性窗口。
    """
    return "ts_decay_linear(%s, %d)" % (expression, d)


def reduce_correlation_by_group_neutralize_sweep(expression: str, group: str) -> str:
    """
    **[生产相关优化 (中性化扫频)]**
    - **逻辑 (Logic):** 与生产系统因子相关性过高时，可以通过改变横截面中性化的参照系来逃逸（如从行业切换到子行业或市值中性）。
    - **模板 (Template):** `group_neutralize(<alpha>, <group>)`
    - **使用算子 (Operators Used):** `group_neutralize`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
      - `group`: 候选分组字段。
    """
    return "group_neutralize(%s, %s)" % (expression, group)


def reduce_correlation_by_delay_signal(expression: str, days: int = 1) -> str:
    """
    **[信号延时去相关]**
    - **逻辑 (Logic):** 如果当日相关性过高，而该因子具有趋势持续性，延后几天入场可以极大地错开生产库因子的同质化轨道。
    - **模板 (Template):** `ts_delay(<alpha>, {days})`
    - **使用算子 (Operators Used):** `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - `expression`: 原始因子表达式。
      - `days`: 延时天数，推荐 1 到 2 天。
    """
    return "ts_delay(%s, %d)" % (expression, days)
