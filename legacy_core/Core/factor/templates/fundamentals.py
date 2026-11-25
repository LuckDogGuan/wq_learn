def zscore_normalization(field, group="subindustry"):
    """
    **分组 Z-Score 归一化**
    - **逻辑 (Logic):** 对基本面数据进行归一化，以识别与同行相比，某只股票是便宜还是昂贵。
    - **模板 (Template):** `group_zscore(<field>, <group>)`
    - **使用算子 (Operators Used):** `group_zscore`
    - **参数建议 (Parameter Recommendations):**
      - `<group>`: `subindustry`、`industry` 或 `sector`。`subindustry` 提供最细粒度的比较。
    """
    return "group_zscore(%s, %s)" % (field, group)

def rank_difference(field1, field2):
    """
    **排名差值 (价值与盈利能力)**
    - **逻辑 (Logic):** 通过对两个不同特征（例如价值和盈利能力）的截面排名取差值，来进行比较。
    - **模板 (Template):** `rank(<field1>) - rank(<field2>)`
    - **使用算子 (Operators Used):** `rank`
    - **参数建议 (Parameter Recommendations):**
      - `<field1>`: 通常是盈利能力或质量指标（例如 ROE、毛利率）。
      - `<field2>`: 通常是估值指标（例如 P/E、P/B）。
    """
    return "rank(%s) - rank(%s)" % (field1, field2)

def fundamental_trend(field, d=63):
    """
    **基本面趋势 (季度变动)**
    - **逻辑 (Logic):** 测量某个基本面指标在特定时期（通常是一个季度）内的改善或恶化情况。
    - **模板 (Template):** `(<field> - ts_delay(<field>, {d})) / ts_delay(<field>, {d})`
    - **使用算子 (Operators Used):** `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - `{d}`: 对于季度数据为 63，对于年度数据为 252。
    """
    return "(%s - ts_delay(%s, %d)) / ts_delay(%s, %d)" % (field, field, d, field, d)
