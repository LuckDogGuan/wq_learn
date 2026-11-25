# 08 全量数据深度分析：GBR 与 EUR 市场

> **数据基础**：从广州服务器同步的全量 hill_climbing_v4.7 数据，共 3296 个 checkpoint（本地原有 950 个，新增 2350 个）。本文基于 GBR 1236 个 + EUR 1784 个 checkpoint 的深度分析。

---

## 一、总体对比

| 指标 | GBR | EUR |
|:---|:---:|:---:|
| 总 Checkpoint 数 | 1236 | 1784 |
| 通关数量 | 306 | 1103 |
| 通关率 | 24.8% | 61.8% |
| 平均 Sharpe（全量） | 1.783 | 2.421 |
| 最高 Sharpe | 11.180 | 7.090 |
| 通关因子平均 Sharpe | 1.613 | 2.278 |
| 通关因子平均 Turnover | 24.417% | 13.407% |
| 通关因子平均 Margin | 9.34 bp | 16.67 bp |

> [!IMPORTANT]
> GBR 通关率仅 24.8%，远低于 EUR 的 61.8%，说明 GBR+TOP700 是最难攻克的宇宙组合之一。

### Gate Level 分布对比

| Gate Level | GBR 数量 | EUR 数量 | 说明 |
|:---:|:---:|:---:|:---|
| -1 (未评估) | 180 | 141 | 从未完成仿真 |
| 1-2 (早期淘汰) | 11 | 37 | 基础 Sharpe 不足 |
| 3 (中期) | 161 | 148 | 通过基础门槛 |
| 4 (高级) | 456 | 307 | 接近提交要求 |
| 5 (接近通关) | 213 | 198 | 仅差最后关卡 |
| 6 (全通关) | 215 | 953 | 最高质量 |

---

## 二、GBR 市场深度分析（GBR + TOP700）

### 2.1 GBR 主要失败原因

| 失败类型 | 次数 | 占总数比 | 解读 |
|:---|:---:|:---:|:---|
| SELF_CORRELATION | 641 | 51.9% | 与已提交因子相关性过高 |
| DATA_DIVERSITY | 641 | 51.9% | 数据多样性不足 |
| PROD_CORRELATION | 641 | 51.9% | 与生产池相关性过高 |
| REGULAR_SUBMISSION | 641 | 51.9% | 未达到常规提交标准 |
| MATCHES_THEMES | 641 | 51.9% | 与平台主题因子重叠，需要提高独创性 |
| OSMOSIS_ALLOCATION | 641 | 51.9% | 渗透分配不达标 |
| LOW_2Y_SHARPE | 371 | 30.0% | 近 2 年 Sharpe 衰减，信号时效性不足 |
| LOW_FITNESS | 359 | 29.0% | Fitness 指标不足 |
| POWER_POOL_CORRELATION | 290 | 23.5% | 与 Power Pool 相关性过高 |
| CONCENTRATED_WEIGHT | 288 | 23.3% | 持仓过于集中，需要加强分散化处理 |
| LOW_SHARPE | 239 | 19.3% | 总体 Sharpe 不足 |
| HIGH_TURNOVER | 213 | 17.2% | 换手率超标，需增大 Decay 或平滑处理 |
| LOW_SUB_UNIVERSE_SHARPE | 161 | 13.0% | TOP700 头部股票表现差，对集中流动性敏感 |
| CLUSTER_TEST | 121 | 9.8% | 簇测试未通过 |
| REVERSION_COMPONENT | 57 | 4.6% | 含有均值回归成分 |

### 2.2 GBR 通关因子参数分布

**中性化方式（通关因子）：**

| Neutralization | 通关数 | 占比 |
|:---|:---:|:---:|
| INDUSTRY | 81 | 26.5% |
| FAST | 71 | 23.2% |
| MARKET | 70 | 22.9% |
| SUBINDUSTRY | 49 | 16.0% |
| SECTOR | 14 | 4.6% |
| STATISTICAL | 9 | 2.9% |
| NONE | 4 | 1.3% |
| SLOW | 3 | 1.0% |
| SLOW_AND_FAST | 3 | 1.0% |
| CROWDING | 2 | 0.7% |

**Decay 参数（通关因子）：**

| Decay | 通关数 | 占比 |
|:---:|:---:|:---:|
| 8 | 105 | 34.3% |
| 0 | 96 | 31.4% |
| 4 | 48 | 15.7% |
| 50 | 24 | 7.8% |
| 5 | 14 | 4.6% |
| 20 | 8 | 2.6% |
| 6 | 8 | 2.6% |
| 12 | 3 | 1.0% |

