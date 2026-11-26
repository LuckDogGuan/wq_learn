# `AQP202611`（2026 年 11 月 Alpha Quality Project）专项优化日志

> [!IMPORTANT]
> **日志定位**：本文件为 `AQP202611` 竞赛的专项优化与追踪真源，记录每次 API 诊断快照、等权 3-Alpha 组合数学寻优结果、标签/描述变更记录与剩余窗口期冲刺动作。
> **截止时间**：`2026-11-30T23:59:59-05:00`（**北京时间 `2026-12-01 12:59:59`**）。
> **操作红线**：严格遵守 `AGENTS.md`（D1-Only、永不自动 `POST /alphas/{id}/submit`、`PATCH /alphas/{id}` 改标签/描述须经用户显式确认）。

---

## 1. 核心真相澄清：为什么目前显示“第 348 名”？

经 `GET /competitions/AQP202611/boards/leader`（2026-11-26 10:32 CST）实测核验：

| 指标 | API 实测结果 | 含义解读 |
| --- | --- | --- |
| 总参赛人数 | **`1,327` 人** | 截至 2026-11-26 10:32 CST |
| 第 1–5 名 | `AA17617`, `AA21439`, `AA21983`, `AA40425`, `AB61897`（均 `alphas=3`） | **纯按 User ID 字母表升序排列** |
| 第 46–50 名（奖金线） | `AS14569` … `AS66470`（均 `alphas=3`） | 同上，榜单尚无任何分数字段 |
| 第 76–80 名 | `BJ65592` … `BK74354`（均 `alphas=3`） | 同上 |
| **本账号（第 348 名）** | **`JG81923`（`alphas=3`）**，前后为 `JG69762`(#347)、`JH56177`(#349) | **并非表现落后！**仅因首字母 `JG` 排在 `AA–JF` 之后 |

**结论**：
1. **11 月 5 日–11 月 30 日仅为“标签锁定与描述完善窗口期”**，当前榜单尚未计入 OS Sharpe 分数，所有标满 3 条 Alpha 的用户按字母序占位。
2. **真正的胜负在 11 月 30 日截止后结算**，评审两大核心维度（源自 `GET /competitions/AQP202611/agreement`）：
   - **等额资金等权组合（Equal-Weighted）Out-of-Sample Sharpe**（平分按平均 OS Fitness 等）；
   - **英文 Alpha Hypothesis Description 质量**（清晰阐述 Idea、数据逻辑、算子逻辑，严禁空描述或文不对题）。
3. **奖金结构**：前 **50 名** 均有一次性现金津贴（#1 \$2,000 / #2 \$1,200 / #3 \$800 / #4–10 \$250 / #11–25 \$150 / #26–50 \$80）。只要组合等权 OS Sharpe 够高且描述扎实，不仅能进前 80，完全有希望直接冲击**前 50 拿奖**！

---

## 2. 现有 30 条 USA OS 全量组合优化（含新提交 `e71w5Qrl`）

2026-11-25 21:03 EST（北京时间 11-26 10:03）账号新提交了第 30 条 USA OS Alpha：**`e71w5Qrl`**（`USA/TOP3000/D1`, `model31`, `REGULAR + SINGLE_DATA_SET`, IS Sharpe `1.71`, **2Y Sharpe `2.63`**, Margin `18.58bp`, SC `0.536`, PC `0.694`）。
经 `GET /alphas/e71w5Qrl` 实测，其 `is.checks.MATCHES_COMPETITION` 明确包含 **`AQP202611`**，**确认完全具备参赛资格**！

### 2.1 `e71w5Qrl` 与其他 2026 顾问期 Regular USA OS 的 10Y 日收益相关性
| 对比 Alpha ID | 10Y 日收益 Pearson 相关 | 协同点评 |
| --- | :-: | --- |
| `O0rqZ3aY`（核心 #1，IS 2.63） | **`0.117`** | 极低相关！完美正交 |
| `ZYoW7wMZ`（当前第 3 条，IS 2.07） | **`0.081`** | 几乎完全独立！ |
| `A10Ygvdl`（2023 最稳，IS 2.28） | **`0.117`** | 极低相关！ |
| `3q936AEN`（当前第 2 条，IS 2.36） | `0.245` | 低相关 |
| `9qRa7wde`（IS 1.77） | `0.046` | 近零相关 |
| `3qA6dvlN`（2023 IS 2.73） | `0.058` | 近零相关 |

### 2.2 等权 3-Alpha 组合全排列寻优对比（对齐 `2,494` 交易日 `2014–2023`）

| 方案 | 3 条 Alpha 组合 | 10Y 等权 Sharpe | 2Y (`22–23`) Sharpe | 2023 单年 Sharpe | 10Y 最差单年 Sharpe | 平均两两相关 | 最大两两相关 | 平均 Fitness | 平均 PC | 综合评价 |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| **当前已标（旧）** | `O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ` | 2.996 | 2.918 | 0.822 | 0.82 | 0.428 | 0.502 | 1.71 | 0.622 | 前两条同源 `anl4_eps` 相关 0.502，拖累分散度；2023 偏弱 |
| **★ 新最优 A（最高 10Y & 2Y）** | **`e71w5Qrl` + `O0rqZ3aY` + `ZYoW7wMZ`** | **3.151** | **3.483** | 1.819 | 1.29 | **0.187** | **0.361** | 1.49 | 0.651 | **全池第 1（含 PP 池也第 1）！**相关腰斩至 0.187，2Y 暴涨 +0.565；仅需为 `e71w5Qrl` 补写英文描述并替换 `3q936AEN` |
| **★ 新最稳 B（最强 2023 & 无弱年）** | **`e71w5Qrl` + `O0rqZ3aY` + `A10Ygvdl`** | **3.125** | 3.015 | **2.223** | **1.70** | 0.253 | 0.525 | **1.54** | 0.653 | **10 年最差单年仍高达 1.70！**无 `trade_when`、全员 10/10 全正、RN Sharpe 强；需为 `e71w5Qrl` 与 `A10Ygvdl` 补写描述 |
| **备选 C** | `e71w5Qrl` + `O0rqZ3aY` + `3q936AEN` | 3.086 | 3.089 | 2.141 | 1.22 | 0.288 | 0.502 | **1.59** | 0.649 | 保留高 Margin(22.1bp) 的 `3q936AEN`，剔除含 `trade_when` 且 2023 微负的 `ZYoW7wMZ` |

---

## 3. 未来 5 天冲刺策略（冲击 Top 50 / Top 80）

基于等权组合 Sharpe 公式 $S_{\text{port}} \approx \frac{S_1 + S_2 + S_3}{\sqrt{3 + 2(\rho_{12} + \rho_{13} + \rho_{23})}}$，当前优化分两步走：

### 第一步：零回测成本立即可执行（API `PATCH /alphas/{id}`，今日即可落地）
- **换掉 `3q936AEN` → 换入 `e71w5Qrl`**（方案 A：`e71w5Qrl` + `O0rqZ3aY` + `ZYoW7wMZ`，或方案 B：`e71w5Qrl` + `O0rqZ3aY` + `A10Ygvdl`）。
- 立即通过 API 为 `e71w5Qrl` 写入高质量英文三段式 `Idea + Rationale` 描述（见第 4 节），并调整 `AQP202611` 标签（严格保持恰好 `3 / 3` 条）。
- 这一步零回测成本即可将等权 10Y Sharpe 从 `2.996` 提到 **`3.151`**，2Y Sharpe 从 `2.918` 提到 **`3.483`**，2023 Sharpe 从 `0.822` 翻倍至 **`1.82–2.22`**。

### 第二步：剩余 4 天（11/26–11/30）精准攻克“第 3 槽位正交王牌”（目标将组合推至 `3.35–3.55+`）
- **锁定前 2 槽**：
  - Slot 1：`O0rqZ3aY`（`analyst4` EPS + `fundamental6` 资产负债，IS `2.63`）
  - Slot 2：`e71w5Qrl`（`model31` 资产周转 + 应计项目，2Y `2.63`，与 Slot 1 相关 `0.117`）
- **专攻 Slot 3（替换 `ZYoW7wMZ` 或 `A10Ygvdl`）**：
  - **目标画像**：`USA / TOP3000 / D1 / REGULAR`；**避开 `analyst4` EPS 与 `model31`**；主攻高正交数据集（如 `model30`、`model110`、`sentiment`、`news`、`option`、`shortinterest`、`fundamental` 非资产负债维度、或 `USA Alphas=0` 新字段）；
  - **硬门槛**：IS Sharpe `≥ 2.00`、2Y Sharpe `≥ 2.20`、Fitness `≥ 1.20`、PC `< 0.70`、SC `< 0.65`、与 `O0rqZ3aY` 和 `e71w5Qrl` 两两日收益相关 **均 `< 0.15`**；
  - **收益测算**：一旦在 11/30 前由用户手工提交这样 1 条 Slot 3 新星并换标入队，3-Alpha 等权 10Y Sharpe 可直接跃升至 **`3.40–3.55`**、2Y Sharpe 冲上 **`3.60–4.00`**！

---

## 4. `e71w5Qrl` 推荐英文 Description（待用户确认后随 API 一并写入）

> **Idea:**
> Identify US equities that simultaneously exhibit strong asset efficiency (high recent asset turnover) and conservative accounting quality (favorable prior-quarter accruals) within their subindustry, applying non-linear lower-envelope rank conjunction, exponential decay smoothing, and middle-tail trimming to concentrate capital in high-conviction, low-turnover fundamental leaders.
>
> **Rationale for data used:**
> Both fields originate from the `model31` fundamental-quality dataset (`SINGLE_DATA_SET` / ATOM). `mdl31_ab1_ass_tvr_last_qtr` measures last-quarter asset turnover, capturing capital deployment efficiency and revenue generation per unit of assets. `mdl31_ab1_acc_prior_qtr` captures prior-quarter accrual quality, distinguishing sustainable cash-backed earnings from accounting-driven earnings inflation. Combining both within `subindustry` peers isolates firms with durable operational efficiency and earnings quality.
>
> **Rationale for operators used:**
> `ts_backfill(..., 21)` forward-fills quarterly reporting gaps without introducing look-ahead bias. `rank(...)` maps each fundamental metric onto a uniform cross-sectional percentile, and `min(rank_A, rank_B)` enforces a conservative conjunction requiring strength on both turnover efficiency and accrual quality simultaneously. `ts_decay_linear(..., 22)` smooths the composite signal over one trading month to suppress reporting-date noise and maintain low turnover (~5.2%) and high margin (~18.6 bps). `group_rank(..., subindustry)` enforces peer-relative neutrality, while `tail(..., lower=0.25, upper=0.75, newval=0.5)` neutralizes noisy middle-quintile positions to focus risk budget on the top and bottom quartiles under `REVERSION_AND_MOMENTUM` neutralization (`decay=4`, `truncation=0.08`).

---

## 5. API 操作与迭代日志

| 日期时间 (CST) | 版本 / 动作 | 当前 3 条组合 | 10Y / 2Y / 2023 等权 Sharpe | 平均两两相关 | 榜单状态（`boards/leader`） | 备注与下一步 |
| --- | --- | --- | :-: | :-: | --- | --- |
| `2026-11-25 15:47` | 初次打标 (`PATCH`) | `O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ` | `2.996` / `2.918` / `0.822` | `0.428` | 未查 | 完成 3/3 绑定与前两条英文描述 |
| `2026-11-26 10:32` | 全量诊断 & 30-OS 寻优 | `O0rqZ3aY` + `3q936AEN` + `ZYoW7wMZ`（待升级） | 当前 `2.996` → 可升 **`3.151` / `3.483` / `1.819`** | `0.428` → **`0.187`** | Rank `348 / 1,327`（实证为字母序占位，非 OS 实分） | 发现新 OS `e71w5Qrl` 具资格且极度正交（相关 `0.08–0.12`）；待用户确认后执行方案 A/B 换标 + 攻克 Slot 3 |
| `2026-11-26 10:37` | **执行方案 A 换标 (`PATCH`) & 平台验真** | **`e71w5Qrl` + `O0rqZ3aY` + `ZYoW7wMZ`** | **`3.151` / `3.483` / `1.819`**（最差单年 `1.29`） | **`0.187`**（最大 `0.361`） | `3 / 3` 已验真绑定 `AQP202611`（`alphas=3`, Rank `348` 字母序） | ① 移除 `3q936AEN` 的 `AQP202611`（保留 `SC_IS_HIGHT` 与 `1219` 字描述）；② 为 `e71w5Qrl` 追加 `AQP202611`（保留 `Useful` 与别名 `SC 0.536 PC 0.694`）并写入 `1734` 字符英文三段式描述；③ 平台实时返 `competitions: [AQP202611]`。按用户指令暂不回测挖掘（待额度恢复后视需要攻克 Slot 3） |
| `2026-11-26 10:48` | **历史库合并 (`legacy_merge_bf5a03b26e`) 筛出 USA Slot 3 遗珠** | 保持 `e71w5Qrl` + `O0rqZ3aY` + `ZYoW7wMZ` | 保持 `3.151` / `3.483` / `1.819` | `0.187` | 零额度只读排查完成 | 从 `legacy_core` 合并的 22,105 条 D1 因子中锁定 2 条正交 USA Slot-3 种子：① **`GrGZ9vvx`**（`other335`, Sharpe `1.73`, Fit `1.23`, **Margin `34.82bp`**, SC `0.413`, 0 FAIL，仅需拉升 `2Y=0.67`）；② **`1Yp6GbbX`**（`sentiment_weighting_method1`, 裸 Sharpe `1.66`, **SC `0.103`**，仅需平滑/截断降换手）。详见 [legacy_merge_and_screening_report.md](legacy_merge_and_screening_report.md) |
