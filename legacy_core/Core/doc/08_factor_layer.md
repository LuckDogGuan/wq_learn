# 08 — `Core/factor/` 因子生成层

## 职责

纯代数表达式生成与过滤，**不含任何 HTTP 调用、数据库操作或文件 IO**。

---

## `factor/generator/alpha_factory.py`

依赖：只有 `Core.constants.global_ops`（算子常量）+ 标准库 `itertools`、`collections`。

### 工厂函数

| 函数 | 说明 |
|---|---|
| `ts_factory(op, field)` | 时序操作符：生成 5/22/66/120/240 天 5 种窗口表达式 |
| `ts_comp_factory(op, field, factor, paras)` | 带超参的时序复合操作符（ts_percentage, ts_decay_exp_window, ts_moment, ts_entropy） |
| `vector_factory(op, field)` | 向量操作符（结合 `cap`） |
| `twin_field_factory(op, field, fields)` | 双字段交互（ts_corr, ts_cov 等） |
| `group_factory(op, field, region)` | 截面分组操作符，覆盖 market/sector/industry/subindustry/cap_bucket 等 15+ 分组条件 |
| `first_order_factory(fields, ops_set)` | 一阶 Alpha 批量生成主工厂 |
| `get_group_second_order_factory(first_order, group_ops, region)` | 二阶（一阶 + group 截面）批量生成 |
| `trade_when_factory(op, field, region)` | 条件交易触发因子（**注：AGENTS.md 禁止使用 trade_when**） |

---

## `factor/filter/`

### `expression_checker.py` — 语法验证器

```python
def verify_alpha_expression(expr) -> bool
```
- 本地 AST 解析，验证算子名称、参数个数、括号匹配。
- **提交前必须经过此检查**，防止消耗平台 API 限额提交语法错误的 Alpha。

### `analyzer.py` — 因子分析工具

```python
def categorize_factors(factor_list) -> dict
def analyze_keyword_frequency(exprs) -> dict
def filter_by_keywords(exprs, keywords) -> list
def filter_by_metrics(df, sharpe_min, fitness_min, turnover_min, turnover_max) -> pd.DataFrame
```

---

## `constants/global_ops.py`

全量算子签名库，包含所有 BRAIN 平台支持的算子名称、参数规格定义。供 `expression_checker` 和 `alpha_factory` 调用。

## 4. `Core/factor` 有用文件详细说明

本目录模板只负责生成 Alpha expression 字符串，不负责字段存在性、权限、回测或提交检查。模板输出必须经过本地表达式验证和平台实时检查。

### 4.1 专题模板

- `templates/momentum_reversal.py`：`momentum_20d` 生成 20 日相对变化；`short_term_reversal` 生成负的 `ts_delta`；`price_volume_divergence` 生成 `-ts_corr(rank(high), rank(field), d)`；`double_difference_acceleration` 生成二阶差分；`overnight_gap_reversal` 使用 `open` 和前一日 `close` 处理跳空。注意 `price_volume_divergence` 固定使用 `high`，不是任意两字段相关性模板。
- `templates/fundamentals.py`：`zscore_normalization` 默认按 `subindustry` 做 `group_zscore`；`rank_difference` 比较两个字段的截面排名；`fundamental_trend` 默认用 63 日窗口计算变化率。季度字段可先测试 63，年度字段可测试 252。
- `templates/cross_sectional.py`：提供组内排名、`zscore(quantile(...))`、`normalize(pasteurize(...))`、`inverse` 和 `densify`。这组主要是截面预处理包装器，不一定单独构成完整 Alpha。
- `templates/advanced_ops.py`：提供线性衰减、平均差异、`ts_step` 相关、极值时间、鲁棒对数、复利缩放、回填、收益波动开方和历史分位数。`scaled_cumulative_product` 要求输入接近收益率，不应直接套价格水平。
- `templates/statistical_risk.py`：提供 `ts_ir`、负峰度、负历史 Z-Score、累计冲击、最大差值和缺失惩罚。`data_stability_check` 是表达式内缺失惩罚，不等同于字段目录 coverage。
- `templates/sentiment_analyst.py`：提供新闻情绪短长均值比较、分析师预期修正和论坛情绪/价格背离。示例字段只表示使用方向，必须从实时目录确认。

### 4.2 风险和集中度模板

`templates/risk_and_correlation.py` 用于已有 Alpha 的后处理：`optimize_turnover_with_decay` 尝试平滑降换手，`optimize_weight_concentration_neutralize` 和 `optimize_weight_concentration_rank` 尝试分散头寸，三个 `reduce_correlation_*` 函数用于衰减、分组中性化和延时扫频。后处理会同时改变 Sharpe、Margin、Turnover、自相关和收益来源，必须重新回测。

`templates/pc_control.py` 的四个函数共享较深的行业中性化、向量平均、时序均值和乘积结构：

```text
ts_product(group_neutralize(-ts_mean(vec_avg(field), d1), industry), scale)
```

`pc_control_rank` 使用组内排名，`pc_control_zscore` 使用组内 Z-Score，`pc_control_vol_adjust` 再除以近期波动，`pc_control_ts_rank` 再做时序排名。默认 `d1=240`、`scale=5`；波动调整额外使用 `vol_d=21`，时序排名额外使用 `rank_d=60`。表达式较深，应在已有候选出现集中度问题时受控使用。

`templates/forum_advanced_solutions.py` 是经验型实验模板：`apply_rank_by_side_and_diff` 可能需要当前账户没有的 `rank_by_side` 权限；`inner_group_neutralize_with_outer_ram` 返回的设置字典不会自动写入回测参数；`resolve_reversion_component` 当前是占位逻辑，最终原样返回输入，不能当作自动修复器。

