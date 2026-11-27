# WorldQuant BRAIN Workspace — AGENTS.md

仅记录不可逾越的红线、实证避坑点与关键真源路径（目录说明见 [README.md](README.md)）。

## 1. 硬红线（严禁违反）

1. **严格 D1-Only**：全链路锁定 `settings.delay == 1`，严禁任何 `Delay = 0 (D0)` 回测。
2. **Decision #3 算子永久禁令**：永久禁止 `add (+)`、`multiply (*)`、`trade_when`；双分支融合统一用 `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))`。
3. **绝不自动提交 & 标签/别名/Margin 优先铁律（全过线自动 PATCH）**：永不调用 `POST /alphas/{id}/submit`。全部条件通过（RA 硬检 `0 FAIL` + `SC < 0.65` + 池内正交 + `PC < 0.70`）打 **`Useful`** 标签（独立 PPA 线打 **`PPA_Useful`**）；**凡通过 RA 硬检且 `SC < 0.65` 者统一写别名 `SC 0.xxx PC 0.xxx`**（仅 PC 未过者或同簇低 Margin 备选打 **`SC_PASS`**）；**其他条件全通过时严格优先保留 `Margin` 越高越好的因子**；**只要指标与参数全部过线，直接自动执行 `PATCH /alphas/{id}` 修改标签/别名（含同簇高 Margin 升级替换）并在回复中向用户提示，无需事前询问**。
4. **硬保护只读资产与已完成台账**：严禁删除/改写 `legacy_core/Core/runtime_data/`（1,532 文件）、`reference/`（静态参考库）；严禁读取/打印/提交 `Password/config.yaml`；SQLite `COMPLETED_FULL` 行永久不可被重启去重（`DEDUP_SKIPPED`）覆盖。
5. **只对账一次、绝不盲重发**：遇 `429 / 5xx / 超时 / 缺子 ID` 仅存指纹标 `PENDING_RECONCILE`，冷却后只读对账 1 次，仍未观测落 `RESULTS_UNOBSERVED`。
6. **无 GUI、广州低内存（1.9 GiB RAM）与地区并发线程上限**：不建本地 Web GUI；后台任务必配 SQLite WAL Checkpoint、10m 认证刷新、10s 重连、流式低内存扫描与 `MemoryMax=512M`；**地区并发硬上限：`GLB` 最多 `3` 个线程，其他所有地区最多 `4` 个线程**（代码层 `WeightedSlotSemaphore` 与 `parse_region_caps` 强制封顶）；新模块必配 `tests/` 单测与 AST 校验。

## 2. 核心研究与平台避坑要点（防止再次错过）

1. **7 层概念严禁混为一谈**（官方术语表：[BRAIN_OFFICIAL_GLOSSARY.md](docs/official_guides/BRAIN_OFFICIAL_GLOSSARY.md)）：
   `Dataset（数据集）` ≠ `Data Field（数据字段）` ≠ `Operator（算子，永不拉黑）` ≠ `Template（模板）` ≠ `Expression（表达式）` ≠ `Simulation Settings（设置）` ≠ `Alpha`。
2. **8:2 查资料优先级 + 可复用自动化规则 + 批次台账复盘**：
   - **严格 8:2 资料优先级**：遇到提效/降 PC/排雷问题，**80% 优先查阅「王哥 skill（`worldquant-brain-cyber-game-king`）+ Top100 黄金顾问（`wq-top-advisors-skill`）+ 管理员原创发帖」**；**仅当前三者无法解决时，才用 20% 查阅普通论坛资料**；
   - **可复用经验与动态微调真源**：筛选/提效/模板规则固化在 [REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md](docs/整理与研究/records/rules/REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md) 与 [reusable_experience_rules.json](wq_research_v2/config/reusable_experience_rules.json)；除 RA 硬门槛外，小范围参数（`decay`/`truncation`/窗口/中性化/剪枝）可多轮微调，且**数据集优先、持续试新集**；
   - **每批必记漏斗与好坏复盘**：通过 `wq_research_v2/batch_audit_logger.py` 自动记录每批（地区/字段/模板/一二三阶段过关数）与过好/过差/超时批次根因至 [batch_audit_ledger.md](docs/整理与研究/records/experiments/batch_audit_ledger.md) 及 [sc_pass_pc_rescue_queue.json](docs/整理与研究/records/experiments/sc_pass_pc_rescue_queue.json)；
   - 每个地区独立建档优化（[docs/整理与研究/regions/](docs/整理与研究/regions/README.md)），优先专注 1–2 个高 Base 方向，每 2 小时复查止损换向；全量落盘 SQLite 不丢弃好结果。
