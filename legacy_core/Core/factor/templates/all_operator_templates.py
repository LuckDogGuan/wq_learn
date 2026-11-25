"""
自动生成的全量算子模板库 (已通过本地 AST 严密校验)
"""

# =============================================================================
# Time Series Operators
# =============================================================================

def ts_mean(field, short=5, long=60):
    """
    **[Ts Mean]**
    - **逻辑 (Logic):** ATOM 论坛经典：长短期移动平均线交叉 (均值回归或动量跟随)。
    - **模板 (Template):** `ts_mean({field}, {short}) / ts_mean({field}, {long})`
    - **使用算子 (Operators Used):** `ts_mean`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_mean({field}, {short}) / ts_mean({field}, {long})"

def ts_delta(field, d=5):
    """
    **[Ts Delta]**
    - **逻辑 (Logic):** 基础趋势动量：衡量过去一段时间内的绝对变化量。
    - **模板 (Template):** `ts_delta({field}, {d})`
    - **使用算子 (Operators Used):** `ts_delta`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_delta({field}, {d})"

def ts_zscore(field, d=20):
    """
    **[Ts Zscore]**
    - **逻辑 (Logic):** 时间序列 Z-Score：识别资产在纵向时间轴上的极度高估或低估。
    - **模板 (Template):** `ts_zscore({field}, {d})`
    - **使用算子 (Operators Used):** `ts_zscore`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_zscore({field}, {d})"

def ts_sum(field, d=5):
    """
    **[Ts Sum]**
    - **逻辑 (Logic):** 累计冲击：汇总一段时间内的总量，常用于捕获流动性/资金持续流入（如成交量）。
    - **模板 (Template):** `ts_sum({field}, {d})`
    - **使用算子 (Operators Used):** `ts_sum`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_sum({field}, {d})"

def ts_ir(field, d=20):
    """
    **[Ts Ir]**
    - **逻辑 (Logic):** 信息比率（Information Ratio）：风险调整后的超额收益潜力评估。
    - **模板 (Template):** `ts_ir({field}, {d})`
    - **使用算子 (Operators Used):** `ts_ir`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_ir({field}, {d})"

def ts_std_dev(field, d=20):
    """
    **[Ts Std Dev]**
    - **逻辑 (Logic):** 历史波动率评估：用于衡量资产自身的不确定性或风险溢价。
    - **模板 (Template):** `ts_std_dev({field}, {d})`
    - **使用算子 (Operators Used):** `ts_std_dev`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_std_dev({field}, {d})"

def ts_corr(field1, field2, d=20):
    """
    **[Ts Corr]**
    - **逻辑 (Logic):** 时序相关性（如量价相关性）：判断价格变动是否有交易量配合。
    - **模板 (Template):** `ts_corr({field1}, {field2}, {d})`
    - **使用算子 (Operators Used):** `ts_corr`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_corr({field1}, {field2}, {d})"

def ts_count_nans(field, d=60):
    """
    **[Ts Count Nans]**
    - **逻辑 (Logic):** 数据稀疏度/流动性惩罚：识别近期频繁停牌或缺乏报价的资产。
    - **模板 (Template):** `-ts_count_nans({field}, {d})`
    - **使用算子 (Operators Used):** `ts_count_nans`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"-ts_count_nans({field}, {d})"

def ts_covariance(field1, field2, d=60):
    """
    **[Ts Covariance]**
    - **逻辑 (Logic):** 时序协方差：衡量两资产或属性绝对协同运动的强度。
    - **模板 (Template):** `ts_covariance({field1}, {field2}, {d})`
    - **使用算子 (Operators Used):** `ts_covariance`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_covariance({field1}, {field2}, {d})"

def ts_decay_linear(field, d=10):
    """
    **[Ts Decay Linear]**
    - **逻辑 (Logic):** 线性衰减平滑：相比简单均值，赋予近期数据更高权重，捕捉最新趋势。
    - **模板 (Template):** `ts_decay_linear({field}, {d})`
    - **使用算子 (Operators Used):** `ts_decay_linear`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_decay_linear({field}, {d})"

