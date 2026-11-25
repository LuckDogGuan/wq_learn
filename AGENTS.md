# WorldQuant BRAIN Workspace — AGENTS.md

仅记录不可逾越的红线、实证避坑点与关键真源路径（目录说明见 [README.md](README.md)）。

## 1. 硬红线（严禁违反）

1. **严格 D1-Only**：全链路锁定 `settings.delay == 1`，严禁任何 `Delay = 0 (D0)` 回测。
2. **Decision #3 算子永久禁令**：永久禁止 `add (+)`、`multiply (*)`、`trade_when`；双分支融合统一用 `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))`。
3. **绝不自动提交**：永不调用 `POST /alphas/{id}/submit`。合格候选只打标签（RA 线打 **`Useful`**，独立 PPA 线打 **`PPA_Useful`**），由用户在网页端手工提交；`PATCH /alphas/{id}` 须显式确认或 `--confirm-apply`。
4. **硬保护只读资产**：严禁删除/改写 `legacy_core/Core/runtime_data/`（1,532 文件）、`reference/`（静态参考库）；严禁读取/打印/提交 `Password/config.yaml`。
5. **只对账一次、绝不盲重发**：遇 `429 / 5xx / 超时 / 缺子 ID` 仅存指纹标 `PENDING_RECONCILE`，冷却后只读对账 1 次，仍未观测落 `RESULTS_UNOBSERVED`。
6. **无 GUI & 广州低内存（1.9 GiB RAM）**：不建本地 Web GUI；后台任务必配 SQLite WAL Checkpoint、10m 认证刷新、10s 重连、流式低内存扫描与 `MemoryMax=512M`；新模块必配 `tests/` 单测与 AST 校验。

## 2. 核心研究与平台避坑要点（防止再次错过）

1. **7 层概念严禁混为一谈**（官方术语表：[BRAIN_OFFICIAL_GLOSSARY.md](docs/official_guides/BRAIN_OFFICIAL_GLOSSARY.md)）：
   `Dataset（数据集）` ≠ `Data Field（数据字段）` ≠ `Operator（算子，永不拉黑）` ≠ `Template（模板）` ≠ `Expression（表达式）` ≠ `Simulation Settings（设置）` ≠ `Alpha`。
2. **分地区独立研究 + 绝不丢弃好结果 + 漏斗筛选**：
   - 每个地区必须独立建档、独立对比、结合各自平台门槛与股市特征持续优化（[docs/整理与研究/regions/](docs/整理与研究/regions/README.md)），优先多跑高 Base / 高倍率 D1 地区，方向不对须每 30 分钟复查并及时止损换向；
   - 全量回测结果均落盘 SQLite，通过分层池（`POOL_S / POOL_A / POOL_B / POOL_FLIP / POOL_DROP`）过滤低 Sharpe 噪声自然抬高候选池质量。
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
   - `Alphas=0` 免每日额度窗口于 **`2026-12-06`** 冻结截止；凭据加载须以 `Password/config.yaml` 优先于环境变量。
