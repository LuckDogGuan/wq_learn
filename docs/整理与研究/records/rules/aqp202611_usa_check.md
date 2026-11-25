# `AQP202611`（2026 年 11 月 Alpha Quality Project）零成本全量核查与 3 条 USA OS 标记方案

> [!IMPORTANT]
> **核查基准时间**：2026-11-25（北京时间），全程严格只读 `cnhkmcp`（`get_competition_details`、`get_competition_agreement`、`get_user_alphas(stage="OS")`、`get_alpha_details`、`get_alpha_yearly_stats`、`get_alpha_pnl`），**未对平台执行任何写入或提交操作**。
> **截止红线**：`2026-11-30T23:59:59-05:00`（**北京时间 `2026-12-01 12:59:59`**，距今仅剩 **5 天**）。

---

## 1. 核查核心结论（TL;DR）

1. **报名状态与当前标记进度**：
   - 账号 `JG81923` 在 `AQP202611`（*Alpha Quality Project November 2026*）中状态为 **`ACCEPTED`**（已自动生效）。
   - **全部 29 条 `USA/TOP3000/D1` OS Alpha 中，当前 `0 / 29` 条已标记 `AQP202611`**（`competitions` 与 `tags` 均无 `AQP202611`；全部 92 条 OS 的 `is.checks.MATCHES_COMPETITION` 均处于 `WARNING` 未匹配状态）。
   - **必须由用户在 BRAIN 平台 UI 手动完成标记与描述补充**，零回测成本即可参评。
2. **官方协议关键计分规则（源自 `get_competition_agreement("AQP202611")` 原文实核）**：
   - **精准数量与必备条件**：必须标记**恰好 3 条**既往已提交的 **USA Region** Alpha，**并在比赛窗口期内为其编写合适的英文假设说明（`description`）**（*"tagging three of their previously submitted Alphas in USA Region and adding an appropriate description for the same"*）。
   - **双重评审维度**：按 **Out-Sample Sharpe** 与 **Alpha 假设描述质量（quality of the Alpha hypothesis as part of the description）** 综合评审。
   - **等权组合计分（核心策略拐点！）**：3 条 Alpha 按**等额资金等权合成（Equal-Weighted）**计算组合 OS Sharpe；平分按平均 OS Fitness 等排序。因此**低两两相关性分散组合显著优于盲选高相关同族三胞胎**！
   - **奖金池（一次性专项津贴）**：第 1 名 `US\$ 2,000` · 第 2 名 `US\$ 1,200` · 第 3 名 `US\$ 800` · 第 4–10 名各 `US\$ 250` · 第 11–25 名各 `US\$ 150` · 第 26–50 名各 `US\$ 80`。
3. **立即行动推荐（三选一，按平台 UI 实际可选资格拍板）**：
   - **【首选 · 纯 Regular 稳健高分散组合】**：**`O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ`**（3 条全为 2026 顾问期 `REGULAR`、无 `COMPENSATED_ALPHA` 警示、平均 PC=`0.622`、等权 10Y IS Sharpe=**`3.00`**、2Y Sharpe=**`2.92`**、平均 Fitness=`1.71`、平均两两相关=`0.428`）。
   - **【首选备选 A · 纯 Regular 10/10 年全正收益 + 最强风险中性】**：**`O0rqZ3aY` + `3q936AEN` + `A10Ygvdl`**（10/10 年全为正收益、2023 组合 Sharpe=`1.33`、平均 Fitness=**`1.76`**、RN Sharpe 全员 `≥1.53`，且不含 `trade_when`；缺点是三者同属 `anl4_afv4_eps_mean/EV + fnd6/assets` 家族，平均两两相关 `0.536`，10Y 组合 Sharpe=`2.93`）。
   - **【若 UI 允许标记 Power Pool Alpha · 2026 顾问期最高 10Y 组合 Sharpe】**：**`O0rqZ3aY` + `3q936AEN` + `omYMxop5`**（等权 10Y IS Sharpe=**`3.07`** 居首、10/10 年全正、2023 组合 Sharpe=`1.20`、平均两两相关降至 **`0.385`**，`omYMxop5` 已有完整英文描述；须在 UI 确认 `POWER_POOL_ELIGIBLE` 是否可选）。
   - **【关键必做补充动作】**：`O0rqZ3aY`、`3q936AEN`、`A10Ygvdl` 当前 `regular.description` 均为 **`null`**（空白），标记时**务必同步填入文末第 5 节已备好的英文 `Idea + Rationale` 描述**！