def ts_product(field, d=5):
    """
    **[Ts Product]**
    - **逻辑 (Logic):** 滚动乘积：通常用于计算复利累积收益率。
    - **模板 (Template):** `ts_product(1 + {field}, {d})`
    - **使用算子 (Operators Used):** `ts_product`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_product(1 + {field}, {d})"

def ts_regression(y, x, d=60):
    """
    **[Ts Regression]**
    - **逻辑 (Logic):** 滚动回归截距/斜率：衡量两序列之间长期的线性敏感度 (Beta)。
    - **模板 (Template):** `ts_regression({y}, {x}, {d})`
    - **使用算子 (Operators Used):** `ts_regression`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_regression({y}, {x}, {d})"

def ts_step(field, d=20):
    """
    **[Ts Step]**
    - **逻辑 (Logic):** 时间步长发生器：与 ts_regression 配合使用以寻找时间维度的线性趋势。
    - **模板 (Template):** `ts_regression({field}, ts_step({d}), {d})`
    - **使用算子 (Operators Used):** `ts_step`, `ts_regression`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_regression({field}, ts_step({d}), {d})"

def ts_returns(field, d=1):
    """
    **[Ts Returns]**
    - **逻辑 (Logic):** 指定窗口期内的百分比收益率。
    - **模板 (Template):** `ts_returns({field}, {d})`
    - **使用算子 (Operators Used):** `ts_returns`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_returns({field}, {d})"

def ts_max_diff(field, d=20):
    """
    **[Ts Max Diff]**
    - **逻辑 (Logic):** 最大震幅突破：捕捉近期内最具爆发力的方向破位。
    - **模板 (Template):** `ts_max_diff({field}, {d})`
    - **使用算子 (Operators Used):** `ts_max_diff`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_max_diff({field}, {d})"

def ts_kurtosis(field, d=60):
    """
    **[Ts Kurtosis]**
    - **逻辑 (Logic):** 尾部风险度量：峰度用于监测出现极端行情的几率。
    - **模板 (Template):** `ts_kurtosis({field}, {d})`
    - **使用算子 (Operators Used):** `ts_kurtosis`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_kurtosis({field}, {d})"

def ts_rank(field, d=60):
    """
    **[Ts Rank]**
    - **逻辑 (Logic):** 时序排名：判断当前状态处于历史分布的相对位置。
    - **模板 (Template):** `ts_rank({field}, {d})`
    - **使用算子 (Operators Used):** `ts_rank`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_rank({field}, {d})"

def days_from_last_change(field):
    """
    **[Days From Last Change]**
    - **逻辑 (Logic):** 沉寂期监测：记录上次状态变化至今的天数，常用于研报更新或评级变动。
    - **模板 (Template):** `days_from_last_change({field})`
    - **使用算子 (Operators Used):** `days_from_last_change`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"days_from_last_change({field})"

def last_diff_value(field, d=5):
    """
    **[Last Diff Value]**
    - **逻辑 (Logic):** 上一次突变幅度：关注事件发生前后的跳跃动能。
    - **模板 (Template):** `last_diff_value({field}, {d})`
    - **使用算子 (Operators Used):** `last_diff_value`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"last_diff_value({field}, {d})"

def ts_arg_max(field, d=20):
    """
    **[Ts Arg Max]**
    - **逻辑 (Logic):** 创新高倒计时：距离最近一次极大值过去的天数，值越小动能越新。
    - **模板 (Template):** `ts_arg_max({field}, {d})`
    - **使用算子 (Operators Used):** `ts_arg_max`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_arg_max({field}, {d})"

def ts_arg_min(field, d=20):
    """
    **[Ts Arg Min]**
    - **逻辑 (Logic):** 创新低倒计时：距离最近一次极小值过去的天数，常用于抄底验证。
    - **模板 (Template):** `ts_arg_min({field}, {d})`
    - **使用算子 (Operators Used):** `ts_arg_min`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_arg_min({field}, {d})"

def ts_av_diff(field, d=20):
    """
    **[Ts Av Diff]**
    - **逻辑 (Logic):** 乖离率：当前值偏离移动平均线的程度。
    - **模板 (Template):** `ts_av_diff({field}, {d})`
    - **使用算子 (Operators Used):** `ts_av_diff`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_av_diff({field}, {d})"