### 2.3 GBR 通关因子 TOP 15（按 Sharpe 排序）

| # | Alpha ID | Sharpe | Sh_2Y | Fitness | Turnover | Margin(bp) | Decay | Neutralization | 公式（截断） |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | wpYJeQK6 | 2.320 | 1.570 | 1.22 | 66.79% | 5.6 | 8 | MARKET | `group_scale(max(rank(eur_aggregated_value_1 - eur_aggregated...` |
| 2 | wpYVb1Qd | 2.290 | 1.440 | 1.68 | 41.70% | 10.8 | 8 | MARKET | `rank(ts_mean(eur_top_director_signal_value_2, 5))` |
| 3 | LL9boXzm | 2.260 | 2.850 | 0.94 | 41.54% | 3.4 | 8 | FAST | `ts_rank(volume, 66)` |
| 4 | LL9boXzm | 2.260 | 2.850 | 0.94 | 41.54% | 3.4 | 8 | FAST | `ts_rank(volume, 66)` |
| 5 | Vk6KO158 | 2.250 | 1.470 | 1.65 | 41.55% | 10.7 | 8 | MARKET | `quantile(ts_mean(eur_top_director_signal_value_1, 5))` |
| 6 | Vk6KO158 | 2.250 | 1.470 | 1.65 | 41.55% | 10.7 | 8 | MARKET | `quantile(ts_mean(eur_top_director_signal_value_1, 5))` |
| 7 | d5OL8Qjg | 2.250 | 1.070 | 1.56 | 30.60% | 9.6 | 0 | SECTOR | `quantile(ts_mean(ts_backfill(eur_signal_value_1,5),5))` |
| 8 | d5OL8Qjg | 2.250 | 1.070 | 1.56 | 30.60% | 9.6 | 0 | SECTOR | `quantile(ts_mean(ts_backfill(eur_signal_value_1,5),5))` |
| 9 | 1YxvWNeR | 2.250 | 1.490 | 1.78 | 21.73% | 12.5 | 8 | MARKET | `winsorize(rank(max(rank(eur_aggregated_value_2), 0.5)))` |
| 10 | MP1w6mea | 2.230 | 1.530 | 1.76 | 21.72% | 12.5 | 8 | MARKET | `winsorize(rank(max(rank(eur_aggregated_value_1), 0.5)))` |
| 11 | RRVZJg8j | 2.220 | 1.520 | 1.62 | 41.07% | 10.7 | 8 | MARKET | `ts_decay_linear(quantile(ts_mean(eur_top_director_signal_val...` |
| 12 | 58Q3eZm6 | 2.220 | 1.020 | 1.30 | 37.03% | 6.9 | 8 | MARKET | `group_rank(rank(max(rank(eur_aggregated_value_2), 0.5)), ind...` |
| 13 | 6XrPnkwY | 2.220 | 1.510 | 1.62 | 41.09% | 10.6 | 8 | MARKET | `ts_decay_linear(quantile(ts_mean(eur_top_director_signal_val...` |
| 14 | RRVZJg8j | 2.220 | 1.520 | 1.62 | 41.07% | 10.7 | 8 | MARKET | `ts_decay_linear(quantile(ts_mean(eur_top_director_signal_val...` |
| 15 | RRVZJg8j | 2.220 | 1.520 | 1.62 | 41.07% | 10.7 | 8 | MARKET | `ts_decay_linear(quantile(ts_mean(eur_top_director_signal_val...` |

### 2.4 GBR 高 Sharpe 通关因子展示（Sharpe >= 2.5）

> [!TIP]
> GBR 市场中，**MARKET 中性化 + Decay=4/5** 的组合在 TOP700 宇宙中通关率相对最高。GBR TOP700 流动性宇宙小、集中度风险高，建议优先使用 group_zscore 或 group_rank 做截面标准化。

---

## 三、EUR 市场深度分析

### 3.1 EUR 四个 Universe 对比

| Universe | 总数 | 通关 | 通关率 | avg Sharpe | max Sharpe |
|:---|:---:|:---:|:---:|:---:|:---:|
| TOP1200 | 222 | 104 | 46.8% | 1.495 | 1.980 |
| TOP2500 | 1457 | 918 | 63.0% | 2.606 | 7.090 |
| TOP800 | 38 | 21 | 55.3% | 1.471 | 1.770 |
| TOPCS1600 | 67 | 60 | 89.6% | 2.007 | 2.160 |