---

## 2. 全部 29 条 USA OS Alpha 两代分群审计与排雷

经 `get_user_alphas(stage="OS")` 与 `get_alpha_details` 逐条核对，本账号 29 条 `USA/TOP3000/D1` OS Alpha 严格分为两个历史世代：

| 分群 | 数量 | 提交日期范围 | IS 区间 / OS 起始 | 分类构成 | 平台合规与排雷结论 |
| --- | :---: | --- | --- | --- | --- |
| **A 群 · 2026 顾问正式期** | **13 条** | `2026-06-01` – `2026-09-07` | 10Y (`2014–2023`) / `os.startDate=2024-01-01` | 8 条 `REGULAR` + 5 条 `POWER_POOL_ELIGIBLE` | **核心候选池**。无 `COMPENSATED_ALPHA: WARNING`；含完整 `prodCorrelation`、`selfCorrelation`、`investabilityConstrained` 与 `riskNeutralized`（注：顾问期近期 OS 指标在 API 返回 `None` 属平台窗口展示机制）。 |
| **B 群 · 2025 挑战期（Challenge）** | **16 条** | `2025-10-28` – `2025-11-14` | 5Y (`2018–2023`) / `os.startDate=2023-01-21` | 16 条 `REGULAR`（均带 `competitions=['challenge']`） | **高风险慎用群**。全部带 `os.checks: COMPENSATED_ALPHA: WARNING` 且 `is.prodCorrelation` 未留存（如 `889bj3jl` 名称自标 `PC0.9666`）。虽可见 2023 历史 OS 指标（`wpmNbAY1` OS Sh=2.07、`rK3qPjpj` OS Sh=1.71、`LLWKZ7EL` OS Sh=1.50），但 `wpmNbAY1` 仅 0 算子单字段 `anl4_adjusted_netincome_ft`（假设单薄且同字段 `xARZ27Vw` PC=0.9906），且 2023 IS 表现弱（`rK3qPjpj` 2023 IS=-2.59、`LLWKZ7EL` 2023 IS=-4.66）。仅作 UI 确认可选后的备选参考。 |

### A 群（13 条 2026 顾问期 USA OS）明确排雷项（不建议标记）
- **`E5k9E9gr`**（`POWER_POOL_ELIGIBLE + SINGLE_DATA_SET`）：虽 Fitness=`2.11`、Margin=`90.2bp`，但 **`PC = 0.9995`** 且 `IS Sharpe = 1.51 < 1.58`（`LOW_SHARPE: WARNING`）。
- **`xARZ27Vw`**（`POWER_POOL_ELIGIBLE + SINGLE_DATA_SET`）：**`PC = 0.9906`**、SC=`0.9234`、IS Sharpe=`1.35`、RN Sharpe=`0.73`，且 `description` 为随手中文测试句（*"Idea: just do it ，i think..."*），严重扣分。
- **`P01ljqLx`**（`REGULAR`）：**`PC = 0.7649`**、SC=`0.7649`（均超 `0.70`），且其 `description` 文不对题（代码为 `group_neutralize(ts_zscore(...), pv13_...)`，描述却写了 `trade_when` 与 `returns`）。
- **`XgKL25az`**（`POWER_POOL_ELIGIBLE`）：IS Sharpe=`2.05`、Fit=`1.56`，但 **`PC = 0.7359 > 0.70`**、SC=`0.6869`。
- **`JjdlElYO`**（`POWER_POOL_ELIGIBLE`）：**`PC = 0.7277 > 0.70`**，且 `IS_LADDER_SHARPE: WARNING (1.52 < 1.58)`。
- **`3qAvQxk6`**（`REGULAR`）：`PC = 0.6996`（紧贴 `0.70` 边界）、Fitness 仅 `1.07`、RN Sharpe=`1.08`、`description` 为原始 JSON 格式。