def ts_backfill(field, d=60):
    """
    **[Ts Backfill]**
    - **逻辑 (Logic):** 数据修补：填充缺失的季报或停牌数据以维持序列连续性。
    - **模板 (Template):** `ts_backfill({field}, {d})`
    - **使用算子 (Operators Used):** `ts_backfill`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_backfill({field}, {d})"

def ts_scale(field, scale=1):
    """
    **[Ts Scale]**
    - **逻辑 (Logic):** 规模锚定：强制将时间序列结果标准化为总和固定的范围，以便加权整合。
    - **模板 (Template):** `ts_scale({field}, {scale})`
    - **使用算子 (Operators Used):** `ts_scale`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_scale({field}, {scale})"

def ts_quantile(field, d=60):
    """
    **[Ts Quantile]**
    - **逻辑 (Logic):** 时序分位数分布：精确掌握当下在历史分布中的具体分位，比 ts_rank 更平滑。
    - **模板 (Template):** `ts_quantile({field}, {d})`
    - **使用算子 (Operators Used):** `ts_quantile`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_quantile({field}, {d})"

def ts_delay(field, d=1):
    """
    **[Ts Delay]**
    - **逻辑 (Logic):** 历史滞后项：构建动量或防反转的最基础骨架。
    - **模板 (Template):** `ts_delay({field}, {d})`
    - **使用算子 (Operators Used):** `ts_delay`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"ts_delay({field}, {d})"

def kth_element(field, d=20, k=5):
    """
    **[Kth Element]**
    - **逻辑 (Logic):** [纯底层计算算子，返回时序中第K个元素，通常通过其他ts_ops隐式调用。]
    - **模板 (Template):** `kth_element({field}, {d}, {k})`

# =============================================================================
# Cross Sectional Operators
# =============================================================================
    - **使用算子 (Operators Used):** `kth_element`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"kth_element({field}, {d}, {k})"

# =============================================================================
# Cross Sectional Operators
# =============================================================================

def rank(field):
    """
    **[Rank]**
    - **逻辑 (Logic):** 截面排名：寻找市场上最好或最差的标的，屏蔽绝对值的市场大盘波动。
    - **模板 (Template):** `rank({field})`
    - **使用算子 (Operators Used):** `rank`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"rank({field})"

def quantile(field):
    """
    **[Quantile]**
    - **逻辑 (Logic):** 截面分位数去极值：极大地削弱肥尾异常数据的影响。
    - **模板 (Template):** `quantile({field})`
    - **使用算子 (Operators Used):** `quantile`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"quantile({field})"

def normalize(field):
    """
    **[Normalize]**
    - **逻辑 (Logic):** 减均值标准化：跨截面平滑基础财务数据。
    - **模板 (Template):** `normalize({field})`
    - **使用算子 (Operators Used):** `normalize`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"normalize({field})"

def zscore(field):
    """
    **[Zscore]**
    - **逻辑 (Logic):** 截面标准差归一：经典的异常值标准化手段。
    - **模板 (Template):** `zscore({field})`

# =============================================================================
# Transformational Operators
# =============================================================================
    - **使用算子 (Operators Used):** `zscore`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"zscore({field})"

# =============================================================================
# Transformational Operators
# =============================================================================

def pasteurize(field):
    """
    **[Pasteurize]**
    - **逻辑 (Logic):** 超级容错处理：抹除 Inf 和 NaN，防止表达式在实盘熔断崩溃。
    - **模板 (Template):** `pasteurize({field})`
    - **使用算子 (Operators Used):** `pasteurize`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"pasteurize({field})"

