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

## 2026-11-28 17:28 CST · 知识层补充：本地知识库 MCP 帖子逐点验证

- `[TRACK:alphaforge_agy_dsh_v4]` 按用户要求用 cnhkmcp 读取论坛帖 44557921849623《进一步增强你的AI检索论坛能力——本地知识库MCP构建（附部分代码）》：brain_client Basic 认证成功（has_jwt=true），Playwright/Chromium + /hc/zh-cn/signin SSO 后抓取正文 9007 字、2 评论、4 图，落盘 doc/forum_post_44557921849623.md/.json。Zendesk 社区 API 直读返回 401（受限社区），故走 cnhkmcp Playwright 兜底（符合 AGENTS 2.4「API 优先、浏览器兜底」）。
- 逐点验证与可直接采纳要点见 doc/本地知识库MCP_路线4_补充分析_20261128.md；WORKFLOW 新增「五、知识层增强」：可直接采纳「极致懒加载 / 代码保护切块+全文反查 / 动态采样 / 双表隔离 / API 优先」，LanceDB+BGE 向量层与 LLM QA 标 P2 待实测。本轮 0 回测、0 打标、0 提交。

## 2026-11-28 17:52 CST · 知识层 P2 落地：LLM 原子化 + 向量库

- `[TRACK:alphaforge_agy_dsh_v4]` 按用户要求落地两个 P2 项：① **LLM 原子化**——旧 `gemini` npm CLI 已弃用（IneligibleTierError），改用 Antigravity CLI `agy.exe`（1.5.19）的 `gemini-3.8-flash-medium`；脚本 `scripts/forum_kb/atomize.py` 把帖子 44557921849623 原子化为 8 对 QA（`data/forum_kb/qa/44557921849623.qa.md`）。② **向量库**——已装 `lancedb 0.41.0` + `sentence-transformers 6.3.0` + `torch 2.12.0+cpu`；`BAAI/bge-small-zh-v1.5`（512 维，CPU 0.1s/篇）嵌入 + LanceDB `wqb_forum_experiences` 表（含 FTS 倒排索引）+ 混合检索 `search(query_type="hybrid").text(q).vector(qv)` 验证通过（`scripts/forum_kb/build_index.py`）。本轮 0 回测、0 打标、0 提交。

## 2026-11-28 19:40 CST · 知识层 P2 收口 3/3：Top100 全量原子化 + 官方双表 + FastMCP 双工具

- `[TRACK:alphaforge_agy_dsh_v4]` 按用户要求继续 P2 剩余 1/3 并推 GitHub：① **批量原子化**——新增 `ingest_forum.py`（并发 6、断点续跑、失败重试），`reference/forum/top100_2026Q4` 全量 264 篇 + 原帖 1 篇 = **265 篇 QA**；首轮 15 篇因 Windows 命令行 32K 上限报 `WinError 206`，改为长帖按段落切段再合并（`MAX_INPUT_CHARS=18_000`）后全部补齐。② **官方层入库**——新增 `ingest_official.py`（代码保护切块；管理员帖限 10 块/篇、跳过 >300KB 合辑），`wqb_official_guides` **1,928 块**（官方准则 92 + 管理员帖 1,836）。③ **MCP 服务**——新增 `server.py`（FastMCP stdio）：`search_wqb_official_guidelines`（先官方准则后管理员帖、注入当日日期）、`search_wqb_forum_experience`（候选池 30 → 前 7 核心 + 随机采样 → 按帖子 ID 回读 `reference/forum` 原文），`verify_mcp.py` 端到端通过（握手 + 两工具命中 + 7 篇全文反查）。
- 三个实测坑已写进 `scripts/forum_kb/README.md`：LanceDB 0.41 `table_names()→list_tables()` / `create_fts_index→create_index(FTS)`；默认 simple 分词器中文 BM25 零命中 → `FTS(base_tokenizer="ngram", 2~3)`；**Windows 进入 anyio 事件循环后再 import numpy/scipy/torch 永久卡死扩展 DLL 加载** → Windows 在事件循环前预导入重库（≈13s 冷启动），Linux/macOS `WQB_KB_PRELOAD=0` 纯懒加载。
- 单测 `scripts/forum_kb/tests` **15 passed**（切块/QA 校验/长帖切段合并/批量计划/MCP 装配/AST 懒加载红线），`wq_research_v2/tests` 77 passed 无回归。本轮 0 回测、0 打标、0 提交；LanceDB 与 QA 产物在 `data/`（gitignore），入库仅代码与文档。

