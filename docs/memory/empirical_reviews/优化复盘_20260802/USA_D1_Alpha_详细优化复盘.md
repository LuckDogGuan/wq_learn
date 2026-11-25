# USA / D1 / REGULAR Alpha 挖掘：详细优化过程与结论

更新时间：2026-08-02  
工作范围：USA、EQUITY、D1、REGULAR、`max_trade=OFF`、P2Y、单数据集、1–2 个字段、操作符数量小于 6。  
提交边界：没有调用 `submit_alpha`，没有自动提交，没有创建自动化任务；Alpha 提交仍由用户手动完成。

## 1. 先说结论

这轮工作不是“没有认真测试”，而是同时遇到了两类问题：

1. 平台层面有 429 限流、300 秒超时、子模拟取消和“完成后无 Alpha ID”。这些批次只能判定为 `PENDING` 或 `RESULTS_UNOBSERVED`，不能拿来证明字段好或坏。
2. 对已经真正落库、并且指标可观察的 Alpha，最常见的失败不是 Fitness，而是 2Y Sharpe 和风险中性化表现。很多表达式在 IS 上看起来不错，经过风险中性化后收益消失，或者只在训练期有效。

截至当前进度文件：

- 已记录 80 个批次段落、67 个不同数据集。
- 按每批最多 8 条表达式计算，名义测试规模约 640 条表达式；但其中有待定、超时、无 Alpha ID 和表达式错误，不能把 640 条都当作有效 Alpha 结果。
- 已确认的 Alpha 均为 `UNSUBMITTED`；没有任何 Alpha 同时通过全部基础门槛，因此没有进入 robust、严格过拟合、生产相关性或属性设置。
- 当前没有 `READY_TO_SUBMIT` Alpha，也没有可以安全提交的候选。

目标硬门槛是：

| 检查项 | 要求 |
|---|---:|
| IS Sharpe | `>1.58` |
| IS Fitness | `>1` |
| 2Y Sharpe | `>1.6` |
| Margin | `>10bp` |
| Turnover | `>5%` 且 `<30%` |
| 风险中性 Sharpe | `>1` |
| 风险中性 Fitness | `>0.7` |
| 风险中性 Margin | `>10bp` |
| 操作符数 | `<6` |
| 数据使用 | 单数据集、1–2 字段 |
| 相关性 | 候选相关性 `<0.4`；生产相关性必须明确且不超过 `0.7` |

注意：平台 Margin 原始值是小数。例如 `0.012267 = 122.67bp`，不是 0.012267bp。

## 2. 实际采用的优化流程

### 2.1 字段筛选

先读取平台数据集和字段清单，优先选择：

- 金字塔倍率较高、字段 `alphaCount=0` 或使用量很低的数据集；
- 覆盖率高、定义清楚、可以解释收益来源的字段；
- 和已经失败的新闻情绪、短卖压力、普通分析师预测不同的收益来源；
- 同一批只用 1–2 个字段，避免把多个数据集混在一起。

### 2.2 表达式模板

每批固定 8 个表达式，主要比较：

- 横截面水平：`rank(field)`；
- 20 日变化：`rank(ts_delta(field,20))`；
- 20 日均值：`rank(ts_mean(field,20))`；
- 20 日线性衰减：`rank(ts_decay_linear(field,20))`；
- 滚动标准化：`rank(ts_zscore(field,20))`；
- 均值差：`rank(ts_av_diff(field,20))`；
- 时间序列排名和最小值：`rank(ts_rank(field,20))`、`rank(ts_min(field,20))`；
- VECTOR 字段先用 `vec_avg`，例如 `rank(vec_avg(field))`。

没有使用 `trade_when`、`add`、`multiply`。一次 `hump(rank(field),0.01)` 出现“需要 1 个输入、收到 2 个”的表达式错误，之后移除了这个写法。

### 2.3 质量闸门

顺序一直是：

