# WorldQuant BRAIN Workspace — AGENTS.md

本文件定义 `C:\Wq\WorldQuant Brain` 统一仓库的全局开发、研究、API 与安全边界。所有 Agent 与开发者必须严格遵守，严禁遗漏关键实证知识点。

## 1. 不可逾越的安全与业务红线

1. **D1-Only 硬锁**：当前阶段所有研究、筛选、模板与回测严格锁定 **`Delay = 1 (D1)`**，严禁发起任何 `Delay = 0 (D0)` 回测。
2. **Decision #3 算子永久禁令**：永久禁止使用 **`add` (`+`)、`multiply` (`*`)、`trade_when`**。双分支信号组合统一使用表达式级 **`min(rank(expr_A), rank(expr_B))`** / **`reverse(min(rank(expr_A), rank(expr_B)))`**（必要时 `max(...)`）。
3. **绝不自动正式提交**：严禁任何脚本或 Agent 调用 `/alphas/{id}/submit`（`Formal Alpha Submission`）。合格候选通过无 GUI 轻量标签工作流打上 **`Useful`**（RA 线）或 **`PPA_Useful`**（独立 PPA 线），由用户亲自在 BRAIN 平台筛选并手工提交。`PATCH /alphas/{id}`（含 `set_alpha_properties`）须经用户当次显式确认或 `--confirm-apply`。
4. **硬保护资产与只读目录**：
   - `legacy_core/Core/runtime_data/`（1,532 文件）：**永远不能删除，只能读取**。
   - `reference/`（2026Q4 榜单、254 篇管理员原创帖、264 篇前百精选帖与审计清单）：**静态参考库，严禁覆盖修改**。
   - `Password/config.yaml`：唯一平台凭据，严格 `.gitignore`，**严禁读取打印进对话、入日志或提交 Git**。
5. **只对账一次、绝不盲重发**：遇 `429 / 5xx / 超时 / 缺子 ID` 仅持久化指纹标 `PENDING_RECONCILE`，冷却后只读对账 1 次，仍未观测落 `RESULTS_UNOBSERVED`，严禁盲重发 POST。
6. **无 GUI & 低内存运维纪律（`experience_profile.md` + 广州 1.9 GiB 约束）**：
   - `wq_research_v2` **不建本地 Web 看板/GUI**，统一用 **`Useful`** 标签交付；
   - 后台任务必有 SQLite WAL Checkpoint、10m 认证刷新与 10s 断线重连；扫描必须前置下推 API 过滤条件、流式逐页处理、**绝不扫描多余历史或驻留全量大对象在 RAM**；
   - 新模块必须配 `tests/` 离线单测并过 AST 静态导入校验；每次逻辑变更同步更新 `README.md` 与 `doc/`。

---

## 2. 关键平台规则与实证避坑知识库（严禁下次遗漏！）

### 2.0 严格概念分层与分地区独立作战（严禁混为一谈！）
- **官方术语表本地真源**：[BRAIN_OFFICIAL_GLOSSARY.md](docs/official_guides/BRAIN_OFFICIAL_GLOSSARY.md)（完整保存官方 Support Article `4902349883927`）。
- **7 层概念绝不混用**：**`Dataset（数据集）` ≠ `Data Field（数据字段）` ≠ `Operator（算子，永不拉黑）` ≠ `Template（抽象模板）` ≠ `Expression（填好字段的表达式）` ≠ `Simulation Settings（模拟设置）` ≠ `Alpha（带 ID 与实测结果的实体）`**。
- **按地区与市场微观结构独立分文件记录与优化**：所有地区规则、股市特征、实验对比与失败复盘必须独立存放在 [docs/整理与研究/regions/](docs/整理与研究/regions/README.md)（当前首战唯一聚焦 **[DEU_TOP500_D1.md](docs/整理与研究/regions/DEU_TOP500_D1.md)**，严禁跨地区混池对比或盲目同时铺开 5 个地区）。
- **绝不丢弃好结果 + 漏斗筛选思维**：每条回测结果必须完整落盘 SQLite，通过分层池（`POOL_S / POOL_A / POOL_B / POOL_FLIP / POOL_DROP`）过滤低夏普噪声自然拉升候选池整体质量，而非强行复杂化垃圾种子或误丢中间好因子。

