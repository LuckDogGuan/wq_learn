# 广州服务器历史运行失败、低效表达式与模板实证复盘（`guangzhou`）

> [!IMPORTANT]
> - **数据来源**：`ssh guangzhou` 只读全量解析 `/root/worldquont/爬山代码/hill_climbing_v4.7/`（7,894 个 checkpoint + 11,488 条 `history_v4.7.json`）、`/root/worldquont/Core/runtime_data/template_usage/summary_v5.csv`（1,285 条模板×区域×阶段统计）及 `/root/worldquont/Ra_reach/output/`（V5/V6/V7 日志与 11 月筛选表）。
> - **核心目的**：在清理广州服务器多余磁盘日志前，把所有**效果差、撞车、活锁、高换手失败**的实证教训完整沉淀，用于直接喂给 `wq_research_v2` 的静态门禁与黑名单策略。

---

## 1. 五大历史低效与故障根因（必须在新引擎中彻底杜绝）

| # | 广州历史故障 / 低效模式 | 量化实证证据 | 根本原因 | `wq_research_v2` 防治措施 |
| :-: | --- | --- | --- | --- |
| **1** | **爬山程序 `1YWw2RRX` ↔ `88N0amKm` 61.5% CPU 死循环活锁** | `1YWw2RRX` 最终 `Sharpe=1.42, Fit=0.76, Margin=5.74bp`（多项 FAIL）但系统无限重选原地打转，当日实际产出 `0/3000` | 缺少“低基线/无改善早停”与轮次封顶，把未过一关/二关的差种子反复拉入循环 | 强制 Stage-0 早停 + 每源最多有限轮次 + 超过阈值无增益直接写 `BlacklistRegistry` |
| **2** | **荒谬极端窗口与违规算子参数** | 实测出现 `ts_decay_linear(..., 12000)`（近 50 年窗口！）及 `ts_target_tvr_decay(..., lambda_max=5)` 导致 `RESULTS_UNOBSERVED` | 旧爬山对窗口无上限校验，且未拦截 `JX79797 #15` 红线（`lambda_max > 1` 反增换手） | `expr_validator.py` 强制校验 `lambda_max ≤ 1.0` 及合理窗口范围，严禁生成 `> 504` 的极端 `ts_decay_linear` |
| **3** | **过度集中 `USA/TOP1000` 与 `GBR/UNKNOWN` 零产率黑洞** | 近 400 个 checkpoint 中 `USA/TOP1000` 占 129 个但平均最高 Sharpe 仅 **`1.303`**；`summary_v5.csv` 中 `GBR/UNKNOWN` 跑完 **1,112 次仅改善 4 次（`hard_pass=0`）**；`GBR/INSIDERS`（193 次）与 `GBR/INSTITUTIONS`（191 次）改善率为 **`0%`** | 缺乏 Stage-0 字段质量闸门（`dateCoverage ≥ 0.60` + WDS 蓝海过滤），在低覆盖/拥挤字段上盲目铺模板；且多条相同表达式重复提交 | 先走 Stage-0 WDS 四差距 + `Alphas=0` 清洗字段卡，且 `sim_runner.py` 强哈希去重杜绝重复跑同式 |
| **4** | **`RA V6` 死等 `Margin > 13bp` 与 `V5` 阻塞式死等 `PC 200 空体`** | `2026-11-25` 日志显示 `filtered_RAs_20261125.xlsx` 共 100 条（`SC_IS_HIGHT=34`, `PC_IS_HIGHT=32`, `Useful=5`），但 V6 因 `Margin>13bp` 过滤后 `取=0` 每 5 分钟空转；V5 同步卡在单条 PC `3×60s` 轮询导致吞吐极低 | ① V6 固定 `13bp` 门槛未结合 Region 实际与 `92→100` 阶段目标；② V5 同步阻塞等 PC 且旧 SC 缓存落后导致 `Useful` 过期 | `wq_research_v2` 彻底解耦：**异步非阻塞 `pc_poller.py`** + 全量最新 **92-OS 本地 SC 缓存** + 轻量流式扫描只打 `Useful` 标签 |
| **5** | **磁盘空间告急（`41G / 50G`, `86%`）与大日志堆积** | `/var/log/journal` 占 **`4.0 GB`**；废弃 GUI（`gui` + `wq_gui`）占 **`2.08 GB`**；`hill_climbing_source/source_state_v6.sqlite3` 占 **`2.78 GB`** + `template_usage/events*.jsonl` 占 **`675 MB`** + `Ra_reach/output` 占 **`565 MB`** | 全量历史明细事件日志无限追加不轮转，且在 1.9 GiB 低内存机上堆积多份旧 GUI 与旧备份 | 结论归档后清理 journal、旧安装脚本、废弃 GUI 与旧日志，新引擎 `wq_research_v2` 采用精简 SQLite WAL + 流式扫描严控内存与磁盘 |

---

## 2. 历史差表现表达式 / 字段 / 模板典型反例登记（避免重踩）

### 2.1 明显低效的字段与写法（来自近 400 个 `hill_climbing_v4.7` checkpoint）

