# WorldQuant BRAIN Workspace — AGENTS.md

本文件定义 `C:\Wq\WorldQuant Brain` 统一仓库的全局开发、研究与安全边界。所有 Agent 与开发者必须严格遵守。

## 1. 不可逾越的安全与业务红线

1. **D1-Only 硬锁**：当前阶段所有研究、筛选、模板与回测严格锁定 **`Delay = 1 (D1)`**，严禁发起任何 `Delay = 0 (D0)` 回测。
2. **Decision #3 算子永久禁令**：永久禁止使用 **`add` (`+`)、`multiply` (`*`)、`trade_when`**。双分支信号组合统一使用表达式级 **`min(rank(expr_A), rank(expr_B))`** / **`reverse(min(rank(expr_A), rank(expr_B)))`**（必要时 `max(...)`）。
3. **绝不自动正式提交**：严禁任何脚本或 Agent 调用 `/alphas/{id}/submit`（`Formal Alpha Submission`）。合格候选最多标为 `GATE4_CANDIDATE_FOR_MANUAL_REVIEW`，由用户亲自在 BRAIN 平台提交。`set_alpha_properties`（`Remote Rename Application`）必须经用户当次显式确认。
4. **硬保护资产与只读目录**：
   - `legacy_core/Core/runtime_data/`（1,532 文件）：**永远不能删除，只能读取**。
   - `reference/`（2026Q4 榜单、254 篇管理员原创帖、264 篇前百精选帖与审计清单）：**静态参考库，严禁覆盖修改**。
   - `Password/config.yaml`：唯一平台凭据，严格 `.gitignore`，严禁打印、入日志或提交 Git。
5. **只对账一次、绝不盲重发**：遇 `429 / 5xx / 超时 / 缺子 ID` 仅持久化指纹标 `PENDING_RECONCILE`，冷却后只读对账 1 次，仍未观测落 `RESULTS_UNOBSERVED`，严禁盲重发 POST。
6. **工程纪律（`experience_profile.md`）**：拒绝臃肿单体脚本；后台任务必有 SQLite Checkpoint、10m 认证刷新与 10s 断线重连；新模块必须配 `tests/` 离线单测并过 AST 静态导入校验；每次逻辑变更同步更新 `README.md` 与 `doc/`。

## 2. 统一目录职责地图

| 顶层目录 | 定位 | Git 追踪 |
| --- | --- | :---: |
| `wq_research_v2/` | **唯一活跃开发引擎**（模块化 D1-Only 研究、筛选、回测、本地 SC/PC 与消融归因） | 是 |
| `data/` | `wq_research_v2/` 运行期 SQLite WAL 账本、便携 PnL 缓存、日志与导出 | 否（仅 `.gitkeep`） |
| `docs/整理与研究/` | 唯一战略总计划（`00`–`09`）与节点记录（`records/`） | 是 |
| `docs/official_guides/` | 高确定性官方总结、官方链接、SPC API、课件与《Finding Alphas》笔记 | 是 |
| `docs/memory/` | 高确定性实证复盘（黑名单登记表、USA D1 复盘、Master 指南、224/RA 审计） | 是 |
| `reference/` | **永久只读参考库**：`2026Q4` 前百榜单、254 管理员原创、264 前百精华与审计账本 | 是 |
| `config/standards/` | RA / PPA 本地标准与禁用字段 JSON | 是 |
| `legacy_core/` | 冻结只读历史 `Core/`（含硬保护 `runtime_data/`）与旧管线参考 | 代码是 / `runtime_data` 否 |
| `scripts/` | 精选可复用小工具（`corr_map`、`webdata_unexploited_analytics` 等）与运维脚本 | 是 |
| `tests/` | 38 个历史离线核心回归与单元测试 | 是 |
| `staging/` | **待实证验证暂存区**：模板、待验总结、MAB 实验与旧分析工具（验证有效晋升，无效删除） | 是 |
| `WebDataScope-1.0.6/` | 唯一离线字段快照源（35.22 MB `data/`，Stage-0 筛选入口） | 否 |
| `Password/` | 唯一有效平台凭据目录 | 否 |
