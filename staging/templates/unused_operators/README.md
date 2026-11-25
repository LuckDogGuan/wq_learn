# WorldQuant BRAIN 未使用算子深度挖掘与模板库指南

> **基准口径**: **2026 年 7 月 1 日及以后提交的 Alpha 因子 (共 63 个)** vs. **平台当前授权可用算子 (共 83 个)**  
> **核心依托**: 整合「WorldQuant Brain 黄金顾问团」（王哥/赛博游戏王、贺六浑、小虎、华子哥、大角羊、点塔王等）精选实战经验  
> **存储路径**: `factor/templates/unused/`

---

## 目录
1. [基准口径调整与反选统计大纲 (2026年7月后)](#1-基准口径调整与反选统计大纲)
2. [48 个未使用操作符全景清册](#2-48-个未使用操作符全景清册)
3. [黄金顾问团核心指导经验 (Top Advisors Insights)](#3-黄金顾问团核心指导经验)
4. [31 个核心高价值算子的经济学逻辑与进阶模板](#4-31-个核心高价值算子的经济学逻辑与进阶模板)
5. [17 个辅助/语法算子的理性定位（放着不处理的具体原因）](#5-17-个辅助语法算子的理性定位)
6. [与已有 `factor/templates` 模板的对照与升级](#6-与已有-factortemplates-模板的对照与升级)
7. [快速使用与单元测试](#7-快速使用与单元测试)

---

## 1. 基准口径调整与反选统计大纲

根据用户明确要求，因早期历史提交的因子编写风格与算子选用规范不统一，本次统计**仅锁定 2026 年 7 月 1 日至今已提交的 Out-of-Sample (OS) 阶段因子**进行穿透反选：

* **平台已授权可用操作符总数**: **83 个**
* **2026 年 7 月后已提交因子总数**: **63 个**
* **2026 年 7 月后已使用的操作符总数**: **35 个**  
  *(最高频算子：`ts_zscore` 35次, `rank` 34次, `subtract` 33次, `divide` 24次, `ts_decay_linear` 17次, `winsorize` 15次, `multiply` 14次, `group_zscore` 14次, `ts_mean` 13次, `quantile` 13次...)*
* **反选得出：2026 年 7 月后从未在提交因子中使用过的操作符**: **48 个**  
  *(相比于全历史 89 个因子的统计，新增了 8 个在 7 月后未曾使用的高价值/辅助算子：`ts_corr`, `trade_when`, `bucket`, `group_cartesian_product`, `ts_product`, `abs`, `greater`, `less`)*

---

## 2. 48 个未使用操作符全景清册

这 48 个未使用的操作符按平台底层机制与数据维度划分为七大门类：

| 类别 (Category) | 2026 年 7 月后未用算子列表 | 数量 | 特点与定位 |
| :--- | :--- | :---: | :--- |
| **Time Series (时序)** | `ts_regression`, `ts_ir`, `ts_quantile`, `ts_kurtosis`, `ts_max_diff`, `ts_corr`*(新)*, `ts_product`*(新)*, `days_from_last_change`, `ts_covariance`, `ts_returns`, `ts_sum`, `ts_count_nans`, `kth_element`, `ts_target_tvr_hump`, `ts_step` | 15 | 涵盖特质残差动量、夏普型信息比率、价量背离、几何复利累积、高斯逆映射等**核心 Alpha 引擎** |
| **Transformational (转换)** | `trade_when`*(新)*, `bucket`*(新)*, `tail` | 3 | 低换手事件驱动门控、市值/波动率分桶中性化、极端白噪声过滤 |
| **Vector (向量)** | `vec_min`, `vec_max`, `vec_range`, `vec_stddev`, `vec_count` | 5 | 专用于处理新闻 NLP 嵌入与分析师预测向量；贺六浑极值匹配与共识分歧度度量核心 |
| **Group (分组)** | `group_cartesian_product`*(新)*, `group_std_dev`, `group_sum`, `group_mean`, `group_count` | 5 | 双重分类笛卡尔积中性化、行业内部分化度配对、行业总规模聚合、样本宽度门控 |
| **Cross Sectional (截面)** | `zscore`, `normalize` | 2 | 保留真实分布距离的标准化与带截断限制的均值市场中性化 |
| **Arithmetic (算术)** | `abs`*(新)*, `inverse`, `log`, `sqrt`, `power`, `sign`, `pasteurize` | 7 | 绝对跳跃波动率、估值倒数收益率转换、边际效用递减对数压缩、异常值清洗 |
| **Logical (逻辑判断)** | `greater`*(新)*, `less`*(新)*, `and`, `or`, `not`, `equal`, `not_equal`, `greater_equal`, `less_equal`, `if_else`, `is_nan` | 11 | 纯条件门控、状态机切换与动态掩码辅助构件，不建议独立构造 Alpha |

---

## 3. 黄金顾问团核心指导经验

在设计模板前，我们深入查阅了「WorldQuant Brain 黄金顾问团」顶级顾问的论坛精选帖子与实战手稿，提炼出以下核心准则：

### 1. 贺六浑 (Rank 6 JR23144) ——「同向极值匹配原则」
* **痛点**: 多数顾问在处理向量数据（如新闻向量 `nws17_ssc`、`nws20_ghc_lna`）时，习惯无脑使用 `vec_avg()` 或 `vec_sum()`。平均化会严重抹平极端黑天鹅或突发重大利好的冲击峰值。
* **心法**: **当外层逻辑寻找极值时，内层必须配合极值算子！**
  * 外层求极小（如 `ts_min`）匹配内层 `vec_min`：`group_scale(ts_min(vec_min(vec_field), 110), industry)`
  * 贺六浑实证对比：常规组 `vec_avg` 的 Sharpe 为 1.71, Fitness 为 0.96；而同向极值匹配组 `vec_min` 的 **Sharpe 跃升至 1.81，Fitness 突破 1.05**，且生产相关性极低！

### 2. 王哥 / 赛博游戏王 (Rank 3 ZS59763) ——「算子平替降相关神技」
* **痛点**: 很多因子回测指标极其优秀，但因为使用了常见的 `ts_rank` 或 `ts_zscore`，在提交时因与生产池现有因子相关性（`PROD correlation >= 0.70`）过高而被平台硬性拦截。
* **心法**: 对于基本面及分析师数据，**`ts_quantile(x, d, driver='gaussian')`** 与 `ts_rank`、`ts_scale` 在经济学逻辑上高度等价，但由于其非线性逆高斯分布映射特性，**能在保持 IS/OS 优异表现的同时，将生产相关性直接拉低 0.05 ~ 0.15**，是救活高相关因子的绝杀技！

### 3. 小虎 (Rank 24 LW67640) ——「ts_regression 剥离系统性 Beta 架构」
* **痛点**: 简单价格动量往往随大盘系统性 Beta 起伏，在风格急剧切换时出现深幅回撤。
* **心法**: 利用 `ts_regression(y, benchmark, d, lag=0, rettype=0)` 跑过去 d 天的时序 OLS 回归。
  * `rettype=0` 返回纯净残差 $\epsilon = y - (\alpha + \beta x)$，剥离市场/行业风险，提炼纯正特质超额动量；
  * `rettype=2` 返回动态斜率 $\beta$，度量弹性敏感度；
  * `rettype=6` 返回残差标准差 $\sigma_\epsilon$，作为收益稳定性的筛选权重。

### 4. 顾问 SM60004 & 华子哥 (Rank 9) ——「双重笛卡尔积中性化与分歧度度量」
* **心法**: 
  * 针对多国家或大盘池（如 EUR/GLB/USA），利用 **`group_cartesian_product(country, industry)`** 或 **`bucket(rank(cap), range='0.2,1,0.2')`** 构建细分二维中性化矩阵，能在不牺牲 Sharpe 的前提下大幅击穿生产相关性；
  * `vec_range` (极差) 和 `vec_stddev` (标准差) 是度量分析师与新闻舆情**观点分歧度 (Opinion Disagreement)** 的无价之宝。分歧度越大的股票不确定性越高，长线具有显著的负溢价，适合做空或取负向排序。

### 5. 大角羊 (Rank 51 MZ45384) ——「低换手事件门控与去噪截断」
* **心法**: 
  * `trade_when` 是压降高换手率（解决 Turnover > 40% 失败红线）的最强利器，通过设定放量或波动率启动条件更新持仓，未触发时保持仓位锁定（`-1`）；
  * 使用 `tail(x, lower, upper, 0)` 抹平中间 60%~70% 的微弱白噪声，只对处于两侧极端状态的强信号建仓，兼具防权重集中与降换手双重收益。

---

## 4. 31 个核心高价值算子的经济学逻辑与进阶模板

全部模板函数已封装至 `factor/templates/unused/unused_alpha_templates.py`，支持直接调用并参数化配置，并通过了本地 PLY AST 验证：

### 模块一：时序回归与特质超额收益 (Time Series Regression & Idiosyncratic Alpha)

#### 1. 时序回归特质残差动量 (`ts_regression_residual_alpha`)
* **涉及算子**: `ts_regression`, `group_rank`
* **模板**: `group_rank(ts_regression({y_field}, {x_benchmark}, {d}, lag=0, rettype=0), {group})`
* **金融语义**: 基于 CAPM 理论，对个股收益相对基准进行滚动回归。`rettype=0` 剥离系统性 Beta 与基准暴露，提炼个股特质超额残差动量。

#### 2. 时序回归动态 Beta 弹性选股 (`ts_regression_dynamic_beta`)
* **涉及算子**: `ts_regression`, `group_rank`
* **模板**: `group_rank(ts_regression({y_field}, {x_benchmark}, {d}, lag=0, rettype=2), {group})`
* **金融语义**: `rettype=2` 动态追踪个股对系统性因子的边际敏感度 $\beta$。牛市放量期做多高 Beta，震荡弱市中取反做多低 Beta 防御资产。

#### 3. 时序协方差量价敏感度 (`ts_covariance_sensitivity`)
* **涉及算子**: `ts_covariance`, `group_rank`
* **模板**: `group_rank(ts_covariance({y_field}, {x_field}, {d}), {group})`
* **金融语义**: 相比无量纲相关系数 (ts_corr)，时序协方差融入了变量本身的波动振幅，对于放量异动突破和剧烈共振具备更强的敏感性。

#### 4. 时序量价相关性背离与动能衰竭 (`ts_corr_pv_divergence`) *(7月后新增)*
* **涉及算子**: `ts_corr`, `group_rank`
* **模板**: `group_rank(-ts_corr({price}, {vol}, {d}), {group})`
* **金融语义**: 价格上涨伴随缩量（顶背离）代表主力出逃与动能衰竭；缩量阴跌或放量滞跌孕育反弹转折。取负向捕捉量价背离反转。

---

### 模块二：风险调整与肥尾控制 (Risk-Adjusted & Tail Risk Control)

#### 5. 时序信息比率动量 (`ts_ir_sharpe_momentum`)
* **涉及算子**: `ts_ir`, `group_rank`
* **模板**: `group_rank(ts_ir({field}, {d}), {group})`
* **金融语义**: `ts_ir(x, d) = ts_mean / ts_std_dev`，直接计算滚动夏普比率。惩罚单日暴涨但高波动的虚假脉冲，精选稳步上涨的长牛标的。

#### 6. 时序峰度肥尾风险折价 (`ts_kurtosis_tail_risk_discount`)
* **涉及算子**: `ts_kurtosis`, `group_rank`
* **模板**: `group_rank(-ts_kurtosis({field}, {d}), {group})`
* **金融语义**: 峰度度量厚尾程度。高峰度个股未来遭遇黑天鹅闪崩风险极高。取负向给予收益平稳、轻尾的安全资产估值溢价。

#### 7. 周期高点距离与超跌均值修复 (`ts_max_diff_drawdown_reversal`)
* **涉及算子**: `ts_max_diff`, `ts_std_dev`, `group_rank`
* **模板**: `group_rank(-ts_max_diff({price_field}, {d}) / ts_std_dev({price_field}, {d}), {group})`
* **金融语义**: `ts_max_diff(x, d) = x - ts_max(x, d) <= 0`，度量个股相对周期最高点的跌幅深度。标准化后取反用于超跌反弹修复。

---

### 模块三：分布变换与相关性降维 (Distribution Transformation & Correlation Reduction)

#### 8. 时序高斯分位数逆映射 (`ts_quantile_gaussian_normalizer`)
* **涉及算子**: `ts_quantile`, `group_rank`
* **模板**: `group_rank(ts_quantile({field}, {d}, driver='gaussian'), {group})`
* **金融语义**: 逆高斯累积分布映射，将偏斜财务比率转换为标准正态分布。王哥实证证明其可在保持经济学语义下，将生产相关性 (prod corr) 压降 0.05~0.15。

#### 9. 全截面真度量 Z-Score (`cross_sectional_zscore_distance`)
* **涉及算子**: `zscore`, `group_zscore`, `group_neutralize`
* **模板**: `group_neutralize(zscore(group_zscore({field}, {group})), {group})`
* **金融语义**: 避免 `rank()` 强行压缩为均匀分布抹平真实价值差距，保留相对市场均值的真实偏离方差，增强深度价值因子有效性。

#### 10. 截面均值去心与截断归一化 (`cross_sectional_normalize_clamped`)
* **涉及算子**: `normalize`
* **模板**: `normalize({field}, {use_std}, {limit})`
* **金融语义**: 减去截面均值并除以截面标准差，并将极值截断在 `[-limit, +limit]` 内，一步完成市场中性化、缩放与防单票集中度超标。

#### 11. 尾部极端事件截断过滤 (`tail_extreme_event_filter`)
* **涉及算子**: `tail`, `ts_zscore`, `group_neutralize`
* **模板**: `group_neutralize(tail(ts_zscore({field}, {lookback}), {lower}, {upper}, 0), {group})`
* **金融语义**: 抹平中间 70% 无信息含量的平庸股票，只对处于两侧极端状态的强信号建仓，显著压制换手率并提升单票胜率。

---

### 模块四：事件衰减与动态更新 (Event Decay & Recency Dynamics)

#### 12. 事件变动双曲时效衰减 (`days_from_last_change_decay_weight`)
* **涉及算子**: `days_from_last_change`, `ts_decay_linear`, `group_rank`
* **模板**: `group_rank(ts_decay_linear({event_field}, {smooth_d}) / (1 + days_from_last_change({event_field})), {group})`
* **金融语义**: 市场对未预期重大事件（分析师大幅上调、评级突变）的消化随时间呈双曲递减。以 `(1 + days_from_last_change)` 作为分母，赋予新事件更高权重。

#### 13. 信息发布新鲜度排序 (`days_from_last_change_recency_rank`)
* **涉及算子**: `days_from_last_change`, `group_rank`
* **模板**: `group_rank(-days_from_last_change({event_field}), {group})`
* **金融语义**: 行业内越刚更新事件数据的公司越处于资金关注焦点下，优先配置最新催化剂标的。

#### 14. 离散历史基准锚点跳变率 (`kth_element_discrete_anchor`)
* **涉及算子**: `kth_element`, `abs`, `group_rank`
* **模板**: `group_rank(({field} - kth_element({field}, {d}, {k})) / (abs(kth_element({field}, {d}, {k})) + 0.001), {group})`
* **金融语义**: 针对低频公布或跳跃式预测，`kth_element(x, d, 1)` 定位到真正的上一次披露基准，避免固定 lag 取到空值或重复值。

#### 15. 停牌与信息披露摩擦折价 (`ts_count_nans_reporting_friction`)
* **涉及算子**: `ts_count_nans`, `group_rank`
* **模板**: `group_rank(-ts_count_nans({field}, {d}), {group})`
* **金融语义**: 统计缺失值频次，度量停牌、流动性枯竭或披露延迟带来的信息摩擦折价。

---

### 模块五：行业内部离散与截面聚合 (Intra-Group Dispersion & Aggregation)

#### 16. 行业内部分化度与偏离回归 (`group_std_dev_divergence_pairs`)
* **涉及算子**: `group_std_dev`, `group_mean`, `group_rank`
* **模板**: `group_rank(({field} - group_mean({field}, 1, {group})) / (group_std_dev({field}, {group}) + 0.0001), {group})`
* **金融语义**: 用 `group_std_dev` 捕捉行业成分股分化程度，度量个股偏离行业调和均值的标准化距离，实施行业内对冲回归交易。

#### 17. 行业总量聚合与龙头市场份额 (`group_sum_market_dominance`)
* **涉及算子**: `group_sum`, `group_rank`
* **模板**: `group_rank({field} / (group_sum({field}, {group}) + 0.0001), {group})`
* **金融语义**: 计算个股财务规模占行业总盘子（group_sum）的比重，构建衡量行业主导地位与定价权的护城河因子。

#### 18. 行业样本宽度保护门控 (`group_count_breadth_filter`)
* **涉及算子**: `group_count`, `if_else`
* **模板**: `if_else(group_count(1, {group}) > {min_count}, {alpha_expr}, 0)`
* **金融语义**: 过滤成分股仅 1~2 只的小众空心行业，防止中性化时单票权重过度集中。

#### 19. 双重分类笛卡尔积精细化中性化 (`group_cartesian_dual_neutralize`) *(7月后新增)*
* **涉及算子**: `group_cartesian_product`, `group_neutralize`
* **模板**: `group_neutralize({alpha_signal}, group_cartesian_product({group1}, {group2}))`
* **金融语义**: 将两个分类（如 industry 与 country）交叉相乘构建二维细分网格进行中性化，彻底洗净跨国别与跨行业的双重风格暴露，大幅压降生产相关性。

#### 20. 市值规模分位数动态分桶中性化 (`bucket_cap_neutralize`) *(7月后新增)*
* **涉及算子**: `bucket`, `rank`, `group_neutralize`
* **模板**: `group_neutralize({alpha_signal}, bucket(rank({size_field}), range={range_step}))`
* **金融语义**: `bucket` 将股票按市值分为 5 或 10 组，在各个市值层级内部实现多空对冲平衡，杜绝市值偏好导致的伪 Alpha。

---

### 模块六：向量多维情绪与分析师预测极值 (Vector Multi-Dimensional Sentiment)

#### 21. 贺六浑同向极值匹配：极小新闻反弹 (`vec_min_extreme_sentiment_reversion`)
* **涉及算子**: `vec_min`, `ts_min`, `group_scale`
* **模板**: `group_scale(ts_min(vec_min({vec_field}), {d}), {group})`
* **实证支撑**: 贺六浑 (Rank 6) 证实内层 `vec_min` 匹配外层 `ts_min`，USA 市场 Sharpe 突破 1.81，Fitness 破 1.05。

#### 22. 贺六浑同向极值匹配：极大情绪催化动量 (`vec_max_extreme_sentiment_momentum`)
* **涉及算子**: `vec_max`, `ts_max`, `group_scale`
* **模板**: `group_scale(ts_max(vec_max({vec_field}), {d}), {group})`
* **金融语义**: 锁定向量维度中最乐观的情绪爆发点，捕获高潮期动量收益。

#### 23. 向量跨维度分歧度与预期争议 (`vec_range_opinion_polarization`)
* **涉及算子**: `vec_range`, `group_rank`
* **模板**: `group_rank(vec_range({vec_field}), {group})`
* **金融语义**: 向量极差度量分析师与市场观点对立程度，高分歧股票往往伴随长期负向收益折价。

#### 24. 分析师预测离散度与共识确定性 (`vec_stddev_consensus_uncertainty`)
* **涉及算子**: `vec_stddev`, `group_rank`
* **模板**: `group_rank(-vec_stddev({vec_field}), {group})`
* **金融语义**: 标准差越小代表分析师盈利预测共识越坚定，给予业绩高确定性标的估值溢价。

---

### 模块七：基础非线性变换与换手调谐 (Non-Linear Transforms & Execution Control)

#### 25. 时序几何复利累积超额收益 (`ts_product_geometric_compounding`) *(7月后新增)*
* **涉及算子**: `ts_product`, `add`, `group_rank`
* **模板**: `group_rank(ts_product(add({returns_field}, 1), {d}) - 1, {group})`
* **金融语义**: 替代存在线性近似误差的 `ts_sum`，还原真实复利复权收益曲线。

#### 26. 绝对价格跳跃强度与未预期异动 (`abs_price_jump_intensity`) *(7月后新增)*
* **涉及算子**: `abs`, `ts_mean`, `group_rank`
* **模板**: `group_rank(ts_mean(abs({returns_field}), {d}), {group})`
* **金融语义**: `abs(returns)` 剥离涨跌方向，度量价格波动的绝对跳跃幅度，构建微观流动性冲击与波动率因子。

#### 27. 估值乘数倒数与盈利收益率 (`inverse_valuation_yield`)
* **涉及算子**: `inverse`, `add`, `group_rank`
* **模板**: `group_rank(inverse(add({pe_field}, 0.0001)), {group})`
* **金融语义**: P/E 转为 E/P，收敛右侧极端发散分布，改善横截面排序对称性。

#### 28. 对数边际压缩量价冲击 (`log_compressed_shock`)
* **涉及算子**: `log`, `ts_delta`, `group_rank`
* **模板**: `group_rank(ts_delta(log(add({volume_field}, 1)), {d}), {group})`
* **金融语义**: 自然对数压缩成交量的幂律长尾，体现资金边际效用递减规律。

#### 29. 平方根平滑波动率特征 (`sqrt_volatility_scaling`)
* **涉及算子**: `sqrt`, `abs`, `group_rank`
* **模板**: `group_rank(sqrt(abs({variance_field})), {group})`
* **金融语义**: 时间平方根扩散法则还原波动率尺度。

#### 30. 异常值与非池资产防御清洗 (`pasteurize_safety_wrapper`)
* **涉及算子**: `pasteurize`
* **模板**: `pasteurize({alpha_expr})`
* **金融语义**: 将 INF 及非 Universe 资产置为 NaN，防止组合权重异常溢出。

#### 31. 自适应换手率目标动态阻尼 (`ts_target_tvr_hump_controller`)
* **涉及算子**: `ts_target_tvr_hump`
* **模板**: `ts_target_tvr_hump({alpha_expr}, lambda_min={lambda_min}, lambda_max={lambda_max}, target_tvr={target_tvr})`
* **金融语义**: 保持优秀信号逻辑不变的前提下，自适应调控 hump 阻尼，将换手率精准压制至 target_tvr（如 10%）。

#### 32. 放量突破事件交易与持仓锁定 (`trade_when_volume_breakout`) *(7月后新增)*
* **涉及算子**: `trade_when`, `ts_mean`
* **模板**: `trade_when({vol} > ts_mean({vol}, {d}), {signal}, -1)`
* **金融语义**: 仅在放量突破时更新买卖信号，其余时间锁定仓位（`-1`），直击高换手率痛点。

#### 33. 双重市场状态门控条件触发 (`trade_when_dual_regime`)
* **涉及算子**: `trade_when`, `and`, `greater`
* **模板**: `trade_when(and({vol_shock}, {vol_fast} > {vol_slow}), {signal_expr}, -1)`
* **金融语义**: 展示逻辑算子在量化交易中的唯一正统归宿——作为宏观/波动状态机触发条件。

---

## 5. 17 个辅助/语法算子的理性定位（放着不处理的具体原因）

根据用户叮嘱：“实在是没有好的模板，那就不处理，放着即可，要说明一下”。

以下 **17 个算子**在金融逻辑上**绝不具备独立生成 Alpha 超额收益的经济学机理**，我们严格恪守量化研究纪律，**坚决不为凑数而硬造垃圾伪 Alpha 模板**，并给出其“放着不处理”的理性事实与工程定位：

| 算子名 | 底层类别 | 为何坚决不独立编造 Alpha 模板（放着不处理的原因） | 在量化工程中的实际定位 |
| :--- | :--- | :--- | :--- |
| `greater` (`>`) | 逻辑比较 | 仅输出布尔阶跃（0或1），若单独作为 Alpha 会导致多头仅有极少数二值持仓，直接引发单票权重集中度暴雷 (`Max Weight > 10% FAIL`) | 仅用于 `trade_when` 或 `if_else` 的前置条件触发 |
| `less` (`<`) | 逻辑比较 | 同上，单纯小于判断没有截面连续收益预期，单独回测必然产生极端二值阶跃 | 仅用于条件判断（如跌破止损阈值） |
| `greater_equal` (`>=`) | 逻辑比较 | 二值布尔结果，无法衡量资产间连续的相对强弱差距 | 仅用于门控阈值边界判断 |
| `less_equal` (`<=`) | 逻辑比较 | 二值布尔结果，无截面秩排序方差 | 仅用于门控阈值边界判断 |
| `equal` (`==`) | 逻辑判等 | 连续金融价格/指标在浮点数精度下几乎永不相等，单体作为 Alpha 产生全零信号 | 仅用于离散标签的匹配（如特定分类代码判断） |
| `not_equal` (`!=`) | 逻辑不等 | 连续变量几乎恒为 1，无横截面有效信息量 | 仅用于异常常数代码排除 |
| `and` | 逻辑与 | 纯二元布尔组合，单体无法决定投资组合的资产配置比例 | 复合条件状态机（如放量且波动突破）的连结符 |
| `or` | 逻辑或 | 纯二元布尔组合，单独作为 Alpha 信号毫无经济学意义 | 容错型触发条件的连结符 |
| `not` | 逻辑非 | 仅翻转布尔值，不包含任何基本面或量价超额收益预期 | 状态反向门控 |
| `if_else` | 条件分支 | 三元分支算子本身不是信号，而是分支调度器；其价值完全取决于分支内部所填写的 Alpha 表达式 | 作为模式切换容器（如大行业用模型A，小行业用模型B） |
| `is_nan` | 空值判断 | 数据缺失与否本身不构成线性多空超额收益，强行作为 Alpha 属于伪逻辑 | 用于数据清洗、自定义缺失值回填与停牌过滤掩码 |
| `ts_step` | 时序计数器 | 恒定单调自增常数（1, 2, 3...），横截面上所有股票完全相同，完全没有横截面区分度 | 仅用于系统底层时钟对齐或时序回归的时间轴虚拟变量 |
| `vec_count` | 向量长度 | 统计向量非空维度数，在绝大多数金融数据集中为固定物理常数（如 768 或 1024 维） | 仅用于向量数据完整性校验 |
| `power` | 算术乘方 | 针对负数开非整数幂会直接返回数学虚数报错并置为 NaN，极其危险！在 WQ 平台中一律由保留符号的 `signed_power` 替代 | 语法冗余算子，实战中一律被 `signed_power` 淘汰 |
| `sign` | 符号提取 | 仅输出 +1, -1, 0，彻底丢弃了因子的幅度与强弱信息，直接使截面权重变成块状台阶分布 | 仅偶用于信号反转乘子，严禁单独作为 Alpha 信号 |
| `ts_sum` | 时序累加 | 简单累加容易随时间序列发散，且未做时间长度除法，金融分析中通常使用更精准的 `ts_mean` 或几何复利 `ts_product` | 基础运算原材料，放着即可 |
| `ts_returns` | 时序收益率 | 基础收益率计算函数 `(x - delay)/delay`，本质是原始特征的衍生加工器，而非策略模板逻辑 | 作为各动量因子的底层数据输入，无需单独包装假模板 |

---

## 6. 与已有 `factor/templates` 模板的对照与升级

在本次开发前，工作区根目录下已存在 `factor/templates/` 模板文件夹。通过深度对比分析，原有模板存在以下几个明显局限：

1. **原 `all_operator_templates.py` 过于单薄机械**:
   * 大量函数仅是单算子的简单套壳（例如 `ts_quantile(field, d)` 仅返回一行代码），缺少与截面中性化、行业分组、波动率调整的复合嵌套，直接回测容易遭遇 Sub-universe Sharpe 或 Weight Concentration 失败。
2. **缺乏关键参数支持导致语法报错**:
   * 例如 `ts_regression` 原有模板未支持 `rettype` 与 `lag`，无法根据需要选择残差、Beta 还是标准误；
   * `ts_target_tvr_hump` 缺少平台必需的具名参数 `lambda_min=`、`lambda_max=`、`target_tvr=`，直接回测会触发语法报错。
3. **未引入顶级顾问的成熟经验**:
   * 原模板未收录贺六浑的「同向极值匹配」、王哥的「高斯逆映射降相关」、小虎的「残差剥离动量」、SM60004 的「笛卡尔积双重中性化」等实战体系。

在全新的 `factor/templates/unused/` 中，我们不仅补齐了全部 31 个高价值算子的参数化组合，更将参数具名规范与 PLY Lex-Yacc AST 校验机制全面落实，确保拿来即用。

---

## 7. 快速使用与单元测试

### 在 Python 脚本中引入使用
```python
from factor.templates.unused import (
    ts_regression_residual_alpha,
    ts_quantile_gaussian_normalizer,
    ts_corr_pv_divergence,
    group_cartesian_dual_neutralize,
    trade_when_volume_breakout,
    vec_min_extreme_sentiment_reversion
)

# 1. 小虎时序回归残差动量（剥离基准 Beta）
expr1 = ts_regression_residual_alpha(y_field="returns", x_benchmark="market_returns", d=120)
# -> group_rank(ts_regression(returns, market_returns, 120, lag=0, rettype=0), subindustry)

# 2. 点塔王量价时序相关性背离反转
expr2 = ts_corr_pv_divergence(price="close", vol="volume", d=20)
# -> group_rank(-ts_corr(close, volume, 20), subindustry)

# 3. 笛卡尔积双重分组中性化（击穿生产相关性）
expr3 = group_cartesian_dual_neutralize(alpha_signal="ts_zscore(sales / enterprise_value, 60)", group1="industry", group2="country")
# -> group_neutralize(ts_zscore(sales / enterprise_value, 60), group_cartesian_product(industry, country))

# 4. 放量突破事件交易与持仓锁定（大幅压降换手率）
expr4 = trade_when_volume_breakout(signal="group_rank(ts_zscore(close, 20), industry)", vol="volume", d=20)
# -> trade_when(volume > ts_mean(volume, 20), group_rank(ts_zscore(close, 20), industry), -1)
```

### 执行自动化单元测试
我们在 `factor/templates/unused/test_unused_templates.py` 中编写了严格的 AST 语法校验测试：
```bash
python factor/templates/unused/test_unused_templates.py
```
**测试结果**: 33 个模板函数全部通过本地 PLY Lex-Yacc AST 语法校验，**PASS 率 100% (33/33)**。
