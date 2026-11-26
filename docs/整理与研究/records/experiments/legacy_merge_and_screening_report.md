# `legacy_core` → `wq_research_v2` 历史数据库合并与 D1 因子筛选报告

> [!IMPORTANT]
> **执行批次**：`legacy_merge_bf5a03b26e`（`2026-11-26 10:47 CST`）
> **只读与红线保障**：全程以 `?mode=ro` 严格只读访问 `legacy_core/Core/runtime_data/`（零写入、零删除）；严格锁定 `Delay = 1 (D1-Only)`；写入 `data/wq_v2_ledger.db` 的独立表 `legacy_alphas`、`legacy_datasets`、`legacy_merge_runs`，零触碰 `sim_tasks` 与 `COMPLETED_FULL` 行；全程 **0 次回测消耗**。

---

## 1. 合并总览与地区 × 层级分布

* **数据源**：`hill_climbing_source/events.jsonl`（221.6 MB）+ `template_usage/events*.jsonl`（v1–v4，共 382.9 MB）+ `catalog.db`（478.0 MB，只读提取 D1 数据集元数据）。
* **吞吐与结果**：流式扫描 **`310,506`** 行 → 去重合并 **`22,105`** 条唯一 D1 Alpha + **`5,543`** 条 D1 数据集至 `data/wq_v2_ledger.db`。

| 地区 | `TIER_S_READY_CHECK`（合规达标待直查） | `TIER_A_PARAM_TUNE`（单轴微调） | `TIER_B_REFACTOR_OP`（高质需 Decision #3 重构） | `TIER_C_EXPLORE_SEED`（探索种子） | `ALREADY_OS` | `LOW_PRIORITY` | 合计 |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **EUR** | **2,020** | 2,538 | 528 | 2,133 | 3 | 1,372 | 8,594 |
| **GBR** | **2,854** | 1,307 | 640 | 2,125 | 6 | 4,177 | 11,109 |
| **GLB** | **410** | 203 | 87 | 862 | 2 | 717 | 2,281 |
| **USA** | **2** | 0 | 0 | 24 | 0 | 95 | 121 |
| **总计** | **5,286** | **4,048** | **1,255** | **5,144** | **11** | **6,361** | **22,105** |

---

## 2. 重点筛选出的高潜可优化因子清单（按优先级排序）

### 2.1 USA / TOP3000 / D1（`AQP202611` 第 3 槽位正交候选种子）
经只读 API（`GET /alphas/{id}`，零回测成本）逐条复核：

| Alpha ID | 数据集 / 字段 | 当前实测指标 | 状态与排雷结论 | 定向优化方案（待额度恢复后执行） |
| --- | --- | --- | --- | --- |
| **`GrGZ9vvx`** | `other335` (`oth335_hc_combined_all_region_hedge`) | Sharpe **`1.73`**, Fit **`1.23`**, TO `3.65%`, **Margin `34.82bp`**, SC `0.413`, **0 FAIL** | **首选 USA 历史遗珠！**与当前 AQP 前两槽（`O0rqZ3aY` / `e71w5Qrl`）完全跨数据集正交；仅差 `LOW_2Y_SHARPE = 0.67 < 1.58`（WARNING） | ① 加 `group_rank(..., subindustry)` + `ts_decay_linear(10/22)`；② 扫 `REVERSION_AND_MOMENTUM` / `CROWDING` / `STATISTICAL` 与 `decay {2,4,6}`；③ 必要时与高 2Y 字段做 `min(rank_A, rank_B)` 双分支拉起 2Y |
| **`1Yp6GbbX`** | `EARNINGS` (`sentiment_weighting_method1`) | 裸 1 算子 `-zscore(...)` 即达 Sharpe **`1.66`**, Ret `39.14%`, **SC `0.103`** | 原始裸信号极强且极低自相关；仅因 `decay=0 / neut=NONE / truncation=0` 导致 `HIGH_TURNOVER(1.75)` 与 `CONCENTRATED_WEIGHT` | 标配 1 批降换手救活：`group_rank(ts_decay_linear(rank(-sentiment_weighting_method1), 10/22), subindustry)` + `truncation=0.06/0.08` + `INDUSTRY/SUBINDUSTRY` + `decay=4/6` |
| `88l3qaWz` | `probability_label4_5quantile_5day_ohlcv_2` | Sharpe `1.67`, Fit `0.75`, TO `30.4%`, Margin `3.99bp`, SC `0.176` | 备选种子；需拉高 Fitness 与 Margin（`ts_decay_linear(22)` + `tail`） | 次优先备选 |
| ~~`LLGLR3dv`~~ | `five_week_change_gross_notional_volume` | 表面 Sharpe `3.90`, Fit `3.21` | **已排雷（死字段陷阱）**：API 实查为 `TOP2000`、`testPeriod=P2Y` 且 `LOW_2Y_SHARPE = 0.0`（近 2 年无信号） | **剔除**，同步反哺筛选规则 |