3. **RA 与 PPA 彻底分离 + 平台 PPA-First 四大陷阱**（四阶段流程：[d1_4stage_pipeline.json](docs/整理与研究/workflow/d1_4stage_pipeline.json) · [网页版](docs/整理与研究/workflow/d1_4stage_pipeline.html)）：
   - 先跑通简单的 RA 四阶段主线，不与 PPA 混用；
   - 满足 PPA 结构（≤8 唯一算子［`ts_backfill`/`group_backfill` 豁免］、≤3 唯一字段［分组字段豁免］）时系统默认**先跑 PPA 检查**；若因 **PPA 自相关 ≥ 0.50**（且 Sharpe 未高出 +10%）失败回退 RA 也失败，UI 常报错 **`Prod Correlation FAIL`**，实为假象；
   - 移除 `PowerPoolSelected` 标签不会退出 PPA 自相关池；
   - Pure PPA 强制要求英文描述 `≥100` 字符、匹配当期 Power Pool Theme（国家级 RA 主题无效；部分 `PPA+ATOM` 在非主题区也会被拦）、满 3 月限 `≤1/天、≤10/月`；同时过 RA 则自动 Hybrid，通常不占 Pure PPA 配额。
4. **API 目录、Chrome MCP 与相关性假阳性红线**：
   - 全量离线 API（123 接口）与算子（167 个）真源：[WQAPI_HUALABTECH_REFERENCE.md](docs/official_guides/WQAPI_HUALABTECH_REFERENCE.md)；
   - 涉及 `AQP202611`、`SPC` 等平台操作可直接用 `chrome-devtools` MCP 抓包并代码化执行（`AQP202611` 实证 `submissions=false`，加标签即参赛；`GET /users/self/activities/simulations` 查每日真实回测数）；
   - **`cnhkmcp:check_correlation` 空体假通过陷阱**：遇 `HTTP 200` 空体误返 `all_passed: true`，严禁轻信，统一用 `wq_research_v2/pc_poller.py`（标 `PENDING_PC_COMPUTING`）；
   - 本地 SC 统一用全量同步的 `data/sc_cache_v2/os_pnl_cache.db` 并做 `N×N` 池内两两正交剪枝（`<0.68`）。
5. **实证失败教训（[guangzhou_history_postmortem.md](docs/整理与研究/records/experiments/guangzhou_history_postmortem.md) & [t0_calibration_report.md](docs/整理与研究/records/rules/t0_calibration_report.md)）**：
   - 严禁无上限爬山、`ts_decay_linear(..., >252)` 与 `ts_target_tvr_decay(..., lambda_max > 1)`；
   - 生产直跑 `FULL`（`QUICK` 仅快 8% 且丢 `rn_sharpe`）；
   - 阶段 3 必先修 **`LOW_2Y_SHARPE ≥ 1.58`**（历史占 49% 失败），首选实证冠军分组算子 `group_zscore`/`group_rank`/`group_neutralize(..., subindustry)` 与前置平滑（`ts_mean 22`/`ts_decay_linear 10`）；
   - **`CHN/TOP2000U` 融券双负假象**：因 A 股高融券成本（~4–6%/年），零信号在 `+x` 与 `reverse(x)` 上可同时打出 `-1.5 ~ -2.5` Sharpe（如 `other496` 实测 `+x=-2.26` 且 `-x=-1.95`）！严禁单看负 Sharpe 误判翻转，早停与筛选须以**正向 Sharpe**及正反对称差为准；
   - `Alphas=0` 免每日额度窗口于 **`2026-12-06`** 冻结截止；`2Y Test (testPeriod='P2Y0M0D')` 与全局 `maxTrade='ON'` 暂不开启（定于 **`2026-12-10`** 两周后尝试）；凭据加载须以 `Password/config.yaml` 优先于环境变量。

