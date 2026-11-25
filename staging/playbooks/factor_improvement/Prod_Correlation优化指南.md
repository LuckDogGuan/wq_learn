# Prod Correlation 过高优化指南

基于 WorldQuant Brain 黄金顾问团（wq-top-advisors-skill）的实战经验总结，针对提交因子时遇到的 Prod Correlation 过高问题，可以采取以下核心优化手段：

## 1. 调整中性化设置 (Neutralization)
这是顾问们最推荐且行之有效的首选方法。
- **尝试不同的中性化类别**：在系统设置中切换不同的 Neutralization 选项（如 Industry, Subindustry, Sector, Market 等）。
- **使用冷门风格中性化**：在特定地区（例如 ASI 亚太地区），尝试使用 `slow_factors` 等风格的中性化。据测试，这类中性化使用人数较少，能有效避开拥挤交易，极大提高通过率（来源：顾问 XW35731）。
- **行业与市值的双重中性化**：未中性化的因子容易在小盘股或特定高波动行业上产生过度暴露。建议在代码中利用 `group_neutralize` 显式剔除行业（`indclass`）和市值（`cap`）等因素的影响，提取纯粹的 Alpha，这能立竿见影地降低与公共库因子的相关性（来源：顾问 QP72475 点塔王）。

## 2. 利用 Group 操作符重构信号
- **多维度分组处理**：使用不同于常规的基准字段对数据进行分组，并配合 `group_rank` 或 `group_neutralize` 操作符进行处理。这不仅有助于降低高频波动带来的 Turnover，还能通过改变横截面特征显著降低 Prod Correlation（来源：顾问 SM60004）。

## 3. 调整时间平滑与衰减参数 (Decay)
- **改变 Decay 设置**：因子末端的平滑处理会很大程度决定它的形态。适当微调 Decay 的数值，或者利用平滑滚动信号（如 `ts_mean(ts_rank(x, day), day)`），可以改变因子曲线的频域特征，从而“错开”与公共池高相关因子的波峰波谷。

## 4. 控制模板“探索度”，避免同源同质化
- **降低单模板的参数发散**：很多常规模板（通过暴力遍历时间参数和操作符）跑出来的 Alpha 往往结构高度相似，很容易“死成一片”。建议固定时间参数和外层操作符（将探索度降为 1），以小参数空间挖掘微弱基础信号，避免在同一个无价值或拥挤的字段上浪费算力，进而减少相关性报错（来源：顾问 LW67640 小虎）。
- **利用 LLM (大模型) 介入生成变体**：代码生成的模板过于刚性（Rigid），容易导致生成的变体互相之间相关性极高。引入大模型（如 GPT）进行细微的 AST 替换（如颠倒操作符顺序、`ts_rank` 与 `rank` 巧妙转换）、或者做“风格控制与逻辑评估”，可以在生成阶段打破结构重复，从根源上降低废稿率（来源：顾问 LW67640、MH33574）。

## 5. ⚠️ 特别注意：PPAC 比赛中的隐藏报错机制
- **报错可能是被“借壳”了**：如果你在提交 Power Pool Alpha 时（已知 PPAC 规则豁免 Prod Correlation 检查），却依然收到类似于 “Prod correlation 0.93 is above cutoff of 0.7” 的 FAIL 提示，**请不要盲目去降 Prod Correlation**。
- **真正原因**：这通常是因为你的 Alpha 与系统中**已标记为 Power Pool 的 Alpha 相关系数超过了 0.5 的阈值**。系统未能正确返回 Power Pool 相关性超标的错误，而是借用了 Prod Correlation 的报错模板。此时应该去检查 Self-Correlation（来源：顾问 JR23144 贺六浑）。

## 6. 进阶操作符运用 (来自社区高质量分享)
如果常规参数调整无法降相关性，可尝试通过特定的数学或时间序列算子，进行**非线性映射**或**降维打击**：
- **`ts_arg_max` / `ts_arg_min`**：跳出绝对数值，用“时间距离”丈量市场记忆。量价因子传统上只用当天的量乘当天的价，通过 `ts_arg_max` 寻找一段时间内极值点出现的位置（天数倒数），可以巧妙避开同质化逻辑。
- **`ts_median`**：对抗极端胖尾。挖掘隐藏的偏度 (Skewness) Alpha，相比容易被极端值主导的 `ts_mean`，中位数逻辑生成的相关性显著更低。
- **`hump`**：限制 alpha 因子的变化率，在降低 turnover 的同时，也由于其特殊的滞后保留机制（t 日与 t-1 日变动过小则保留原值），有时能间接降低 Prod Correlation。
- **`normalize` 和指数运算**：对信号进行标准化，或使用指数运算 `power(x, exp)` 调整其分布形状。

