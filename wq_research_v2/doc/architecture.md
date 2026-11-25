# `wq_research_v2` 架构说明与运行手册

## 1. 模块分层（13 个低耦合单责模块）

| 层级 | 模块 | 职责 |
| --- | --- | --- |
| 基础配置 | `config_loader.py` + `config/*.json` | 路径发现、D1 门槛、Gold 81 算子、42 缺陷模板与 5:5 模板声明式配置 |
| 高可用传输 | `auth_session.py`、`quota_tracker.py` | 10m 认证续签、10s 断线重连、`verify=True`、全量 `X-Ratelimit-*` 捕获、EST/EDT 自动日切与 429 熔断 |
| 源头筛选 | `wds_adapter.py`、`field_screener.py` | 复用 `legacy_core/Core/tools/webdata_quality` 与 `webdata_unexploited_analytics`，融合华子哥四大差距、管理员推荐、`JX79797`/`JX14975`/`KZ79256` 门控与 `GBR/DEU` Live 兜底 |
| 静态门禁 | `expr_validator.py` | 自研无副作用 FASTEXPR Lexer+AST 解析器，落地 10 条不可绕过 D1/Decision #3/Alphas=0 校验 |
| 并发回测与账本 | `sim_runner.py`、`ledger_store.py` | 加权 `SlotSemaphore`（GLB 占 2 槽）、2–10 Multi-Sim、原生 `QUICK/FULL`、SQLite WAL 8 表 Checkpoint、只对账一次绝不盲重发、Quick/Full 分账 |
| 相关性与预检 | `sc_local.py`、`pc_poller.py` | 便携式 `os_pnl_cache.db`（`zlib+float64`）、零假零本地 SC、`N×N` 候选两两矩阵与贪心正交筛选；异步非阻塞远程 PC 与 `/check` 状态机（零 `/submit`） |
| 评估、消融与停用 | `ra_evaluator.py`、`ablation_engine.py`、`blacklist_registry.py`、`pyramid_planner.py` | 厂字型秒杀、D1 四关评价、零 `+`/`*` 双分支消融、Stage-0 快速降级与 200 样本作用域自动停用/一键恢复、5:5 批次规划 |

## 2. 故障恢复与断点续传机制

- 所有批次与单条任务状态实时写入 `data/wq_v2_ledger.db`（WAL 模式）。
- 网络抖动时 `NetworkMonitor` 清除 `network_available` 信号暂停新任务，每 10 秒探测重连并自动刷新凭证。
- 进程意外重启后运行 `python -m wq_research_v2 sim resume` 读取未终态任务；已发出的 `SUBMITTED`/`PENDING_RECONCILE` 任务严格执行“只读对账一次，未观测则转 `RESULTS_UNOBSERVED`”，杜绝重复发包。

## 3. 无 GUI 轻量 `Useful` 标签交付与低内存扫描规范（对齐广州后台扫描）

本项目**不建设**本地 Web 看板 / GUI，直接采用 BRAIN 平台原生标签闭环：
1. **统一可用标签 `Useful`**：仅对通过四关（IS 门槛 + 全量本地 SC + 候选池两两正交 + 远程 PC `< 0.70` 与 `/check`）的候选，在用户显式确认（`--confirm-apply`）后调用 `PATCH /alphas/{id}` 补打 **`Useful`** 标签，随后由用户在平台网页端筛选 `Useful` 自主决定手工提交（永不调用 `/submit`）。
2. **低内存定向扫描（参考广州 `RA V7` 后台扫描）**：
   - 按增量小窗口（如近 24h / 指定窗口）分片拉取，且在 API 查询阶段前置过滤 `stage=IS&status=UNSUBMITTED&settings.delay=1` 及基础 Sharpe/Fitness 门槛，**绝不扫描无关历史或无关区域**；
   - PnL 序列与校验记录逐条流式落盘至 SQLite（`os_pnl_cache.db` / `wq_v2_ledger.db`），处理完即释放内存对象，避免把全量 JSON 或 DataFrame 长期驻留 RAM，确保低配云服务器稳定常驻运行。