1. 先确认 Alpha 是否真的落库；
2. 再检查 IS Sharpe、Fitness、2Y Sharpe、Margin、Turnover；
3. 再检查风险中性 Sharpe/Fitness/Margin；
4. 只有全部基础门槛通过，才允许 robust、严格过拟合、生产相关性和属性设置；
5. 生产相关性缺失或大于 0.7，直接排除；
6. 最终提交由用户手动完成。

因此，很多 Alpha 的 `PROD_CORRELATION=PENDING` 并不代表它有机会提交，因为它们在更早的基础门槛已经失败。

## 3. 代表性 Alpha 的逐条复盘

以下例子选自近期有完整 Alpha ID 和指标的批次。它们说明了“看起来局部很好”为什么仍然不能提交。

### 3.1 `equity_kpi_forecast`：IS Fitness/Margin 好，但风险中性化完全消失

字段：`forecast_consensus_surprise_percent`、`directional_confidence_flag`，VECTOR，覆盖率约 0.365–0.380，均为 `alphaCount=0`。  
Multisim：`214Qyq3Lf5a68J1TlwRcpO7`。

| Alpha ID | 表达式 | IS Sharpe | Fitness | Turnover | Margin | 2Y Sharpe | RN Sharpe / Fitness | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `88pmPQQo` | `rank(vec_avg(forecast_consensus_surprise_percent))` | 0.98 | 1.66 | 5.85% | 122.67bp | 0.10 | -0.03 / 0.00 | Sharpe、2Y、RN 失败 |
| `KPGKr9Gk` | `rank(ts_decay_linear(vec_avg(directional_confidence_flag),20))` | 0.99 | 1.67 | 8.16% | 87.17bp | 0.02 | 0.63 / 0.21 | Fitness/Margin/换手局部合格，但核心失败 |
| `LLGPZ1da` | `rank(ts_zscore(vec_avg(directional_confidence_flag),20))` | 1.09 | 1.40 | 24.22% | 32.86bp | 0.21 | 0.41 / 0.11 | 最接近基础 Sharpe，但仍远低于 1.58 |

优化方向：

- 已尝试 `vec_avg`、z-score、20 日均值和衰减；
- 均值/衰减确实能把换手压到 5%–30%，并抬高 Fitness/Margin；
- 但风险中性 Sharpe 最高只有 0.63，2Y Sharpe 最高 0.21；
- 结论：优化“有效地改善了局部指标”，但没有改善真正的提交条件。该字段族目前不值得继续做参数美容。

### 3.2 `global_seasonal_model` / TOP3000：事件置信度 IS 尚可，2Y 不延续

字段：`confidence_bucket3_timeseries_event_5d`、`daily_pricevol_12m_r20_quantile1_prob`，覆盖率约 0.997，均为 `alphaCount=0`。  
Multisim：`4xCy5Tey14VJ8O1woAZKqes`。

| Alpha ID | 表达式 | IS Sharpe | Fitness | Turnover | Margin | 2Y Sharpe | RN Sharpe / Fitness |
|---|---|---:|---:|---:|---:|---:|---:|
| `GreR9PXG` | `rank(confidence_bucket3_timeseries_event_5d)` | 0.65 | 0.75 | 22.47% | 26.47bp | -0.01 | 1.75 / 0.51 |
| `KPE1Z3zk` | `rank(ts_decay_linear(confidence_bucket3_timeseries_event_5d,20))` | 0.60 | 0.89 | 4.52% | 120.97bp | -0.06 | 0.63 / 0.14 |
| `O0x3gOzv` | `rank(ts_mean(daily_pricevol_12m_r20_quantile1_prob,20))` | 0.56 | 0.77 | 6.04% | 78.10bp | -0.02 | -1.26 / -0.38 |

优化方向：

- 原始事件置信度的风险中性 Sharpe 达到 1.75，是本批次的局部亮点；
- 但是基础 Sharpe 只有 0.65，2Y Sharpe 接近 0，风险中性 Fitness 只有 0.51；
- 衰减显著改善了换手和 Margin，却把换手压到 5% 以下；
- 结论：风险中性局部有效，但不能弥补 IS 和 2Y 失败。该模型只能作为“风险中性有信号、但不可提交”的研究样本。