def densify(field):
    """
    **[Densify]**
    - **逻辑 (Logic):** 稀疏向量稠密化：使得仅有少量事件发生的稀疏矩阵可用作平滑因子。
    - **模板 (Template):** `densify({field})`
    - **使用算子 (Operators Used):** `densify`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"densify({field})"

def tail(field, lower=0.9, upper=1.0, new_val=0):
    """
    **[Tail]**
    - **逻辑 (Logic):** 尾部截取过滤：仅保留特定分位数以上或以下的标的，剔除噪音中间层。
    - **模板 (Template):** `tail({field}, {lower}, {upper}, {new_val})`
    - **使用算子 (Operators Used):** `tail`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"tail({field}, {lower}, {upper}, {new_val})"

def trade_when(condition, alpha):
    """
    **[Trade When]**
    - **逻辑 (Logic):** 事件驱动开关：当条件满足时才更新持仓，否则保持上一期仓位。非常适用于低频或新闻驱动策略。
    - **模板 (Template):** `trade_when({condition}, {alpha}, -1)`
    - **使用算子 (Operators Used):** `trade_when`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"trade_when({condition}, {alpha}, -1)"

def bucket(field):
    """
    **[Bucket]**
    - **逻辑 (Logic):** 离散分箱化：将连续信号打散为分档特征，可降低线性拟合过拟合风险。
    - **模板 (Template):** `bucket(rank({field}), range=`0.2, 1, 0.2`)`
    - **使用算子 (Operators Used):** `bucket`, `rank`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"bucket(rank({field}), range='0.2, 1, 0.2')"

def abs(field):
    """
    **[Abs]**
    - **逻辑 (Logic):** 绝对值剥离：评估变动幅度而非方向。
    - **模板 (Template):** `abs({field})`
    - **使用算子 (Operators Used):** `abs`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"abs({field})"

def log(field):
    """
    **[Log]**
    - **逻辑 (Logic):** 对数压缩：处理极具爆发性、且呈指数增长的数据序列。
    - **模板 (Template):** `log({field})`
    - **使用算子 (Operators Used):** `log`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"log({field})"

def sign(field):
    """
    **[Sign]**
    - **逻辑 (Logic):** 符号提取：仅保留方向，彻底过滤极值干扰。
    - **模板 (Template):** `sign({field})`
    - **使用算子 (Operators Used):** `sign`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"sign({field})"

def sqrt(field):
    """
    **[Sqrt]**
    - **逻辑 (Logic):** 开方平滑：在空间上进行阻尼，效果强于log但不如rank。
    - **模板 (Template):** `sqrt(abs({field}))`
    - **使用算子 (Operators Used):** `sqrt`, `abs`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"sqrt(abs({field}))"

def min(field1, field2):
    """
    **[Min]**
    - **逻辑 (Logic):** 木桶理论探测器：多因子之间求最小，表示所有逻辑必须同时得到满足。
    - **模板 (Template):** `min({field1}, {field2})`
    - **使用算子 (Operators Used):** `min`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"min({field1}, {field2})"

def max(field1, field2):
    """
    **[Max]**
    - **逻辑 (Logic):** 多重保障探测器：多信号中只要有一者极为突出即可采用。
    - **模板 (Template):** `max({field1}, {field2})`
    - **使用算子 (Operators Used):** `max`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"max({field1}, {field2})"

def inverse(field):
    """
    **[Inverse]**
    - **逻辑 (Logic):** 反转倒数：通常用于将 PE 变为 EP，赋予更合理的正向线性结构。
    - **模板 (Template):** `inverse({field})`
    - **使用算子 (Operators Used):** `inverse`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"inverse({field})"

def scale(field):
    """
    **[Scale]**
    - **逻辑 (Logic):** 总量恒定映射：强制某日总体资产暴露恒定，规避大牛熊市的资金膨胀风险。
    - **模板 (Template):** `scale({field}, 1)`
    - **使用算子 (Operators Used):** `scale`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"scale({field}, 1)"