---

## 3. Top 8 最佳 USA OS Alpha 综合排序与全维度实测表

> **说明**：Margin 已按官方口径精确换算（API 小数 `0.01 = 100bp`）；`10Y 正年数` 源自 `get_alpha_yearly_stats` 实测。

| 排名 | Alpha ID | 提交日 & 世代 | 分类 | IS Sharpe | Fitness | TO | Margin (bp) | IC / RN Sharpe | PC / SC | 2Y / Ladder | 正收益年数 (2023 IS) | OS 实测 (仅 B 群可见) | Description 状态 | 核心信号与风控点评 |
| :-: | --- | --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | --- | --- | --- |
| **1** | **`O0rqZ3aY`** | `2026-09-06` (A群) | `REGULAR` + `CLUSTER` | **2.63** | **1.96** | 7.91% | 17.5 | **2.49 / 1.94** | **0.645 / 0.543** | 2.17 (2Y) | **10/10** (`0.99`) | `None` (窗口期) | **`null`（必补！）** | 全池绝对核心！IS/Fit/IC/RN/Cluster(`1.63`) 全面断层第一；`anl4_afv4_eps_mean/EV` 与 `fnd6_drlt/assets` 行业排名取大 + `ts_target_tvr_decay` |
| **2** | **`3q936AEN`** | `2026-09-07` (A群) | `REGULAR` | **2.36** | **1.73** | **6.04%** | **22.1** | **2.18 / 1.53** | **0.607 / 0.548** | 2.18 (2Y) | **10/10** (`0.88`) | `None` (窗口期) | **`null`（必补！）** | 低换手高 Margin 优等生；`anl4_afv4_eps_mean/EV (120d)` 与 `fnd6_acox/assets` 全市场排名取大 + `decay=4`；与 `O0rqZ3aY` 相关 `0.502` |
| **3** | **`A10Ygvdl`** | `2026-09-07` (A群) | `REGULAR` | **2.28** | **1.59** | 9.80% | 12.4 | 1.93 / **1.72** | **0.621 / 0.606** | **2.63 (3Y)** | **10/10** (`1.25`) | `None` (窗口期) | **`null`（必补！）** | 3 年阶梯与 RN 稳健性强，2023 Sharpe=`1.25`；与 `O0rqZ3aY`/`3q936AEN` 相关 `0.525`/`0.582` |
| **4** | **`ZYoW7wMZ`** | `2026-06-12` (A群) | `REGULAR` | **2.07** | **1.44** | 8.70% | 13.9 | **1.94 / 1.48** | **0.614 / 0.369** | **2.49 (2Y)** | 8/10 (`-0.08`, 2022=`4.43`) | `None` (窗口期) | **完整英文三段式** | **最佳跨家族 Regular 搭档！** 底层换用 `anl4_..._ptp_low/EV` + `imb5_mktcap` 市值分桶 + 量价负相关门控；与 #1/#2 相关仅 `0.361`/`0.421`（注：含历史 `trade_when` 且 2023 微负 `-0.08`） |
| **5** | **`omYMxop5`** | `2026-06-05` (A群) | `POWER_POOL` | **2.03** | 1.01 | 20.53% | 4.9 | 1.70 / — | 0.676 / **0.267** | 1.32 (`WARN`) | **10/10** (`0.69`) | `None` (窗口期) | **完整英文三段式** | **2026 群最极简分散器！** 仅 2 算子 `ts_rank(anl4_..._fcf_high/EV, 120)` + `STATISTICAL` 中性化；与 #1/#2 相关仅 `0.379`/`0.272`；**须确认 UI 是否允许 Power Pool 参赛** |
| **6** | **`9qRa7wde`** | `2026-06-14` (A群) | `REGULAR` | 1.77 | 1.14 | 11.41% | 9.0 | 1.53 / 1.17 | **0.600 / 0.600** | 2.34 (4Y) | 9/10 (`0.37`) | `None` (窗口期) | `null` | PC 最低的 Regular（`0.6004`），2023 正收益；但与 `ZYoW7wMZ` 同源相关 `0.642` 且含 `UNITS: WARNING` |
| **7** | **`3qA6dvlN`** | `2026-06-07` (A群) | `REGULAR` | 1.66 | 1.05 | 11.31% | 8.9 | 1.39 / 0.97 | 0.673 / **0.141** | 2.58 (2Y) | 9/10 (**`2.73`**) | `None` (窗口期) | **文不对题（须重写！）** | 2023 IS Sharpe=`2.73` 全群最高、SC=`0.141` 极低；但整体 Fit 偏低且现有 `description` 与代码不符（写成了 `ts_av_diff(close,5)`） |
| **8 (B群)** | **`rK3qPjpj`** / **`LLWKZ7EL`** / **`wpmNbAY1`** | `2025-11` (B群 Challenge) | `REGULAR` (`challenge`) | 1.94 / 1.77 / 1.72 | 1.76 / 1.15 / 2.03 | 6.3% / 2.9% / 3.2% | 32.9 / 36.1 / 107.4 | 无记录 | 未留 PC (SC `0.66`/`0.73`/`0.53`) | 3.00 / 2.32 / 2.71 | 5Y IS (`rK3`/`LLW` 2023 IS 负) | **OS Sh=`1.71` / `1.50` / `2.07`** (`Fit=1.38/0.87/2.53`) | 空模板 / `null` / `null` | 历史 2023 OS 实证优秀且与 A 群低相关（`0.00–0.21`）；**但全带 `COMPENSATED_ALPHA: WARNING` + `challenge` 归属**，`wpmNbAY1` 为 0 算子单字段假设薄弱 |

