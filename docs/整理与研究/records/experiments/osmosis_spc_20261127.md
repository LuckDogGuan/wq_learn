# Osmosis 与 SPC 更新记录 · 2026-11-27

时间均为北京时间。Osmosis 目标为平台 `Combined Osmosis Performance > 0.50`。

## Osmosis

| D1 范围 | 更新前 | API 回读 |
| --- | ---: | ---: |
| GLB | 100,000 点 / 14 Alpha | 100,000 点 / 14 Alpha |
| EUR | 100,000 点 / 10 Alpha | 100,000 点 / 10 Alpha |
| GBR | 100,000 点 / 10 Alpha | 100,000 点 / 10 Alpha |
| USA | 0 点 / 0 Alpha | 100,000 点 / 10 Alpha |
| 合格范围 | 3 | 4 |

- 本轮配置基于更新前的官方综合成绩 **-3.22**。11:28 共提交 10 次 `PATCH /alphas/{id}`，均返回 200。`GET /users/self/alphas` 对账与计划一致，`GET /users/self/osmosis/summary` 读到四个合格范围。
- 本轮变量是新增 USA/D1。以下 10 个 Alpha 各由 0 点调整为 10,000 点。`3q936AEN`、`3qA6dvlN`、`3qAvQxk6`、`A10Ygvdl`、`E5k9E9gr`、`E5mWLW0J`、`O0rqZ3aY`、`ZYoW7wMZ`、`e71w5Qrl`、`omYMxop5`。
- 依据 97 条已提交 D1 Alpha 的本地累计 PnL，做日差分、按 book size 归一化，范围内按点数加权，范围间等权。用共同覆盖的 2018-01-23 至 2021-12-31 数据挑选，分别用 2022 和 2023 年检查。依据可投资性约束后 Sharpe、换手率和配对相关性筛出 USA 的 10 条，拟合段最高成对相关性为 0.611。平台公开的序列是截至 2023-12-29 的样本内数据。下表使用原始 PnL 估算，未包含官方税费、周锁定及组合计算口径。

| 配置 | 2022 年样本内 Sharpe | 2023 年样本内 Sharpe | 本轮处置 |
| --- | ---: | ---: | --- |
| 更新前配置 | 4.43 | 5.57 | 基线 |
| 加入 USA/D1 | 5.58 | 5.86 | 已应用并回读 |
| 加入 USA/D1，另在 GBR 以 `bl8LnbA6` 换出 `9qpbKkoo` | 5.83 | 6.13 | 备选 |

本次回读验证了点数生效，官方新一期综合税后 Sharpe 待发布。按官方每周锁定规则，若该配置持续到美东 11 月 29 日周日 23:59，预计从 12 月 7 日所在周起进入日组合计算。复核时记录官网新一期综合成绩、有效 PnL 天数、四个范围点数与当前日报排名，和本轮 -3.22 对比。综合指标按月刷新，指南给出的典型间隔为 4–6 周。[官方 Osmosis 分配指南](https://platform.worldquantbrain.com/learn/documentation/consultant-information/osmosis-allocation-guide-consultants)

本地留档位于 [data/osmosis_allocations/20261127](../../../../data/osmosis_allocations/20261127)。包含 `alpha_before.json`、`alpha_after.json`、`summary_before.json`、`summary_after.json`、`apply_plan.json`、`operations.jsonl` 和 `offline_comparison.json`。

## SPC

11 月 26 日刚补位及切换 30 条配置。两个月的账户级榜单作为之后的观察基线。名次对应各自月份的参赛池，当前得分粒度无法将变化归因到昨天切换的模型或具体提示词。[11 月 26 日切换记录](../../../../legacy_core/pipelines/spc/log/API_实时核验_20261126.md) · [SPC 榜单](https://platform.worldquantbrain.com/competition/spc)

| 榜单月份 | 排名 | 榜单计权提示词 | Scaled Daily PNL 显示 | 有效 PnL 天数 |
| --- | ---: | ---: | ---: | ---: |
| 2026-10 | 88 | 50 | 0.00 | 21 |
| 2026-11 | 2,469 | 50 | 0.00 | 17 |

| 模型 | 核验前计权 | 429 对账后计权 |
| --- | ---: | ---: |
| DeepSeek V3.2 | 20 | 20 |
| Claude Fable 5 | 9 | 9 |
| Claude Opus 4.8 | 7 | 7 |
| Gemini 3.8 Flash | 4 | 4 |
| Claude Sonnet 5 | 3 | 3 |
| GLM 5 | 3 | 3 |
| Kimi K2.5 | 2 | 2 |
| Qwen3 235B | 2 | 2 |
| GPT | 0 | 0 |
| 合计 | 50 | 50 |

- 两次完整 API 读取的 216 条记录逐 ID 一致。50 条计权配置均为 Daily、`1.00`、`Active`。未计权记录中有 47 条 `Unstable Output`、14 条 `Failed`。
- 11:29，给 AM112 的 DeepSeek V3.1 创建零权重试跑时，平台返回 HTTP 429，响应未带 `Retry-After`，具体限额类型未取得。停止写入。11:30 仅做一次只读对账，未见新记录，标记 `RESULTS_UNOBSERVED`。同批 R1 未发送。
- 后续候选优先 **DeepSeek V3.2**。以 AM109 的 Claude Sonnet 5（`DXmEpx4`）为对照，复用同一提示词、样例和更新频率，按 V3.2、V3.1、R1 顺序准备了三个零权重版本。三个版本均待创建，计划中 GPT 为 0。模型 ID 取自本次 `OPTIONS /competitions/spc/submissions` 实时枚举。

本地留档位于 [data/spc_logs/20261127_check](../../../../data/spc_logs/20261127_check)。包含前后完整快照、汇总、实时模型目录、操作日志、原试跑计划和更新后的 `next_trial_plan.json`。
