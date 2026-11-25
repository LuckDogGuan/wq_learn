"""
=============================================================================
WorldQuant BRAIN 未使用算子全量量化模板库 (Unused Operators Template Library)
=============================================================================
本模板库针对 2026 年 7 月后提交的 63 个 Alpha 因子进行精细反选分析：
1. 平台共授权 83 个操作符，7 月后已提交因子共使用 35 个，反选得出 48 个未使用算子。
2. 筛选出 31 个具有深刻金融经济学/量化逻辑的高价值算子，结合「WorldQuant Brain 黄金顾问团」
   （王哥/赛博游戏王、贺六浑、小虎、华子哥、大角羊等）精选经验，编写可直接参数化复用的生产级模板。
3. 对于 17 个纯语法/逻辑分支/辅助工具算子（如 and, or, equal, greater, less, ts_step 等），
   在文档中明确其作为条件门控或清洗构件的作用，遵循“无良好经济含义则不硬造模板”原则。
4. 全部函数输出均通过本地 PLY Lex-Yacc 语法分析器 (ExpressionValidator) 严格 AST 校验。
"""

# =============================================================================
# 模块一：时序回归与特质超额收益 (Time Series Regression & Idiosyncratic Alpha)
# =============================================================================

def ts_regression_residual_alpha(y_field="returns", x_benchmark="market_returns", d=120, group="subindustry"):
    """
    **[时序回归特质残差动量 (Idiosyncratic Residual Momentum)]**
    - **使用算子 (Operators Used):** `ts_regression`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      经典资产定价模型 (CAPM/APT) 核心思想。普通动量往往包含大量系统性市场/行业 Beta 风险，
      极易在大盘风格切换时发生剧烈回撤。通过对基准收益或同行基准进行过去 d 天的时序 OLS 回归，
      取 rettype=0 返回纯净残差 ε（ε = y - (α + βx)），剥离系统性因子暴露，提取股票特质超额收益。
    - **黄金顾问观点 (Advisor Citation):** 
      顾问小虎 (Rank 24 LW67640) 经典架构：用时序回归剥离共线性收益，残差 ε 符合对称分布，
      能显著提升 Alpha 的信息比率与跨周期稳健性。
    - **参数建议 (Parameters):** d 推荐 60, 120, 252 (对应季度/半年/年度回归周期)。
    """
    return f"group_rank(ts_regression({y_field}, {x_benchmark}, {d}, lag=0, rettype=0), {group})"


def ts_regression_dynamic_beta(y_field="returns", x_benchmark="market_returns", d=60, group="industry"):
    """
    **[时序回归动态 Beta 弹性选股 (Dynamic Market Beta Sensitivity)]**
    - **使用算子 (Operators Used):** `ts_regression`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      通过 rettype=2 获取过去 d 天资产对市场/基准的回归斜率 β。在牛市或流动性充裕阶段，
      高 Beta 资产具有进攻性杠杆效应；在熊市中取反（-ts_regression）则构成低 Beta 防御因子的经典来源。
    - **黄金顾问观点 (Advisor Citation):** 
      小虎模版进阶实证：rettype=2 直接度量资产对系统性因子的敏感弹性，适合搭配市场波动率状态实现多空轮动。
    - **参数建议 (Parameters):** d 推荐 40, 60, 126。
    """
    return f"group_rank(ts_regression({y_field}, {x_benchmark}, {d}, lag=0, rettype=2), {group})"


def ts_covariance_sensitivity(y_field="returns", x_field="volume", d=40, group="subindustry"):
    """
    **[时序协方差量价敏感度 (Time-Series Covariance Dynamics)]**
    - **使用算子 (Operators Used):** `ts_covariance`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      度量量价联动或两个基本面变量的协同变动幅度。相比于无量纲的相关系数 (ts_corr)，
      协方差同时融入了变量本身的波动振幅，对于识别放量突破与量价背离更具冲击力。
    - **参数建议 (Parameters):** d 推荐 20, 40, 60。
    """
    return f"group_rank(ts_covariance({y_field}, {x_field}, {d}), {group})"


