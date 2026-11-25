# 双层多 Agent 执行计划与运行边界（D1-Only 版）

> [!IMPORTANT]
> **核心架构纠偏**：绝不让 LLM 通过 MCP 充当“每日 4,000 次发包循环器”（既达不到吞吐，又缺乏 10s 断线重连/SQLite Checkpoint，还会爆炸消耗上下文）。本计划采用 **「上层 Antigravity 多 Agent 决策编排 + 下层 `wq_research_v2/` 确定性 Python 吞吐引擎」** 的双层解耦架构，全链路强制锁定 **`settings.delay == 1`（不做 D0）**。

---

## 1. 双层分工与硬边界

### Layer 1 · Antigravity LLM 多 Agent 策略与治理层（子代理继承 Neon 高思考等级 `Model="inherit"`）

| 角色 | 权限边界 | 核心输入与日常职责 | 必须落盘的交付物（写入 `records/`） |
| --- | --- | --- | --- |
| **资料 Agent** | 只读 `cnhkmcp` + 只读本地语料（严禁发起回测或修改文件） | ① 核验官方 D1 规则、通知红线（11-30 AQP / 12-06 `Alphas=0` / 12-20 ASI PPA）与 D1 金字塔缺口；② 抓取空白 D1 塔字段元数据、`datecoverage ≥ 5年` 与 `Alphas=0` 资格快照；③ 维护 5:5 知识源（254 管理员原创 + 2026Q4 前 100 实证作者）。 | `records/rules/*.md`、`records/fields/FLD-*.md`、`records/sources/method_pool_50_50.md` |
| **实验设计 Agent** | 只读卡片 + 生成实验配置（严禁直接调用回测写接口） | ① 基于 `Field Card` 与 5:5 方法池编写带闭环预测的 `Hypothesis Card`；② 设计 Stage-0 快速探针（24–40 条 + 阳性对照）与 Stage-1 200 样本单变量消融矩阵（按 ATLAS L0–L6、表达式级 `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))` 等单轴推进）；③ 静态自检 `delay==1`、**永久禁用算子 `add`/`multiply`/`trade_when`**、Gold 84 算子白名单（拦截缺失的 `ts_median`）、`hump=` 关键字、`REVERSION_AND_MOMENTUM`、`<6` op 与 42 条缺陷模板过滤。 | `records/hypotheses/HYP-*.md`、`records/experiments/EXP-*-spec.json` |
| **复核与归因 Agent** | 只读回执/SQLite/PnL（严禁发回测、严禁调用 `submit_alpha` 或 `set_alpha_properties`） | ① 独立复核阶段指标（2Y/RN/区域 Margin 底线/年度 PnL/厂字型）与并行本地 SC 矩阵；② 审核阳性对照与反对意见，签发 `FAST_DEMOTED` / `Blacklist Card`（附详尽原因与单参数挽救路径）；③ 对四关终检全过候选打包 `CANDIDATE_FOR_MANUAL_REVIEW`；④ 执行阶段切换前 Grill-with-Docs 审查。 | `records/blacklist/BLK-*.md`、`records/experiments/EXP-*-review.md`、人工复核审查包 |
| **主控协调 Agent** | 唯一总账管理者与任务编排入口 | ① 维护 [00_索引.md](00_索引.md) 与北极星看板（92→100 / 金字塔 / 4,000 产能）；② 执行已拍板治理（永久禁用 `add`/`multiply`/`trade_when`、广州两服务暂停隔离、近 60 天未提交池扫描、单一根 Git 仓库收拢），并就清理执行与高风险变更呈报用户二次确认；③ 将通过静态校验的 `Experiment Batch Spec` 交由下层 `wq_research_v2/` 引擎执行，并对账终检远程 PC 与每日产量。 | `00_索引.md`、`records/cleanup/*.md`、`records/daily_volume/VOL-*.md` |

### Layer 2 · 确定性 Python 执行引擎（`wq_research_v2/`，遵循 `experience_profile.md`）

承担全部高吞吐、长周期、网络容错与持久化工作（详架构见 [08_工程架构与D1排期.md](08_工程架构与D1排期.md)）：
- **硬门禁内置**：`expr_validator.py` 与 `sim_runner.py` 强制静态断言 **`settings["delay"] == 1`**（拒发任何 D0 Payload）、**永久拦截禁用算子 `add (+)` / `multiply (*)` / `trade_when`** 与缺失算子 `ts_median`；内置禁止调用 `/alphas/{id}/submit`（无任何 `Formal Alpha Submission` 代码路径）；`set_alpha_properties`（`Remote Rename Application`）默认禁用且须显式 CLI 二次确认参数。
- **高可用与精准对账**：`10 分钟` 凭证自动刷新 + `10 秒` `NetworkMonitor` 断线重连 + `SQLite Checkpoint` 断点续传 + 原生 `simulationMode: "QUICK"|"FULL"` / `maxPosition` 透传 + 全量 `X-Ratelimit-*` 响应头捕获 + **只对账一次、绝不盲重发**协议 + 本地 SC（修复 3 大假零缺陷 + 92 OS 同步 + 池内两两 SC）+ 远程 PC `200 空体` 异步状态机。