### 2.1 RA 与 PPA 彻底分离与平台“PPA-First”提交检查真相
- **研究分离铁律**：**RA 常规因子**与 **PPA 主题池因子**必须完全分开建流程、分开打标签（`Useful` vs `PPA_Useful`），先跑通简单的 RA 四阶段主线，切忌混为一谈。
- **结构化四阶段流程唯一真源**：机读 JSON 位于 [d1_4stage_pipeline.json](docs/整理与研究/workflow/d1_4stage_pipeline.json)，可视化网页版位于 [d1_4stage_pipeline.html](docs/整理与研究/workflow/d1_4stage_pipeline.html)。
- **PPA-First 路由优先级与四大必知陷阱**：
  1. 只要表达式满足 PPA 结构条件（**唯一算子 ≤ 8**［`ts_backfill`/`group_backfill` 豁免］、**唯一数据字段 ≤ 3**［分组字段 `country/industry/subindustry/sector/market/currency/exchange` 豁免］、TO 1%–70%、Sharpe ≥ 1 潜力），点击检查时系统**默认先跑 PPA 检查**（与 Alpha 命名无关）。
  2. **假 `Prod Correlation FAIL` 陷阱**：若 PPA 检查失败（最常见：**PPA 池自相关 ≥ 0.50** 且 Sharpe 未高出最高相关 PPA `+10%`），系统会回退跑完整 RA 检查；若 RA 也失败，界面可能报错 `Prod Correlation FAIL`，根因实为 PPA 自相关！
  3. **`PowerPoolSelected` 池永久性**：提交后哪怕移除 `PowerPoolSelected` 标签，该 Alpha **仍保留在 PPA 自相关计算池内**。
  4. **Pure PPA 硬门槛与配额**：Pure PPA 免检 Prod Correlation / 非 PPA Self-Corr / Fitness / IS Ladder，但**强制要求英文描述 ≥ 100 字符（Idea + Rationale）**、必须匹配**当期活跃 Power Pool Theme**（国家级 RA 主题不能解锁 Pure PPA；非主题区部分 `PPA+ATOM` 也会被按 Pure PPA 拦截）、满 3 个月后每榜单限 `≤ 1/天、≤ 10/月`；若同时通过完整 RA 标准则自动按 **Hybrid (PPA+RA)** 提交，通常**不占 Pure PPA 配额**。

### 2.2 API 目录、Chrome DevTools MCP 抓包与相关性假阳性红线
- **离线全量 API 与算子目录**：已从 `https://wqapi.hualabtech.com/#api/` 完整归档 **123 个 API 操作**与 **167 个算子参考**至 [WQAPI_HUALABTECH_REFERENCE.md](docs/official_guides/WQAPI_HUALABTECH_REFERENCE.md) 及机读 JSON（`docs/official_guides/wqapi_hualabtech/api-catalog.json`、`operator-reference.json`）。
- **竞赛 / AQP / SPC 自动化授权**：涉及 `AQP202611`、`SPC` 等平台页面或未公开接口时，可直接通过 `chrome-devtools` MCP 抓取真实网络请求并用代码直接操作（如 `AQP202611` 已实证 `submissions=false`，官方参与方式即 `PATCH /alphas/{id}` 加 `AQP202611` 标签 + 英文描述；`GET /users/self/activities/simulations` 可直查每日真实回测次数）。
- **`cnhkmcp:check_correlation` 空体假通过陷阱**：当 BRAIN `/correlations/prod` 返回 `HTTP 200` + `Retry-After` + **空响应体**（后端异步排队）时，`cnhkmcp:check_correlation` 会误返回 `{"checks": {}, "all_passed": true}`！**严禁将其当通过**；必须统一使用 `wq_research_v2/pc_poller.py`（严格标 `PENDING_PC_COMPUTING`）。
- **本地 SC 必须全量同步且做 `N×N` 池内去重**：旧 `sc_engine.py` 缓存停在 2026-09-09（89/92），曾漏判 3 条与新 OS `1YWNm9eM` 高相关（0.81–0.93）的过期 `Useful`；必须使用 `wq_research_v2/sc_local.py` 的可移植 SQLite 缓存 `data/sc_cache_v2/os_pnl_cache.db` 并执行 `N×N` 两两矩阵剪枝（`< 0.68`）。