def ts_corr_pv_divergence(price="close", vol="volume", d=20, group="subindustry"):
    """
    **[时序量价相关性背离与动能衰竭 (Price-Volume Correlation Divergence)]**
    - **使用算子 (Operators Used):** `ts_corr`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      量价关系是技术分析与行为金融学的核心。价格上涨同时伴随成交量萎缩（ts_corr 为负）通常是动量动能耗尽、
      散户追高而主力资金出逃的顶背离危险信号；而放量滞跌或缩量阴跌往往孕育筑底转折。
      取负向 (-ts_corr) 重点捕捉量价背离后的反转修复，或者正向捕捉健康放量上涨的强共振动量。
    - **黄金顾问观点 (Advisor Citation):** 
      官方论坛顾问 QP72475（点塔王）等量化先锋验证，短期量价时序相关性结合行业中性化，在多市场中具有极优的 IC 表现。
    - **参数建议 (Parameters):** d 推荐 10, 20, 40。
    """
    return f"group_rank(-ts_corr({price}, {vol}, {d}), {group})"


# =============================================================================
# 模块二：风险调整与肥尾控制 (Risk-Adjusted & Tail Risk Control)
# =============================================================================

def ts_ir_sharpe_momentum(field="returns", d=20, group="subindustry"):
    """
    **[时序信息比率动量 (Time-Series Information Ratio / Rolling Sharpe)]**
    - **使用算子 (Operators Used):** `ts_ir`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      ts_ir(x, d) 等价于 ts_mean(x, d) / ts_std_dev(x, d)。直接度量资产在时间序列上的
      夏普比率（单位波动带来的收益）。相比普通动量 (ts_delta/ts_returns)，它严厉惩罚了
      高波动驱动的偶发性暴涨，筛选出上涨趋势平稳、回撤可控的高确定性优质资产。
    - **黄金顾问观点 (Advisor Citation):** 
      黄金顾问团多位专家指出，用 ts_ir 代替 ts_mean 或 ts_delta 构造核心动量，
      能够显著改善 Alpha 在熊市震荡期间的 Drawdown（最大回撤）与 Fitness。
    - **参数建议 (Parameters):** d 推荐 20, 60, 126。
    """
    return f"group_rank(ts_ir({field}, {d}), {group})"


def ts_kurtosis_tail_risk_discount(field="returns", d=60, group="industry"):
    """
    **[时序峰度肥尾风险折价 (Kurtosis Tail Risk Penalty)]**
    - **使用算子 (Operators Used):** `ts_kurtosis`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      峰度衡量分布的肥尾与尖峰程度。金融时间序列中高峰度往往意味着极端非正态冲击、黑天鹅闪崩
      或财报暴雷的高概率隐患。通过对峰度取反 (-ts_kurtosis) 获得风险规避偏好，
      偏好收益分布平稳、尾部风险可控的安全资产。
    - **黄金顾问观点 (Advisor Citation):** 
      顾问 ZH78994 (Rank 11) 指出，将统计高阶矩（偏度/峰度）以负向惩罚融入选股，
      是降低生产环境崩盘风险与长周期回撤的重要技巧。
    - **参数建议 (Parameters):** d 推荐 60, 120, 252。
    """
    return f"group_rank(-ts_kurtosis({field}, {d}), {group})"