> 注：其余 13 条 B 群挑战期 Alpha（如 `889bj3jl` 标称 `PC0.9666`、`P0N1agGE` OS Sh=`1.08`、`akYK6pKv` OS Sh=`-1.09` 等）综合质量与合规度均显著弱于上述 Top 8，不列入推荐。

---

## 4. 实测 PnL 两两相关性矩阵与等权 3-Alpha 组合优选

基于 `get_alpha_pnl` 拉取的真实每日 PnL（A 群对齐 **`2,494` 交易日** `2014–2023`；含 B 群对齐 **`1,474` 交易日** `2018–2023`），精确计算两两日收益 Pearson 相关系数：

### 4.1 A 群（2026 顾问期 7 强）两两相关矩阵

| Alpha ID | `O0rqZ3aY` | `3q936AEN` | `A10Ygvdl` | `ZYoW7wMZ` | `9qRa7wde` | `3qA6dvlN` | `omYMxop5` |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **`O0rqZ3aY`** | 1.000 | 0.502 | 0.525 | **0.361** | 0.407 | 0.475 | **0.379** |
| **`3q936AEN`** | 0.502 | 1.000 | 0.582 | **0.421** | 0.364 | 0.352 | **0.272** |
| **`A10Ygvdl`** | 0.525 | 0.582 | 1.000 | 0.395 | 0.348 | 0.350 | 0.270 |
| **`ZYoW7wMZ`** | 0.361 | 0.421 | 0.395 | 1.000 | 0.642 | 0.374 | 0.277 |
| **`9qRa7wde`** | 0.407 | 0.364 | 0.348 | 0.642 | 1.000 | 0.516 | 0.351 |
| **`3qA6dvlN`** | 0.475 | 0.352 | 0.350 | 0.374 | 0.516 | 1.000 | 0.294 |
| **`omYMxop5`** | 0.379 | 0.272 | 0.270 | 0.277 | 0.351 | 0.294 | 1.000 |

### 4.2 等权 3-Alpha 组合 Sharpe 精确回测对比（直击 AQP 官方等权计分规则）