def hump(field, threshold=0.01):
    """
    **[Hump]**
    - **逻辑 (Logic):** Hump 算子：消除日内微小波动，除非信号变动超过特定阈值，否则按兵不动降低手续费。
    - **模板 (Template):** `hump({field}, {threshold})`

# =============================================================================
# Group Operators
# =============================================================================
    - **使用算子 (Operators Used):** `hump`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"hump({field}, {threshold})"

# =============================================================================
# Group Operators
# =============================================================================

def group_sum(field, group='sector'):
    """
    **[Group Sum]**
    - **逻辑 (Logic):** 集群动能汇总：计算整个行业的总流量或总利润。
    - **模板 (Template):** `group_sum({field}, {group})`
    - **使用算子 (Operators Used):** `group_sum`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_sum({field}, {group})"

def group_mean(field, group='sector'):
    """
    **[Group Mean]**
    - **逻辑 (Logic):** 集群锚点：整个行业的平均值基准。
    - **模板 (Template):** `group_mean({field}, 1, {group})`
    - **使用算子 (Operators Used):** `group_mean`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_mean({field}, 1, {group})"

def group_neutralize(field, group='sector'):
    """
    **[Group Neutralize]**
    - **逻辑 (Logic):** 纯净行业中性化：剔除大盘和行业级别的波动共性，保留个股独异阿尔法。
    - **模板 (Template):** `group_neutralize({field}, {group})`
    - **使用算子 (Operators Used):** `group_neutralize`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_neutralize({field}, {group})"

def group_rank(field, group='subindustry'):
    """
    **[Group Rank]**
    - **逻辑 (Logic):** 集群内部竞争排名：在细分行业内寻找龙头股。
    - **模板 (Template):** `group_rank({field}, {group})`
    - **使用算子 (Operators Used):** `group_rank`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_rank({field}, {group})"

def group_std_dev(field, group='sector'):
    """
    **[Group Std Dev]**
    - **逻辑 (Logic):** 集群内离散度：衡量行业内部分歧，分歧大时往往意味着结构性行情爆发。
    - **模板 (Template):** `group_std_dev({field}, {group})`
    - **使用算子 (Operators Used):** `group_std_dev`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_std_dev({field}, {group})"

def group_count(field, group='sector'):
    """
    **[Group Count]**
    - **逻辑 (Logic):** 集群容量：衡量该行业板块的热门程度或标的数量。
    - **模板 (Template):** `group_count({field}, {group})`
    - **使用算子 (Operators Used):** `group_count`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_count({field}, {group})"

def group_scale(field, group='sector'):
    """
    **[Group Scale]**
    - **逻辑 (Logic):** 集群缩放：强制每个行业的信号暴露等额，防止资金过度集中于大板块。
    - **模板 (Template):** `group_scale({field}, {group})`
    - **使用算子 (Operators Used):** `group_scale`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_scale({field}, {group})"

def group_zscore(field, group='sector'):
    """
    **[Group Zscore]**
    - **逻辑 (Logic):** 极强的集群内标准化：判断某股票在其同行中是否极度异常（通常用于价值因子的相对高低估）。
    - **模板 (Template):** `group_zscore({field}, {group})`
    - **使用算子 (Operators Used):** `group_zscore`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_zscore({field}, {group})"

def group_backfill(field, group='sector', d=20):
    """
    **[Group Backfill]**
    - **逻辑 (Logic):** 通过截面集群均值去填补个股的数据空缺。
    - **模板 (Template):** `group_backfill({field}, {group}, {d})`
    - **使用算子 (Operators Used):** `group_backfill`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_backfill({field}, {group}, {d})"

def group_cartesian_product(group1='sector', group2='industry'):
    """
    **[Group Cartesian Product]**
    - **逻辑 (Logic):** [无直接财务经济学意义，底层分类乘积聚合使用。]
    - **模板 (Template):** `group_cartesian_product({group1}, {group2})`
    - **使用算子 (Operators Used):** `group_cartesian_product`
    - **参数建议 (Parameter Recommendations):**
      - 建议根据目标频率或具体策略调整参数。
    """
    return f"group_cartesian_product({group1}, {group2})"