### 3.3 `global_seasonal_model` / TOP1000：Fitness/Margin 上升，但风险中性更差

Multisim：`3Jo8ZE7oh59g9Dr4QRgzfiF`。字段是 `confidence_bucket2_timeseries_regime_5d` 与 `opt_20d_return_quantile3_confscore`。

| Alpha ID | 表达式 | IS Sharpe | Fitness | Turnover | Margin | 2Y Sharpe | RN Sharpe / Fitness |
|---|---|---:|---:|---:|---:|---:|---:|
| `GreR9QOx` | `rank(ts_mean(confidence_bucket2_timeseries_regime_5d,20))` | 0.77 | 1.19 | 2.89% | 207.18bp | 0.06 | 0.24 / 0.03 |
| `A17AELQY` | `rank(ts_decay_linear(confidence_bucket2_timeseries_regime_5d,20))` | 0.76 | 1.16 | 3.41% | 172.05bp | 0.05 | 0.00 / 0.00 |
| `xAdZ5l1n` | `rank(ts_decay_linear(opt_20d_return_quantile3_confscore,20))` | 0.67 | 1.00 | 7.56% | 73.00bp | 0.03 | -0.54 / -0.12 |

优化方向是否有效：

- 对 IS Fitness、Margin 和低换手有效；
- 对 IS Sharpe、2Y Sharpe、风险中性化无效；
- 说明平滑在这里是在“降低交易频率”，不是在创造稳定预测收益；
- 结论：不再把低换手高 Fitness 当成成功信号，除非 2Y 和风险中性同时改善。

### 3.4 `board_network`：先有表达式错误，修正后仍然失败

数据集：`board_network`，字段 `mean_connection_significance_score`、`network_eigenvector_centrality_metric`。  
错误批次：`3R4MI140H4mC9Cr19APqHDk0`。  
错误原因：`hump(rank(field),0.01)` 的参数形式不合法，平台报告“需要 1 个输入、收到 2 个”。这不是字段质量结论，而是模板错误。

修正批次：`2j8d28ed75cBaVmg1Uy95Iy`。

| Alpha ID | 表达式 | IS Sharpe | Fitness | Turnover | Margin | 2Y Sharpe | RN Sharpe / Fitness |
|---|---|---:|---:|---:|---:|---:|---:|
| `xAdZG6rq` | `rank(mean_connection_significance_score)` | -0.07 | -0.02 | 9.61% | -1.26bp | -1.29 | 0.93 / 0.54 |
| `mLVv73a9` | `rank(ts_mean(network_eigenvector_centrality_metric,20))` | 0.50 | 0.62 | 7.13% | 53.42bp | -0.22 | 0.26 / 0.08 |
| `e7xjGpaN` | `rank(ts_delta(network_eigenvector_centrality_metric,20))` | -0.48 | -0.16 | 1.68% | -15.93bp | -1.36 | 0.35 / 0.07 |

优化方向：

- 修正表达式后，平台可正常运行，说明问题确实在模板而不是接口；
- 均值模板可以把换手放进 5%–30%，但 2Y 仍为负；
- 结论：表达式错误修正有效，但策略优化无效；董事网络字段不再扩展。

### 3.5 `analyst_revision_horizons`：低换手版本仍没有延续性

第一批字段：`analyst_revision_score_change_30d_long`、`stock_global_percentile_rank_long`。  
对账 Alpha：`N1RZeNoo`、`zqRVr3zR`、`QP98Yvdg`、`9q7nExoq`、`WjV5LOkd`、`wpEr9Q6Y`、`omgdoE2k`、`3qeNjogZ`。