## 7. 构建低相关 Alpha 组合 (Super Alpha 视角)
如果你在构建 SA 时发现整体 Prod Corr 偏高，可参考以下“单一信号到信号网络”的经验：
- **条件叠加**：`multiply(mind_shield_diff, ts_corr(mind_shield_diff, ts_mean(mind_shield_diff, 10), 5))` 这种条件叠加方式能显著降低相关性，因为它引入了额外的决策维度。
- **前移检查**：在 SA 的 Selection 阶段，直接在提取逻辑中加入 `(prod_correlation < 0.6) && (prod_correlation > 0.1)`，这样不仅提高合成后的通过率，也能避免 Combo 内组件“撞车”。
- **非线性重度去相关打分**：构造打分因子时，使用非线性函数惩罚高相关性组件，如 `1 / (power(prod_correlation, 2) + 0.05)`，比纯线性的 `(1 - prod_correlation)` 更能在组合层面抑制高相关。

## 8. 实盘测试验证记录 (持续更新)
为了验证社区中讨论的各类“降 PC 算子”的真实效果，我们选取了基础 Prod Corr 偏高（约 0.6569）的因子（基准：`ts_target_tvr_decay(winsorize(ts_ir(avg_pct_change_estimate_quarter_revenue_7d,22)), lambda_min=0, lambda_max=1, target_tvr=0.20)`）进行对照实验：

- **`ts_arg_max` 操作符**：【✅ 有效】
  * **实验**：使用 `rank(ts_arg_max(inner, 10))` 替代原有数值逻辑。
  * **结果**：Prod Correlation 从 **0.6569** 暴降至 **0.3700**！
  * **结论**：极度破坏了原有同质化信号的结构，去相关效果极其显著。但需注意，该算子会大幅度改变信号本质（例如从基本面数值变为极值距离），可能导致原本的 Sharpe 坍塌。后续挖掘需要**重点关注**在保证逻辑成立的前提下使用 `ts_arg_max`。

- **`normalize` 操作符**：【❌ 无明显效果】
  * **实验**：在信号外层包裹 `normalize(inner)`。
  * **结果**：Prod Correlation 依然是 **0.6569**，毫无变化。
  * **结论**：系统在评估截面相关性时本身就会进行类似的排位/标准化处理，仅做线性的 `normalize` 无法实现去相关。

- **`group_neutralize` 与 `hump`**：
  * **实验**：尝试手动剔除 `cap`、`indclass` 以及使用 `hump` 降频。
  * **结果**：部分设置在当前 EUR 市场下直接引发了 Simulation Error（报错）。
  * **结论**：在使用高阶算子时，必须严格遵守底层数据字典的限制（例如 EUR 市场是否支持特定的分组字段，`hump` 的参数边界等）。

- **`subindustry` 中性化替换 `sector` (细粒度中性化)**：【✅ 极度有效 / 低损首选】
  * **原始因子**：`1YzlrjQJ` (PC = **0.7221**, Sharpe = 1.65, Fitness = 1.08)
  * **实验因子**：`RR1zRdVa` (`group_neutralize(ts_zscore(eps / close, 252) - ts_zscore(cashflow_fin / cap, 252), subindustry)`)
  * **结果**：Sharpe 飙升至 **1.78**，Fitness 1.10，且 Prod Correlation 成功降至 **0.6476**（成功降至 0.7 阈值以下）！
  * **结论**：将行业中性化（sector）切换为更细维度的子行业中性化（subindustry），不仅能大幅提升基本面策略的 Sharpe（因为在同细分行业内选股更纯粹），而且能有效与平台大盘因子去共线性，是最优的低损耗降相关手段。

- **非线性映射 `sign(x)*power(x,2)`**：【〽️ 有效降相关，但严重损耗收益】
  * **原始因子**：`1YzlrjQJ` (PC = **0.7221**, Sharpe = 1.65)
  * **实验因子**：`LLdzLk99` (`group_neutralize(sign(X)*power(X,2), sector)`)
  * **结果**：Prod Correlation 降至 **0.6540**（低于 0.7），但 Sharpe 暴跌至 **1.25**，Fitness 降至 0.85，未通过硬门槛。
  * **结论**：虽然非线性映射能有效破坏信号分布从而规避线性相关性惩罚，但对已经高度标准化的截面因子，平方映射会破坏原有的线性预测逻辑，导致 Sharpe/Fitness 严重受损，仅能在 Sharpe 空间极大的因子上作为备选。

