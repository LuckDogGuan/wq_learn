# 地区独立作战档案：`DEU / TOP500 / D1`（德国市场 · RA 常规主线首选）

> [!IMPORTANT]
> **当前唯一主攻地区**：先专注把 `DEU / TOP500 / D1` 这一条 RA 主线跑透、跑稳、跑出批量结果，再推广到下一个地区。本文件严格区分 **数据集 / 数据字段 / 算子 / 模板 / 表达式 / 模拟设置 / Alpha 结果**，并持续滚动记录实盘结论与漏斗筛选优化。

---

## 1. 德国股票市场特征与 BRAIN 平台规则（因地制宜）

### 1.1 市场微观结构特征
- **标的池规模**：`TOP500` 覆盖德国流动性前 500 只上市股（核心涵盖 DAX / MDAX / SDAX 工业制造、汽车、化工、科技、医疗与金融板块）。
- **单一市场/单一货币优势**：相比 `GLB` 或 `ASI`，德国股票池几乎全在欧股/欧元体系内，**没有跨币种/跨时区割裂问题**，因此不需要复杂的多国 `COUNTRY` 切分，`SUBINDUSTRY` / `INDUSTRY` / `REVERSION_AND_MOMENTUM` / `CROWDING` 中性化效果清晰直接。
- **机构主导与基本面定价**：德国市场以机构与欧洲长线资金为主，分析师盈利修正（`analyst93`）、深度学习趋势预测（`model264`）、财报质量与应计比率（`fundamental6/89/93`）往往具有较好的中期延续性，且中低换手更容易守住 `Margin ≥ 10bp`。

### 1.2 BRAIN 平台 `DEU / TOP500 / D1` 精确规则
- **账号现状**：常驻 Gold 区域；当前账号在 `DEU` 有 **`0` 条已提交 OS Alpha** → 本地自相关池为空（`NO_PEERS_IN_REGION`，零历史撞车包袱！只需防候选池内部 `N×N` 两两互撞 `< 0.68`）。
- **金字塔红利**：6 个空白 D1 金字塔均享 **`1.8×`** 高倍率（`model`, `analyst`, `other`, `fundamental`, `news`, `sentiment`）。
- **RA 常规硬门槛（不混 PPA）**：
  - `Delay = 1`（硬锁）
  - `Sharpe > 1.58` · `Fitness > 1.0` · `1% < Turnover < 70%` · `Max Stock Weight < 10%`
  - `Sub-Universe Sharpe` PASS · `Cluster Test ≥ 1.0`
  - 单数据集（`ATOM`）跳过 `IS_LADDER_SHARPE`，重点守住 **`LOW_2Y_SHARPE > 1.58`**
  - 经验交易成本安全垫：**`Margin ≥ 10bp`**（`margin >= 0.0010`）
  - 相关性终检：本地 SC `< 0.68`、候选池两两 `< 0.68`、远程 PC `< 0.70`
- **并发与免额度优势**：`DEU` 仅占 **1 个并发槽**（`GLB` 占 2 槽），且在 **`2026-12-06`** 前我们已核验出 **189 个 `Alphas = 0` 免每日额度字段**（详见 [FLD-P2-DEU-TOP500-D1.md](../records/fields/FLD-P2-DEU-TOP500-D1.md)）。

---

## 2. 严格分层资产清单（字段 ≠ 模板 ≠ 表达式 ≠ 设置）

### 2.1 数据集与清洗后数据字段（Data Fields）
| 批序 | 数据集 (Dataset) | 目标塔 (倍率) | 队列 | 已清洗可用字段数 | 核心类型与注意点 |
| :-: | --- | :-: | :-: | :-: | --- |
| **第 1 梯队** | `model264` | `model` (`1.8×`) | `Alphas=0` 免额 | **24 个 MATRIX** (`cov=99.6%`, `dCov=1.0`) | 含义为“预测未来下跌概率”，量价/分析师子族先验负向 `reverse(...)`，波动率/特殊项需验正向 |
| **第 2 梯队** | `analyst93` | `analyst` (`1.8×`) | `Alphas=0` 免额 | **38 个真 VECTOR** (`cov=63–65%`, `dCov=1.0`) | 已剔除 5 个 `*_analyst` 纯 ID 陷阱；适合 `vec_avg` / `vec_max` / `vec_min` |
| **第 3 梯队** | `other250` | `other` (`1.8×`) | `Alphas=0` 免额 | **9 个真 VECTOR** (`cov=61.3%`, `dCov=1.0`) | 电商商品评分/畅销排名/价格带；金额字段须用 `ts_rank`/`ts_returns` 消量纲 |
| **第 4 梯队** | `fundamental6` / `89` / `93` | `fundamental` (`1.8×`) | `NORMAL` / `Alphas=0` | `fnd6` 高覆盖 MATRIX + `fnd89/93` 比率 | `fnd6` 原始金额须做比率消除市值偏差；严禁 `*_curcd` 货币代码 |

