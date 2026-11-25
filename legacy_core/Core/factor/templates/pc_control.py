def pc_control_rank(field, d1=240, scale=5):
    """
    **位置集中度控制（排序法）**
    - **逻辑 (Logic):** 使用 group_rank 严格控制位置集中度（PC），并对长尾极值进行惩罚。
    - **模板 (Template):** `group_rank(ts_product(group_neutralize(-ts_mean(vec_avg(<field>), {d1}), industry), {scale}), industry) - 0.5`
    - **使用算子 (Operators Used):** `group_rank`, `ts_product`, `group_neutralize`, `ts_mean`, `vec_avg`
    - **参数建议 (Parameter Recommendations):**
      - `d1`: 均值时间窗口长度，默认 240。
      - `scale`: 乘数缩放，默认 5。
    """
    return "group_rank(ts_product(group_neutralize(-ts_mean(vec_avg(%s), %d), industry), %d), industry) - 0.5" % (field, d1, scale)


def pc_control_zscore(field, d1=240, scale=5):
    """
    **位置集中度控制（Z-Score法）**
    - **逻辑 (Logic):** 使用 group_zscore 缓解极值影响，同时保留截面上的部分幅度差异。
    - **模板 (Template):** `group_zscore(ts_product(group_neutralize(-ts_mean(vec_avg(<field>), {d1}), industry), {scale}), industry)`
    - **使用算子 (Operators Used):** `group_zscore`, `ts_product`, `group_neutralize`, `ts_mean`, `vec_avg`
    - **参数建议 (Parameter Recommendations):**
      - `d1`: 均值时间窗口长度，默认 240。
      - `scale`: 乘数缩放，默认 5。
    """
    return "group_zscore(ts_product(group_neutralize(-ts_mean(vec_avg(%s), %d), industry), %d), industry)" % (field, d1, scale)


def pc_control_vol_adjust(field, d1=240, scale=5, vol_d=21):
    """
    **位置集中度控制（波动率调整法）**
    - **逻辑 (Logic):** 通过除以因子近期时间序列的标准差来进行调整，以防止在高方差期间出现仓位聚集。
    - **模板 (Template):** `<base> / (ts_std_dev(<base>, {vol_d}) + 0.001)` 其中 `<base> = ts_product(group_neutralize(-ts_mean(vec_avg(<field>), {d1}), industry), {scale})`
    - **使用算子 (Operators Used):** `ts_product`, `group_neutralize`, `ts_mean`, `vec_avg`, `ts_std_dev`
    - **参数建议 (Parameter Recommendations):**
      - `d1`: 均值时间窗口长度，默认 240。
      - `scale`: 乘数缩放，默认 5。
      - `vol_d`: 波动率时间窗口长度，默认 21。
    """
    base = "ts_product(group_neutralize(-ts_mean(vec_avg(%s), %d), industry), %d)" % (field, d1, scale)
    return "%s / (ts_std_dev(%s, %d) + 0.001)" % (base, base, vol_d)


def pc_control_ts_rank(field, d1=240, scale=5, rank_d=60):
    """
    **位置集中度控制（时间序列排序法）**
    - **逻辑 (Logic):** 在生成信号之前，使用 ts_rank 在时间序列上对因子进行归一化，从而自然限制截面上的极值。
    - **模板 (Template):** `ts_rank(ts_product(group_neutralize(-ts_mean(vec_avg(<field>), {d1}), industry), {scale}), {rank_d}) - 0.5`
    - **使用算子 (Operators Used):** `ts_rank`, `ts_product`, `group_neutralize`, `ts_mean`, `vec_avg`
    - **参数建议 (Parameter Recommendations):**
      - `d1`: 均值时间窗口长度，默认 240。
      - `scale`: 乘数缩放，默认 5。
      - `rank_d`: 时间序列排序窗口长度，默认 60。
    """
    return "ts_rank(ts_product(group_neutralize(-ts_mean(vec_avg(%s), %d), industry), %d), %d) - 0.5" % (field, d1, scale, rank_d)


def pc_control_tail_wrapper(base_expr, lower=-1.1, upper=1.1, newval=0):
    """
    **结构层PC降维：截尾保留两端 (Tail Wrapper)**
    - **逻辑 (Logic):** 只保留信号强度两端的极值，将中间段置零。可有效改变原信号的仓位结构以降低PC。
    - **适用场景:** 配合 group_zscore 使用效果较好。
    - **模板 (Template):** `tail({base_expr}, lower={lower}, upper={upper}, newval={newval})`
    """
    return f"tail({base_expr}, lower={lower}, upper={upper}, newval={newval})"


def pc_control_rank_by_side_wrapper(base_expr, group="industry"):
    """
    目前这个 rank_by_side 无效。 
    **结构层PC降维：按方向分组排序 (Rank By Side Wrapper)**
    - **逻辑 (Logic):** 对信号的纯多头与纯空头部分分别进行排序。显著改变原有的纯线性截面排序结构。
    - **模板 (Template):** `rank_by_side({base_expr}, {group})`
    """
    return f"rank_by_side({base_expr}, {group})"


def pc_control_exchange_sector_grouping(field, d1=240, scale=5):
    """
    **结构层PC降维：交易所与板块交叉分组 (Exchange x Sector Grouping)**
    - **逻辑 (Logic):** 改变截面分组的暴露维度。相比于单一的 industry 分组，使用 exchange 结合 sector 能提供不同视角的同质化控制。
    - **模板 (Template):** `group_zscore(ts_product(group_neutralize(-ts_mean(vec_avg(<field>), {d1}), exchange), {scale}), sector)`
    """
    return "group_zscore(ts_product(group_neutralize(-ts_mean(vec_avg(%s), %d), exchange), %d), sector)" % (field, d1, scale)