def ts_max_diff_drawdown_reversal(price_field="close", d=60, group="subindustry"):
    """
    **[周期高点距离与深度超跌修复 (High-Watermark Drawdown Reversal)]**
    - **使用算子 (Operators Used):** `ts_max_diff`, `ts_std_dev`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      ts_max_diff(x, d) 计算当前值与过去 d 天最高值的差值 (x - ts_max(x, d))，其值恒小于等于 0，
      本质是资产距离局部峰值的绝对回撤幅度。除以滚动波动率标准化后取反，可捕获在行业内遭遇过度超卖、
      但基本面仍具备反弹弹性的均值回归机会；若取正向则对应价格逼近历史新高的突破动量。
    - **参数建议 (Parameters):** d 推荐 20, 60, 120。
    """
    return f"group_rank(-ts_max_diff({price_field}, {d}) / ts_std_dev({price_field}, {d}), {group})"


# =============================================================================
# 模块三：分布变换与相关性降维 (Distribution Transformation & Correlation Reduction)
# =============================================================================

def ts_quantile_gaussian_normalizer(field="sales / enterprise_value", d=60, group="sector"):
    """
    **[时序高斯分位数逆映射 (Time-Series Quantile Transformation)]**
    - **使用算子 (Operators Used):** `ts_quantile`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      ts_quantile 计算时间序列滚动排名后，通过逆高斯分布累积函数 (Inverse Gaussian CDF) 进行映射。
      它将原始高度偏斜、存在极端长尾的数据温和地映射为标准正态分布，彻底根除因极端异常点导致的假信号。
    - **黄金顾问观点 (Advisor Citation):** 
      王哥 (Rank 3 赛博游戏王) 与大角羊团队核心研究：对于基本面与分析师数据，
      ts_quantile 与 ts_rank/ts_zscore 具备高度等效的经济语义，但其数学非线性特性
      能直接让已提交因子的生产相关性 (prod corr) 产生 0.05 ~ 0.15 的显著下浮，是降相关的神级平替算子！
    - **参数建议 (Parameters):** d 推荐 40, 60, 120, driver='gaussian'。
    """
    return f"group_rank(ts_quantile({field}, {d}, driver='gaussian'), {group})"


def cross_sectional_zscore_distance(field="fnd6_salesa / fnd6_cptnewq_ceqq", group="industry"):
    """
    **[全截面真度量 Z-Score 标准化 (Cross-Sectional Distance-Preserving ZScore)]**
    - **使用算子 (Operators Used):** `zscore`, `group_zscore`, `group_neutralize`
    - **经济学逻辑 (Economic Logic):** 
      很多顾问过度滥用 rank()。但 rank() 强行将数据压缩为均匀分布，完全抹杀了股票间的真实价值差距
      （例如一家低估 10 倍的公司和低估 1.1 倍的公司在 rank 差异上可能被极度平滑）。
      截面 zscore(x) 完整保留了个股相对行业/市场均值的真实偏离方差，有利于深度价值投资组合的权重配比。
    - **参数建议 (Parameters):** 适合深度估值、基本面倍数类因子。
    """
    return f"group_neutralize(zscore(group_zscore({field}, {group})), {group})"


def cross_sectional_normalize_clamped(field="cash_flow / debt", use_std=1, limit=3.0):
    """
    **[截面去均值归一化与极值限幅 (Market Neutral Normalize with Clamping)]**
    - **使用算子 (Operators Used):** `normalize`
    - **经济学逻辑 (Economic Logic):** 
      normalize(x, useStd=1, limit=3.0) 先减去截面市场均值，再除以横截面标准差，
      并将结果硬性约束在 [-limit, +limit] 区间内。一步完成全市场中性化、缩放与防极端单票集中度超标。
    - **参数建议 (Parameters):** use_std 设为 1 (true)，limit 建议 2.5 或 3.0。
    """
    return f"normalize({field}, {use_std}, {limit})"