## 3. 跨 AI 工具续接与「主 Agent + 子 Agent」控制变量闭环 (`wq-d1-closed-loop`)

- **防上下文爆炸启动协议**：切换任何 AI 工具（Claude Code / Cursor / Codex / Antigravity）或执行 `/compact` 后，**只读 3 个轻量真源（`< 8 KB`）**：本文件 + [CORE_STATE.json](docs/agents/CORE_STATE.json) + [OPTIMIZATION_LEDGER.json](docs/agents/OPTIMIZATION_LEDGER.json)（详细切换与启动口令见 [HANDOFF_GUIDE.md](docs/agents/HANDOFF_GUIDE.md)，跨工具技能见 [.agents/skills/wq-d1-closed-loop/SKILL.md](.agents/skills/wq-d1-closed-loop/SKILL.md)）。
- **基础版/通用版冻结真源**：当前已跑通 `4,893 FULL/天` 的稳定流水线已完整冻结于 [d1_ra_baseline_v1_frozen.json](docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json) 与 [D1_RA_BASELINE_V1_MANUAL.md](docs/整理与研究/workflow/D1_RA_BASELINE_V1_MANUAL.md)；任何流程修改若劣化可一键回退。
- **任务时长与中途检查**：常规任务按预计工作量和运行强度设计为 **3–24 小时**。预计超过 **6 小时**的任务，启动后最迟 **4 小时**做第一次轻量检查，此后相邻两次检查最多间隔 **4 小时**。优先用现有巡检，只读核对是否按计划运行、已完成数和满足本轮条件数（待判定单列）。具体口径见 [闭环技能](.agents/skills/wq-d1-closed-loop/SKILL.md)。
- **主从闭环与阶段纪律**：
  1. **种子筛选固化**：严格执行华子哥 WDS 四差距 + 顾问课堂 53 课规则（[worldquant-classroom-reference](docs/顾问课堂视频总结/worldquant-classroom-reference/SKILL.md) / `field_screener.py`：选新集/`Alphas=0`、明确经济假设、`cov>=0.75`、`dateCov>=0.60`、必要时 6 步探查字段真实更新频率）。
  2. **Stage 1–2 标准化快筛**：默认固定 `decay=0`、`neutralization=SUBINDUSTRY`，支持开启 `FAST/QUICK` 模式（`simulationMode="QUICK", testPeriod="P0Y0M"`）初筛与 `seed_pruner.py`（`jaccard=0.78`）剪枝。
  3. **Stage 3–4 强制 `FULL` + 控制变量法**：Stage 3 严禁 `FAST/QUICK`；子 Agent 每轮只改 1–2 个参数（如 `decay ∈ {0, 5, 20}` 轮询），嵌套 `>=5` 层标 `OVER_NESTED_TEMP_PC_FIX`（严禁 `tail(..., newval=0)` 外套 `hump`）；下轮必先验真并将 **`[有效] xxx 情况有效`** / **`[无效] yyy 情况无效`** 写入 [OPTIMIZATION_LEDGER.json](docs/agents/OPTIMIZATION_LEDGER.json)。

## Agent skills

### Issue tracker

Local markdown: specs and tickets live under `.scratch/<feature>/` (tracked by git). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), used only for tickets, never for Alpha tags. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.
