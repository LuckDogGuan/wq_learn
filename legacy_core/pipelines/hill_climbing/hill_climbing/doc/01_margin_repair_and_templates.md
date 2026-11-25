# 条件式 Margin 修复与模板

## 1. 入口判定

统一接口 `evaluate_margin_repair_readiness(stats, stage)` 只检查当前阶段的五项便宜数字指标：

- Sharpe、Fitness、P2Y 和 Turnover 必须完整并通过当前阶段门槛；
- Margin 必须可观察且未通过当前阶段门槛；
- SC、PC 和平台总检查不作为 Margin 修复的入口条件；
- Margin 已通过时立即退出该路由，继续普通阶段或相关性检查。

这一定义中的“满足 RA 条件”仅指满足当前阶段除 Margin 外的数字门槛，不代表最终 Alpha 已通过。

## 2. 固定 8 条组成

每个父任务恰好包含 8 条表达式，并只改变一个主要方向：

| 数量 | 修复家族 | 规则 |
|---:|---|---|
| 2 | 局部结构 | 原表达式的上下相邻窗口，保持字段、数据集、方向和骨架 |
| 2 | 收益/换手平衡 | Turnover 高于区间中点时用 `ts_decay_linear(expr, 2/5)`；否则用 `ts_av_diff(expr, 22/66)` |
| 2 | 分布与集中度 | 只有检查结果存在集中度/长尾证据时使用 `winsorize` 和合法分组中性化；否则用额外局部窗口 |
| 2 | 经济关系 | 同数据集、双 MATRIX、语义相关时使用虎哥 Series 2；否则使用同 Region×Category 的经济 `PROBATION` 模板 |

补位顺序是：同角色局部邻域 → 同范围经济模板 → 新参数 Challenger。LOW_PRIORITY 不参与普通补位，DISABLED_SCOPE 不再使用。仍不足 8 条时状态为 `BLOCKED_INCOMPLETE_MARGIN_BATCH`，不会 POST，也不会跨 Category 拼批。

所有候选继续满足单一真实数据集和字段类型合法。完整新表达式展开后最多 5 个操作符，并禁用主动引入 `trade_when/add/multiply`；继承源表达式的局部变体只检查新增算子，不因历史遗留算子或复杂度被拒绝。

## 3. 第二批条件与候选采用

Margin 批次占用当前阶段原有预算，不增加 `{Stage1:2, Stage2:4, Stage3:5}` 上限。每阶段最多两个 Margin 批次。

只有首批至少一条候选同时满足以下条件，才允许第二批：

- 保留当前阶段所有非 Margin 数字门槛；
- Turnover 仍在当前阶段有效范围；
- Margin 至少提升 1bp，或直接跨过当前阶段 Margin 门槛。

候选比较采用 Margin 专用词典序，不能让高 Margin 但 Turnover 跌破下限的候选胜出。连续总分只作为末端同层参考，不驱动 Margin 路由。

## 4. 虎哥 Series 2 边界

只注册以下两个模板：

- `hu_ge.series2_residual_stddev`：对两个经济相关字段做回归后观察残差波动；首批 `d=120`。
- `hu_ge.series2_beta_lagged`：观察字段关系的滞后 Beta；首批 `d=120, lag=5`。

首批出现有效改善后，第二批才挑战 `d=252`，不生成参数笛卡尔积。两个输入必须来自同一数据集且均为 MATRIX；字段描述或数据集语义必须能证明二者存在关系，禁止随机配对。

未启用项：

- Series 1 忽略 `field_b`，不注册；
- Series 3 已有负面实证，不注册；
- Series 4 展开后操作符超限，不注册；
- Series 5 的 `rettype` 与注释语义不一致，不注册。

虎哥模板只是经济假设 Challenger，不预设可以提高 Margin，仍需在当前 Region×Category 的完整结果上学习。

## 5. v5 学习账本

当前统一学习版本为 `region-category-stage-routes-v5`，Margin 事件通过 `repair_goal=MARGIN` 区分，写入：

- `Core/runtime_data/template_usage/events_v5.jsonl`
- `Core/runtime_data/template_usage/summary_v5.csv`

v4 及更早账本只读保留，不影响 v5 排序。只有 `candidate_origin=FORMAL_TEMPLATE` 的正式完整结果进入表现分母；普通局部探针、PENDING、429、10054、缺指标和重复生成不写成表现样本。重复拒绝按运行与原因聚合，恢复得到的相同完整结果按稳定事件键去重。

关键事件字段包括：

- `repair_goal=MARGIN`、`repair_family`、`hu_ge_variant`；
- `margin_repair_ready_before`、`non_margin_gates_retained`；
- `margin_bp_before/after/delta`、`margin_threshold_crossed`；
- `turnover_before/after`、`turnover_retained`；
- `sc_retained_if_observed`。

有效改善必须保留非 Margin 门槛和 Turnover，并使 Margin 提升至少 1bp 或跨门槛。状态规则：

| 状态 | 条件摘要 |
|---|---|
| `PROBATION` | 证据不足 |
| `PROMISING` | 至少 2 个不同源有效改善 |
| `CHAMPION` | 至少 8 个完整结果、3 个源、改善率≥25%、保门槛率≥75%，Margin 中位变化为正 |
| `LOW_PRIORITY` | 至少 8 个完整结果且改善率<12.5%，或 Margin 中位变化为负 |
| `DISABLED_SCOPE` | 至少 16 个完整结果、5 个源且零有效改善 |

LOW 每 20 个同范围 Margin 正式父批次最多复检一条；DISABLED 仅模板版本变化后恢复。

## 6. 报表判断

每 10 个逻辑父批次关注：Margin-ready 数量、Margin 批次数、完整结果数、跨门槛数、Margin bp 变化 P25/P50/P75、非 Margin 门槛保留率、Turnover 失效次数，以及各修复家族/虎哥变体的改善率和跨门槛率。

“Margin 变高”不等于有效优化；只有联合门槛仍安全，才计入模板学习和候选采用。