### 4.3 基础算子模板

`templates/all_operator_templates.py` 是全量基础算子示例库，适合查看最小表达式和做模板检查，不负责字段权限、去重、候选限量、平台回测或提交。文件中虽然存在 `trade_when`，但当前项目规则明确禁止使用；`add`、`multiply` 也属于项目禁用边界。

## 5. `generator/alpha_factory.py` 的实际行为

- `ts_factory`：固定生成 5、22、66、120、240 五个窗口。
- `ts_comp_factory`：使用 5、22、66、240 与额外参数做组合。
- `vector_factory`：当前只与 `cap` 组合。
- `twin_field_factory`：与其他字段两两组合，窗口为 5、22、66、240。
- `first_order_factory`：保留原字段，再按 `ts_*`、复合时序、向量和普通算子扩展。
- `group_factory`：套用市场、行业、资产/市值桶、波动/流动性桶和部分 USA 专用分组。
- `get_group_second_order_factory`：对一阶候选继续叠加分组操作，数量会快速膨胀。
- `trade_when_factory`：生成条件交易候选，但当前项目禁止使用。

生成器不会自动完成语法验证、字段验证、权限验证、去重、数量限额或回测。批量生成后必须保留模板、字段、参数和表达式来源，并先做小批量验证。

## 6. `filter/` 中有用的文件

- `expression_checker.py`：入口为 `verify_alpha_expression` 和 `batch_verify_expressions`；只有 `valid == True` 才能通过本地语法门槛。
- `expression_verifier/validator.py`：实际的 AST 和算子校验器；`parsetab.py` 是生成文件，不应手工修改。
- `analyzer.py`：按 coverage 和 alphaCount 分为 Garbage、Unexplored、Emerging、SweetSpot、Crowded；这是本地字段分类，不是最终 Alpha 质量结论。
- `factor_utils.py`：提供关键词频率、关键词筛选和 coverage/alphaCount/dateCreated/valueScore 筛选；调用前应确认 DataFrame 列存在并记录筛选条件。

## 7. 推荐使用顺序和核对清单

```text
实时确认 Region/Universe/数据集/字段
  → 选择一个模板方向并生成少量表达式
  → 去重，记录模板函数、参数和完整表达式
  → expression_checker 验证，valid 必须为 True
  → 实时字段/权限/兼容性检查
  → 平台回测、基础指标、风险和相关性检查
  → 用户手动决定是否提交
```

超时、空响应、缺少 Alpha ID 或未返回生产相关性时，不能当作通过；模板函数名中的“优化 Sharpe”“降低相关性”也不是结果保证。

## 8. 模板注册与使用记录

`factor/template_usage.py` 提供广度探索所需的最小公共能力：

```python
from Core.factor.template_usage import (
    compose_template_batch,
    resolve_template_category,
    select_template_candidates,
    record_template_usage,
    summarize_template_usage,
)
```

- `TEMPLATE_CANDIDATES` 登记普通模板、虎哥一元/二元模板和条件型后处理模板。登记不等于启用；字段语义、字段类型、同数据集、实时算子权限、本地语法和操作符数量会继续过滤。
- 模板学习范围是 `Region + Category`。Category 优先使用主塔末段，字段元数据只作回退；二者冲突时保持 `PENDING_CATEGORY_CONFLICT`，不进入学习。
- 模板按 `SIGNAL_BUILD`、`STABILITY_CONTROL`、`FINAL_REPAIR` 分阶段选择。窗口、Decay、Delay 和 Group 只生成声明白名单内的单轴变体，不生成参数笛卡尔积。
- Stage 1 正式模板必须登记 `ECONOMIC_SIGNAL`、Category 白名单、经济假设和字段语义要求。`economic_signals.py` 只提供最短表达式，收益方向由注册项的语义证据约束，不能按函数名猜测。
- `compose_template_batch()` 固定尝试 4 条经济语义/当前缺口匹配、2 条同范围优胜模板和2条新模板或单轴参数 Challenger；普通 `LOW_PRIORITY` 不补位，每20个同范围正式父批次最多复检1条。不足8条返回空批，调用方不得 POST 或跨 Category 补齐。
- `record_template_usage()` 写入新版 `events_v3.jsonl`；只有 `candidate_origin=FORMAL_TEMPLATE`、基线和结果目标指标都完整的 `COMPLETE/CACHE_HIT` 才进入表现分母。局部探针、基线刷新和自适应修复仍可审计，但不污染正式模板表现。
- 新版状态依次为 `PROBATION`、`PROMISING`、`CHAMPION`、`LOW_PRIORITY`、`DISABLED_SCOPE`。成功必须减少当前阶段硬门槛缺口，并保住此前已经通过的门槛；`PENDING`、429、连接重置、权限/语法/字段错误不进入表现分母。
- 模板状态只影响后续选择，不删除历史。人工可通过记录 `MANUAL_DISABLED` 状态暂停模板，后续仍可恢复。

默认运行时文件位于 `Core/runtime_data/template_usage/`，不应提交 Git：

- `events_v3.jsonl`：经济假设、语义证据、完整基线/结果和目标指标变化的逐候选事件。
- `summary_v3.csv`：只由 v3 正式模板完整结果重建的学习汇总。
- `events_v2.jsonl`、`summary_v2.csv`：只读保留；满足旧版充分负证据的同版本变体只进入初始冷却名单，不作为 v3 样本。
- `events.jsonl`、`summary.csv`：旧评分口径账本，只读保留，不参与新版选择。

`expression_checker` 仍然只是本地语法/签名门槛。模板的字段存在性、当前账户权限、平台指标和本地 SC 必须分别观察；模板名称不是收益保证。