| Region / Uni | 差表现表达式 / 字段 | 历史最高 Sharpe / Fit / TO | 主要失败原因 | 复盘结论 |
| --- | --- | :-: | --- | --- |
| `USA/TOP1000` | `ts_decay_linear(group_rank(multi_classifier_equity_sentiment_score, subindustry), 252)` *(含 `12000` 变体)* | `0.96–1.07` / `0.57–0.61` / `6–8%` | `LOW_SHARPE`, `LOW_FITNESS` | 情绪分类评分在 `TOP1000` 上过长平滑完全稀释信号，且同表达式被反复重跑 |
| `USA/TOP1000` | `ts_decay_linear(group_rank(editorial_commentary_sentiment_score_2, subindustry), 252)` | `1.15` / `0.82` / `8.8%` | `LOW_SHARPE`, `LOW_FITNESS` | 同上，优先切 `TOP3000` 且禁止 `252` 长窗衰减盲套 |
| `USA/TOP1000` | `ts_decay_linear(group_rank(corporate_action_report_sentiment_score, subindustry), 252)` | `1.08` / `0.77` / `8.6%` | `LOW_SHARPE`, `LOW_FITNESS` | 同上，单字段情绪类直接 `252` 衰减回报极低 |
| `USA/TOP1000` | `ts_decay_linear(mcr38_direction_rating, 66)` | `1.13` / `0.58` / `19.7%` | `LOW_SHARPE`, `LOW_FITNESS` | 缺乏横截面标准化（`rank`/`group_rank`）直接衰减 |
| `GBR/TOP700` | `group_neutralize(ts_decay_linear(ts_rank(max(rank(eur_top_signal_value_2), 0.8), 22), 5), subindustry)` (`1YWw2RRX`) | `1.42` / `0.76` / `30.9%` (`5.7bp`) | `LOW_SHARPE`, `LOW_FITNESS` | 在 `MARKET` 中性化外再叠 `subindustry` 削弱信号且卡死爬山队列 |
| 多区 | `ts_target_tvr_decay(hump(rank(ts_mean(...,20))), lambda_min=0, lambda_max=5, target_tvr=0.1)` | `RESULTS_UNOBSERVED` | 参数违规 (`lambda_max=5 > 1`) | 严格禁止 `lambda_max > 1` |

### 2.2 `summary_v5.csv` 高样本量零产率模板（`DISABLED_SCOPE` 实证）

- **`GBR / UNKNOWN` Stage 1（单模板均跑 `108–118` 次，`0` 次改善）**：`economic.information_change (d=10/22/66)`、`economic.persistence (d=22/66/120)`、`economic.short_reversal (d=5)`、`economic.cross_sectional_strength`。
- **`GLB / ANALYST` Stage 1（单模板 `21–24` 次，`0` 次改善）**：`economic.historical_surprise (d=22/66)`、`economic.cross_sectional_strength`、`economic.information_acceleration (d=22)`。
- **`USA / MODEL` Stage 3（`turnover_invalid_count = 13 / 14`）**：`margin.fallback.probe.neighbor.time_window.0` 频繁触发换手超限。

### 2.3 历史已验证的高胜率正向模式（值得在 `wq_research_v2` 复用）

- **Stage-2 `CHAMPION` 稳定器（`EUR/MODEL`）**：
  - `fundamental.group_zscore({"group": "subindustry"})`：**22 / 22 改善（`100%`）**
  - `cross.group_rank({"group": "subindustry"})`：**21 / 21 改善（`100%`）**
  - `post.group_neutralize({"group": "subindustry"})`：**14 / 15 改善（`93.3%`）**
- **高 Sharpe 基线形态（近 400 checkpoint 中 `Sharpe ≥ 2.2`）**：
  - 简洁 1–2 算子直出：`group_zscore(value_momentum_global_percentile, industry)`（`EUR/TOP2500`, Sh `3.26`, Fit `2.77`, Margin `29.8bp`）、`ts_delay(ts_mean(mdl25_21v, 5), 1)`（Sh `2.37`）、`ts_decay_linear(implied_volatility_call_60 - implied_volatility_put_60, 22)`（`USA/TOP3000`, Sh `2.22`, Fit `2.58`, Margin `27.0bp`）——再次印证**短算子链 + 清晰经济含义 >> 盲目堆砌复杂爬山树**。

---

## 3. 近期未提交池失败分布（近 400 checkpoint 统计）

| 阻塞项 | 出现次数（近 400 样本） | 优化对策 |
| --- | :-: | --- |
| `LOW_2Y_SHARPE` | **197** | 严格执行 `SZ83096 #47`：**2Y ≥ 1.58 先行**，缩短过长衰减窗，先看近 2 年再精修 |
| `LOW_SHARPE` | **192** | Stage-0 严格筛字段，摒弃盲扫低覆盖字段；优先 `Alphas=0` 蓝海集 |
| `LOW_FITNESS` | **189** | 严控换手（15–30% 优先），减少冗余嵌套算子 |
| `LOW_SUB_UNIVERSE_SHARPE` | **126** | `subindustry` / `group_cartesian_product(country, industry)` / 市值分桶中性化 |
| `CONCENTRATED_WEIGHT` | **65** | `truncation: 0.08 → 0.04` 或外层 `rank(...)` |

归档时间：2026-11-25。