| 推荐档位 | 3 条 Alpha ID 组合 | 组合类型 | 等权 10Y IS Sharpe | 2Y 组合 Sharpe (`22–23`) | 2023 组合 Sharpe | 平均 IS Fitness | 平均两两相关 | 最大两两相关 | 核心优缺点与适用前提 |
| --- | --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| **★ 主推方案 1（均衡最优 · 纯 Regular）** | **`O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ`** | 3 × `REGULAR` (2026) | **3.00** | **2.92** | 0.82 | **1.71** | **0.428** | 0.502 | **零资格风险**，2Y 组合 Sharpe 全场最高（`2.92`），跨两套底层逻辑（EPS+资产负债 vs 税前利润下界+市值分桶量价），`ZYoW7wMZ` 已有完整描述；须为前两条补写英文描述 |
| **★ 主推方案 2（若 UI 允许 Power Pool · 10Y 第一）** | **`O0rqZ3aY` + `3q936AEN` + `omYMxop5`** | 2 × `REGULAR` + 1 × `PP` (2026) | **3.07** | 2.50 | **1.20** | 1.57 | **0.385** | 0.502 | **2026 顾问期等权 10Y Sharpe 绝对第 1（`3.07`）**，全员 10/10 年正收益，2023 组合 Sharpe 高达 `1.20`，`omYMxop5` 引入 FCF/EV + `STATISTICAL` 正交维度且已有完整描述；**前提：在平台 UI 实测确认 `omYMxop5` 可打 `AQP202611` 标签** |
| **备选方案 3（最稳 2023 + 最高 Fitness · 纯 Regular）** | **`O0rqZ3aY` + `3q936AEN` + `A10Ygvdl`** | 3 × `REGULAR` (2026) | 2.93 | 2.57 | **1.33** | **1.76** | 0.536 | 0.582 | 全员 10/10 年正收益、平均 Fitness 最高（`1.76`）、RN Sharpe 全员 `≥1.53`、无 `trade_when`；仅因同家族相关性偏高，等权 Sharpe 略低于方案 1/2 |
| **备选方案 4（若 UI 允许 B 群 Challenge Alpha）** | **`O0rqZ3aY` + `ZYoW7wMZ` + `LLWKZ7EL`**（或 `rK3qPjpj`） | 2 × 2026 + 1 × 2025 Challenge | **3.23** *(18–23)* | — | *(LLW 23 OS=1.50)* | 1.52 | **0.189** | 0.361 | 极低相关且 `LLWKZ7EL`（ATOM）/`rK3qPjpj` 具已实现 2023 OS 正业绩；**高风控提醒：仅当 BRAIN 官网 AQP202611 标记面板明确显示其可选且不受 `COMPENSATED_ALPHA: WARNING` 排除时考虑** |

---

## 5. 2026-11-30 前人工操作清单与即拷即用英文 Description

> [!CAUTION]
> **系统边界**：本流程严禁调用 `set_alpha_properties` 或 `submit_alpha`。请用户亲自在 WorldQuant BRAIN 网页端完成以下 3 步（耗时约 3–5 分钟，0 回测消耗）：

1. **步骤 1 · 登录确认可选范围**：打开 BRAIN `Alphas` → `Submitted (OS)` 筛选 `Region = USA`，进入 `AQP202611` 标记界面，确认 `omYMxop5`（Power Pool）是否允许加入 `AQP202611`：
   - 若 **允许**：优先采用 **方案 2（`O0rqZ3aY` + `3q936AEN` + `omYMxop5`）**；
   - 若 **仅限 Regular**：优先采用 **方案 1（`O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ`）**（若更看重 2023 近端全正收益与无 `trade_when`，改选 **方案 3：`O0rqZ3aY` + `3q936AEN` + `A10Ygvdl`**）。
2. **步骤 2 · 补全英文 Alpha Hypothesis Description（AQP 官方评分项！）**：
   - `ZYoW7wMZ` 与 `omYMxop5` 已有结构完整的英文三段式描述，可直接保留。
   - 对当前 `description = null` 的 **`O0rqZ3aY`**、**`3q936AEN`**（及若选用 **`A10Ygvdl`**），在平台详情页粘贴下方对应的英文说明并保存：