- **加入时序平滑 `ts_decay_linear`**：【❌ 负优化 / 对基本面因子不适用】
  * **原始因子**：`1YzlrjQJ` (PC = **0.7221**, Sharpe = 1.65)
  * **实验因子**：`Vk3zkO65` (`ts_decay_linear(group_neutralize(X, sector), 10)`)
  * **结果**：Prod Correlation 不降反升至 **0.7273**，且 Sharpe 降至 **1.33**，未通过硬门槛。
  * **结论**：对于更新缓慢、本身即是慢变量的财务基本面因子，强行施加 10 日时序平滑不仅会滞后信号导致夏普受损，更会使其与平台中同样经过时序平滑处理的大量慢因子产生更高的共线共振，导致相关性上升。

- **时序极值距离 `ts_arg_max` 强行转换**：【❌ 逻辑崩溃】
  * **原始因子**：`1YzlrjQJ` (PC = **0.7221**, Sharpe = 1.65)
  * **实验因子**：`e7xG7Lbl` (`group_neutralize(ts_arg_max(X, 10), sector)`)
  * **结果**：Sharpe 反转为 **-0.91**，逻辑崩溃。
  * **结论**：极值出现天数完全偏离了企业基本面价值比较 of the economic meaning, causing the strategy to fail completely.

- **GLB 市场 Subindustry 复合去相关与一致预期**：【✅ 极度有效 / 获得 Golden Alpha】
  * **实验背景**：GLB 市场单独测试传统基本面或单因子时易面临 PC 超标或收益匮乏的问题。我们尝试将 Actual Trailing 财务/质量指标与 Forward 分析师一致预期进行复合，并引入 `subindustry` 细粒度中性化。
  * **实验结果与优化记录**：
    1. **`O0xzG77v` (EBITDA Yield + ROA Subindustry)**:
       * **公式**：`group_neutralize(ts_zscore(ebitda_quarterly / cap, 252) + ts_zscore(fnd28_a_value_08326, 252), subindustry)`
       * **性能**：Sharpe 1.27, Margin 6.04bp, **PC 0.5742** (成功突破)
    2. **`bldz8X5p` (SmartEst FY2 EP Yield + ROA Subindustry)**:
       * **公式**：`group_neutralize(ts_zscore(mdl30_smartestimate_fy2_eps / close, 252) + ts_zscore(fnd28_a_value_08326, 252), subindustry)`
       * **性能**：Sharpe 1.49, Margin 7.01bp, **PC 0.6787** (成功突破)
    3. **`1YzKWwGm` (FY1 Smart CPS Yield + ROA Subindustry)**:
       * **公式**：`group_neutralize(ts_zscore(anl10_cpsfy1_smart_ests_v2_6267 / close, 252) + ts_zscore(fnd28_a_value_08326, 252), subindustry)`
       * **性能**：Sharpe 1.26, Margin 5.77bp, **PC 0.6085** (成功突破)
    4. **`Jjvz87oe` (FY1 Consensus CPS Yield + ROA Subindustry)**:
       * **公式**：`group_neutralize(ts_zscore(anl10_cpsfy1_consensus_6271 / close, 252) + ts_zscore(fnd28_a_value_08326, 252), subindustry)`
       * **性能**：Sharpe 1.25, Margin 5.88bp, **PC 0.6084** (成功突破)
  * **结论**：将 trailing 实际财务数据或 forward 预期收益/现金流指标与质量指标复合，并在细化的 `subindustry` 维度上中性化，是 GLB 市场兼顾夏普、稳定换手且打破 PC 限制的最优打法。


## 9. 自动化 PC 校验与降维重投循环 (推荐实战流程)
在实战挖掘中，我们应该将 PC 校验作为流水线的**最后一环闭环逻辑**。一旦挖掘出 Sharpe > 1.6 的优质因子，必须先提交进行 Prod Correlation 校验：
1. **获取 PC 值**：如果 PC < 0.70，直接入库准备构造 Super Alpha。
2. **触发优化回调**：如果发现 PC ≥ 0.70（例如测试中遇到的 `1YzlrjQJ` 因子 PC 高达 0.72），则**不要直接丢弃**，而是进入“降维重投”池。
3. **多维变异重投**：对该因子进行一组正交变异（如切换为 `subindustry` 中性化、套用 `sign(x)*power(x,2)` 非线性映射、叠加 `ts_decay_linear(x,10)` 等），并行发起仿真。
4. **截取新结果**：在保留 Sharpe > 1.2（适当放宽门槛）的变异体中，重新筛选出 PC < 0.70 的幸存者，从而把原本同质化废弃的“边角料”抢救成低相关的 Alpha 拼图！