### 2.3 广州服务器 (`ssh guangzhou`) 历史实证教训与运行纪律
- **硬件规格**：2 vCPU / **1.9 GiB RAM** (+ 8 GiB Swap) / 50 GB 磁盘，Conda 环境 `Python 3.13.12`（`/root/miniconda3/bin/python`）。
- **历史五大致命低效（详见 [guangzhou_history_postmortem.md](docs/整理与研究/records/experiments/guangzhou_history_postmortem.md)）**：
  1. 严禁无上限爬山导致 61.5% CPU 活锁（如 `1YWw2RRX`↔`88N0amKm`）与荒谬 `ts_decay_linear(..., 12000)` 窗口；
  2. 严禁 `ts_target_tvr_decay(..., lambda_max > 1)`（实证导致 `RESULTS_UNOBSERVED` 且反增换手）；
  3. 严禁盲扫 `USA/TOP1000` 情绪长衰减（均 Sh `1.30`）与 `GBR/UNKNOWN`（1,112 次 0 过关）；优先 `Alphas=0`（**2026-12-06 冻结截止**）与高倍率空白塔；
  4. 近 400 次失败中 **`LOW_2Y_SHARPE` 排第一（197 次）**，阶段 3 必须严格执行 **2Y ≥ 1.58 先行**；
  5. 阶段 2/3 首选实证 `CHAMPION` 分组算子（`group_zscore`/`group_rank`/`group_neutralize` by `subindustry`，实测 93%–100% 改善率）与简洁 1–4 算子表达。

---

## 3. 统一目录职责地图

| 顶层目录 | 定位 | Git 追踪 |
| --- | --- | :---: |
| `wq_research_v2/` | **唯一活跃开发引擎**（模块化 D1-Only 研究、筛选、回测、本地 SC/PC、消融与 `Useful` 标签器） | 是 |
| `data/` | `wq_research_v2/` 运行期 SQLite WAL 账本、便携 PnL 缓存、日志与导出 | 否（仅 `.gitkeep`） |
| `docs/整理与研究/` | 唯一战略总计划（`00`–`09`）、四阶段流程 JSON/HTML（`workflow/`）与节点记录（`records/`） | 是 |
| `docs/official_guides/` | 高确定性官方总结、SPC API、`wqapi.hualabtech.com` 全量 API/算子目录、课件与笔记 | 是 |
| `docs/memory/` | 高确定性实证复盘（黑名单登记表、USA D1 复盘、Master 指南、224/RA 审计） | 是 |
| `reference/` | **永久只读参考库**：`2026Q4` 前百榜单、254 管理员原创、264 前百精华与审计账本 | 是 |
| `config/standards/` | RA / PPA 本地标准与禁用字段 JSON | 是 |
| `legacy_core/` | 冻结只读历史 `Core/`（含硬保护 `runtime_data/`）与旧管线参考 | 代码是 / `runtime_data` 否 |
| `scripts/` | 精选可复用小工具（`corr_map`、`webdata_unexploited_analytics` 等）与运维脚本 | 是 |
| `tests/` | 38 个历史离线核心回归与单元测试 | 是 |
| `staging/` | **待实证验证暂存区**：模板、待验总结、MAB 实验与旧分析工具（验证有效晋升，无效删除） | 是 |
| `WebDataScope-1.0.6/` | 唯一离线字段快照源（35.22 MB `data/`，Stage-0 筛选入口） | 否 |
| `Password/` | 唯一有效平台凭据目录 | 否 |
