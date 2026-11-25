# 运行、断点与日志排障

## 1. Multi-Simulation 状态流

每批只允许一个父任务和 8 个子模拟。提交前完成语法、权限、类型、单数据集、负缓存和重复表达式检查；不足 8 条不 POST。源表达式是继承基线，即使历史上含 `add/multiply/trade_when` 或超过 5 个算子，也不因此拒绝基线刷新和局部优化；只禁止新变体主动增加这些算子。完整新表达式仍少于 6 个算子。

批次已获得 Location 时只读恢复。Location 超过恢复期限仍不可观察时保留 `RESULTS_UNOBSERVED`，不重新 POST。只有 8 条均有 Alpha ID 和完整指标，批次才推进。

## 2. 网络与认证

| 现象 | 分类 | 处理 |
|---|---|---|
| POST 429 | `PENDING_RATE_LIMIT` | 设置账户级 300 秒全局冷却；单批最多两次冷却重试，总 POST≤3 |
| POST 10054/超时/空响应 | `RESULTS_UNOBSERVED` | 网络层不自动重发，保存批次指纹并只读对账 |
| GET 10054/超时 | PENDING | 最多首次加两次重试，等待 2 秒、5 秒 |
| 401 | 认证失效证据 | 只允许一次重新认证和一次原请求重试 |
| 指标缺失 | `PENDING_STAGE_SCORE` | 不格式化或比较空分数，不算失败或通过 |

GET 保持每客户端至少 250ms 间隔。会话能够读取 JWT 到期时间时提前 5 分钟续签；不能读取时采用 150 分钟兜底。日志不得记录 Token、密码或完整敏感查询。

## 3. 数字门槛、SC 与平台检查顺序

P2Y 的唯一数据源是平台 `test.sharpe`。`train.sharpe` 缺少 P2Y 含义，不能用于回退、排序或晋级。评分/目标版本变化后，旧 Stage 完成记录按完整指标重新定位到“最早未通过阶段”，不再从历史批次数推导晋级。

Stage 3 的便宜预筛只包含 Sharpe、Fitness、P2Y、Margin、Turnover。数字门槛全部通过后获取 SC，即使平台总检查此时尚未 PASS，也不能跳过 SC。随后再分别判断平台检查、厂型和数值 PC。

因此应分别观察：

- `gate_status`：PASS/FAIL/PENDING；
- `score_status`：OK/PENDING_SC/PENDING_METRICS；
- `repair_route`：NONE/MARGIN_REPAIR/SC_REPAIR/PC_REPAIR。

明确数字失败优先于缺指标：例如 Margin 失败且 SC 缺失，候选仍是 FAIL，但可以进入 `MARGIN_REPAIR`。

## 4. 常见排障步骤

### 不足 8 条

1. 查候选池指纹是否变化。
2. 区分语法/类型拒绝、重复表达式、负缓存和完整缓存命中。
3. 普通批次从后续候选补齐；Margin 批次按同角色 → 同范围经济模板 → Challenger 补齐。
4. 仍不足时记录 BLOCKED，不进行五分钟循环 POST。

### 有 Location 但结果不完整

1. GET 父任务并记录 status 与 children 数量。
2. 逐个 GET child，保存 child status、message 和 Alpha ID。
3. ERROR/FAILED 写确定性失败和负缓存；CANCELLED 不算性能失败。
4. 仍运行则保留 Location；超过恢复期限转 `RESULTS_UNOBSERVED`。

### 分数为 None

检查 Sharpe、Fitness、P2Y、Margin、Turnover、SC 哪项缺失。日志、邮件和最终摘要统一打印 `PENDING`；不得做 `float - None`、`None:.2f` 或把它记为 `BUG_BLOCKED`。

### Margin 变高但没有晋级

核对候选是否破坏 Sharpe、Fitness、P2Y 或 Turnover。Turnover 跌破下限/超过上限的高 Margin 是无效优化，不应胜出或升级模板。