### 2.2 独立抽象模板库（Templates — 严守 Decision #3 与 5:5 来源）
| 模板 ID | 来源侧 | 抽象模板（`{x}` 为单一清洗后字段 / `{x_a},{x_b}` 为同集双字段） | 经济意图与预期换手 |
| --- | :-: | --- | --- |
| `DEU-T01` | Admin | `reverse(rank({x}))` | 零阶横截面方向探针（检验字段原始预测力） |
| `DEU-T02` | Admin | `rank({x})` | 正向对照组（识别波动率/反转类正向字段） |
| `DEU-T03` | Admin | `reverse(group_rank(ts_zscore({x}, 66), subindustry))` | 季度时序标准化 + 子行业内相对强弱（广州冠军算子） |
| `DEU-T04` | Admin | `reverse(min(rank(ts_zscore({x_a}, 66)), rank(ts_zscore({x_b}, 66))))` | Decision #3 标准双分支共振（同集保 ATOM，无 `+`/`*`） |
| `DEU-T05` | Top100 | `group_zscore(reverse(ts_zscore({x}, 126)), subindustry)` | 半年时序 Z-score + 子行业 Z-score（`SZ83096` 风格） |
| `DEU-T06` | Top100 | `signed_power(group_zscore(reverse(ts_mean({x}, 22)), subindustry), 1.5)` | 月度平滑控换手 + `signed_power` 降 PC 尾部增强 |
| `DEU-T07` | Top100 | `reverse(rank(ts_rank({x}, 126)))` | 半年时序分位（抗极端值与量纲漂移） |
| `DEU-T08` | Top100 | `reverse(group_neutralize(ts_decay_linear(ts_delta({x}, 22), 10), subindustry))` | 1M 边际变化 + 轻度衰减 + 子行业中性化 |

### 2.3 模拟设置基线（Simulation Settings）
- **基线设置（Stage 2 筛选固定）**：`region=DEU`, `universe=TOP500`, `delay=1`, `neutralization=SUBINDUSTRY`, `decay=0`, `truncation=0.04`, `pasteurization=ON`, `unitHandling=VERIFY`, `nanHandling=ON`, `maxTrade=OFF`, `visualization=false`。
- **中性化轮换序列（Stage 3 单轴优化时才切换）**：`SUBINDUSTRY` → `INDUSTRY` → `REVERSION_AND_MOMENTUM` → `CROWDING` → `MARKET`。

---

## 3. 分阶段漏斗筛选策略（不丢弃好结果，通过分层筛选自然抬高池质量）

1. **全量落盘原则**：每一条在 `DEU` 跑完的 Alpha（无论 Sharpe 高低）全部永久存入 SQLite `sim_tasks` 表，**绝不删丢任何中间好结果**。
2. **四级分层池（自然抬升入围质量）**：
   - `POOL_S (GATE3_TIER1_PASS)`：全指标过 RA 门槛（`Sh > 1.58, Fit > 1.0, 2Y > 1.58`, 0 阻断项）→ 直接进 Stage-4 正交去重 + 远程 PC + 打 `Useful`！
   - `POOL_A (NEAR_MISS_ONE_FIX)`：`Sh ≥ 1.35` 且仅差 1 项（如 `2Y` 差一点或 `Weight` 压线）→ 优先进 Stage-3 单变量微调！
   - `POOL_B (SIGNAL_SEEDS)`：`0.80 < Sh < 1.35` 且 2Y 为正、无厂字型 → 保留作为双分支 `min(rank(expr_A), rank(expr_B))` 组合素材池！
   - `POOL_FLIP`：`Sh < -1.20` → 自动记录方向翻转任务 `reverse(...)`！
   - `POOL_DROP`：`-1.20 ≤ Sh ≤ 0.80` 或厂字型平直 → 留在账本做负样本统计（满 200 样本触发作用域归因），不进入精修队列，自然抬升进入精修池的整体 Sharpe！

---

## 4. 实盘运行与持续优化日志（滚动追加）

- **2026-11-25 17:02（T0 校准批 `EXP-T0-FULL` & `EXP-T0-QUICK`，16/16 零错完成）**：详见 [t0_calibration_report.md](../records/rules/t0_calibration_report.md)。
  - **关键实证结论 ①**：`FULL`（`144s`）与 `QUICK`（`132s`）耗时仅差 8.1%，且 `QUICK` 丢失 `rn_sharpe`，因此 `DEU` 生产批**直接全走 `FULL`**；
  - **关键实证结论 ②**：`model264` 原始日频信号直接做 `ts_zscore`/`ts_rank` 换手高达 `67%–101%`，但**前置 `ts_mean(..., 22)` 平滑**后（`gJr6Zd8g`）换手降至 **`2.37%`**、**`Margin = 26.11bp`**、`2Y = +0.55`！已据此将广州 `DEU` 生产模板全线升级为前置平滑（`ts_mean 22` / `ts_decay_linear 10`）+ `subindustry` 分组，并增补 `fundamental6` 低换手财报比率梯队。
- **2026-11-25 17:05（广州 `DEU` 专属 RA 服务上线）**：部署 `worldquant-v2-deu-ra.service`（4 槽 × 8 条 `FULL` Multi-Sim，硬限 `MemoryMax=512M`，日目标 `3,000`，全量保留分池 `deu_ra_funnel_latest.json` 绝不丢弃任何好结果）。
