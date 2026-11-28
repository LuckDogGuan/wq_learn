# 路线 ④：锻造闭环路径（AlphaForge AGY-DSH v4.0）专属运行日志

> **日志标识**：`[TRACK:alphaforge_agy_dsh_v4]`  
> **配套配置**：[alphaforge_v4_config.json](alphaforge_v4_config.json) · **标准 SOP**：[ALPHAFORGE_V4_WORKFLOW.md](ALPHAFORGE_V4_WORKFLOW.md)  
> **规则**：本日志仅记录路线 ④ 的启动回执、P0 预检/漏斗核对、DSH 子代理派单回执（job ID / provider / model / status / tokens）、失败反馈与换向判定、以及三主一备人工复核清单。全局可复用 `[有效]/[无效]` 经验同步写回 [OPTIMIZATION_LEDGER.json](../agents/OPTIMIZATION_LEDGER.json) 以供四条路线共享复用。

---

## 2026-11-28 · 路线 ④ 初始化建档

- `[TRACK:alphaforge_agy_dsh_v4]` **初始化完成**：基于路线 ① 冻结基线（`baseline_v1`）与 [doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md](../../doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md) 完成路线 ④ 建档与工程落地。
- **已落盘模块**：
  - 历史经验复用引擎：`wq_research_v2/src/wq_research_v2/experience_reuser.py`（接入 `OPTIMIZATION_LEDGER.json`、`reusable_experience_rules.json`、`sc_pass_pc_rescue_queue.json`、`worldquant-experience-reuse/references/rules.jsonl`）
  - 路线 ④ 核心门禁/漏斗/反馈/3+1 清单与编排：`wq_research_v2/src/wq_research_v2/alphaforge_v4.py`
  - 统一 CLI 子命令：`python -m wq_research_v2 forge {experience|preflight|funnel|ppa-check|dsh-brief|agy-cmd|roster}`
  - Antigravity CLI 启动器：`scripts/ops/launch_alphaforge_v4.py`（默认 dry-run，检测到 `agy.exe` 后可 `--execute`）
- **当前状态**：`READY_FOR_MANUAL_LAUNCH`（不干扰广州正在运行的路线 ② `multi_region_matrix_v2` 主守护进程）。

## 2026-11-28 16:52 CST · 默认路线与 Codex CLI 只读验收

- `[TRACK:alphaforge_agy_dsh_v4]` 路线 ④ 已设为仓库启动默认，主控切为 Codex CLI。启动器优先选桌面随附版本。PATH 上的 0.133.0 对默认模型和 `gpt-5.4-mini` 均报 `model_not_in_accessible_catalog`。
- [V] 桌面 CLI 0.171.0-alpha.13.2 使用 `gpt-6.2-sol` 读出默认路线及 EFF-29／INEFF-38，退出码 0，回执 `ALPHAFORGE_VERIFY_OK`。原始日志 `data/alphaforge_v4_runs/20261128T085100.561157Z.log`。
- [V][U] `--verify-dsh` 读到相同启动摘要，内层 `dsh_worker_config` 需要审批，当前策略 `never`，退出码 1。该次没有 probe 或 worker 回执。原始日志 `data/alphaforge_v4_runs/20261128T085206.725241Z.log`。
- [V] 外层 Codex 会话已完成 DSH 探测和独立任务。Job `hub-11-mx05snxj`，session `session-83f26c14-a6ff-4496-a3f0-c6f304d53ac8`，`dsh-opencode-go/deepseek-v4.1-flash`，`done`，输入 5754／输出 3318 tokens。仅复核既有案例；子代理实际读了 3 次，超出简报的 2 次上限。
- [V] Antigravity 默认与轻量模型均返回个人额度 HTTP 429。保留原始日志 `20261128T084103.254276Z.log` 与 `20261128T084354.698669Z.log`。
- [V][U] EFF-29/30 的 USA RAM 把 ≥0.70 PC 碰撞从 1,080 降至 1，但原始 2Y 0.77→0.55。INEFF-38/39 各 8 条 FULL 均无 RA 硬检通过，USA 4 条官方判定仍待定且已观察指标低于门槛。广州允许的只读尾日志显示估计进度 696/4500，实时额度值未观测。下一轮从现有 ASI 常规队列选择新种子，仅切 QUICK→FULL，核对 2Y、Fitness、JPN、Robust。r37 未观测指纹保留。本轮新回测、打标、提交均为 0。

## 2026-11-28 17:07 CST · Codex CLI 内部 DSH 验收

- [V] 原命令复现 `dsh_worker_config` 需要审批，而非交互 CLI 的全局审批策略为 `never`。同一 CLI 只给该工具加进程级授权后，返回 `mode=hub`、`hub_reachable=true`。原始日志 `20261128T090157.279455Z.log` 和 `dsh-approval-probe-20261128.jsonl`。
- [V] 三步工具授权后，首次派单 `hub-12-mx06pnyf` 虽返回 `done`，实际读取 0 次。该 worker 通过终端读取文件，简报禁止终端，验收退出 1。原始日志 `20261128T090440.765411Z.log`。
- [V] `python scripts/ops/launch_alphaforge_v4.py --verify-dsh` 退出 0。结构化事件依次记录绑定成功、`tool_call_verified=true` 和 Job `hub-13-mx06roht`（session `session-60dcdf89-0bd6-4cb8-864d-82fa60d3a1a8`），`dsh-opencode-go/deepseek-v4.1-flash`，`done`，输入 1386／输出 116 tokens。Worker 执行 1 次指定只读命令，回传 `alphaforge_agy_dsh_v4`。原始日志 `data/alphaforge_v4_runs/20261128T090616.194098Z.log`。
