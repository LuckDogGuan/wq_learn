# 模板与算子验证：证据、生命周期与验证设计

2026-11-27（含 15:35 修订）· 范围：D1 RA 主线 · **这是核心验证任务（T17）**。
数据：`data/exports/task_template_rows.csv`（广州台账只读导出，15,193 条已完成任务，**FULL 6,865 + QUICK 8,328**）、批级导出 `batch_audit_latest.json`、旧库 `legacy_alphas`（2026-07/08）、`OPTIMIZATION_LEDGER.json`、`REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md`。
复现：[task_template_audit.py](../../../../scripts/analysis/task_template_audit.py)（任务级，配对）、[template_pack_audit.py](../../../../scripts/analysis/template_pack_audit.py)（批级，仅作旁证）。证据标记见 [GLOSSARY.md](../../../../GLOSSARY.md)。

> **修订说明**：首版把批审里的 `completed_full=14,729` 当成 FULL 条数使用。任务级导出显示它**合并了 FULL 与 QUICK**（FULL 仅 6,865），首版的“FULL”数字应读作“已完成（两种模式混合）”。本版全部改按模式拆分重算，首版结论中依赖该口径的数字已更正。

## 1. 结论先行

| # | 发现 | 等级 |
| --- | --- | --- |
| 1 | **FULL-only** 命中（Sharpe≥1.58 且 Fitness≥1.0）465 条，**97.2% 来自 58 个数据集中的 5 个**（`ASI/multifactor_return_pred` 169、`EUR/model25` 125、`EUR/model77` 77、`USA/model31` 54、`ASI/model39` 27），这 5 个占 FULL 行数的 29.9% | `[V]` 描述性 |
| 2 | 其中“没有任何 FAIL 项”的只有 116 条：`USA/model31` 54、`EUR/model25` 51、`EUR/model77` 10；**ASI 命中 0 条无 FAIL**（口径仅数 FAIL 名，PENDING/WARNING 另论，见 T04） | `[V]` |
| 3 | 标准 Stage-1 八模板包（`RA-ADM`/`RA-TOP`/`RA-DUAL`）占 FULL 的 **73.6%**（5,051/6,865），只出 **27** 个命中（0.5%）；精修与其他（1,814 FULL）出 **438** 个（24.1%）。精修是对已出色母版的爬山，不是模板证据 | `[V]` |
| 4 | **同字段同设置的配对比较**（四个模板族，见 §2）：模板族排名**随地区而变**，并非“一个冠军通吃” | `[V]` 配对、`[C]` 地区 |
| 5 | `EUR`：`group_zscore(x, industry)`（原汁、无平滑）在有信号的字段里 **FULL 79%、QUICK 85%** 夺第一；与手册中 `LD22811 #13` 的 `EUR/model25` 冠军骨架说法一致 | `[V]`（EUR 内两种模式同向） |
| 6 | `ASI`（仅 QUICK 可比）：同一模板族夺第一 59%，`group_rank(ts_decay_linear(x,10),subindustry)` 24% | `[V]` 单模式 |
| 7 | `USA`：FULL 里 `group_rank(ts_decay_linear(·,10))` 52%、`group_rank(ts_zscore(ts_mean(·,5),66))` 37%；QUICK 里原汁 `group_zscore(x, industry)` 53%。**两种模式相反**，且 FULL/QUICK 字段集合不同（352 个 FULL 字段里只有 109 个出现在 QUICK），USA 排名 | `[C]` 不能定论 |
| 8 | 基线 `group_zscore(ts_mean(x,22), subindustry)` 在有信号字段里**很少夺第一**（QUICK 各地区 0–7%，FULL-EUR 16%、FULL-USA 2%）。它是 Admin 帖骨架，也是此前默认基线 | `[V]` 配对 |
| 9 | 中性化（同字段同模板，对比 `SUBINDUSTRY`）：FULL `REVERSION_AND_MOMENTUM` +0.35（40 对，95% 更好、0% 更差）、`CROWDING` +0.17（40 对）、`INDUSTRY` +0.11（54 对）；QUICK `COUNTRY` +0.30（64 对）、`CROWDING` +0.05、`REVERSION_AND_MOMENTUM` 0.00、`STATISTICAL` −0.13。**`REVERSION_AND_MOMENTUM` 两种模式不一致** | `[V]` 配对、`[C]` |
| 10 | 近期完成任务 Sharpe≥1.25 的占比（混合口径）约 8.4%，旧库 67.5%：旧库不能用来给现役模板排名 | `[V]` |