| Alpha ID | 表达式 | IS Sharpe | Fitness | Turnover | Margin | 2Y Sharpe | RN Sharpe / Fitness |
|---|---|---:|---:|---:|---:|---:|---:|
| `N1RZeNoo` | `rank(analyst_revision_score_change_30d_long)` | 0.60 | 0.46 | 41.04% | 11.62bp | -0.04 | 0.41 / 0.04 |
| `zqRVr3zR` | `rank(stock_global_percentile_rank_long)` | 0.62 | 0.65 | 21.75% | 22.29bp | -0.05 | 1.07 / 0.23 |
| `WjV5LOkd` | `rank(ts_mean(analyst_revision_score_change_30d_long,20))` | 0.60 | 0.83 | 3.84% | 123.65bp | -0.02 | 0.24 / 0.03 |

结论：`ts_mean` 对换手和 Margin 有效，对 2Y 和风险中性无效；原始版本甚至出现高换手。该字段族暂时停止继续扩展。

## 4. 更早批次的整体结果

### 4.1 盈利质量/现金流：有局部 Margin，没有交易效率组合

`sustainable_profit` 已完成多个批次，覆盖现金回报、盈利能力、利润增长、资产增长、杠杆变化和财务费用覆盖等字段。最佳基础 Sharpe 约 0.70，`gross_profitability_operating_assets` 的 Margin 最高约 11.30bp，但换手约 0.5%，低于 5%；风险中性 Sharpe 最高约 0.48。结论是“收益方向有弱信号，但不可交易/不可提交”。

### 4.2 新闻情绪/文本：覆盖率高，但高频噪声明显

`news_sentiment_dl` 覆盖率约 0.9998，但原始信号换手约 109%–138%，Sharpe 约 0.59–0.64；长窗口、平滑和 hump 版本仍有约 108%–129% 换手，风险中性 Sharpe 最高约 0.11。  
`news_sentiment_transfer` 的换手约 31.8%–93.6%，Sharpe 约 0.62–0.69。  
结论：平滑没有把新闻族同时变成低换手、高 Sharpe、强 2Y 的策略，停止参数美容。

### 4.3 `quant_factor_lib`：换手合格，但 Margin 和风险中性化不足

该数据集覆盖信用综合分、implied alpha、Merton/Altman/CHS、偿债比率、破产压力和利率字段，并在 TOP3000/TOP2000 复测：

- 换手大多约 9%–27%，是少数交易频率合格的字段族；
- Sharpe 最高约 0.92；
- Fitness 最高约 1.72；
- Margin 最高约 0.86bp，远低于 10bp；
- 2Y Sharpe 最高约 0.19；
- 风险中性 Sharpe 最高约 0.18。

结论：收益来源稳定但弱，继续换字段或换窗口的预期收益低，暂时停止。

### 4.4 短卖、订单流、期权和图形预测：短期噪声或换手失控

- `us_short_sale`：原始换手约 41%–54%，平滑后最低约 5.57%，但 Sharpe 0.50、Fitness 0.64、Margin 0.73bp、2Y -0.11，风险中性 Sharpe 约 -0.52。
- `order_flow_imb`：换手约 46.62%–83.70%，Sharpe 0.49–0.60，2Y 为负，风险中性最高约 0.95。
- `option3`：Sharpe 0.46–0.66，换手 2.88%–35.34%；某个 ATM call IV z-score 风险中性 Sharpe 1.81，但基础 Sharpe、2Y 和 Margin 不足。
- `pattern_scores`：换手 3.08%–11.00%，Sharpe 0.50–0.66，2Y 为负；风险中性最高约 1.57，仍未超过 1。
- `event_return_model`：唯一进入换手区间的表达式为 `rank(ts_decay_linear(winsorize(prob_rank_bin1_5d_img_news),20))`，换手 10.62%、Sharpe 0.61、Fitness 0.86、Margin 4.69bp、2Y 0，风险中性 Sharpe 1.03；依然无法通过基础门槛。

这些结果说明“风险中性 Sharpe 单项较好”不能代替基础 Sharpe、2Y 和 Margin。

### 4.5 分析师、内部人、社交和另类数据：局部指标有亮点，组合门槛仍失败

