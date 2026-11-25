# Stage 1 四批与即时晋级

## 目标

Stage 1 不放宽 Sharpe、Fitness、P2Y、Margin、Turnover 和 SC 门槛，而是用最多四批扩大有经济含义的候选方向。每批仍为固定 8 条 Multi-Simulation；任一批出现 PASS 就停止本阶段剩余预算。

## 四批结构

| 批次 | 组成 | 运行条件 |
|---|---|---|
| B1 | 原式 P2Y 基线 + 7 条同字段、同骨架邻域 | 固定首批 |
| B2 | 4 Stage 0 + 2 经济模板 + 1 范围优胜 + 1 Challenger | B1 未 PASS 时固定运行 |
| B3 | 4 未尝试 Stage 0/单轴参数 + 2 不同经济假设 + 1 优胜 + 1 Challenger | 门槛数增加、总缺口减少至少 0.05，或 Margin-ready |
| B4 | 4 最大缺口定向 + 2 范围优胜 + 2 新变体 | B3 有效改善或有明确单门槛修复机会 |

Margin-ready 的优先级高于“无总体改善即停止”，但不会抢占 B1/B2。B2 完成后，下一批可切换为现有 `2+2+2+2` Margin 修复批。

## Stage 0 边界

Stage 0 是 Stage 1 的模板组，不是新的运行阶段。首版注册截面 Rank、时序 Rank、基本面同比/比率、模型或情绪 Z-score、价格乖离、成交量异动、Put/Call、期权偏度、宏观中枢偏离和事件频率。

- 二字段模板必须同数据集且语义关系明确。
- VECTOR 先经已有合法归约。
- 新候选不得引入 `add`/`multiply`/`trade_when`。
- `stage0_sentiment_polarity` 和 `stage0_analyst_surprise` 首版不注册。
- 候选不足 8 条时不 POST，不跨 Category 补位。

## 即时分支

Stage 1 PASS 按硬门槛距离、相对质量和连续分排序，同一源最多保留 3 条不同模板家族、不同规范化表达式的分支。Stage 2 的每条分支最多产生 1 条 Stage 3 分支，因此一个根源全程最多 3 条路径。

分支使用现有 SQLite `candidates` 载荷保存 `branch_id`、根源、父源、家族和阶段计数，不新增表。40 条观察窗仅更新相对质量和健康报表，不改变分支状态。

## 缓存与计数

- `stage_plan_cursor`：已考察的模板方向。
- `stage_post_batches_used`：真实 POST 的父批次，只有它消耗阶段预算。
- `stage_cache_batches_reused`：完整缓存折算的批次，只用于报表。
- `stage_observed_candidates`：当前阶段唯一完整结果数。
- `stage_branches`：当前阶段选出的即时交接分支。

缓存可以直接产生 PASS 并即时晋级，但不增加 `stage_post_batches_used`。缓存数量不能把未过门槛候选写成 `STAGEx_COMPLETE`。