**直接含义**：你的直觉“多数一般”在数据里表现为：**没有任何一个模板在所有地区都占优，且标准八模板包在 FULL 上几乎不产出（0.5%）**。有效的“少数”是“某地区 × 某模板族 × 某中性化”的组合。因此不该按全局排名删模板，而应按地区建 Stage-1 的模板顺序。AGENTS.md 规定算子永不拉黑，筛选单位是“模板在某地区/数据集/设置下的用法”。

**不能由此推出的**：(a) 单个算子的作用——四个族同时改了平滑、归一化方式和分组，无法归因到单个算子，需要 §3 的单轴实验；(b) 拥挤度——导出里没有按模板的 PC，且 PC 只在过门槛后才计算，缺失占绝大多数；(c) QUICK 排名能否代表 FULL——两种模式的字段集合不同（T09）。

## 2. 模板族与初始登记

Stage-1 每个模板带反向，配对比较取两个方向中较好者。四个模板族：

| 族 | 表达式（骨架） | 来源 | 配对证据 | 建议状态 | 等级 |
| --- | --- | --- | --- | --- | --- |
| F1 | `group_zscore(ts_mean(x,22), subindustry)` | Admin `WL13229` | 很少夺第一；FULL 两地区均值偏低 | `MODIFY`，只留作对照基线，不再当默认主力 | `[V]` 配对 |
| F2 | `group_rank(ts_decay_linear(x,10), subindustry)` | Admin `WL13229` | USA-FULL 第一（52%）；EUR 在两种模式均为 0% 夺第一 | `KEEP`（USA）；`RETIRE`候选（EUR，需复核） | `[C]` 地区 |
| F3 | `group_rank(ts_zscore(ts_mean(x,5),66), subindustry)` | Top100 `SZ83096` | USA-FULL 37%；其余多处偏弱 | `PROBATION` | `[C]` |
| F4 | `group_zscore(x, industry)`（无平滑） | Top100 `LD22811` | EUR 两种模式 79–85%；ASI-QUICK 59%；USA 两模式不一致 | `KEEP`（EUR、ASI）；USA `PROBATION` | `[V]` EUR、`[C]` 其余 |

其余登记（批级旁证，仅作线索）：`RA-NLG`（`tail25-d22-sub`）略优于基线；`RA-DUAL-GRANK-MIN-*` 各中性化版本在 Stage-1 通过率上与基线差 ≤1.3pt，看不出区别；`RA-TSR` 样本小且偏负；`T0-TOP-03`（`signed_power(group_zscore(reverse(ts_mean(x,22)),subindustry),1.5)`）只有单个 `DEU/model264` 样本（换手 2.4%、Sharpe 0.45），仅作结构候选 `[R]`。

生命周期：`UNTESTED → PROBATION → KEEP | MODIFY | RETIRE`，加标志 `CROWDED`。状态变化至少要：同字段同设置的配对证据 + 样本量写明。

## 3. 验证实验设计（工单 06；额度 500–1000 FULL，已授权）

**目的**：把“模板族/算子/中性化是否真有效”从观察变成受控配对，并回答“公开模板变异后是否更好”。**PC 仅描述性记录，不设门槛**：PC 是与他人已提交因子的重合/相似度，降不下来很正常；评判看 Sharpe、2Y、Fitness、换手、Margin 与相对字面版的保留。

**样本**：QUICK 中已被证明“有信号”（任一族 Sharpe≥0.8）的字段，现有 ASI 49、EUR 54、USA 84、GLB 9 个，优先挑 `Alphas=0` 免额字段（至 `2026-12-06`）与你当前点塔 category 内的字段。每个字段方向取 QUICK 中较好的一侧，不重复跑反向。选 70–140 个字段。

**每字段 7 条 FULL（每条相对 V0 只改一轴）**：

| 变体 | 表达式 | 回答的问题 |
| --- | --- | --- |
| V0 | `group_zscore(x, industry)` | 基线（字面 F4） |
| V1 | `group_zscore(ts_mean(x,22), industry)` | 加平滑是否有益 |
| V2 | `group_zscore(ts_decay_linear(x,10), industry)` | 另一种平滑 |
| V3 | `group_rank(x, industry)` | 归一化方式（zscore ↔ rank） |
| V4 | `group_zscore(x, group_cartesian_product(country, industry))` | 分组变异 |
| V5 | `signed_power(group_zscore(x, industry), 0.5)` | 非线性变异 |
| V6 | `group_rank(ts_decay_linear(x,10), subindustry)`（字面 F2） | 跨族对照 |