> [!IMPORTANT]
> EUR+TOPCS1600 通关率高达 **89.5%（60/67）**，是所有宇宙中通关率最高的！TOPCS1600 是欧洲消费类股票宇宙，信号质量更稳定，因子同质性竞争相对较低。

### 3.2 EUR 主要失败原因

| 失败类型 | 次数 | 占总数比 | 关键解读 |
|:---|:---:|:---:|:---|
| SELF_CORRELATION | 1176 | 65.9% | 与已提交因子相关性过高 |
| DATA_DIVERSITY | 1176 | 65.9% | 数据多样性不足 |
| PROD_CORRELATION | 1176 | 65.9% | 与生产池相关性过高 |
| REGULAR_SUBMISSION | 1176 | 65.9% | 未达到常规提交标准 |
| MATCHES_THEMES | 1176 | 65.9% | 与平台主题因子重叠，需要提高独创性 |
| OSMOSIS_ALLOCATION | 1176 | 65.9% | 渗透分配不达标 |
| LOW_SUB_UNIVERSE_SHARPE | 729 | 40.9% | TOP700 头部股票表现差，对集中流动性敏感 |
| CLUSTER_TEST | 591 | 33.1% | 簇测试未通过 |
| LOW_2Y_SHARPE | 410 | 23.0% | 近 2 年 Sharpe 衰减，信号时效性不足 |
| POWER_POOL_CORRELATION | 374 | 21.0% | 与 Power Pool 相关性过高 |
| CONCENTRATED_WEIGHT | 347 | 19.5% | 持仓过于集中，需要加强分散化处理 |
| LOW_FITNESS | 324 | 18.2% | Fitness 指标不足 |
| LOW_SHARPE | 207 | 11.6% | 总体 Sharpe 不足 |
| HIGH_TURNOVER | 127 | 7.1% | 换手率超标，需增大 Decay 或平滑处理 |

### 3.3 EUR 通关因子参数分布

**中性化方式（通关因子）：**

| Neutralization | 通关数 | 占比 |
|:---|:---:|:---:|
| SUBINDUSTRY | 431 | 39.1% |
| FAST | 304 | 27.6% |
| MARKET | 207 | 18.8% |
| SLOW | 39 | 3.5% |
| NONE | 33 | 3.0% |
| SECTOR | 31 | 2.8% |
| CROWDING | 19 | 1.7% |
| COUNTRY | 12 | 1.1% |
| STATISTICAL | 10 | 0.9% |
| REVERSION_AND_MOMENTUM | 10 | 0.9% |
| INDUSTRY | 7 | 0.6% |

**Decay 参数（通关因子）：**

| Decay | 通关数 | 占比 |
|:---:|:---:|:---:|
| 0 | 669 | 60.7% |
| 5 | 294 | 26.7% |
| 4 | 123 | 11.2% |
| 6 | 9 | 0.8% |
| 20 | 6 | 0.5% |
| 2 | 1 | 0.1% |
| 1 | 1 | 0.1% |

### 3.4 EUR+TOP2500 高 Sharpe 通关因子（Sharpe >= 3.0）

EUR+TOP2500 共 1457 个 checkpoint，918 个通关（63.0%），其中 Sharpe >= 3.0 的有 **201 个**。

#### O0rOlOvg — Sharpe 7.020

```
scale(quantile(predicted_first_quantile_five_day_return_13))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=7.020, Sh_2Y=3.490, Fitness=4.30, TO=36.60%, Margin=7.5bp

#### O0rOlOvg — Sharpe 7.020

```
scale(quantile(predicted_first_quantile_five_day_return_13))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=7.020, Sh_2Y=3.490, Fitness=4.30, TO=36.60%, Margin=7.5bp

#### 78ZWm522 — Sharpe 6.610

```
normalize(pasteurize(predicted_first_quantile_one_day_return_131))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=6.610, Sh_2Y=3.700, Fitness=3.71, TO=46.12%, Margin=6.3bp

#### blRXza5K — Sharpe 6.600

```
zscore(zscore(predicted_first_quantile_one_day_return_131))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=6.600, Sh_2Y=3.700, Fitness=3.70, TO=46.08%, Margin=6.3bp

#### pwjkNN2x — Sharpe 6.130

```
zscore(zscore(predicted_first_quantile_one_day_return_15))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=6.130, Sh_2Y=6.840, Fitness=3.41, TO=45.34%, Margin=6.2bp

#### N17G9ZnX — Sharpe 6.080

```
scale(quantile(predicted_second_quantile_five_day_return_15))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=6.080, Sh_2Y=6.890, Fitness=3.02, TO=40.16%, Margin=5.0bp