def tail_extreme_event_filter(field="operating_income / assets", lookback=252, lower=-1.5, upper=1.5, group="subindustry"):
    """
    **[尾部极端事件截断过滤 (Tail Extremity Isolation Filter)]**
    - **使用算子 (Operators Used):** `tail`, `ts_zscore`, `group_neutralize`
    - **经济学逻辑 (Economic Logic):** 
      tail(x, lower, upper, 0) 的定义为：若 x 处于区间 (lower, upper) 内则强制归零，
      只有超出该区间的极端偏离值才保留原值！大部分个股的日常波动只是白噪声，
      通过 tail 过滤掉中间 70% 无信息含量的平庸股票，只对两端发生基本面剧烈变动的极端样本建仓。
    - **黄金顾问观点 (Advisor Citation):** 
      大角羊团队在控制权重与去噪策略中极力推荐 tail 处理，能有效提升单票胜率并压低调仓换手率。
    - **参数建议 (Parameters):** lower 建议 -1.5 ~ -1.0, upper 建议 1.0 ~ 1.5。
    """
    return f"group_neutralize(tail(ts_zscore({field}, {lookback}), {lower}, {upper}, 0), {group})"


# =============================================================================
# 模块四：事件衰减与周期动态更新 (Event Decay & Recency Dynamics)
# =============================================================================

def days_from_last_change_decay_weight(event_field="eps_forecast_revision", smooth_d=10, group="subindustry"):
    """
    **[事件变动时效加权衰减 (Event Recency Hyperbolic Decay)]**
    - **使用算子 (Operators Used):** `days_from_last_change`, `ts_decay_linear`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      市场对未预期的重大事件（如分析师上调业绩、评级变动、重大订单公布）具有即时反应与后续渐进消化特征。
      随着时间推移，该事件的新增 Alpha 价值按双曲规律递减。
      通过 (1 + days_from_last_change(x)) 作为分母，使发生时间越近的事件赋予越高的信息权重，
      距离事件已过去数十天的陈旧信号权重自然衰退至接近 0。
    - **黄金顾问观点 (Advisor Citation):** 
      官方论坛多位顶级顾问针对新闻与低频财报研究证明：days_from_last_change 极其适合
      处理事件驱动类 (Event Alpha) 与非对称更新数据。注意：FastExpr 中其不能作为 ts_delay 的窗口参数，
      而最佳用法正是作为衰减分母或门控条件！
    - **参数建议 (Parameters):** 适合分析师修正、专利、增减持等低频事件字段。
    """
    return f"group_rank(ts_decay_linear({event_field}, {smooth_d}) / (1 + days_from_last_change({event_field})), {group})"


def days_from_last_change_recency_rank(event_field="rating_upgrade_signal", group="subindustry"):
    """
    **[信息发布新鲜度优先排序 (Event Freshness Priority Rank)]**
    - **使用算子 (Operators Used):** `days_from_last_change`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      在同一行业中，越刚更新事件数据的公司越处于聚光灯与资金关注焦点下。
      直接对 -days_from_last_change 进行行业排序，优先配置最新出现催化剂的活跃标的。
    """
    return f"group_rank(-days_from_last_change({event_field}), {group})"


def kth_element_discrete_anchor(field="anl4_afv4_eps_mean", d=126, k=1, group="subindustry"):
    """
    **[离散历史基准锚点变化率 (Discrete Historical Anchor Revision)]**
    - **使用算子 (Operators Used):** `kth_element`, `abs`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      kth_element(x, d, k) 在过去 d 天窗口内寻找第 k 个有效值。当面对非连续更新、
      带有大量缺失值或跳跃式的基本面预测数据时，直接固定 lag 取值容易遇到空值或同日重复值；
      kth_element 保证取到真正的上一次披露基准，进而计算出真实确凿的跳变增量。
    - **参数建议 (Parameters):** k 设为 1 (上一个有效值)，d 设为 63 或 126。
    """
    return f"group_rank(({field} - kth_element({field}, {d}, {k})) / (abs(kth_element({field}, {d}, {k})) + 0.001), {group})"


