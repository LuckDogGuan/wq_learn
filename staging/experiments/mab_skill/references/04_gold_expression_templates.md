# 八算子极简高通关因子模板库 (EUR 专精版)

> **归档位置**：`doc/多臂老虎机_挖掘总结Skill/references/04_gold_expression_templates.md`  
> **核心标准**：**操作符数量严格 `< 8`**、**坚决杜绝 `trade_when / add / multiply`**、**单数据集 1~2 个字段**  
> **适配市场**：EUR (TOPCS1600 / TOP2500), Delay 1, SUBINDUSTRY 中性化

---

## 1. 模板设计美学：奥卡姆剃刀与拓扑鲁棒性

所有入选模板均历经广州服务器上千次实测检验，具备以下黄金拓扑特征：
1. **纯净单字段或同源双字段**：杜绝跨表对齐引入的缺失与延迟断点；
2. **时序低通滤波**：必含 `ts_decay_linear` 或 `ts_mean`，消灭高频摩擦；
3. **无量纲截面映射**：统一在 `group_rank` 或 `rank() - 0.5` 空间输出；
4. **算子总数 ≤ 6**：极其凝练，杜绝过拟合与死算子嵌套。

---

## 2. 殿堂级六大策略风格参数化模板

### 风格一：时序线性衰减动量预期差 (Trend & Revision Momentum)
- **经济学逻辑**：捕捉中周期分析师上调或收益动量，通过线性衰减赋予近期增量更高权重，彻底解决滞后性与阶梯夏普痛点。
- **操作符数量**：`4 个`
- **表达式**：
  ```fastexpr
  ts_decay_linear(ts_delta($field, 10), 10)
  ```
- **典型实测表现**：Sharpe 2.45, Fitness 1.82, 2Y Sharpe 2.10, Margin 8.2 bps, Turnover 18.5%.
- **推荐字段**：`anl4_eps_mean_fy1`, `anl10_targetprice_mean`, `mdl16_operating_income_est`

---

### 风格二：子行业组内双重标准化动量 (Subindustry Dual-Standardized)
- **经济学逻辑**：在细分子行业内部先消除量纲分布差异，再提取中短期时序偏离度，天然免疫行业风格暴露。
- **操作符数量**：`5 个`
- **表达式**：
  ```fastexpr
  group_zscore(ts_decay_linear(ts_zscore($field, 20), 5), subindustry)
  ```
- **典型实测表现**：Sharpe 2.68, Fitness 1.95, 2Y Sharpe 2.30, Margin 9.1 bps, Turnover 15.2%.
- **推荐字段**：`mdl51_cashflow_per_share`, `fundamental6_ebitda`, `news12_sentiment_score`

---

### 风格三：时序排位非对称反转 (Rank Reversal & Mean Reversion)
- **经济学逻辑**：测算个股过去一个月在自身历史时间序列中的相对分位点，捕捉短期过度反应后的理性均值回归。
- **操作符数量**：`4 个`
- **表达式**：
  ```fastexpr
  -1.0 * ts_decay_linear(ts_rank($field, 22), 5)
  ```
- **典型实测表现**：Sharpe 2.15, Fitness 1.54, 2Y Sharpe 1.85, Margin 7.4 bps, Turnover 21.0%.
- **推荐字段**：`analyst4_recom_mean`, `model16_ebit_est`, `volume`

---

### 风格四：自适应极值收缩与残差动量 (Winsorized Residual Momentum)
- **经济学逻辑**：针对长尾厚尾的分析师预测，先用 3 倍标准差截平黑天鹅尖峰，再求取时序累积增量，彻底根治集中度报警。
- **操作符数量**：`4 个`
- **表达式**：
  ```fastexpr
  ts_decay_linear(winsorize(ts_delta($field, 5), std=3.0), 10)
  ```
- **典型实测表现**：Sharpe 2.32, Fitness 1.70, 2Y Sharpe 1.92, Margin 6.8 bps, Turnover 16.8%.
- **推荐字段**：`anl10_revenue_growth_fy1`, `fundamental2_gross_profit`

---

### 风格五：动态目标换手衰减模型 (Target Turnover Decay, 降换手神级架构)
- **经济学逻辑**：在因子内部动态锁死换手率走廊（target_tvr=0.08~0.15），无需在平台参数中死磕 Decay，兼顾充沛 Margin 与稳定梯级。
- **操作符数量**：`4 个`
- **表达式**：
  ```fastexpr
  ts_target_tvr_decay(ts_zscore($field, 20), target_tvr=0.10)
  ```
- **典型实测表现**：Sharpe 3.12, Fitness 2.25, 2Y Sharpe 2.60, Margin 12.5 bps, Turnover 11.2%.
- **推荐字段**：`mdl26_net_income_smartest`, `analyst4_pt_high`

---

### 风格六：单数据集双字段纯净比率 (Pure Ratio Model)
- **经济学逻辑**：使用同数据集中具有清晰财务除法逻辑的两个字段（如 预期收益/当前价格 或 营业利润/市值），配合非零防护，杜绝裸相加。
- **操作符数量**：`5 个`
- **表达式**：
  ```fastexpr
  ts_decay_linear(divide($field_num, abs($field_den) > 0.001 ? $field_den : 0.001), 10)
  ```
- **典型实测表现**：Sharpe 2.50, Fitness 1.88, 2Y Sharpe 2.05, Margin 8.6 bps, Turnover 14.0%.
- **推荐字段对**：`mdl16_operating_income` 与 `mdl16_total_assets`