总量 490（70 字段）到 980（140 字段）。设置沿用 Stage-1 默认（`decay=0`、`SUBINDUSTRY`、`truncation 0.04`、`maxTrade OFF`），不与中性化同改；中性化另设 §3 附注的小实验。

**预登记的判据（草案，可由你改）**：某变体在某地区“被支持”，当且仅当在该地区有信号字段上，相对 V0 的配对 ΔSharpe 均值 >0、胜率 ≥60%、样本 ≥30 个字段，且符号检验 p<0.05；“被否定”当 ΔSharpe 均值 <0 且同样显著。其余记 `[U]`。结果写入 `OPTIMIZATION_LEDGER.json`（`[有效]`/`[无效]` + 坐标）。

**约束**：D1；不含 `+`、`*`、`trade_when`；变体含 `group_cartesian_product`/`signed_power` 前需通过本地 AST 与算子白名单；嵌套深度和算子数用 `compute_expression_nesting_metrics` 记录；不挤占主线 `4,500/天`；经现有 runner（4 并发、`FULL`），429/5xx/超时按“只读对账一次”规则。**启动前我会把生成的表达式清单与预算给你确认一次（因为会在广州守护进程上排队，与点塔共用并发槽）。**

**附注·中性化小实验**（可选，≤120 条）：对 EUR 有信号字段取 V0，在 `SUBINDUSTRY / INDUSTRY / CROWDING / REVERSION_AND_MOMENTUM / COUNTRY` 下各跑一次（5 × 24 字段），检验 §1 第 9 点的不一致。

## 4. 算子层面（只作线索）

旧库按 `(region, 字段集合)` 配对的“含该算子 vs 不含”Sharpe≥1.25 占比差（**旧库口径，`[C]` 弱**）：偏负 `ts_delta`（−25pt）、`ts_returns`、`abs`、`vec_avg`；偏正 `ts_decay_linear`（+16pt）、`rank`（+13pt）、`ts_zscore`（+8pt）、`quantile`、`group_zscore`（+6pt）；`group_rank` −10pt，与手册把它列为冠军骨架冲突，记 `conflicted`。现役口径下的算子结论要等 §3 的 V1–V5 实验。

## 5. 既有经验二次使用审计（初判，完整版见工单 07）

| 经验 | 判断 | 二次使用前的最小验证 |
| --- | --- | --- |
| 手册：`LD22811 #13` 的 `group_zscore(x, industry)` 是 `EUR` 冠军骨架 | **本次在 EUR 配对数据中复现** `[V]` | 无需再验；USA 勿照搬 |
| IMP-01 `adv20` 门控 | `[C]` 仅 `EUR/model25` 家族；同手册有反例 | 目标字段上做 `{0.20,0.30,0.40}` 软门控单轴 |
| IMP-02 降 PC 组合 | `[C]` 单谱系；PC 不是本验证的目标 | 不再作为验证指标 |
| IMP-03 单变量迭代 | 方法论，有内部事故佐证 | 沿用 |
| IMP-04 数据集第一 | **规模化支持** `[V]`（5/58 数据集 97.2% 命中） | 选集仍按地区独立测 |
| T0 校准（`DEU/model264`） | 耗时/限速标定可用；**模板排名无效** | — |
| 手册“机构基本面大集优于冷门舆情集” | `[C]`；`ASI/multifactor_return_pred` 不属此类却产出最多 | 新集按 Stage-0 规则判断 |

## 6. 局限与下一步

- 观察性数据；配对消除了字段效应，但不消除“字段被选来跑哪个模式”的时间/策略差异。
- “有信号”按 Sharpe≥0.8 定义，会带来选择效应；对该条件下的比较，不外推到死字段。
- 未做多重比较校正；样本小于 30 对的结论只作方向。
- 零失败仍继承 T04 的 PENDING/WARNING 口径问题。
- 工单：`.scratch/template-screening/`；导出脚本 `scripts/ops/export_guangzhou_task_templates.py`（只读）。
