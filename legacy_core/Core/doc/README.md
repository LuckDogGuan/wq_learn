# Core 模块文档索引

2026-09-07 更新：当前接口以 [13_review_contract.md](13_review_contract.md) 和 Core/README.md 为准。
01–12 文档保留历史设计背景，其中测试目录、目录同步、提交、分页与默认导出描述可能已过时。

本目录 (`doc/`) 记录 `代码/优化代码/Core` 各子模块的完整设计逻辑，供代码审核使用。

## 文档列表

| 文件 | 描述 |
|---|---|
| [01_architecture.md](01_architecture.md) | 整体架构与模块依赖关系 |
| [02_api_layer.md](02_api_layer.md) | `Core/api/` HTTP 层详细设计 |
| [03_sim_engine.md](03_sim_engine.md) | `Core/sim/sim_engine.py` 模拟调度逻辑 |
| [04_alpha_manager.md](04_alpha_manager.md) | `Core/sim/alpha_manager.py` Alpha 管理逻辑 |
| [05_sc_ppac_engine.md](05_sc_ppac_engine.md) | `Core/sim/sc_engine.py` 本地 SC/PPAC 计算引擎 |
| [06_validator.md](06_validator.md) | `Core/sim/validator.py` 提交前验证逻辑与职责分离规则 |
| [07_data_layer.md](07_data_layer.md) | `Core/data/` 本地数据层 (SQLite) 设计 |
| [08_factor_layer.md](08_factor_layer.md) | `Core/factor/` 因子工厂与过滤器设计 |
| [09_test_guide.md](09_test_guide.md) | `Core/tests/` 测试体系与 Mock 规范 |
| [10_background_download.md](10_background_download.md) | `Core/test/background_download.py` 与 `CatalogDB.fetch_all_scopes()` 的下载、跳过、upsert 和重试逻辑 |
| [11_runtime_data.md](11_runtime_data.md) | 运行时数据库、SC/PPA 缓存、日志和工具目录整理 |
| [12_activity_api.md](12_activity_api.md) | `activity_api.py` 用户活动与 Alpha Pyramid 分类读取 |

## 核心设计原则

1. **单一网络出口**：所有 HTTP 请求必须经过 `Core.api.BrainClient`，禁止在业务层 `import requests`。
2. **SC/PPAC 本地，PC 远端**：自相关性和 PPA 相关性只走本地缓存计算；生产相关性只走平台 `/check` 接口，两者严格分离，禁止互相 fallback。
3. **无滚动 Shim**：旧路径文件（`auth/auth_lib.py`、`data/data_fetcher.py`）保留为向前兼容 shim，只做 re-export，不含业务逻辑。