- `analyst_base_ref`：Sharpe 0.57–0.66，Fitness 0.21–0.26，换手约 176%–189%，风险中性 Sharpe -0.44 至 0.04。
- `mfm_model_output`：Sharpe 0.56–0.63，Fitness 0.77–0.91；`hedge_fund_ownership_factor1` 的风险中性 Sharpe 最高 1.25，但基础 Sharpe、2Y、Margin 仍失败。
- `fund_holdings_panel`：基础 Sharpe 0.61–0.73，风险中性最高 1.99，但换手、Margin 或 2Y 不足。
- `macro63`：低换手 0.22%–2.75%，但 Sharpe 0.14–0.61，2Y 为负。
- `socialmedia8`、`ai_news_scores`、`finnews_nlp_scores` 等新闻/社交字段普遍表现为高换手、低 2Y、弱风险中性化。
- `analyst10`、`ai_equity_alpha`、`web_traffic_engage` 等模型/分析师字段有些 Fitness 或风险中性 Sharpe 亮点，但基础 Sharpe和 2Y 不能同时通过。

## 5. 哪些优化有效，哪些无效

| 优化方法 | 对什么有效 | 对什么无效 | 最终判断 |
|---|---|---|---|
| `ts_mean` | 降低换手、提高部分 IS Fitness/Margin | 2Y Sharpe、风险中性化 | 只作预筛选，不是通过证明 |
| `ts_decay_linear` | 降低短期噪声和换手 | 经常把换手压到 5% 以下，2Y仍弱 | 局部有效 |
| `ts_zscore` | 有时提升风险中性 Sharpe或区分度 | 常导致换手上升，2Y不稳定 | 需谨慎 |
| `ts_delta` | 能测试事件变化和新信息 | 很多字段变成高频噪声 | 对新闻/关系字段多为无效 |
| `vec_avg` | 让 VECTOR 字段可以合法进入表达式 | 不自动创造收益 | 必要预处理，不是 alpha 优化 |
| `hump` | 理论上可限制交易变化 | 错误参数会导致模拟失败；当前没有稳定收益证据 | 暂停使用该写法 |
| 换 universe | 能识别 TOP3000/TOP1000/TOP500 的稳定性差异 | 没有把 2Y 和风险中性同时推过门槛 | 用于验证，不当作优化本身 |
| 换数据集 | 增加风格和金字塔覆盖 | 目前尚未找到硬门槛通过者 | 必须基于收益来源切换 |
| 论坛模板 | 可提供方向和算子思路 | 部分论坛正文读取失败，不能替代实时回测 | 只作启发，不作证据 |

## 6. 为什么目标会受阻

### 平台原因

- 多次返回 `429`，必须暂停 5 分钟；
- 多次等待 300 秒超时；
- 有些 multisim 显示成功，但子模拟没有 Alpha ID；
- 有些子模拟被取消或返回 `HTTP 504`；
- 这些结果不能当作字段失败，也不能重复创建，否则会污染实验记录。

### 策略原因

- 2Y Sharpe 几乎普遍远低于 1.6，是最稳定的硬伤；
- 风险中性化后收益常消失，说明收益可能只是市场、行业、规模或其他暴露；
- 平滑虽然改善换手和 Margin，却经常降低 Sharpe 或把换手压到 5% 以下；
- 原始新闻、关系和短期预测字段经常超过 30% 换手；
- 低覆盖率 VECTOR/KPI 字段容易出现持仓集中、单边多头和样本不稳定；
- IS 指标和 test/2Y 指标不一致，存在明显过拟合或收益衰减。

### 流程原因

- 生产相关性在基础门槛失败时没有必要继续查询；
- 因此当前没有生产相关性结果，不表示 Alpha 合格，而是更早已被淘汰；
- 没有任何候选满足“基础门槛 → robust → 严格过拟合 → 生产相关性 → 属性设置”的完整链路。

