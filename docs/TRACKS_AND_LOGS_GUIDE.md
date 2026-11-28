# WorldQuant BRAIN 四条路线正式命名与日志一一对应手册

> **最后更新**：`2026-11-28 08:50 CST`  
> **用途**：固化本工作区四条独立研究路线的**正式中文/英文名称**、使用场景、全局通用纪律（**高换手必降/低换手跳过**、**先跑满 4,500 常规额度再切豁免字段**、**放宽 PC 多优化一轮**、**指标全过线自动 PATCH 打标并提示**）以及**一一对应的日志与台账路径**，方便随时查阅、复盘与回退。

---

## 一、四条正式路线总览与日志一一对应表

| 路线编号与正式名称 | 英文 / 日志标识 (`track_id`) | 核心定位与使用场景 | 配置与流程真源 | **一一对应台账与日志（绝不混写）** | 平台标签区分 |
| --- | --- | --- | --- | --- | --- |
| **路线 ①：基础优化路径** | `baseline_v1`<br>(`Baseline v1.0`) | **冻结回退基准**：`EUR / USA` 双区 + 单一 `v4` 模板 + `FULL` 流水线（已实证 `4,893 FULL/天`）。当新策略效果劣化时随时一键回退。 | [d1_ra_baseline_v1_frozen.json](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json)<br>[D1_RA_BASELINE_V1_MANUAL.md](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/workflow/D1_RA_BASELINE_V1_MANUAL.md) | • 冻结基线节点：`git commit 50939d68`<br>• 日志前缀：`[TRACK:baseline_v1]` | `Useful` / `SC_PASS` |
| **路线 ②：多域星阵路径** | `multi_region_matrix_v2`<br>(`Multi-Region Matrix v2.0`) | **当前广州主线**：严控高覆盖种子 × **5 地区轮巡**（`EUR / USA / GLB / ASI / KOR`）× **3 套差异化模板族配对** × **先跑满 4,500 常规额度再切 `Alphas=0` 豁免字段（不混跑，略超无妨）** × 每 **3–4 小时**定时复查。 | [goal/run_config.json](file:///c:/Wq/WorldQuant%20Brain/goal/run_config.json)<br>[docs/agents/CORE_STATE.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/CORE_STATE.json)<br>[wq-d1-closed-loop/SKILL.md](file:///c:/Wq/WorldQuant%20Brain/.agents/skills/wq-d1-closed-loop/SKILL.md) | • 实时 SQLite：`data/wq_v2_ledger.db`（广州 `/root/worldquont/data/wq_v2_ledger.db`）<br>• 运行日志：`/root/worldquont/data/deu_ra_runner.log`（前缀 `[TRACK:multi_region_matrix_v2]`）<br>• 批次复盘总账：[batch_audit_ledger.md](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/records/experiments/batch_audit_ledger.md)<br>• 有效/无效归因：[OPTIMIZATION_LEDGER.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/OPTIMIZATION_LEDGER.json)<br>• 降 PC 队列：[sc_pass_pc_rescue_queue.json](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/records/experiments/sc_pass_pc_rescue_queue.json) | `Useful` / `SC_PASS` + 别名 `SC 0.xxx PC 0.xxx` |
| **路线 ③：亚太孤岛实验线** | `asi_isolated`<br>(`ASI Isolated Track`) | **完全硬隔离专题线**：基于官方置顶帖 `45233242695703`（`ASI/D1 Power Pool Workshop 03`），按需人工单启；**不接入主调度器**。注：平台实测 ASI 无 `Delay=0`，仅 `ASI-D1` 可用，`ASI-D0` 双重锁定。 | [asi_isolated_config.json](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_isolated_config.json)<br>[ASI_D0_D1_WORKFLOW.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/ASI_D0_D1_WORKFLOW.md)<br>[POST_45233242695703_ANALYSIS.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/POST_45233242695703_ANALYSIS.md) | • 独立 SQLite：`data/asi_isolated_ledger.db`（严禁写主线库）<br>• 独立实验日志：[asi_experiment_log.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_experiment_log.md)（前缀 `[TRACK:asi_isolated]`） | `ASI_EXP_D1` / `PPA_Useful` / `ASI_EXP_D0` |
| **路线 ④：锻造闭环路径** | `alphaforge_agy_dsh_v4`<br>(`AlphaForge v4.0`) | **基于基础路线增强的 Codex CLI + DSH 闭环线**：落地 [ALPHAFORGE_WORKFLOW_REVIEW_20261128.md](file:///c:/Wq/WorldQuant%20Brain/doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md)（P0 入口硬门禁与美东日漏斗 + P1 失败传回原方向/2 批换向预算/PPA-First 归因 + P2 三主一备人工复核清单）；**Codex CLI 主控 + DSH (`dsh_crew` MCP) 子代理**，内置 `ExperienceReuser` 自动复用四层历史经验。 | [alphaforge_v4_config.json](file:///c:/Wq/WorldQuant%20Brain/docs/alphaforge_v4/alphaforge_v4_config.json)<br>[ALPHAFORGE_V4_WORKFLOW.md](file:///c:/Wq/WorldQuant%20Brain/docs/alphaforge_v4/ALPHAFORGE_V4_WORKFLOW.md)<br>[launch_alphaforge_v4.py](file:///c:/Wq/WorldQuant%20Brain/scripts/ops/launch_alphaforge_v4.py) | • 独立 SQLite：`data/alphaforge_v4_ledger.db`（只读复用 `data/wq_v2_ledger.db` 与 `data/sc_cache_v2/os_pnl_cache.db`）<br>• 专属运行日志：[alphaforge_v4_log.md](file:///c:/Wq/WorldQuant%20Brain/docs/alphaforge_v4/alphaforge_v4_log.md)（前缀 `[TRACK:alphaforge_agy_dsh_v4]`）<br>• 共享经验归因写回：[OPTIMIZATION_LEDGER.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/OPTIMIZATION_LEDGER.json) | `Useful` / `SC_PASS` + 别名 `SC 0.xxx PC 0.xxx`（三主一备人工复核，永不自动 `/submit`） |

---

## 二、全路线共用三大核心操作规则（2026-11-26 更新）

### 1. 通用降换手规则（所有流程必做，低换手跳过）

代码固化于 `wq_research_v2.ra_evaluator.evaluate_turnover_action()`，综合「王哥 Skill + 黄金顾问团 + BRAIN AlphaTest（`Fitness = Sharpe × sqrt(|Returns| / max(Turnover, 0.125))`）」与 Decision #3 红线：

| 换手率区间 (`Turnover`) | 判定动作 | 具体操作要求 |
| --- | --- | --- |
| **`TO < 8%` (`< 0.08`)** | **`SKIP_LOW_TURNOVER`（跳过！）** | **严禁再做降换手操作**（不套 `hump` / `ts_target_tvr_decay` / 拉大 `decay`），避免稀释 Sharpe 或触发 `LOW_TURNOVER (< 1%)` 失败。 |
| **`8% ≤ TO ≤ 18%`** | **`KEEP_NORMAL`（保持）** | 健康区间，不强制降换手；仅当 `Fitness < 1.0` 且 `TO > 12.5%` 时可单轴轻测 `decay ∈ {2, 4, 5}`。 |
| **`TO > 18%` (`> 0.18`)** | **`REDUCE_HIGH_TURNOVER`（必降换手）** | 按单变量控制法依次尝试：① **参数平滑** `decay ∈ {0, 5, 20}`（王哥防断崖检验）；② **前置/融合后平滑** `ts_decay_linear(..., 10/22)` 或 `ts_mean(..., 5/10/22)`；③ **软调仓约束** `ts_target_tvr_decay(..., lambda_min=0, lambda_max=0.9, target_tvr=0.08..0.15)`（严禁 `lambda_max > 1`）；④ **温和防抖** `hump(..., hump=0.01)`（**红线：外层已含 `tail(..., newval=0)` 时严禁套 `hump`，ASI `MINVOL1M` 亦慎用 `hump`**）。**永久禁用 `trade_when`**。 |

### 2. 严格先后次序：先跑满 `4,500` 常规额度，再考虑 `Alphas=0` 豁免字段（不混跑）

代码固化于 `wq_research_v2.daemon_ra_runner.resolve_quota_queue_policy()` 与双队列分离调度（`normal_specs` 与 `alpha0_specs` 独立游标）：
- **阶段一（当日 `NORMAL` 已完成 `< 4,500`）**：锁定 **`NORMAL_ONLY`**，仅执行常规字段与 Stage-3 精修队列，**不同步混跑 `UNUSED_ALPHA0`**（在途批次结束时略微超过 `4,500` 无妨）；
- **阶段二（当日 `NORMAL` 已完成 `≥ 4,500`）**：常规额度任务完成后，自动切入 **`ALPHA0_EXEMPT_ONLY`**，开始运行 `UNUSED_ALPHA0`（`Alphas=0` 免额字段，免费期至 `2026-12-06`），直至免额队列跑完或 `API remaining ≤ 80` 安全休眠。

### 3. 适度放宽 PC 分布表准入，多给 1 轮专项优化机会

代码固化于 `wq_research_v2.pc_poller.parse_pc_histogram_records()`：
- 主力 **`Useful`** 交付门槛仍保持 **`PC < 0.70`**（严控低相关性交付质量）；
- **放宽进入专项降 PC 的门槛（多优化 1 轮）**：
  - `pc_max` 上限：`0.75 → 0.78`；
  - `≥ 0.70` 碰撞生产因子总数：`≤ 5 → ≤ 10`；
  - `≥ 0.80` 桶碰撞数：`0 → ≤ 2`；
  - 专项降 PC 最多轮次：**`2 轮 → 3 轮`**（比之前多优化 1 轮）；超过 3 轮无改善或明显拥挤（`pc_max > 0.78` 或 `≥ 0.70` 碰撞 `> 10`）再归档 `PC_STUCK_DORMANT` 休眠。

### 4. 地区并发线程上限红线（代码与文档双重强制）

代码固化于 `wq_research_v2.sim_runner.WeightedSlotSemaphore`（`MAX_THREADS_GLB = 3`、`MAX_THREADS_OTHER_REGION = 4`）及 `daemon_ra_runner.parse_region_caps()`：
- **`GLB` 地区**：最多 **`3` 个并发线程**（即使命令行传入更大值也会被自动截断至 `3`）；
- **其他所有地区**（`USA / EUR / ASI / KOR / DEU / HKG / GBR / CHN / IND / AMR`）：最多 **`4` 个并发线程**（即使命令行传入更大值也会被自动截断至 `4`）。

### 5. 全指标过线自动 `PATCH` 标签/别名规则（无需事前询问，事后提示）

- 只要候选因子通过全部参数与硬检门槛（RA `0 FAIL` + `SC < 0.65` + 池内正交 + `PC < 0.70` 打 **`Useful`**；同簇出现更高 `Margin` 冠军则自动升级替换并将旧版降为 **`SC_PASS`**；仅 PC 未过者打 **`SC_PASS`**，统一写别名 `SC 0.xxx PC 0.xxx`），**直接自动执行 `PATCH /alphas/{id}` 修改标签与别名，随后在汇报中向用户提示已修改内容即可，无需再事前询问确认**；
- **红线不变**：任何情况下**严禁自动调用 `POST /alphas/{id}/submit`**（最终提交仍完全由用户本人操作）。

---

## 三、如何快速切换或调用某条路线

- **继续「多域星阵路径」**：在启动口令里明确指定路线 ②。广州现有守护仍按已有部署运行。
- **回退「基础优化路径」**：按 [D1_RA_BASELINE_V1_MANUAL.md](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/workflow/D1_RA_BASELINE_V1_MANUAL.md) 恢复广州启动命令至 `EUR,USA` 冻结版参数。
- **人工单启「亚太孤岛实验线」**：在对话中明确指示“按「亚太孤岛实验线」独立配置启动 `ASI-D1` 探索（落盘 `data/asi_isolated_ledger.db` 并记录至 `asi_experiment_log.md`）”。
- **启动默认路线 ④「锻造闭环路径」**。入口、验收命令和日志位置见 [START_HERE.md](../goal/START_HERE.md)。