## 5. 统计口径

报表用唯一批次指纹、候选键和 Alpha ID 去重。Stage 通过率只以该阶段完整可观察结果为分母；PENDING 和网络错误不占分母。

每 10 个逻辑父批次输出：

- 逻辑父批次、实际 POST 次数、额度、429/10054/401 与全局冷却；
- 核心指标、P2Y、全门槛观察率和各阶段 PASS/FAIL/PENDING；
- Margin-ready、Margin 跨门槛、非 Margin 保留率和 Turnover 失效；
- Stage 3 数字通过后的 SC 获取率；
- 每千次回测新增完整 Stage 3 通过数；
- 模板家族、版本、参数、改善率和跨门槛率。
- SQLite 中的唯一源、唯一批次、源领取次数、重复领取、连续无新候选源和不足 8 条阻塞数。
- Stage 1 B1/B2/B3/B4 各自运行数和 PASS 批数、Stage 1→2/Stage 2→3 即时交接、分支创建/合并数。
- `stage_post_batches_used` 与缓存命中分开；只有前者代表真实消耗的父批次。

2026-09-01 本地只读重放的两个历史快照如下，均是旧控制面的修复前基线，不能证明本次 SQLite/路由代码已经在线生效：

- `2026-08-31`：30 个逻辑父批、240 个额度，Stage 1 完整可观察 189 条、PASS 5 条（2.65%），Stage 2 完整 24 条、PASS 0，Stage 3 为 0；8 个源累计出现 80 次 `7/8`，按新指纹阻塞规则预计只保留 8 条阻塞事件，可消除 72 次重复调度。
- `2026-08-29`：501 个逻辑父批、4,008 个额度，Stage 1 可观察 PASS 率 48.48%，Stage 2 为 19.76%，Stage 3 为 0；Margin-only 记录 Stage 1/2/3 分别为 93/44/31 条，确认 18 条 `float - NoneType` 异常。19 个源累计出现 1,299 次 `7/8`，预计只保留 19 条阻塞事件，可消除 1,280 次重复调度。

## 6. 历史故障经验

2026-08-25 曾出现 `densify` 接收 MATRIX 字段导致首个 child ERROR、其余 7 个 CANCELLED。经验是：本地语法正确不代表平台单位类型正确；父任务失败后仍要逐 child 读取真实状态，不能把整批统一摊成 FAILED。当前分类字段模板只接受平台元数据明确标记的 GROUP/CATEGORY 字段。

曾出现确定性 `7/8` 候选长期每五分钟重试。当前候选在切批前先做二次过滤并从后续项补齐；候选池指纹不变且补不满时保持 BLOCKED。

## 7. 恢复与验证边界

调度必须先查 SQLite：最早到期的 `PENDING_RATE_LIMIT` 批次优先，其次是已有 Location 的只读对账批次，最后才领取新源。源领取通过事务把可领取状态原子改为 `OPTIMIZING`，两个进程不能同时拿到同一源。相同候选池的 7/8 批次保存候选池、评分、代码和路由集合指纹；这些输入未变化时不再领取。

关键状态位于：

- `hill_climbing_v4.7/history_v4.7.json`：表达式缓存和 pending Multi-Simulation；
- `hill_climbing_v4.7/<AlphaID>_checkpoint_v4.7.json`：源 Alpha 优化位置；
- `Core/runtime_data/hill_climbing_source/source_state_v6.sqlite3`：源队列、批次断点、原子领取与聚合事件；
- `Core/runtime_data/hill_climbing_source/state.json`：首次迁移来源与只读备份，不再写入；
- `Core/runtime_data/template_usage/events_v5.jsonl`：完整正式模板结果和聚合拒绝事件；
- `Core/runtime_data/hill_climbing_budget/state.json`：共享日额度。

本地测试只能证明控制流和数据口径，不能证明实时权限、字段单位、SC/PC 或平台性能。真实烟雾测试需要单独授权，且仍不得自动提交或修改平台属性。