## 7. “200 个因子仍无结果就判定垃圾字段”的正式规则

从现在开始按以下规则执行，避免无限重复调参：

### 7.1 计数方式

- “200 个”按同一字段的**有效、可观测、已完成回测 Alpha**计数；
- 每个 Alpha 必须有 Alpha ID、完整 IS/2Y/风险中性指标；
- `PENDING`、`RESULTS_UNOBSERVED`、429、超时、无 Alpha ID、表达式错误不计入 200；
- 同一表达式重复创建不计为新的因子；仅改变无意义参数也不计为真正的新策略风格；
- 应至少覆盖多个合理骨架和一个以上 universe，避免把某一次平台故障误判为字段垃圾。

### 7.2 判定条件

如果同一字段经过最多 200 个有效 Alpha 测试，仍没有一个同时达到：

- IS Sharpe >1.58；
- Fitness >1；
- 2Y Sharpe >1.6；
- Margin >10bp；
- Turnover 5%–30%；
- 风险中性 Sharpe >1、Fitness >0.7、Margin >10bp；
- 操作符数 <6，单数据集，生产相关性明确且不超过 0.7；

则将该字段标记为：

> `FIELD_VERDICT = GARBAGE_CANDIDATE`

含义是：在当前 USA/D1/REGULAR 研究范围内，继续投入时间的预期收益过低，停止该字段族扩展，转向新的金字塔/数据集。它不是数学上证明字段永远无效，而是一个有实验预算约束的工程结论。

### 7.3 目前的提前停止字段族

以下字段族尚未必都达到 200 个有效 Alpha，但已经出现清晰的失败模式，因此先停止扩展，不能伪称已经达到“200 个垃圾字段”标准：

- 新闻情绪/新闻 NLP：高换手、短期噪声；
- 关系强度/董事网络：集中度高、2Y 弱、风险中性化差；
- `quant_factor_lib`：换手合格但 Margin、2Y、风险中性化长期不足；
- 短卖/订单流：高换手或低 Sharpe；
- 事件预测：局部风险中性改善，但基础 Sharpe、2Y、Margin 不足；
- 低覆盖率 KPI：IS Fitness/Margin 好看，但风险中性后收益消失。

这些是“当前阶段停止扩展”，不是“已达到 100 条后的正式垃圾字段判定”。

## 8. 后续建议

1. 新数据集第一批仍用 8 条表达式，但先把字段覆盖率、数据类型、潜在集中度和预期换手记录下来。
2. 第一轮就优先淘汰明显高换手（>30%）和明显低换手（<5%）字段，节省平台调用。
3. 对每个字段保留一个原始版本、一个均值版本、一个衰减版本和一个 z-score 版本，避免 8 条表达式只是重复美容。
4. 只要 IS Sharpe、2Y Sharpe 或风险中性 Fitness 明显失败，就不要调用 robust、过拟合和生产相关性接口。
5. 只有全部基础门槛通过，才建立候选表，并记录 Alpha ID、表达式、单数据集分类、风险中性指标、候选相关性和生产相关性。
6. 任何平台故障继续按“冷却 5 分钟 → 唯一对账 → 保留状态 → 不重复创建”执行。
7. 每 10 个有效批次更新一次多样性复盘；每个字段累计 200 个有效 Alpha 仍无合格结果时，执行 `FIELD_VERDICT = GARBAGE_CANDIDATE`，并停止该字段；同一数据集再按字段结果汇总是否 `STOP_DATASET`。

操作符不参与淘汰，只在登记表中记录其与字段的实验组合、表达式和结果。

## 9. 最终状态

- 合格可提交 Alpha：0。
- 已进入 robust/严格过拟合的 Alpha：0。
- 已设置属性的 Alpha：0。
- 已提交 Alpha：0。
- 自动化任务：0。
- 当前结论：继续挖掘，但必须从新的、未重复且收益来源不同的数据集或 universe 开始；不能把局部高 Fitness、局部高 Margin 或单项风险中性 Sharpe 当作成功。
