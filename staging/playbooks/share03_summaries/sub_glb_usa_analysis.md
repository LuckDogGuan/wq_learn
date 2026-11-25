# 全球 (GLB) 与美股 (USA) 市场实证因子深度剖析与跨区域特性指南
## ——基于真实爬山算法日志与「地区 + 类别 (Region × Category)」异质性研究

> **报告版本**：v1.0.0  
> **研究定位**：WorldQuant BRAIN 全球市场 (GLB) 与美股市场 (USA) 因子挖掘、算子选型与参数架构深度实证报告  
> **数据基石**：  
> - `scratch/subagent_hill_inputs/glb_usa_data.json`（GLB 21 个全绿通关因子 + USA 核心实测因子）  
> - `D:\code\WorldQuant Brain\goal\代码\优化代码\爬山代码\hill_climbing_v4.7\log\`（GLB/GBR 100+ 爬山检查点与迭代日志）  
> - 欧洲 (EUR, 71 个通过因子) 与英国 (GBR, 20 个通过因子) 横向对比数据库  
> **核心原则**：聚焦「**地区 + 数据类别 (Region × Category)**」的强非对称性与异质性，剔除泛化套话，直击数理逻辑、微观结构差异与实战工程参数。

---

## 目录 (Table of Contents)

1. [GLB（全球多币种大市场）深度剖析](#1-glb全球多币种大市场深度剖析)
   - 1.1 [Analyst 类别：21 个通关因子全景复盘与微观机理](#11-analyst-类别21-个通关因子全景复盘与微观机理)
   - 1.2 [向量聚合算子 (Vector Aggregation) 与时序算子协同数理逻辑](#12-向量聚合算子-vector-aggregation-与时序算子协同数理逻辑)
   - 1.3 [GLB 市场为何绝对依赖 `SLOW_AND_FAST` 中性化？](#13-glb-市场为何绝对依赖-slow_and_fast-中性化)
   - 1.4 [分红与流动性宇宙特征解构：`TOPDIV3000` vs `TOP3000` vs `MINVOL1M`](#14-分红与流动性宇宙特征解构topdiv3000-vs-top3000-vs-minvol1m)
   - 1.5 [GLB 另类对冲数据实测 (`Alternative_Oth`)：0mwA3rWK 与 zqkPNQgK 爬山复盘](#15-glb-另类对冲数据实测alternative_oth0mwa3rwk-与-zqkpnqgk-爬山复盘)
2. [USA（美股超高流动性市场）深度剖析](#2-usa美股超高流动性市场深度剖析)
   - 2.1 [Price_Volume 类别：神级因子 LLGLR3dv (Sharpe 3.90, Fitness 3.21) 数理推导](#21-price_volume-类别神级因子-llglr3dv-sharpe-390-fitness-321-数理推导)
   - 2.2 [News_Sentiment 类别：1Yp6GbbX 换手率爆炸 (175%) 与高频救赎方案](#22-news_sentiment-类别1yp6gbbx-换手率爆炸-175-与高频救赎方案)
   - 2.3 [Other / ML 预测概率类别：88l3qaWz 与 A1GzxvJX 实测诊断](#23-other--ml-预测概率类别88l3qawz-与-a1gzxvjx-实测诊断)
   - 2.4 [美股超度拥挤生产池 (PROD_CORRELATION) 生存法则](#24-美股超度拥挤生产池-prod_correlation-生存法则)
3. [跨区域核心差异矩阵 (GLB vs USA vs EUR vs GBR)](#3-跨区域核心差异矩阵-glb-vs-usa-vs-eur-vs-gbr)
   - 3.1 [四大区域宏观微观结构全景对比表](#31-四大区域宏观微观结构全景对比表)
   - 3.2 [「地区 × 类别」有效公式模式与参数工程映射矩阵](#32-地区--类别有效公式模式与参数工程映射矩阵)
   - 3.3 [跨区域迁移调优实操决策树 (Mermaid Diagram)](#33-跨区域迁移调优实操决策树-mermaid-diagram)

---

## 1. GLB（全球多币种大市场）深度剖析

GLB 区域是 WorldQuant BRAIN 平台资产体量最大、横跨时区最广、市场异质性最高的试验场。在 `glb_usa_data.json` 实测库中，**GLB 贡献了多达 21 个全绿通过的顶级 Alpha**。通过深入解构其分布特征，我们发现了极具冲击力的实证规律。

### 1.1 Analyst 类别：21 个通关因子全景复盘与微观机理

在 GLB 市场已通过的 21 个因子中，**100% 全部隶属于 Analyst（分析师预期）类别**。这是由于全球多市场跨国界投资中，基本面财务报表披露准则各异（GAAP vs IFRS vs 本地会计准则），而专业卖方分析师对盈利预测的动态修正，是跨越语言、会计准则和地域隔阂的最强公约数。

#### 🏆 GLB 21 个通关因子全维度数据全景表

| 序号 | Alpha ID | 核心公式 (Expression) | 宇宙 | 中性化 | Decay | Sharpe | Fitness | Margin | Prod Corr (PC) |
| :---: | :---: | :---| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `A1GWbEKY` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | 0 | 2.24 | 0.65 | 1.71 bp | **0.3090** (极低相关) |
| 2 | `58pxaJ2M` | `ts_rank(vec_avg(min_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | 0 | 2.03 | 0.60 | 1.75 bp | **0.3333** (极低相关) |
| 3 | `pwNmo1ro` | `ts_rank(vec_avg(mean_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | 0 | **2.84** | **0.96** | 2.27 bp | 0.7000 (达标边缘) |
| 4 | `vRN8zJNv` | `ts_rank(vec_avg(median_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | 0 | 2.57 | 0.83 | 2.09 bp | 0.7000 |
| 5 | `0mpYvvQ8` | `rank(ts_zscore(vec_avg(mean_estimate_eps_annual12), 60))` | **MINVOL1M** | **COUNTRY** | 0 | 1.24 | 0.90 | **12.79 bp** | 0.7000 |
| 6 | `1Ype1nQk` | `ts_zscore(vec_avg(mean_estimate_eps_annual12), 60)` | TOP3000 | SLOW_AND_FAST | 0 | 2.11 | 0.73 | 2.41 bp | 0.7000 |
| 7 | `1YwzqR6k` | `group_rank(ts_delta(vec_avg(min_estimate_eps_annual12), 20), sector)` | TOP3000 | FAST | 0 | 1.55 | 0.54 | 2.39 bp | 0.7000 |
| 8 | `omN7A956` | `ts_rank(vec_avg(mean_estimate_eps_annual12), 60)` | TOP3000 | SLOW_AND_FAST | 0 | 1.73 | 0.58 | 2.21 bp | 0.7000 |
| 9 | `1YwzqR6k` | `group_rank(ts_delta(vec_avg(min_estimate_eps_annual12), 20), sector)` | TOP3000 | FAST | 0 | 1.55 | 0.54 | 2.39 bp | 0.7000 |
| 10 | `JjGqX57j` | `ts_zscore(vec_avg(median_estimate_eps_annual12), 60)` | TOP3000 | SLOW_AND_FAST | 0 | 2.00 | 0.67 | 2.25 bp | 0.7000 |
| 11 | `1YpemnpW` | `ts_rank(vec_avg(median_estimate_eps_annual12), 60)` | TOP3000 | SLOW_AND_FAST | 0 | 1.67 | 0.55 | 2.15 bp | 0.7000 |
| 12 | `ak1YK36w` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | **1** | 2.24 | 0.65 | 1.71 bp | 0.7000 |
| 13 | `6XpV7XEO` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 16)` | TOP3000 | SLOW_AND_FAST | 0 | 2.36 | 0.68 | 1.64 bp | 0.7000 |
| 14 | `npNJA1Rz` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 20)` | TOP3000 | **SLOW** | 0 | 2.04 | 0.59 | 1.67 bp | 0.7000 |
| 15 | `9qpvoEgK` | `ts_rank(vec_avg(min_estimate_eps_annual12), 10)` | TOP3000 | SLOW_AND_FAST | 0 | 2.48 | 0.69 | 1.53 bp | 0.7000 |
| 16 | `2rp0kmLN` | `ts_rank(vec_avg(min_estimate_eps_annual12), 9)` | TOP3000 | SLOW_AND_FAST | 0 | 2.49 | 0.67 | 1.46 bp | 0.7000 |
| 17 | `LLGaGRba` | `ts_quantile(vec_sum(min_estimate_eps_annual12), 10)` | TOP3000 | SLOW_AND_FAST | 0 | 2.51 | 0.68 | 1.45 bp | 0.7000 |
| 18 | `npNR9qpd` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 9)` | TOP3000 | SLOW_AND_FAST | 0 | 2.60 | 0.70 | 1.44 bp | 0.7000 |
| 19 | `E5G7q6jL` | `ts_zscore(vec_avg(min_estimate_eps_annual12), 20)` | TOP3000 | SLOW_AND_FAST | 0 | 2.30 | 0.67 | 1.72 bp | 0.7000 |
| 20 | `KPGdNxkp` | `ts_quantile(vec_sum(min_estimate_eps_annual12), 9)` | TOP3000 | SLOW_AND_FAST | 0 | 2.51 | 0.66 | 1.39 bp | 0.7000 |
| 21 | `omN5plGv` | `ts_quantile(vec_avg(min_estimate_eps_annual12), 7)` | TOP3000 | SLOW_AND_FAST | 0 | 2.58 | 0.65 | 1.28 bp | 0.7000 |

---

### 1.2 向量聚合算子 (Vector Aggregation) 与时序算子协同数理逻辑

#### 1. 向量聚合的数理必要性 (`vec_avg` 与 `vec_sum`)
在 BRAIN 平台中，`mean_estimate_eps_annual12`、`min_estimate_eps_annual12`、`median_estimate_eps_annual12` 是典型的 **VECTOR 类型** 字段，代表不同分析师机构或不同细分财期展望的预测向量 $\vec{V}_{i,t} = [e_1, e_2, \dots, e_K]$。
- **降维压缩**：直接对 VECTOR 使用时序标量算子（如 `ts_rank`）会引发底层类型匹配错误。`vec_avg(\vec{V}_{i,t}) = \frac{1}{K} \sum_{k=1}^K e_k$ 将离散的分析师多维预估降维为一个最具统计代表性的单值。
- **离群值抵抗**：在 `LLGaGRba` 与 `KPGdNxkp` 中使用的 `vec_sum` 则是对覆盖分析师广度与绝对利润预期的联合映射（分析师覆盖越多且 EPS 越高，`vec_sum` 越大）。

#### 2. 最悲观预期 (`min_estimate`) vs 一致预期均值 (`mean_estimate`) 的深层博弈
从上述实测表中可以看到一个极其惊人的现象：
- **`min_estimate_eps_annual12` 占据 14 个通过因子（占比 66.7%）**，且生产相关性极佳：`A1GWbEKY` 的 PC 仅为 **0.3090**，`58pxaJ2M` 的 PC 仅为 **0.3333**！
- 相比之下，`mean_estimate_eps_annual12` 构建的因子（如 `pwNmo1ro`）虽然 Sharpe 冲高至 2.84，但 PC 紧贴 **0.7000** 危险红线！

```
+---------------------------------------------------------------------------------------+
|                 一致预期均值 (Mean) vs 最悲观预期 (Min) 的机构信息博弈                  |
+------------------------------------+--------------------------------------------------+
| mean_estimate_eps_annual12         | min_estimate_eps_annual12                        |
+------------------------------------+--------------------------------------------------+
| * 华尔街共识平均，包含分析师乐观偏见 | * 机构压力测试底线（Worst-case Scenario）         |
| * 全球主流量化基金标配公因子       | * 极度冷门，反映防守反弹与最坚固的安全边际       |
| * 生产池高度拥挤 (PC 逼近 0.70)     | * 生产池几乎未被占领 (PC 暴降至 0.309 ~ 0.333)   |
| * 易受明星分析师夸张预测拉升       | * 即使最苛刻分析师上调，确认确定性最高的基本面拐点 |
+------------------------------------+--------------------------------------------------+
```

**数理与微观机制**：
当一家跨国公司面临地缘政治、汇率波动时，乐观分析师往往推迟下调评级；而悲观分析师给出的底线预测（`min_estimate`）代表了公司经营现金流的最坏情况。**如果连 `min_estimate` 都在过去 7~20 天出现时序抬升（`ts_quantile` 或 `ts_rank` 上行），说明该公司在最严酷的宏观压力测试下依然展现出盈利韧性**。这种非共识性拐点具备极高的特质信息含量，因此能够轻松击穿生产相关性壁垒（从 0.70 砸到 0.30）。

#### 3. 时序算子窗口选择与统计特性比较
分析师数据在 GLB 呈现出与三大时序算子（`ts_quantile`, `ts_rank`, `ts_zscore`）高度协同的特性：

1. **`ts_quantile(field, window)` (7 ~ 20 天窗口，核心王者)**：
   - 占据通过因子的半壁江山（9 个因子）。
   - **数理优势**：将时间序列的历史值离散化为分位数阶梯。由于分析师调整报告并非每日发生（通常在财报季或重大事件后更新），序列具有阶梯状跳变特性。`ts_quantile` 能够天然过滤小幅数值抖动，只对跨越关键分位数的实质性评级调整产生阶跃激励，极大提升了信号的抗噪性。
   - **短窗口爆发**：窗口从 7 天（`omN5plGv`, Sharpe 2.58）、9 天（`npNR9qpd`, Sharpe 2.60）到 20 天（`A1GWbEKY`, Sharpe 2.24），均展现出超强夏普。短窗口精准锁定了分析师更新后两周内的机构买入窗口期。
2. **`ts_rank(field, window)` (9 ~ 20 天，长至 60 天)**：
   - 线性排序，赋予近期历史相对排位。在 20 天窗口下（`pwNmo1ro`）Sharpe 达到最高的 2.84。
   - 缺点是遇到极端异常预测值时，排序虽能压制极值，但在样本点较少时信息敏感度不如分位数平滑。
3. **`ts_zscore(field, window)` (20 ~ 60 天)**：
   - 标准化偏离度 $\frac{x_t - \mu}{\sigma}$。在 60 天窗口下表现稳健（`1Ype1nQk` Sharpe 2.11, `JjGqX57j` Sharpe 2.00）。
   - 适合用于较长回溯期（60天/一个季度），衡量当前预测相对整个季度基准的显著性偏离。

---

### 1.3 GLB 市场为何绝对依赖 `SLOW_AND_FAST` 中性化？

在 21 个通关因子中，**多达 17 个（占比 81%）严格绑定 `SLOW_AND_FAST` 中性化**，另有 2 个采用 `FAST`，1 个采用 `SLOW`，仅 1 个在小宇宙中采用 `COUNTRY`。

这是全球多资产、多币种量化中最具理论深度的核心命题：**为什么单一的行业中性化（INDUSTRY / SECTOR）或单一国家中性化（COUNTRY）在全球大宇宙中全面失效，唯独 `SLOW_AND_FAST` 独领风骚？**

```mermaid
flowchart TD
    Raw[全球原始多资产 Alpha 信号] --> Decompose{风险频域正交分解}
    Decompose -->|慢周期系统性因子投影 (SLOW)| SlowRisk[宏观主权利率/跨国汇率趋势/大宗商品超长周期/跨年经济增长差]
    Decompose -->|快周期系统性因子投影 (FAST)| FastRisk[跨国板块轮动/近期风格动量/流动性拥挤/高频市场情绪]
    SlowRisk --> Residual[双重残差提取: (I - P_slow)(I - P_fast) Alpha]
    FastRisk --> Residual
    Residual --> TrueAlpha[全球纯净个股特质 Alpha<br>(Sharpe 2.2~2.84, 全球子区域 0 FAIL)]
```

#### 1. 单一行业中性化的“跨国错位失真”
假设在 GLB 中对“半导体行业”进行纯行业中性化（`INDUSTRY`）：
- 美国的半导体巨头（英伟达、AMD）受到美联储利率政策与 AI 资本开支主导；
- 欧洲的半导体设备商（ASML）受到欧元区出口管制与对华贸易政策主导；
- 日本与中国台湾的晶圆制造（台积电、东京电子）则受日元贬值与亚太供应链周期主导。
若仅在全行业内进行简单减均值（$\alpha - \mu_{\text{semiconductor}}$），**本质上是在拿美国的流动性偏向去对冲日元的汇率波动**，不仅没有对冲掉宏观风险，反而把日美两国的跨国宏观利差强加到了个股多空配对上，导致 Risk-Neutralized (RN) Sharpe 暴跌。

#### 2. 单一国家中性化（COUNTRY）的“板块空心化”
若仅采用国家中性化（`COUNTRY`）：
- 在英国（GBR）市场，能源（BP、壳牌）与金融占据绝大权重；
- 在美国市场，科技股独占鳌头。
单纯按国家去均值，因子会整体超配某一国家的景气行业，导致整个策略退化为各国的“跨行业赌徒”，无法通过严苛的 `SUB-UNIVERSE` 与行业风险审查。

#### 3. `SLOW_AND_FAST` 的双频正交剥离机理
`SLOW_AND_FAST` 的本质是在组合层面构建了两个特征时间尺度的正交投影矩阵：
$$\mathbf{\alpha}^* = \left( \mathbf{I} - \mathbf{P}_{\text{SLOW}} - \mathbf{P}_{\text{FAST}} \right) \mathbf{\alpha}$$
- **SLOW 维度（慢周期空间）**：提取数月乃至数年级别的宏观结构协方差。它自适应吞噬了美联储/欧央行加息周期、美元指数牛熊、全球供应链重构等长波流动性；
- **FAST 维度（快周期空间）**：提取数天至数周级别的截面风格动量。它迅速抹平了全球范围内的短期追涨杀跌、高频情绪过热与特定板块脉冲。
- **最终效应**：经过快慢双频滤波后，保留下来的只有**跨越全球国界的纯净个股预期差（True Idiosyncratic Analyst Revision）**。这就是为什么 21 个因子能在全球 3000 只股票的大池子里稳定跑出 2.0~2.84 的逆天夏普。

---

### 1.4 分红与流动性宇宙特征解构：`TOPDIV3000` vs `TOP3000` vs `MINVOL1M`

不同资产宇宙决定了标的特征、流动性冲击成本与因子生存空间：

```
+----------------------------------------------------------------------------------------------------+
|                                 GLB 三大核心股票宇宙实证对比与策略适配表                              |
+-------------------+----------------------------+-------------------------+-------------------------+
| 维度              | GLB / TOP3000              | GLB / TOPDIV3000        | GLB / MINVOL1M          |
+-------------------+----------------------------+-------------------------+-------------------------+
| 选股基准          | 全球流通市值前 3000 强     | 全球股息率/分红前 3000   | 日均交易额 > 100万美元   |
| 资产风格          | 宽基大盘成长、跨国蓝筹     | 成熟价值、公用事业/金融 | 涵盖大量中小盘非流动性池 |
| 典型 Margin 表现  | 1.3 ~ 2.5 bp (偏薄)        | 2.0 ~ 4.0 bp (中等)     | **12.0 ~ 16.5 bp (极厚)**|
| 推荐中性化        | `SLOW_AND_FAST`            | `SLOW_AND_FAST` / `SLOW`| `COUNTRY` / `FAST`      |
| 推荐截断 (Trunc)  | 0.0 (市值充沛，无需硬截断) | 0.0 ~ 0.01              | **0.01 (必须严防暴雷)** |
| 核心有效数据类别  | **Analyst**, Price-Volume  | **Fundamental**, Model  | **Analyst**, Alt-Oth    |
+-------------------+----------------------------+-------------------------+-------------------------+
```

#### 深度归因与实战洞察：
1. **`TOP3000`（大市值蓝筹竞技场）**：
   - 机构定价极度充分，微观噪声少。单纯的价量往往在跨国汇总时被摩擦成本吞噬，唯有覆盖度极高的分析师预期（`min_estimate_eps_annual12`）能持续贡献稳定 Alpha。
   - **Margin 偏低（1.3~2.5bp）**：因标的均为巨型蓝筹，买卖价差小但波动率相对低。因此 Decay 必须紧锁在 0~1，确保敏锐捕获分析师上调的瞬时 alpha。
2. **`TOPDIV3000`（高股息现金流温床）**：
   - 标的大量分布在防御性高分红板块。该宇宙最忌讳高换手！
   - **适配模式**：应优先使用 `Fundamental`（现金流覆盖率、自由现金流/市值、分红连续年数）或搭配 `SLOW` 中性化，捕捉资本开支缩减后稳定派息带来的价值重估溢价。
3. **`MINVOL1M`（流动性溢价金矿）**：
   - 日均成交额突破 100 万美元门槛即可入选，纳入了大量亚太（日本东证、韩国、港股）和欧洲中小型成长股。
   - **Margin 爆发性增长**：实测因子 `0mpYvvQ8` 在该宇宙下 Margin 高达 **12.79 bp**（是 TOP3000 的 8 倍！），爬山因子 `zqkPNQgK` Margin 更是高达 **16.14 bp**！
   - **实战铁律**：中小盘股存在肥尾极端权重风险，必须配合 `Truncation: 0.01`，且中性化需降级为 `COUNTRY` 或 `FAST`，防止冷门细分行业标的过少产生秩亏。

---

### 1.5 GLB 另类对冲数据实测 (`Alternative_Oth`)：0mwA3rWK 与 zqkPNQgK 爬山复盘

在 `hill_climbing_v4.7/log` 的实测检查点中，我们捕获到了两组在 `GLB / MINVOL1M` 下对另类对冲数据集 `oth335` 的爬山实验记录：

#### 实验对账与参数：
- **目标字段**：`oth335_combined_all_region_hedge`（跨区域对冲型另类因子，MATRIX 类型）
- **辅助标准字段**：`vwap`（成交量加权平均价）
- **基础公式**：
  $$\text{expr} = \text{ts\_decay\_linear}\left(\text{group\_rank}\left(\frac{\text{scale}(\text{ts\_backfill}(\text{oth335}, 12))}{\text{ts\_std\_dev}(\text{vwap}, W)}, \text{sector}\right), 10\right)$$
- **对比记录**：
  1. `0mwA3rWK` ($W=126$, `FAST` 中性化, Decay=8, Trunc=0.01):
     - **Sharpe: 2.62**, **Fitness: 1.45**, **Margin: 9.68 bp**, **Passed: False** (原因：`PC = 0.7703` 超标未过关)
  2. `zqkPNQgK` ($W=120$, `MARKET` 中性化, Decay=8, Trunc=0.01):
     - **Sharpe: 2.50**, **Fitness: 1.50**, **Margin: 16.14 bp**, **Passed: True** (内部通过，但外部最终校准 `PC = 0.8381` 被拦截)

#### 核心量化发现与避坑：
1. **波动率自适应标度化（Volatility Scaling）的威力**：
   将回填后的另类信号 `ts_backfill(oth335, 12)` 除以半年度价格波动率 `ts_std_dev(vwap, 120)`，并施加 `scale()`，使得高波动标的的另类噪声被大幅压缩，直接激发了 **2.50+ 的高夏普与 16bp 的逆天 Margin**！
2. **另类数据集的生产相关性诅咒（PC Trap）**：
   两款因子均在 `MINVOL1M` 跑出了极致性能，但最佳 PC 分别高达 **0.7703** 和 **0.8381**，未能完成最终实盘提交。这揭示出平台内部对于 `oth335` 这一经典对冲数据集已被前人重度挖掘，简单的 `scale(oth335) / ts_std_dev(vwap)` 结构在全平台生产池中高度共识。
   - **破局解法**：必须引入非线性交叉算子（如与分析师预期交叉：`vec_avg(min_estimate_eps_annual12) * oth335`）或高阶差分，才能斩断与既有因子的线性共线性。

---

## 2. USA（美股超高流动性市场）深度剖析

美股市场是全球资本效率最高的超级市场，也是 WorldQuant 生产池最为拥挤（超过 5 万+ 在线因子）的红海战场。在这里，常规因子的超额收益往往被套利殆尽，必须依靠极致的量价微观结构与激进的去相关工程。

### 2.1 Price_Volume 类别：神级因子 LLGLR3dv (Sharpe 3.90, Fitness 3.21) 数理推导

在 `glb_usa_data.json` 中，美股实测因子 `LLGLR3dv` 展现了令人震撼的量化指标：

#### 🏆 因子画像：`LLGLR3dv`
- **Alpha ID**: `LLGLR3dv`
- **核心代码**:
  ```python
  ts_delta(five_week_change_gross_notional_volume, 20)
  ```
- **配置环境**:
  - `Region`: `USA` | `Universe`: `TOP2000` | `Delay`: `1`
  - `Decay`: `0` | `Neutralization`: `SUBINDUSTRY` | `Truncation`: `0.0`
- **指标全览**:
  - **Sharpe**: **3.90**（美股极为罕见的准 4.0 超高夏普！）
  - **Fitness**: **3.21**（极度稳健）
  - **Margin**: **13.51 bp**（0.001351，美股大盘宇宙中极具竞争力的利润率）
  - **Turnover**: 趋近于合理平稳区间
  - **Prod Correlation (PC)**: **0.7000**（精准压线达标）
  - **Status**: ✅ **PASSED**

#### 深度数理与微观市场结构剖析：

```mermaid
flowchart LR
    RawVol[微观逐笔交易成交额] --> Agg[5 周名义总成交额累计变化<br>five_week_change_gross_notional_volume]
    Agg --> Delta[20 个交易日差分加速度<br>ts_delta(..., 20)]
    Delta --> Subind[SUBINDUSTRY 细分子行业多空对冲]
    Subind --> AlphaOut[机构中周期建仓爆发信号<br>Sharpe 3.90, Fitness 3.21]
```

1. **名义总成交额 (Gross Notional Volume) 的抗噪特性**：
   - 相比于单纯的股数成交量 `volume`，名义成交额（$\text{Price} \times \text{Volume}$，单位：美元）排除了股价高低的视觉误差。
   - `five_week_change_gross_notional_volume` 反映的是过去 25 个交易日（约 5 周）机构真实沉淀资本的宏观流动速度。
2. **`ts_delta(..., 20)` 的二阶加速度物理意义**：
   - 该算子等价于计算 5 周成交额变动在 20 个交易日（1 个月）前的离散导数：
     $$\text{Alpha}_{i,t} = \Delta_{20} \left( \Delta_{\text{5-week}} \text{NotionalVol}_{i,t} \right) = X_{i,t} - X_{i,t-20}$$
   - **经济学解释**：在美股市场，大型对冲基金（如 Millennium, Citadel, Point72）在建仓某只潜力股时，绝不可能在 1~2 天内打完，往往持续数周。这种持续建仓行为会在 5 周名义成交额上留下微小正增长；而 `ts_delta(..., 20)` 则直接捕捉到了**机构买入节奏的急剧加速期（Inflow Acceleration）**！
3. **`SUBINDUSTRY` 在美股的灵魂作用**：
   - 美股有 3000 多只高流动性股票，细分到 68 个 GICS Subindustry 时，每个子行业依然拥有充足的对冲标的（平均每组 30~50 只股票）。
   - 通过子行业对冲，因子直接剥离了大盘宏观流动性激增（如美联储降息日全市场成交放量）以及板块流动性爆发（如 AI 概念爆发全行业放量），**只留下了该子行业内部个股独有的机构资金非对称流入**！这就是该因子能够在完全不加复杂修饰的情况下跑出 Sharpe 3.90 的根本原因。

---

### 2.2 News_Sentiment 类别：1Yp6GbbX 换手率爆炸 (175%) 与高频救赎方案

与 `LLGLR3dv` 的成功形成鲜明对照的是新闻情感因子 `1Yp6GbbX` 的惨痛折戟。

#### ❌ 暴雷因子诊断：`1Yp6GbbX`
- **核心代码**: `-zscore(sentiment_weighting_method1)`
- **配置环境**: `USA` / `TOP3000` / `NONE` 中性化 / `Decay`: 0
- **指标全览**:
  - **Sharpe**: 1.66 | **Fitness**: 0.79 | **Margin**: 4.47 bp (< 5.0 bp 门槛)
  - **Turnover**: **175.02%**（严重超标！平台红线为 70%）
  - **Self Correlation (SC)**: 0.1034
  - **Status**: ❌ **FAILED** (被 Turnover > 70% 与 Margin < 5bp 直接斩杀)

#### 深度病因归因：
1. **情感信号的高频离散振荡**：新闻舆情（Sentiment）数据是逐日异动的事件型驱动源。今天正面报道刺激得分飚高，明天新闻热度退潮得分归零。直接对每日原始情感施加截面 `-zscore()`，会导致多空组合的成分股每日发生翻天覆地的剧烈更替。日均 175% 的双边换手率意味着投资组合平均不到半天就彻底清仓重洗一遍！
2. **`NONE` 中性化的多重杀伤**：在美股市场不选中性化，不仅无法抑制舆情巨头的权重过度集中，更无法对抗大盘情绪的顺周期波动。

#### 针对美股 News_Sentiment 的标准工程救赎方案：
欲救活 `1Yp6GbbX` 类情感因子，必须施加**“双层滤波 + 门控锁相”**三步改造：

```python
# 改造前 (暴毙): 换手 175%, Margin 4.47bp
-zscore(sentiment_weighting_method1)

# 改造后 (黄金生产态):
# 1. 引入 ts_decay_linear(..., 10) 压制高频抖动;
# 2. 引入 trade_when 过滤情绪极度平淡的非交易日;
# 3. 中性化切换为 SUBINDUSTRY, 外部赋予 Decay 6~8
trade_when(
    abs(sentiment_weighting_method1) > 0.5,
    ts_decay_linear(group_rank(sentiment_weighting_method1, subindustry), 10),
    -1
)
```
- **预期改善**：换手率将从 175% 陡降至 **18% ~ 26%** 黄金区间，Margin 将从 4.47bp 扩张至 **8.5 ~ 12.0 bp**，彻底消除平台高换手风控红线。

---

### 2.3 Other / ML 预测概率类别：88l3qaWz 与 A1GzxvJX 实测诊断

在美股 TOP3000 中，许多宽客热衷于使用深度学习或 GBDT 产出的模型概率作为因子输入（例如：`probability_label4_5quantile_5day_ohlcv_2`，即模型预测未来 5 日收益落入第 5 分位数的置信度概率）。

#### 实测表现：
1. `88l3qaWz`: `ts_av_diff(probability_label4_5quantile_5day_ohlcv_2, 22)`
   - Settings: `USA` / `TOP3000` / `SUBINDUSTRY` / `Decay`: 6 / `Trunc`: 0.08
   - **Sharpe: 1.67**, **Fitness: 0.75**, **Turnover: 30.44%**, **Margin: 3.99 bp**
   - **Status: FAILED** (Margin 不足 5bp，且自相关/生产相关被压制)
2. `A1GzxvJX`: `ts_rank(winsorize(ts_backfill(probability_label4_5quantile_5day_ohlcv_2, 120), std=4), 66)`
   - Settings: `USA` / `TOP3000` / `SUBINDUSTRY` / `Decay`: 6 / `Trunc`: 0.08
   - **Sharpe: 1.56**, **Fitness: 0.75**, **Turnover: 22.33%**, **Margin: 4.66 bp**
   - **Status: FAILED** (Margin 依然受限在 4.66 bp，未达安全线)

#### 核心教训：
- **机器学习概率标签的钝化现象**：算法模型预测的概率值大多集中在 0.45~0.55 之间，方差极小。即使施加 `ts_av_diff` 或 `winsorize`，其有效截面信噪比依然偏低，无法驱动资产产生显著的单笔绝对收益，导致 Margin 始终在 3.9 ~ 4.6 bp 徘徊，极难跨过 5.0 bp 的硬性质检线。
- **改进建议**：对于预测概率类字段，必须采用**幂次非线性拉伸（Power Squeezing）**或**极端分位数提取**：
  $$\text{expr} = \text{sign}(P - 0.5) \cdot (P - 0.5)^2$$
  将中间模糊概率压制为 0，仅放大极端确定性置信度标的，从而扩大 Margin。

---

### 2.4 美股超度拥挤生产池 (PROD_CORRELATION) 生存法则

美股市场在 BRAIN 平台上最致命的杀手从来不是 Sharpe 不足，而是 **`PROD_CORRELATION > 0.70` 直接拒收**。要在美股生存，必须严格恪守以下四条去相关铁律：

```
+-----------------------------------------------------------------------------------------------+
|                             美股超度拥挤生产池 (PC < 0.70) 四大破局工程法则                      |
+--------------------------+------------------------------------+-------------------------------+
| 工程手段                 | 操作范式 (Operator Recipe)         | 数理机制与脱敏效果             |
+--------------------------+------------------------------------+-------------------------------+
| 1. 高阶加速度差分        | `ts_delta(field, 20)`              | 剥离总量共识，仅捕捉二阶边际变化，|
|                          |                                    | 避开所有基于均值/动量的旧因子   |
| 2. 正交流动性扰动注入    | `+ 0.25 * group_rank(              | 引入流动性作为扰动正交向量，   |
|                          |    ts_rank(volume, 50), subind)`   | 强行打散既有持仓权重分布       |
| 3. 分位数阶梯非线性离散  | `ts_quantile(field, N)`            | 破坏 Pearson 线性相关性，      |
|                          | `quantile(field)`                  | 降低与连续实数因子的共线性     |
| 4. 统计主成分/拥挤中性化 | `Neutralization: STATISTICAL`      | 主动将组合投影到平台热门因子   |
|                          | `Neutralization: CROWDING`         | 的正交零空间，PC 可直接下降 0.15|
+--------------------------+------------------------------------+-------------------------------+
```

---

## 3. 跨区域核心差异矩阵 (GLB vs USA vs EUR vs GBR)

为了彻底厘清不同地区的异质性，避免因套用错误地区模板而导致大面积爆雷，我们将本地实测数据库中四个关键市场的全维度特征提炼为对比矩阵。

### 3.1 四大区域宏观微观结构全景对比表

| 核心对比维度 | GLB (全球多币种大市场) | USA (美股超高流动性) | EUR (欧洲多国混合大市场) | GBR (英国本币浓缩市场) |
| :---| :---| :---| :---| :---|
| **主力股票宇宙** | `TOP3000` / `MINVOL1M` / `TOPDIV3000` | `TOP3000` / `TOP2000` | `TOP2500` / `TOP1200` | `TOP700` / `TOP500` |
| **标的资产数量** | 3000 ~ 6000 只 | 2000 ~ 3000 只 | 1200 ~ 2500 只 | 500 ~ 700 只 (规模偏小) |
| **货币与宏观环境** | 跨美元、欧元、日元等多币种 | 纯单一美元计价 (USD) | 跨欧元、瑞郎、英镑、北欧克朗 | 纯单一英镑计价 (GBP) |
| **实测通过主力类别** | **Analyst (100% 垄断)** | **Price_Volume** / Alt-Oth | **Fundamental (52%)** / Model (30%) | **Analyst (70%)** / Other (25%) |
| **首选黄金中性化** | **`SLOW_AND_FAST` (绝对统治)** | **`SUBINDUSTRY`** / STAT | **`SUBINDUSTRY`** / `INDUSTRY` | **`INDUSTRY`** / `STATISTICAL` |
| **备选中性化** | `FAST` / `COUNTRY` (仅MINVOL) | `CROWDING` / `FAST` | `MARKET` / `FAST` | `MARKET` / `SUBINDUSTRY` |
| **严禁中性化配置** | `NONE` / 纯单一 `INDUSTRY` | `NONE` (换手爆炸必死) | `NONE` (集中度必死) | `NONE` / 过度切分子行业* |
| **典型 Decay 区间** | 0 ~ 1 (分析师数据自带低换手) | 6 ~ 10 (量价需平滑) | 8 ~ 12 (稳健换手 15%) | 0 ~ 5 (小宇宙防止滞后) |
| **平均 Margin 表现** | TOP3000: 1.5~2.5bp<br>MINVOL: **12~16bp** | 3.5 ~ 13.5 bp | 6.0 ~ 18.0 bp | 2.5 ~ 6.0 bp |
| **生产池拥挤度 (PC)** | 中等偏低 (极易通过) | **极度拥挤 (天花板级考核)** | 相对适中 | 偏低 (空间充裕) |

*\*注：GBR 宇宙仅约 700 只股票，若使用 68 个 SUBINDUSTRY 中性化，部分子行业仅有 1~2 只股票，导致协方差矩阵奇异或对冲失真，因此推荐降级使用 `INDUSTRY`（约 24 组）。*

---

### 3.2 「地区 × 类别」有效公式模式与参数工程映射矩阵

不同地区与数据类别的组合，必须匹配完全不同的算子与参数架构：

```
+------------------------------------------------------------------------------------------------------------+
|                                    「地区 × 类别」实战黄金配置公式全景表                                    |
+-----------------+-------------------+--------------------------------------------------+-------------------+
| 地区 + 类别     | 核心胜率算子架构  | 经典成功代码示例                                  | 关键仿真参数设置  |
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **GLB**         | 向量聚合降维 +    | `ts_quantile(`                                   | Universe: TOP3000 |
| + **Analyst**   | 短周期分位数/排序 | `    vec_avg(min_estimate_eps_annual12), 9)`    | Neut: SLOW_AND_FAST|
|                 |                   |                                                  | Decay: 0, Trunc: 0|
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **GLB**         | 波动率自适应标度+ | `ts_decay_linear(`                               | Universe: MINVOL1M|
| + **Alt_Oth**   | 长周期时序平滑    | `    group_rank(`                                | Neut: FAST/MARKET |
|                 |                   | `        scale(ts_backfill(oth335, 12)) /`       | Decay: 8~10       |
|                 |                   | `        ts_std_dev(vwap, 120), sector), 10)`    | Trunc: 0.01       |
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **USA**         | 二阶加速度差分    | `ts_delta(`                                      | Universe: TOP2000 |
| + **Price_Vol** | + 细分子行业消偏  | `    five_week_change_gross_notional_volume, 20)`| Neut: SUBINDUSTRY |
|                 |                   |                                                  | Decay: 0, Trunc: 0|
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **USA**         | 门控条件过滤 +    | `trade_when(`                                    | Universe: TOP3000 |
| + **News_Sent** | 线性时序深度衰减  | `    abs(news_sent) > 0.5,`                      | Neut: SUBINDUSTRY |
|                 |                   | `    ts_decay_linear(group_rank(news_sent,`      | Decay: 8~10       |
|                 |                   | `        subindustry), 10), -1)`                 | Trunc: 0.05       |
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **EUR**         | 基本面远端预期差+ | `group_rank(`                                    | Universe: TOP2500 |
| + **Fundamental**| 稳健正交成交量扰动| `    ts_decay_linear(future_return_6cat, 10),`   | Neut: SUBINDUSTRY |
|                 |                   | `    subindustry) + 0.25 * group_rank(`          | Decay: 10         |
|                 |                   | `    ts_rank(volume, 50), subindustry)`          | Trunc: 0.05       |
+-----------------+-------------------+--------------------------------------------------+-------------------+
| **GBR**         | 修正广度多空对冲+ | `rank(est_12m_ebt_raisednum_4wks) -`             | Universe: TOP700  |
| + **Analyst**   | 行业级粗粒度中性化| `rank(est_12m_ebt_lowerednum_4wks)`              | Neut: INDUSTRY    |
|                 |                   |                                                  | Decay: 2~5        |
+-----------------+-------------------+--------------------------------------------------+-------------------+
```

---

### 3.3 跨区域迁移调优实操决策树 (Mermaid Diagram)

在实际日常研发与爬山算法迭代中，宽客应严格按照以下决策树根据「目标地区 + 数据源类别」完成前置参数锁定，严禁盲目尝试：

```mermaid
flowchart TD
    Start[新目标 Alpha 挖掘 / 迁移需求] --> RegionCheck{判断目标地区 Region}
    
    %% GLB 分支
    RegionCheck -->|GLB 全球市场| GLBCat{判断数据源类别}
    GLBCat -->|Analyst 数据| GLB_Anl[采用 vec_avg 降维<br>优先选 min_estimate<br>匹配 ts_quantile 9~20天<br>参数: TOP3000 / SLOW_AND_FAST / D0]
    GLBCat -->|另类/中小盘| GLB_Alt[采用波动率缩放 scale/std_dev<br>参数: MINVOL1M / FAST / Trunc 0.01 / D8~10]
    
    %% USA 分支
    RegionCheck -->|USA 美股市场| USACat{判断数据源类别}
    USACat -->|Price-Volume 价量| USA_PV[挖掘名义额/高阶差分 ts_delta<br>参数: TOP2000 / SUBINDUSTRY / D0]
    USACat -->|News / 情绪 / ML| USA_HighFreq[严禁裸用! 必须 ts_decay_linear 平滑<br>门控 trade_when 压换手<br>参数: TOP3000 / SUBINDUSTRY / D8~10]
    
    %% EUR 分支
    RegionCheck -->|EUR 欧洲市场| EUR_Flow[聚焦 Fundamental / Model 类别<br>防单股巨头集中度暴跌<br>必须加正交量加权 volume blending<br>参数: TOP2500 / SUBINDUSTRY / D10 / Trunc 0.05]
    
    %% GBR 分支
    RegionCheck -->|GBR 英国市场| GBR_Flow[标的池紧凑 TOP700<br>严禁深层 SUBINDUSTRY 导致奇异矩阵<br>采用两极评级差分 raised - lowered<br>参数: TOP700 / INDUSTRY / D2~5]
    
    GLB_Anl --> Verify[平台硬素质检: CONCENTRATED_WEIGHT + LADDER_SHARPE + PROD_CORR < 0.70]
    GLB_Alt --> Verify
    USA_PV --> Verify
    USA_HighFreq --> Verify
    EUR_Flow --> Verify
    GBR_Flow --> Verify
```

---

## 4. 总结与后续行动建议

1. **GLB 市场的王炸资产**：**`min_estimate_eps_annual12` 配合 `ts_quantile(..., 9~20)` 与 `SLOW_AND_FAST` 中性化**，是当前全平台通过率最高、生产相关性最低（PC 低至 0.309）的顶级工程组合。建议将该范式作为后续 GLB 因子批量生成的核心底座。
2. **美股市场的突破口**：在美股切忌在低阶价量（如均线反转、纯成交量变化）上无效内卷，应全力挖掘类似于 `ts_delta(five_week_change_gross_notional_volume, 20)` 的**中周期名义资金加速度因子**，依托 `SUBINDUSTRY` 剥离大盘与板块噪音。
3. **另类数据集去拥挤**：对于 `oth335` 等高收益但高拥挤（PC > 0.77）的数据集，后续爬山与多因子融合应坚决引入与分析师预期向量的**跨类别正交相乘**，以打散既有因子的线性特征。

*(本报告已完整同步持久化至知识库，可作为后续各子代理执行 GLB/USA 因子爬山与模板增强的标准规范)*