---

## 2. 首轮校准与多阶段运行流程（广州已暂停隔离）

1. **广州同账号安全隔离（已获批完成）**：原广州 `worldquant-hill-climbing.service`（transient 单元，`Rsl` 61.4% CPU 活锁）与 `worldquant-ra-detection.service`（`Ssl`，持续轮询 `/correlations/prod`）与本地共用同一 BRAIN 账号（`lu***@gmail.com`）。已按用户明确同意通过 `systemctl stop` 干净暂停两项服务（**零删除任何远程代码/数据**，已验证 `inactive` 且 0 残留进程），完整预暂停单元快照与一键恢复命令（含 transient 单元精确 `systemd-run` 参数）见 [guangzhou_isolation_receipt.md](records/rules/guangzhou_isolation_receipt.md)。
2. **两条独立字段队列**：
   - **普通队列（日额 5,000）**：用于 3 个“2→3”准达标金字塔、**近 60 天未提交 D1 池修复**、`GBR/model26` T0 冒烟与高覆盖非零字段。
   - **`Alphas = 0` 免额度队列（12-06 冻结前抢跑）**：仅收纳经 Data Explorer 核实**全部**经济字段为 `Alphas = 0`（可附 9 个 PV1 辅助字段）的 D1 表达式，优先打 `DEU/TOP500/D1`（`model264`/`analyst93`/`other250`）、`ASI/MINVOL1M/D1`（`ai_news_scores`/`model207`）与 `CHN/TOP2000U/D1`（`other496`/`analyst45`）。
3. **T0 小批接口与额度校准（2 组 × 8 条）**：
   - **校准组 1（模式与表达式级 `min` 冒烟）**：`GBR/TOP700/D1 model26` 同一组 8 条表达式（含单分支 `rank(expr_A)`、`rank(expr_B)` 与表达式级双分支 `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))`，严格无 `add`/`multiply`），分别跑 `FULL` 与 `QUICK`（均 `visualization=false`），实测 Quick 是否返 `Margin`、耗时加速比与回执字段。
   - **校准组 2（免额度与响应头实证）**：`DEU/TOP500/D1 model264` 8 条纯 `Alphas = 0` 表达式，逐条记录 `X-Ratelimit-Limit / Remaining / Reset` 前后差值，实证账号真实普通限额、EST 00:00（北京 13:00）重置时间与免额度生效。
4. **并发阶梯爬坡（绝不一步拉满）**：
   - **L1 校准期**：`2 并发 × 8 条`（确认零 429、Checkpoint 断电重启恢复无重发、SC 同步无假零）；
   - **L2 冲刺期（Phase 3，11/29–12/06）**：`4 并发 × 8 条`（双轨推进 92→100 与 12-06 `Alphas=0` 探针/200 样本归因，GLB 按 2 槽折算）；
   - **L3 验收期（Phase 4，12/06–12/09）**：在确认良率与无广州冲突后，爬坡至 **`6–8 并发 × 8–10 条`**（GLB 仍按 2 槽计），验收连续 3 个 EST 平台日（北京 13:00 日切）每日有效完成 ≥ 4,000（遇 429 自动按 `X-RateLimit-Reset` / `Retry-After` 熔断降档）。
5. **日终对账与回流**：每个 EST 平台日结束后，引擎自动导出并由复核 Agent 核签 `records/daily_volume/VOL-YYYY-MM-DD.md`，分列：发起量、`Quick Screened` 量、`Full 有效完成量`（4,000 验收口径）、去重跳过量、技术失败/429/待对账量、Tier-1 通过量、Tier-2（SC+PC）通过量、普通额度与 `Alphas=0` 额度实耗、5:5 来源占比及新增 `Blacklist Card`。

---

## 3. 安全与防失控红线（全 Agent 与引擎共同遵守）

- **绝不越权提交**：任何 Agent 或脚本禁止调用 `submit_alpha`；`set_alpha_properties` 须用户二次确认。
- **绝不绕过静态算子与 D1 硬禁令**：`expr_validator.py` 与实验设计前检强制拦截非 `settings.delay == 1` Payload、**永久禁用算子 `add (+)` / `multiply (*)` / `trade_when`** 及缺失算子 `ts_median`；双字段组合一律采用表达式级 `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))`。
- **绝不误删保护资产**：`legacy_core/Core/runtime_data/`（1,532 文件）、`reference/`（静态只读参考库，含 `TopUser_2026Q4.txt` + 管理员原创 254 篇 + 前百 264 篇）、有效 `Password/config.yaml` 凭据严禁触碰；全工作区已统一收拢至单一根目录 Git 仓库（零嵌套 `.git`）。
- **绝不盲目重发**：遇 `429 / 5xx / 超时 / 缺子 ID` 仅存指纹标 `PENDING`，冷却 5 分钟后按精确 `(expression, settings, time_window)` 只读对账 1 次；仍无观测标 `RESULTS_UNOBSERVED` 人工复核，不计入 200 分母。
- **绝不以局部替代全局**：单条高相关或未过 2Y/RN 的候选不进入 PC 查询，节约 `/correlations/prod` 限频；近邻参数变体家族只计 1 份独立证据。
