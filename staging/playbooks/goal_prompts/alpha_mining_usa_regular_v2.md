# Goal：USA D1 REGULAR 单数据集 Alpha 挖掘（v2）

状态：可直接执行  
版本：v2  ��� 原文件 `alpha_mining_usa_regular.md` 的新增优化版本  
更新时间：2026-07-28

## 目标

在 `EQUITY / USA / delay=1 / REGULAR / max_trade=OFF` 下，找到最多 10 个可供用户人工提交的 Alpha：

- 每个 Alpha 未提交，且来自不同的精确 `dataset_id`；
- 每个 Alpha 只使用 1 个 dataset、1 个 Universe、1–2 个唯一字段，操作符数量 `< 6`；
- 经济假设、模板骨架、字段来源和预期收益来源均可解释；
- 通过基础指标、风险中性化、稳健性、过拟合和相关性检查；
- 平台预检通过后，仅追加 `READY_TO_SUBMIT`，由用户手动提交；
- 优先覆盖当前未点亮的 Pyramid 类别；不得声称已点亮，除非 MCP 返回明确证据。

禁止调用 `create_simulation`、`submit_alpha`；禁止使用 `trade_when`、`add`、`multiply`；禁止创建自动化任务、修改项目代码或修改 `reference/`。

## 输出范围

本 Goal 产生的研究文件只能写入：