### `O0rqZ3aY` 推荐英文 Description
> **Idea:**
> Combine forward analyst earnings-yield momentum with balance-sheet capital structure resilience within each sector, selecting stocks that exhibit either unusually improving forward profitability relative to enterprise value or strong long-term financial positioning relative to total assets, while dynamically controlling daily turnover to preserve signal quality net of trading costs.
>
> **Rationale for data used:**
> `anl4_afv4_eps_mean` captures consensus forward analyst EPS expectations, and dividing by `enterprise_value` forms an enterprise-level forward earnings yield that accounts for both equity and debt financing. `fnd6_drlt` (long-term deferred revenue / balance-sheet obligation metric) scaled by `assets` captures structural fundamental positioning and revenue visibility across capital-intensive firms. `sector` ensures peer-relative comparability across industries with distinct valuation and accounting structures.
>
> **Rationale for operators used:**
> `ts_zscore(..., 252)` normalizes each stock's forward earnings yield against its trailing one-year history to isolate positive expectation inflections. `group_rank(..., sector)` aligns both the earnings-yield inflection signal and the asset-scaled fundamental metric onto a uniform `[0, 1]` cross-sectional scale within each sector. Taking `max(...)` rewards stocks demonstrating strong conviction on either fundamental catalyst without diluting clear signals via linear averaging. Finally, `ts_target_tvr_decay(..., target_tvr=0.08)` adaptively smooths portfolio weights toward an 8% turnover target, reducing trading friction while retaining industry-neutral alpha under `INDUSTRY` neutralization.

### `3q936AEN` 推荐英文 Description
> **Idea:**
> Identify undervalued firms experiencing medium-term upward shifts in forward earnings yield or holding elevated non-operating/other current asset buffers relative to total assets, combining both fundamental dimensions through a non-linear upper-envelope rank and adaptive turnover-targeted smoothing.
>
> **Rationale for data used:**
> `anl4_afv4_eps_mean / enterprise_value` measures consensus forward earnings relative to total firm valuation, highlighting attractively priced earnings power. `fnd6_acox / assets` measures other current assets normalized by total assets, capturing working-capital flexibility and liquidity reserves that help buffer earnings shocks.
>
> **Rationale for operators used:**
> `ts_zscore(..., 120)` detects semi-annual shifts in forward earnings yield relative to each stock's own recent baseline. `rank(...)` transforms both heterogeneous signals into comparable cross-sectional percentiles across `TOP3000`. `max(...)` emphasizes stocks ranking strongly in either earnings-yield improvement or balance-sheet liquidity cushion. `ts_target_tvr_decay(..., target_tvr=0.08)` combined with `decay=4` and `INDUSTRY` neutralization enforces low turnover (~6%) and high margin (~22 bps) while controlling industry exposure.

### `A10Ygvdl` 推荐英文 Description（若采用方案 3 时填写）
> **Idea:**
> Capture sector-relative fundamental upside by combining medium-term forward earnings-yield acceleration with short-term operating liability structure scaled by total assets, stabilized via target-turnover decay under subindustry neutralization.
>
> **Rationale for data used:**
> `anl4_afv4_eps_mean / enterprise_value` reflects consensus forward earnings relative to enterprise valuation. `fnd6_newqv1300_lcoq / assets` measures quarterly other current liabilities relative to total assets, capturing operating working-capital dynamics and trade-credit financing intensity relative to firm scale.
>
> **Rationale for operators used:**
> `ts_zscore(..., 120)` standardizes forward earnings yield over a 120-trading-day window to isolate improving expectations. `group_rank(..., sector)` maps both the forward earnings-yield signal and the quarterly liability-to-assets ratio into sector-neutral cross-sectional percentiles. `max(...)` combines the two signals non-linearly to highlight top-conviction names, and `ts_target_tvr_decay(..., target_tvr=0.08)` suppresses excess turnover while `SUBINDUSTRY` neutralization removes granular industry risk.

3. **步骤 3 · 复核确认**：完成 3 条 Alpha 的 `AQP202611` 标签勾选与描述保存后，在 `AQP202611` 竞赛页面核对已显示 **3 / 3 Tagged USA Alphas**（确保于 **2026-11-30 23:59 EST / 北京时间 12-01 12:59** 前完成）。