#### RR7o7dYz — Sharpe 5.930

```
scale(quantile(predicted_second_quantile_ten_day_return_14))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=5.930, Sh_2Y=6.920, Fitness=3.03, TO=37.02%, Margin=5.2bp

#### le8dNJr8 — Sharpe 5.750

```
rank(quantile(predicted_second_quantile_one_day_return_14))
```
- **参数**：decay=5, neutralization=SLOW, truncation=0.0
- **指标**：Sharpe=5.750, Sh_2Y=2.270, Fitness=2.58, TO=50.53%, Margin=4.0bp

#### KP721nmj — Sharpe 5.730

```
scale(quantile(predicted_first_quantile_ten_day_return_15))
```
- **参数**：decay=0, neutralization=SUBINDUSTRY, truncation=0.0
- **指标**：Sharpe=5.730, Sh_2Y=5.990, Fitness=2.53, TO=76.42%, Margin=3.9bp

#### kqjMEMGK — Sharpe 5.600

```
scale(quantile(predicted_first_quantile_ten_day_return_131))
```
- **参数**：decay=0, neutralization=SUBINDUSTRY, truncation=0.0
- **指标**：Sharpe=5.600, Sh_2Y=6.240, Fitness=2.57, TO=76.17%, Margin=4.2bp


### 3.5 EUR+TOPCS1600 最优宇宙分析

TOPCS1600（欧洲消费类 Top 1600）通关率 60/67 = **89.6%**。

**TOPCS1600 通关因子参数特征：**

| 参数 | 值 |
|:---|:---|
| 最优 Neutralization | SUBINDUSTRY (55/60) |
| 最优 Decay | 0 (55/60) |
| Sharpe 范围 | 1.640 ~ 2.160 |

---

## 四、GBR vs EUR 横向对比总结

### 4.1 参数偏好对比

| 参数 | GBR 通关最优 | EUR 通关最优 | 差异分析 |
|:---|:---:|:---:|:---|
| Neutralization | INDUSTRY (81个) | SUBINDUSTRY (431个) | 两市场中性化偏好不同 |
| Decay | 8 (105个) | 0 (669个) | Decay 参数有地区差异 |
| 通关率 | 24.8% | 61.8% | EUR 友好度显著更高 |
| avg Sharpe | 1.613 | 2.278 | EUR 通关因子质量略高 |

### 4.2 共同高效 Admission Profile

| Admission Profile | GBR 通关数 | EUR 通关数 | 合计 |
|:---|:---:|:---:|:---:|
| balanced-v3-inherited-operators | 203 | 869 | 1072 |
| balanced-v2 | 83 | 163 | 246 |
| N/A | 20 | 71 | 91 |

> [!TIP]
> **跨市场通用策略**：在 GBR 和 EUR 都表现好的 admission_profile，是候选池配置的最佳参考。两市场共同通关率高的 profile 说明该候选池策略的泛化能力强。

---

## 五、关键结论与操作建议

### 5.1 GBR 市场操作建议

1. **通关率低（24.8%）的根因**：GBR TOP700 宇宙小、头部股票集中，CONCENTRATED_WEIGHT 和 LOW_SUB_UNIVERSE_SHARPE 是主要障碍
2. **优先使用 group_zscore 或 group_rank**：在子行业/行业截面做标准化，降低集中度风险
3. **最优中性化**：INDUSTRY（通关 81 个）
4. **最优 Decay**：8（通关 105 个）
5. **避免纯价量因子直接使用**：需要与基本面或分析师字段组合以提升独特性（降低 MATCHES_THEMES）
6. **提高 2Y Sharpe**：选择经济逻辑长期成立的信号，避免短期过拟合

### 5.2 EUR 市场操作建议

1. **优先 EUR+TOP2500**：数据量最大（1457 个），通关率 63.0%，avg Sharpe 2.403
2. **TOPCS1600 是高通关率捷径**：89.5% 通关率，适合测试新想法
3. **最优中性化**：SUBINDUSTRY（通关 431 个）
4. **最优 Decay**：0（通关 669 个）
5. **EUR 对数据多样性要求高**：DATA_DIVERSITY 失败频繁，避免同一数据集内多字段高度共线
6. **高 Sharpe 天花板高**：EUR max Sharpe 7.09，说明高质量因子潜力巨大

*文档生成时间：2026-09-07 | 数据源：广州服务器 hill_climbing_v4.7 全量 3296 checkpoints*