`D:\code\WorldQuant Brain\consultant\gui\doc\goal\总结\`

- 单个候选：`{alpha_id}.md`
- 每 10 个批次：`批次总结.md`
- 不在其他目录写中间记录。

## 执行状态

每个候选必须按以下状态推进，状态只能由证据触发：

`DISCOVERED` → `BASE_PASS` → `ROBUST_PENDING` → `ROBUST_PASS` → `CORR_PENDING` → `READY_TO_SUBMIT`

异常状态：

- `BASE_FAIL`：基础硬门槛失败；
- `ROBUST_FAIL`：稳健性或过拟合检查失败；
- `CORR_PENDING`：共同有效观测不足 252 个交易日；
- `SUBMISSION_BLOCKED`：平台预检、权限或接口连续失败；
- `AWAITING_MANUAL_SUBMISSION`：达到目标数量，但仍等待用户提交。

不得跳过状态、用缺失结果填零、用 `stage="IS"` 单独推断未提交状态，或把 `IS` 结果称为 OS 证明。

## 执行流程

### 1. 初始化与边界确认

1. 使用 cnhkmcp `authenticate`；凭据从 `consultant_core/config.yaml` 读取，禁止输出密码。
2. 获取 `get_platform_setting_options`、`get_datasets`、`get_datafields`、`get_operators`。
3. 获取 `get_pyramid_alphas`、`get_pyramid_multipliers`，选择当前未点亮且可验证的目标类别。
4. 使用 `get_user_alphas(stage="IS")` 作为候选排除线索；只有接口明确返回未提交状态时才排除，不能仅凭参数推断。
5. 对 Region、Universe、字段归属、设置和提交状态逐项 MCP 核验；不猜测。

### 2. 模板选择与研究假设

严格遵循最新 `doc/goal/模板/模板指引.md`：先从 `doc/goal/模板/已验证因子模板.md` 的 100 个模板中选择起点，再进入对应分类文件核对经济含义和变体。论坛总结文件只用于来源索引，不直接作为回测表达式来源。

每个候选只选择一个主模板，并记录：

- 模板类别与文件名；
- 经济机制、字段代理和预期方向；
- 持有周期、换手、Margin 与主要失效环境；
- 选用该模板而不是其他模板的理由。

模板选择顺序：

1. 先选 `已验证因子模板.md` 中与研究方向最接近的编号；
2. 再查对应分类文件，确认字段类型、算子签名、Region 和 Universe；
3. 只有没有合适的已验证模板时，才使用分类文件中的基础模板；
4. 最后才使用 `通用因子结构.md`，并说明没有匹配模板的原因。

模板中出现的 `trade_when`、`add`、`multiply` 仅是参考结构；受本 Goal 顶部禁用规则约束，当前执行不得使用。模板中的 `vector_neut`、`regression_neut`、`group_neutralize` 等也必须先通过 `get_operators` 核验签名后才能落地。

每次替换只能改变一个字段、一个算子或一个窗口；先完成模板编号去重，再进行回测。模板编号、字段替换和变体方向必须写入批次记录。

同一骨架仅替换字段、窗口或正负号不算新的策略风格；每个批次至少覆盖 3 种策略风格。若当前 dataset 的字段族不足以覆盖 3 种风格，记录 `STYLE_COVERAGE_LIMITED`，不通过改写表达式强行凑数。

### 3. 数据集与 Universe

1. 任意时刻只保留一个 `active_dataset` 和一个 `active_universe`。
2. 表达式中的全部字段必须经 `get_datafields` 确认属于同一 dataset。
3. USA D1 存在多个合法 Universe 时，至少探索两个；单个 Alpha 仍只能使用一个 Universe。
4. 当前 dataset 的预登记模板和字段族未耗尽前不得切换；切换时记录原因和已排除范围。
5. 以字段实际属性为准，不因字段名称相似而混用数据集。
6. 对模板占位符逐个映射到真实字段；字段类型不匹配、Vector/标量不匹配或算子签名不明确时，候选停留在 `DISCOVERED`，不得进入回测。

### 4. 批量回测

只使用 cnhkmcp `create_multi_simulation`：

- 每批最多 8 个表达式，最后一批可少于 8 个；不为凑数复制表达式；
- 每批固定 dataset、Universe 和 settings；
- 保存 `batch_id`、`batch_size`、表达式、字段、settings 和原始结果；
- 不虚构 worker 数量。工具未返回并发信息时记录 `CONCURRENCY_UNOBSERVED`；
- 回测仅用于本地研究记录，不触发提交。
- 每批记录模板编号和策略风格；同一模板编号不得在同一批次重复，只替换字段或窗口的变体不得伪装成新模板。

### 5. 基础硬门槛

候选必须同时满足：

- `Sharpe > 1.58`；
- `Fitness > 1`；
- 平台明确口径的 `2Y Sharpe > 1.6`；
- `Margin > 10bp`；
- `0.05 < Turnover < 0.30`；
- 操作符数量 `< 6`，按 AST 子节点统计；
- 1–2 个唯一字段、单一 `dataset_id`；
- MCP 明确确认未提交；
- 所有指标均带单位、时间范围和数据来源。

缺失指标、单位不明、状态不明或只凭 `stage="IS"` 推断的候选不得进入 `BASE_PASS`。

### 6. Robust 与过拟合检查

基础通过后冻结表达式，不得根据 stress 结果调参。执行：

1. 同一表达式、dataset、Universe 下测试 `decay=[0,3,6]`；平台不允许的值记录原因。
2. 基础设置使用 `neutralization=NONE`，另选一个合法的非 `NONE` 风险中性化设置。
3. 风险中性化结果仍需满足 `Sharpe > 1`、`Fitness > 0.7`、`Margin > 10bp`。
4. 检查 yearly stats、2Y 指标、PnL 连续性、覆盖率、drawdown、long/short 数量及单日、年份、行业、风格集中风险。
5. 任一结果缺失记 `ROBUST_PENDING`；硬门槛失败记 `ROBUST_FAIL`。
6. stress 全部通过、PnL 无明显集中、结果产生后未再调参，才同时标记 `ROBUST_PASS` 与 `OVERFIT_PASS`。

### 7. 相关性与平台预检

按顺序执行：

1. `check_correlation` 获取 production correlation；无结果或 `abs(corr) > 0.7` 不通过。
2. 对候选 PnL 按日期合并计算 Pearson correlation；共同有效观测至少 252 个交易日，且 `abs(corr) < 0.4`。
3. 观测不足标记 `CORR_PENDING`，不得填 0；self correlation 仅作诊断记录。
4. 调用 `get_submission_check`；只有平台明确 PASS 才可进入下一状态。
5. 仅当以下条件全部满足时调用 `set_alpha_properties`：
   `BASE_PASS + RISK_NEUTRAL_PASS + ROBUST_PASS + OVERFIT_PASS + 未提交状态确认 + 两类相关性合格 + get_submission_check PASS`。
6. 保留原有 tags，并追加 `READY_TO_SUBMIT`；不擅自修改 color、category 或 osmosis points。

### 8. 候选文件与批次总结

每个 `{alpha_id}.md` 只记录：

- Alpha ID、表达式、模板、dataset、字段、Universe、settings、策略风格；
- 基础、风险中性化、robust、2Y/yearly stats 和相关性结果；
- 状态变更时间、证据来源和平台预检结果；
- 用户手动提交记录；若失败，只记录原因和下一步。

每次人工提交确认后，在同一文件末尾追加三句复盘：

- `有效操作`：1–3 条；
- `帮助不大`：1–3 条；
- `下次复用`：1–3 条。

每完成 10 个批次，在 `总结\批次总结.md` 追加操作符/字段探索率、模板与策略风格覆盖、主要失败原因、过拟合风险、收益归因和下一轮调整；不重复逐个 Alpha 详情。

## 停止与暂停条件

满足任一条件即停止继续挖掘：

1. 找到 10 个来自不同 `dataset_id`、覆盖不同策略风格且带 `READY_TO_SUBMIT` 的 Alpha，状态改为 `AWAITING_MANUAL_SUBMISSION`；
2. 预登记模板和字段族已尝试或有证据排除，论坛没有新的可验证方向，标记 `INCOMPLETE_EXHAUSTED`；
3. 用户要求停止。

单个平台接口连续 3 次失败、权限错误或额度阻塞时暂停 2 分钟，记录真实错误、已完成批次和可恢复位置；不得把暂停写成成功。

`AWAITING_MANUAL_SUBMISSION` 不是最终完成。用户手动提交后，继续核验平台状态、追加提交记录和复盘；全部处理完毕或用户明确结束后，Goal 才算完成。

最终报告必须包含：找到数量、dataset 覆盖、策略风格覆盖、各状态数量、提交记录状态、未解决风险，以及明确声明未调用 `submit_alpha`。
