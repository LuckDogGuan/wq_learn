# 地区独立作战档案：`KOR / TOP600 / D1`（韩国市场 · `1.6×` 空白行为金融探针）

- **宇宙范围**：合法 D1 仅 **`TOP600`**（唯一主池）。
- **市场与规则**：单一市场（不支持 `COUNTRY`），常规 D1 门槛（`Sh>1.58, Fit>1.0, 2Y>1.58`, 经验 `M≥10bp`），1 并发槽；账号当前 **`0` OS**，6 大主塔全享 **`1.6×`**。
- **微观结构**：韩国股市（KOSPI/KOSDAQ）散户交易占比极高、主题轮动与社交论坛情绪强烈，行为金融偏差（外推/显著性/连涨反转）与论坛多空情绪具有突出的本土定价 alpha。
- **首轮实盘核验探针（2026-11-25 `cnhkmcp`）**：
  - **`behavioral_signals`**（`model` **`1.6×`**, `VECTOR` [单值伪 VECTOR，强制只用 `vec_avg`], `cov=86.8%`, `dCov=0.9507`）：`visual_price_path_shape_score` (`aCnt=0`), `consecutive_return_streak_length` (`aCnt=0`), `extreme_daily_return_indicator` (`aCnt=1`), `chronological_return_sequence_correlation` (`aCnt=3`), `price_path_curvature_measure` (`aCnt=5`), `salience_weighted_return_score` (`aCnt=7`) *(严禁裸排 `total_equity_market_value_usd`)*。
  - **`equity_forum_data`**（`other` **`1.6×`**, `VECTOR`, `cov=89.5%`, `dCov=0.9507`）：`distinct_user_count_per_platform` (`aCnt=0`), `total_distinct_participants_count` (`aCnt=2`), `aggregate_comment_volume` (`aCnt=3`), `aggregate_buy_opinion_score` (`aCnt=6`), `aggregate_sell_opinion_score` (`aCnt=7`)。
- **独立漏斗快照**：`data/exports/kor_ra_funnel_latest.json`。

- **2026-11-25 19:16（1 小时定时检查 #1）**：`KOR / behavioral_signals` 完成 `38` 条 `0` 命中（最高 `+0.52`），已止损停跑，KOR 直切散户论坛情绪 **`equity_forum_data`**（`1.6×`）。

- **2026-11-28 09:20 Codex 巡检 [V]**。守护日志确认 KOR/model138 免额线 56 条完成，1 条正向 Sharpe≥0.80（1.79%），最高 0.81，已触发早停。平台 `6XGqboq5` 的 Sharpe 0.81、Margin 21.83bp。后续由现有守护队列切换活动。