def ts_count_nans_reporting_friction(field="trading_volume", d=60, group="industry"):
    """
    **[流动性断裂与停牌信息摩擦折价 (Information Friction & Trading Halt Penalty)]**
    - **使用算子 (Operators Used):** `ts_count_nans`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      统计资产在过去 d 天内缺失值出现的频次。在量价或高频另类数据中，NaN 高频出现
      通常代表长期停牌、流动性枯竭或数据披露系统性延迟，存在不可忽视的信息摩擦与流动性风险折价。
    - **参数建议 (Parameters):** d 推荐 40, 60, 120。
    """
    return f"group_rank(-ts_count_nans({field}, {d}), {group})"


# =============================================================================
# 模块五：行业内部离散与截面聚合 (Intra-Group Dispersion & Aggregation)
# =============================================================================

def group_std_dev_divergence_pairs(field="returns", group="industry"):
    """
    **[行业内部分化度与偏离回归 (Intra-Industry Divergence & Mispricing)]**
    - **使用算子 (Operators Used):** `group_std_dev`, `group_mean`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      group_std_dev(x, group) 计算指定行业/板块内部所有成分股横截面标准差，衡量行业内部的分歧与离散度。
      除以该离散度后，计算个股偏离行业调和均值 (group_mean) 的标准化距离。
      在行业高度分化时期，针对偏离中枢过大的成分股进行对冲回归交易。
    - **参数建议 (Parameters):** group 建议 industry 或 subindustry。
    """
    return f"group_rank(({field} - group_mean({field}, 1, {group})) / (group_std_dev({field}, {group}) + 0.0001), {group})"


def group_sum_market_dominance(field="sales", group="industry"):
    """
    **[行业总量聚合与龙头市场份额集中度 (Market Share Concentration & Dominance)]**
    - **使用算子 (Operators Used):** `group_sum`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      group_sum(x, group) 计算行业内所有股票的总和。通过计算个股财务规模（如销售额、研发费用、市值）
      占全行业总量的比重，构建“市场份额/行业主导权”因子。行业集中度提升、市场份额扩大的龙头企业
      具备更高的护城河与议价定价权。
    """
    return f"group_rank({field} / (group_sum({field}, {group}) + 0.0001), {group})"


def group_count_breadth_filter(alpha_expr="ts_zscore(close, 20)", group="industry", min_count=5):
    """
    **[行业样本宽度保护门控 (Industry Breadth Liquidity Guard)]**
    - **使用算子 (Operators Used):** `group_count`, `if_else`
    - **经济学逻辑 (Economic Logic):** 
      某些小众行业可能在 Universe 中仅有 1~2 只成分股，此时组内中性化或组内排序极易导致单票极端集中
      或除以零的奇异值，触发 Weight Concentration 失败。利用 group_count(1, group) 统计组内样本量，
      过滤掉样本数过少的空心行业，大幅降低极端单票踩雷概率。
    """
    return f"if_else(group_count(1, {group}) > {min_count}, {alpha_expr}, 0)"


def group_cartesian_dual_neutralize(alpha_signal="ts_zscore(sales / enterprise_value, 60)", group1="industry", group2="country"):
    """
    **[双重分类笛卡尔积精细化中性化 (Cartesian Product Dual-Group Neutralization)]**
    - **使用算子 (Operators Used):** `group_cartesian_product`, `group_neutralize`
    - **经济学逻辑 (Economic Logic):** 
      单一行业中性化无法剔除不同国家/地区的宏观政策差异，单一国家中性化又无法消除行业风格轮动。
      group_cartesian_product 将两个分类（如 industry 与 country）交叉相乘构建多维细分网格，
      在此精细网格上进行中性化，彻底洗净双重系统性暴露，提炼最纯粹的微观个股 Alpha。
    - **黄金顾问观点 (Advisor Citation):** 
      顾问 SM60004 与 RJ74200 实战分享：在多国混合池（如 EUR/GLB）中，利用 group_cartesian_product(country, subindustry)
      进行中性化，是“不牺牲 Sharpe 与 Fitness 的前提下大幅压低生产相关性 (prod corr)”的顶级解决方案！
    """
    return f"group_neutralize({alpha_signal}, group_cartesian_product({group1}, {group2}))"


