# T0 实盘校准报告（`wq_research_v2` · `DEU / TOP500 / D1` · `model264` `Alphas=0`）

> [!IMPORTANT]
> - **执行时间**：`2026-11-25 16:57–17:02 CST`（**16 / 16 全部成功，`unobserved = 0`, `errors = 0`**）。
> - **严格遵守**：`Delay = 1` 硬锁、Decision #3（零 `+`/`*`/`trade_when`，实测含两条 `reverse(min(rank(expr_A), rank(expr_B)))`）、100% `Alphas=0` 免额度字段、零 `/submit`。

---

## 1. 四大核心校准结论（硬证据驱动后续放量决策）

| 校准项 | 实盘观测值 | 工程与研究决策 |
| --- | --- | --- |
| **1. `FULL` vs `QUICK` 耗时与指标差异** | `FULL`（8 条）：**`144.0s`**（返回完整 `sharpe / fitness / turnover / margin / returns / 2Y / rn_sharpe`）；<br>`QUICK`（8 条）：**`132.3s`**（仅快 **`8.1%`**，核心指标完全一致，但**丢失 `rn_sharpe`**） | **生产放量一律直跑 `FULL`**！避免 `QUICK → FULL` 二次重跑浪费，单次即可获得完整 Risk-Neutralized 指标与可提交 Alpha ID |
| **2. Decision #3 双分支表达实盘验证** | `reverse(min(rank(ts_delta(mdl264_1l_ifm, 22)), rank(ts_decay_linear(mdl264_1l_m1r_cer_se, 22))))` 顺利编译、零报错完成（`rK0YeVPd` / `MPgO0wk8`） | 表达式级 `min(rank(expr_A), rank(expr_B))` 100% 通过平台编译与回测，确认可大规模用于双强融合 |
| **3. 真实速率限制响应头** | `GET /alphas/{id}` 返回 `x-ratelimit-limit-hour: 2000`, `x-ratelimit-remaining-hour: 1993`, `ratelimit-reset: 3457`；`GET /simulations/{id}` 返回 `retry-after: 5.0`；全程 **0 次 429** | 按 **`4 并发槽 × 8 条 FULL Multi-Sim`** 波次调度，理论吞吐 **`~790 条/小时`**，可在 3–4 小时内安全拉起今日 `2,400–3,000+` 回测体量 |
| **4. `DEU/model264` 信号微观洞察** | 原始日频 `ts_zscore`/`ts_rank` 换手高达 `67%–101%`；唯独先平滑再分组的 `signed_power(group_zscore(reverse(ts_mean(mdl264_1l_lda, 22)), subindustry), 1.5)`（`gJr6Zd8g`）换手骤降至 **`2.37%`**、**`Margin = 26.11bp`**、`2Y = +0.55` | 立即将阶段 1/2 模板升级为**前置平滑（`ts_mean 22` / `ts_decay_linear 10`）+ 子行业分组**，同步加入 `analyst93`、`other250` 与低换手 `fundamental6` 比率 |

---

## 2. 实盘 8 条 `FULL` 明细（`EXP-T0-FULL-1795597066`，`DEU / TOP500 / D1`）

| 模板 ID | 来源侧 | Alpha ID | 表达式 | Sh | Fit | TO | Margin | 2Y | RN Sh |
| --- | :-: | --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `T0-ADM-01` | Admin | `e71mQv06` | `reverse(rank(mdl264_1l_fmc))` | `0.30` | `0.08` | `26.8%` | `1.54bp` | `-0.07` | `0.05` |
| `T0-ADM-02` | Admin | `akR6xwn5` | `reverse(group_rank(ts_zscore(mdl264_1l_fmc, 66), subindustry))` | `-0.59` | `-0.11` | `67.5%` | `-0.73bp` | `-1.70` | `-0.60` |
| `T0-ADM-03` | Admin | `QPWMKg95` | `reverse(min(rank(ts_zscore(mdl264_1l_fmc, 66)), rank(ts_zscore(mdl264_1l_m1d_cer_se, 66))))` | `-0.11` | `-0.01` | `85.1%` | `-0.13bp` | `-1.03` | `-0.04` |
| `T0-ADM-04` | Admin | `rK0YeVPd` | `reverse(min(rank(ts_delta(mdl264_1l_ifm, 22)), rank(ts_decay_linear(mdl264_1l_m1r_cer_se, 22))))` | `0.45` | `0.11` | `37.5%` | `1.18bp` | `-0.64` | `0.30` |
| `T0-TOP-01` | Top100 | `pwWm5ZNX` | `reverse(rank(ts_rank(mdl264_1l_m1d_cer_se, 126)))` | `0.10` | `0.01` | `81.6%` | `0.11bp` | `-0.69` | `0.10` |
| `T0-TOP-02` | Top100 | `E5m1RLGK` | `group_zscore(reverse(ts_zscore(mdl264_1l_m1d_pt_se, 126)), subindustry)` | `0.18` | `0.02` | `52.8%` | `0.28bp` | `0.42` | `0.21` |
| **`T0-TOP-03`** | Top100 | **`gJr6Zd8g`** | **`signed_power(group_zscore(reverse(ts_mean(mdl264_1l_lda, 22)), subindustry), 1.5)`** | **`0.45`** | **`0.22`** | **`2.37%`** | **`26.11bp`** | **`0.55`** | `0.14` |
| `T0-TOP-04` | Top100 | `wpNqbPjx` | `rank(ts_zscore(mdl264_1l_rta, 66))` | `-0.05` | `0.00` | `101.6%` | `-0.05bp` | `0.39` | `0.05` |
