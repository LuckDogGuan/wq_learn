def cross_sectional_group_rank(field, group="sector"):
    """
    **组内中性化排名**
    - **逻辑 (Logic):** 在特定组（例如行业）内对字段进行排名，消除更广泛的市场趋势，并在同行组中寻找相对赢家。
    - **模板 (Template):** `group_rank(<field>, <group>)`
    - **使用算子 (Operators Used):** `group_rank`, `rank`
    - **参数建议 (Parameter Recommendations):**
      - `<group>`: `sector`、`subindustry` 或自定义集群（如 `mdl10_group_name`）。
    """
    return "group_rank(%s, %s)" % (field, group)

def cross_sectional_quantile_zscore(field):
    """
    **分位数 Z-Score 标准化**
    - **逻辑 (Logic):** 结合截面分位数转换来处理极端异常值，然后使用 z-score 来标准化方差。对具有长尾分布的基本面数据极其鲁棒。
    - **模板 (Template):** `zscore(quantile(<field>))`
    - **使用算子 (Operators Used):** `zscore`, `quantile`
    - **参数建议 (Parameter Recommendations):**
      - 普遍应用于变动缓慢的基本面数据，在传递给中性化操作之前使用。
    """
    return "zscore(quantile(%s))" % field

def robust_normalization(field):
    """
    **基于 Pasteurize 的鲁棒归一化**
    - **逻辑 (Logic):** 用截面中性值替换 NaNs 和无穷大值，确保数据集安全可用于下游计算，而不会导致崩溃。
    - **模板 (Template):** `normalize(pasteurize(<field>))`
    - **使用算子 (Operators Used):** `normalize`, `pasteurize`
    - **参数建议 (Parameter Recommendations):**
      - 强烈推荐作为原始财务数据的包装器。
    """
    return "normalize(pasteurize(%s))" % field

def cross_sectional_inverse_value(field):
    """
    **逆值转换**
    - **逻辑 (Logic):** 通常用于反转指标的含义，例如将 P/E 转换为 E/P，这样值越高总是越好。
    - **模板 (Template):** `inverse(<field>)`
    - **使用算子 (Operators Used):** `inverse`
    - **参数建议 (Parameter Recommendations):**
      - 适用于历史上原始值越低表示越“便宜”的估值倍数。
    """
    return "inverse(%s)" % field

def density_compression(field):
    """
    **密度压缩**
    - **逻辑 (Logic):** densify 将平台 Group/Category 字段压缩为密集分组编号。
    - **模板 (Template):** `densify(<field>)`
    - **使用算子 (Operators Used):** `densify`
    - **参数建议 (Parameter Recommendations):**
      - 仅用于平台元数据明确标记为 Group/Category 的字段，不用于 MATRIX/VECTOR。
    """
    return "densify(%s)" % field