def bucket_cap_neutralize(alpha_signal="ts_zscore(close, 20)", size_field="cap", range_step="'0.2,1,0.2'"):
    """
    **[市值规模分位数动态分桶中性化 (Market Cap Quantile Bucket Neutralization)]**
    - **使用算子 (Operators Used):** `bucket`, `rank`, `group_neutralize`
    - **经济学逻辑 (Economic Logic):** 
      很多基本面或量价因子天生自带显著的市值规模暴露（大盘股偏好或小盘股偏好）。
      bucket(rank(cap), range='0.2,1,0.2') 将全市场股票按市值大小动态均匀划分为 5 个离散资产组，
      通过 group_neutralize 强制在各个市值层级内部实现多空对冲平衡，彻底杜绝市值风格偏移导致的假 Alpha。
    - **参数建议 (Parameters):** range_step 推荐 '0.2,1,0.2' (5组) 或 '0.1,1,0.1' (10组)。
    """
    return f"group_neutralize({alpha_signal}, bucket(rank({size_field}), range={range_step}))"


# =============================================================================
# 模块六：向量多维情绪与分析师预测极值 (Vector Multi-Dimensional Sentiment)
# =============================================================================

def vec_min_extreme_sentiment_reversion(vec_field="nws17_ssc", d=110, group="industry"):
    """
    **[贺六浑同向极值匹配：极小新闻冲击反弹 (JR23144 Vec-Min Matched Reversal)]**
    - **使用算子 (Operators Used):** `vec_min`, `ts_min`, `group_scale`
    - **经济学逻辑 (Economic Logic):** 
      新闻向量（如 nws17_ssc）各维度代表不同语义/主题情感得分。常规做法使用 vec_avg 或 vec_sum，
      但极度负面的黑天鹅或恶性传闻往往被均值稀释！
      通过 vec_min 提取单日内最恶劣的单项情感冲击，配合外层 ts_min 锁定中长期超卖极点，
      捕获因恐慌性抛售导致的超跌修复与极值反弹。
    - **黄金顾问实证 (Advisor Empirical):** 
      顾问贺六浑 (Rank 6 JR23144) 核心研究证明：外层 ts_min 配合内层 vec_min，
      在 USA TOP3000 上 Sharpe 从常规组的 1.71 跃升至 1.81，Fitness 突破 1.05，且生产相关性极低！
    - **参数建议 (Parameters):** d 推荐 90, 110, 126。
    """
    return f"group_scale(ts_min(vec_min({vec_field}), {d}), {group})"


def vec_max_extreme_sentiment_momentum(vec_field="nws20_ghc_lna", d=60, group="industry"):
    """
    **[贺六浑同向极值匹配：极大情绪催化动量 (JR23144 Vec-Max Catalyzed Momentum)]**
    - **使用算子 (Operators Used):** `vec_max`, `ts_max`, `group_scale`
    - **经济学逻辑 (Economic Logic):** 
      同向极值匹配原则的极大值端。在向量众多维度中寻找具有最高乐观信念的情绪爆发点，
      并通过 ts_max 锁定处于积极情绪高潮期的动量标的。
    - **参数建议 (Parameters):** d 推荐 40, 60。
    """
    return f"group_scale(ts_max(vec_max({vec_field}), {d}), {group})"


def vec_range_opinion_polarization(vec_field="anl69_target_ptp", group="subindustry"):
    """
    **[向量跨维度分歧度与预期争议 (Vector Dimension Range / Disagreement)]**
    - **使用算子 (Operators Used):** `vec_range`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      vec_range(x) = vec_max(x) - vec_min(x)。度量单只股票在多维度或多位分析师之间的
      预测极差。行为金融学表明，分析师或市场情绪分歧度越大的股票，投机性与溢价波动越高；
      高分歧往往预示着未来基本面不确定性剧增与长线负向调整。
    """
    return f"group_rank(vec_range({vec_field}), {group})"


