# Goal：EUR D1 REGULAR 单数据集 Alpha 挖掘

状态：可直接执行  
更新时间：2026-07-28

## 目标

在 `EQUITY / EUR / delay=1 / REGULAR / max_trade=OFF` 下找到 10 个 Alpha：

- 未提交，且来自 10 个不同的精确 `dataset_id`；
- 每个 Alpha 只使用 1 个数据集、1–2 个唯一字段、少于 6 个操作符；
- 经济假设、模板骨架和收益来源均有实质差异；
- 通过基础指标、风险中性化、稳健性、过拟合、相关性和平台提交预检；
- 通过后保留原标签并追加 `READY_TO_SUBMIT`，方便用户手动提交；
- 优先覆盖当前未点亮的 Pyramid 类别，提交前不得声称已经点亮。

严禁调用 `create_simulation`、`submit_alpha`，严禁使用 `trade_when`、`add`、`multiply`，严禁创建自动化任务、修改项目代码或修改 `reference/`。

## 保存位置

除本 goal 外，本次研究产生的文件只能保存在：

`D:\code\WorldQuant Brain\consultant\gui\doc\goal\总结\`

- 每个进入基础候选的 Alpha：`{alpha_id}.md`；
- 每 10 个回测批次追加：`批次总结.md`；
- 不在其他目录保存中间记录。

## 执行流程

### 1. 实时初始化

1. 用 cnhkmcp `authenticate` 登录；凭据从 `consultant_core/config.yaml` 读取，禁止输出密码。
2. 调用 `get_platform_setting_options`、`get_datasets`、`get_datafields`、`get_operators`。
3. 调用 `get_pyramid_alphas`、`get_pyramid_multipliers`，选择当前未点亮的目标类别。
4. 调用 `get_user_alphas(stage="IS")` 排除重复表达式和已有同源策略；只有响应明确返回未提交状态时才计入候选，不能只由请求参数 `stage="IS"` 推断。
5. 任何设置、字段归属、状态或单位不明确时先用 MCP 核验，不得猜测。

### 2. 数据集与 Universe

1. 任意时刻只允许一个 `active_dataset` 和一个 `active_universe`。
2. 每个表达式中的全部字段必须通过 `get_datafields` 确认属于同一个 `dataset_id`。
3. EUR D1 若有多个合法 Universe，至少探索两个；每个 Alpha 只能使用一个 Universe。
4. 当前数据集的预登记模板和字段族尚未耗尽时不得切换数据集。
5. 只有模板骨架重复、可用字段族已尝试，并查阅近期高质量论坛仍无新方向时才切换；记录切换原因。

### 3. 模板生成

每个模板先记录：

- 经济机制和字段代理；
- 预期方向、持有周期、换手与 Margin；
- 主要收益来源和失效环境；
- 模板骨架、字段族、预处理方式。

先生成最小且有经济意义的模板，再用 cnhkmcp 查论坛。论坛内容按“近期优先，同等质量下高赞和有效评论优先”，必须读正文和评论；只吸收经济逻辑、骨架和验证方法，不照抄公式。

相同骨架只替换字段、窗口或正负号，不算新策略风格。策略风格从 `value`、`momentum`、`reversal`、`quality`、`sentiment_attention`、`flow_event`、`microstructure`、`risk_liquidity` 中标记。

### 4. 批量回测

只使用 cnhkmcp `create_multi_simulation`：

- 每批尽量放 8 条表达式；最后一批可放 2–7 条，不用重复表达式补齐；
- 每批固定 dataset、Universe 和 settings；
- 记录 `batch_id`、`batch_size`、表达式、字段、settings 和原始结果；
- 批次大小不等于可观察的 worker 数；工具未返回并发数时记录 `CONCURRENCY_UNOBSERVED`，不得虚构 8 个 worker。

### 5. 基础硬门槛

以下条件必须全部满足：

- `Sharpe > 1.58`
- `Fitness > 1`
- 平台明确口径的 `2Y Sharpe > 1.6`
- `Margin > 10bp`
- `0.05 < Turnover < 0.30`
- 操作符数量 `< 6`，按 AST 算子节点计数
- 1–2 个唯一字段
- 单一 `dataset_id`
- 明确处于未提交状态

缺失结果、单位不明或只凭 `stage="IS"` 无法确认未提交状态时，不通过。

### 6. Robust 与严格过拟合检查

基础通过后立即冻结表达式，执行：

1. 同一表达式、dataset 和 Universe 下测试 `decay=[0,3,6]`；平台不允许的值记录原因。
2. 基础设置使用 `neutralization=NONE`；另预先选择一个合法非 `NONE` 风险中性化设置。
3. 基础确认结果仍须满足基础硬门槛。
4. 风险中性化确认必须满足 `Sharpe > 1`、`Fitness > 0.7`、`Margin > 10bp`。
5. 检查 yearly stats、2Y 指标、PnL 连续性、覆盖率、drawdown、long/short 数量，以及单一日期、年份、行业或风格集中风险。
6. 确认结果出现后禁止调参；任何表达式改动必须作为新候选重新开始。

任一必需结果缺失为 `ROBUST_PENDING`；任一硬门槛失败为 `ROBUST_FAIL`。IS 结果不得称为 OS 证明。

固定 stress test 全部通过、yearly/PnL 没有明显集中且确认结果出现后未再调参，才同时标记 `ROBUST_PASS` 和 `OVERFIT_PASS`。

### 7. 相关性和可提交标签

依次执行：

1. 用 `check_correlation` 获取 production correlation；没有结果或 `abs(corr) > 0.7` 时不通过。
2. 获取候选 PnL，按日期交集计算候选间 Pearson 相关性；共同有效观测至少 252 个交易日，并满足 `abs(corr) < 0.4`；观测不足时标记 `CORR_PENDING`，不得错位或填零。
3. self correlation 作为诊断项保存，不替代上述硬门槛。
4. 调用 `get_submission_check`；只有平台明确返回通过才进入 `READY_TO_SUBMIT`。
5. 只有 `BASE_PASS + RISK_NEUTRAL_PASS + ROBUST_PASS + OVERFIT_PASS + 未提交状态确认 + production correlation 合格 + 候选间 correlation 合格 + get_submission_check PASS` 全部成立，才用 `set_alpha_properties` 保留已有 tags 并追加 `READY_TO_SUBMIT`，同时写入简短、可解释的 `regular_desc`；没有明确规则时不改 color、category 和 osmosis points。

任何最终复查失败、相关性待定或平台预检未通过的 Alpha 都不得添加 `READY_TO_SUBMIT`。

### 8. 人工提交与记录

严禁调用 `submit_alpha`。用户根据 `READY_TO_SUBMIT` 标签手动提交。

每个 `{alpha_id}.md` 只保留：

- Alpha ID、表达式、dataset、字段、Universe、settings、经济风格；
- 基础、risk-neutralization、robust、2Y/yearly stats 和相关性结果；
- `READY_TO_SUBMIT` 标签写入时间和平台预检结果；
- 用户手动提交时间、提交结果及平台状态；提交后用 MCP 核验；
- 若失败，只记录失败原因和下一步。

每次人工提交尝试都按时间追加“人工操作、平台结果、状态、失败原因”，禁止覆盖历史记录。

每次手动提交结果确认后，在同一文件末尾追加简短复盘：

- `有效操作`：1–3 条；
- `帮助不大`：1–3 条；
- `下次复用`：1–3 条。

每条只写一句，记录有证据的结论，不把单次结果当成普遍规律。

### 9. 每 10 个批次总结

每完成 10 个 `create_multi_simulation` 批次，在 `总结\批次总结.md` 追加一次：

- 操作符探索率、字段探索率；
- 模板骨架和策略风格多样性；
- 预处理和收益来源；
- 主要失败原因及过拟合风险；
- 收益归因、当前知识盲点和下一轮纠偏；
- 当前数据集是否已经耗尽、是否应切换。

总结保持简短，不重复逐个 Alpha 的详情。

## 停止条件

满足任一条件时停止继续挖掘：

1. 获得 10 个来自不同 `dataset_id`、不同策略风格且带 `READY_TO_SUBMIT` 标签的 Alpha，状态改为 `AWAITING_MANUAL_SUBMISSION`；
2. 预登记模板和字段族均已尝试或有证据排除，论坛也没有新的可验证方向，标记 `INCOMPLETE_EXHAUSTED`；
3. 用户要求停止。



`AWAITING_MANUAL_SUBMISSION` 不是任务完成。用户手动提交后，继续核验平台状态、追加提交记录和简短复盘；全部处理完毕或用户明确结束后才完成 goal。

最终必须报告找到的数量、标签状态、提交记录状态、未解决风险，并明确声明没有调用 `submit_alpha`。

## 暂停提交

1. 单个平台接口连续 3 次失败、权限或额度阻塞 暂停提交2分钟。