### 2.2 EUR / GLB / GBR 高 Margin `TIER_S` 零回测直查候选（用于 92→100 与金字塔补塔）
* **EUR（高 Margin 低相关优等生）**：
  * `xAjGG8Qq`（`model110`, `ts_decay_linear(ts_mean(mdl110_score, 120), 22)`）：Sharpe `1.75`, Fit `1.47`, **2Y `1.98`**, **Margin `130.9bp`**, Legacy SC `0.360`。
  * `N17Ldxpe`（`imbalance5`, `ts_mean(imb5_score, 252)`）：Sharpe `1.95`, Fit `1.27`, **2Y `2.26`**, **Margin `83.3bp`**。
  * `3qlkKEAe`（`model26`, `ts_mean(mdl26_ep_yield_smartestimate_fy1, 66)`）：Sharpe `1.79`, Fit `1.50`, 2Y `1.68`, **Margin `87.6bp`**。
* **GLB（`other335` 强 2Y 族）**：
  * `1YwaxQVW` / `E5lg5Mw1` / `GrlMq7JO` / `YP72j9dA`：Sharpe `2.16–2.86`, Fit `1.25–2.05`, **2Y `2.89–3.76`**, Margin `16.4–37.5bp`（可零回测直查最新本地 SC 与远端 PC）。
* **GBR（高 Fit/Margin 族）**：
  * `pwj6rwbg` / `kqjnvbnz` / `1Yw7YZWX`：Sharpe `1.95–2.32`, Fit `1.78–2.31`, 2Y `1.98–2.65`, Margin `31.0–37.4bp`。
* **`TIER_B_REFACTOR_OP`（Decision #3 重构高价值矿脉）**：
  * 历史库大量高分因子仅因使用了 `-1 * (...)` 或 `sign(x) * log(1 + abs(x))` 被拦（如 `3qlJMz6Z` EUR `model38` Sharpe `2.24` / Margin `43.1bp` / SC `0.365`；`P07v135x` GBR Sharpe `2.42` / Fit `2.76` / 2Y `2.44`），分别用 `reverse(...)` 和 `signed_power(rank(x), 0.5)` 一键重构即可合规复现。

---

## 3. 筛选规则升级（由本次审计反哺固化）

1. **严格隔离历史 `2Y_SHARPE` 缺失陷阱**：`hill_climbing_source` 部分历史记录缺少 `sharpe_2y`（如 `LLGLR3dv` 表面 Sharpe `3.90` 实则 `LOW_2Y_SHARPE=0.0`），后续对 `sharpe_2y IS NULL` 的历史候选，**必须先做零额度只读 `GET /alphas/{id}` 核对 `LOW_2Y_SHARPE` 与 `testPeriod`**，确认非死字段后再排入优化队列。
2. **三层漏斗分流**：
   * `TIER_S_READY_CHECK` → 优先零回测额度跑 `sc check` + `pc check`，直接捡漏 92→100；
   * `TIER_A_PARAM_TUNE` → 锁定字段，按 `opt_action_hint` 做单轴微调（`decay` / `truncation` / `group_rank` / 中性化）；
   * `TIER_B_REFACTOR_OP` → 用 `reverse(...)` / `min(rank_A, rank_B)` / `signed_power(rank(x), 0.5)` 替换历史 `+` / `*` / `trade_when` 后复测。
3. **可复用 CLI 工具**：
   ```powershell
   $env:PYTHONPATH="c:\Wq\WorldQuant Brain\wq_research_v2\src"
   python -m wq_research_v2 legacy merge
   python -m wq_research_v2 legacy stats
   python -m wq_research_v2 legacy screen --region USA --min-sharpe 1.4 --top 20
   python -m wq_research_v2 legacy screen --region EUR,GLB --tier TIER_S_READY_CHECK --only-compliant --top 30
   ```