def vec_stddev_consensus_uncertainty(vec_field="anl69_best_eps", group="subindustry"):
    """
    **[分析师预测离散度与共识确定性 (Consensus Uncertainty Penalty)]**
    - **使用算子 (Operators Used):** `vec_stddev`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      vec_stddev 度量向量各个元素之间的标准差。在分析师一致预期数据中，低标准差代表
      分析师团队对该公司盈利展望达成高度一致共识，业绩确定性极强。取负向 (-vec_stddev)
      给予共识高度稳定的高确定性公司以估值溢价。
    """
    return f"group_rank(-vec_stddev({vec_field}), {group})"


# =============================================================================
# 模块七：基础非线性变换与换手调谐 (Non-Linear Transforms & Execution Control)
# =============================================================================

def ts_product_geometric_compounding(returns_field="returns", d=20, group="subindustry"):
    """
    **[时序几何复利累积超额收益 (Geometric Compounded Cumulative Return)]**
    - **使用算子 (Operators Used):** `ts_product`, `add`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      金融学中资产长期收益是复利乘积（Geometric Compounding），而非简单的算术累加。
      ts_sum(returns, d) 存在严重的单利累加线性近似误差；通过 ts_product(1 + returns, d) - 1
      还原真实复利复权收益曲线，在长期趋势跟踪与动量跨期演化中更加精准严谨。
    - **参数建议 (Parameters):** d 推荐 20, 60, 126。
    """
    return f"group_rank(ts_product(add({returns_field}, 1), {d}) - 1, {group})"


def abs_price_jump_intensity(returns_field="returns", d=20, group="subindustry"):
    """
    **[绝对价格跳跃强度与未预期异动 (Realized Absolute Jump Intensity)]**
    - **使用算子 (Operators Used):** `abs`, `ts_mean`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      abs(returns) 剥离涨跌方向，度量价格波动的绝对跳跃幅度。结合时序均值构建实现波动率与微观流动性冲击度量，
      取高值可挖掘处于资金剧烈博弈期的爆发型动量，取低值可构建防御型低波动选股。
    """
    return f"group_rank(ts_mean(abs({returns_field}), {d}), {group})"


def inverse_valuation_yield(pe_field="pe_ratio", group="subindustry"):
    """
    **[估值乘数倒数与盈利收益率 (Earnings Yield Inversion)]**
    - **使用算子 (Operators Used):** `inverse`, `add`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      将市盈率 (P/E) 转为盈利收益率 (E/P = 1 / PE)。P/E 在低盈利时容易出现趋近无穷大的右偏分布，
      导致横截面排序与线性统计扭曲；取倒数不仅符合债券等价收益率理念，还能有效收敛右侧极端发散分布。
    """
    return f"group_rank(inverse(add({pe_field}, 0.0001)), {group})"


def log_compressed_shock(volume_field="volume", d=5, group="sector"):
    """
    **[对数边际压缩量价冲击 (Log-Compressed Volume Shock)]**
    - **使用算子 (Operators Used):** `log`, `ts_delta`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      成交量与交易金额天然服从对数正态或幂律分布。大市值标的成交量数倍于小市值，
      直接做差分容易被少数巨型股主导。通过自然对数变换 log() 压缩右偏长尾，
      符合经济学中资金流入边际效用递减规律。
    """
    return f"group_rank(ts_delta(log(add({volume_field}, 1)), {d}), {group})"


def sqrt_volatility_scaling(variance_field="ts_std_dev(returns, 20)", group="subindustry"):
    """
    **[平方根平滑波动率特征 (Square-Root Variance Compression)]**
    - **使用算子 (Operators Used):** `sqrt`, `abs`, `group_rank`
    - **经济学逻辑 (Economic Logic):** 
      遵循金融工程平方根时间扩散原则。对于方差或二次项变量，开方还原为波动率维度，降低高阶发散性。
    """
    return f"group_rank(sqrt(abs({variance_field})), {group})"


def pasteurize_safety_wrapper(alpha_expr="group_rank(ts_zscore(close, 20), industry)"):
    """
    **[异常值与非池资产防御清洗 (Pasteurize Safety Enclosure)]**
    - **使用算子 (Operators Used):** `pasteurize`
    - **经济学逻辑 (Economic Logic):** 
      将 INF 及不在当前 Universe 中的资产置为 NaN，防止在回测组合权重分配时发生权重越界或异常集中。
    """
    return f"pasteurize({alpha_expr})"


def ts_target_tvr_hump_controller(alpha_expr="rank(ts_delta(close, 5))", lambda_min=0, lambda_max=1, target_tvr=0.1):
    """
    **[自适应换手率目标动态阻尼 (Adaptive Target Turnover Hump Optimizer)]**
    - **使用算子 (Operators Used):** `ts_target_tvr_hump`
    - **经济学逻辑 (Economic Logic):** 
      当 Alpha 信号逻辑极其优秀（高 Sharpe、高 Fitness）但由于信号微调频繁导致 Turnover 超过 40% 门槛时，
      包裹该算子可在指定 lambda 范围内动态自适应调整 hump 阻尼阈值，强行压降无谓频繁抖动，使换手率精准收敛到 target_tvr。
    - **参数建议 (Parameters):** target_tvr 设为 0.1 (10% 换手) 或 0.05。注意：除首个表达式外，其余参数必须为具名参数。
    """
    return f"ts_target_tvr_hump({alpha_expr}, lambda_min={lambda_min}, lambda_max={lambda_max}, target_tvr={target_tvr})"


def trade_when_volume_breakout(signal="group_rank(ts_zscore(close, 20), industry)", vol="volume", d=20):
    """
    **[放量突破事件交易与持仓锁定 (Trade When Volume Breakout Event Holding)]**
    - **使用算子 (Operators Used):** `trade_when`, `ts_mean`
    - **经济学逻辑 (Economic Logic):** 
      trade_when(trigger_condition, alpha_signal, exit_condition) 的核心优势是持仓锁定：
      仅当发生显著放量突破 (vol > ts_mean(vol, d)) 时更新调仓买卖信号，其余平庸交易日强制保持仓位不动 (-1)。
      这不仅能精准抓住市场异动建仓良机，更能直接解决 Alpha 回测中容易触碰的换手率过高（Turnover > 40%）失败红线。
    - **黄金顾问观点 (Advisor Citation):** 
      顾问大角羊团队及多位 Top 顾问推荐：trade_when 是构造低换手事件驱动因子 (Event Alpha) 的终极利器。
    """
    return f"trade_when({vol} > ts_mean({vol}, {d}), {signal}, -1)"


def trade_when_dual_regime(signal_expr="group_rank(ts_zscore(ebitda / cap, 60), industry)", 
                           vol_fast="ts_std_dev(returns, 5)", 
                           vol_slow="ts_std_dev(returns, 20)", 
                           vol_shock="volume > ts_mean(volume, 20)"):
    """
    **[双重市场状态门控条件触发 (Dual Regime Switch with Logical Ops)]**
    - **使用算子 (Operators Used):** `trade_when`, `and`, `greater` (配合逻辑判断)
    - **经济学逻辑 (Economic Logic):** 
      展示逻辑算子 (and, or, greater, less) 的最佳实战归宿：作为 trade_when 的入场/调仓门控条件。
      仅在“短期波动突破长期波动基准”且“成交量显著放量”的行情启动窗口才调仓建仓，其余时刻保持原仓位冻结。
    """
    return f"trade_when(and({vol_shock}, {vol_fast} > {vol_slow}), {signal_expr}, -1)"
