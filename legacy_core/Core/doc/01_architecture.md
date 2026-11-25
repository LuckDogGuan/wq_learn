# 01 — 整体架构与模块依赖关系

## 总体分层设计

```
外部调用脚本 (test/*.py, 主策略脚本)
        │
        ▼
machine_lib.py          ← 向前兼容聚合层，统一对外公开所有符号
        │
        ├─ Core/api/             ← 【唯一网络出口层】
        │     ├── client.py        BrainClient: HTTP 封装 + 429退避 + 重试
        │     ├── auth.py          login(), login_hk(), load_config()
        │     ├── platform.py      get_day1_universe_map(), get_all_valid_scopes()
        │     ├── data_api.py      get_datasets(), get_datafields(), process_datafields()
        │     ├── sim_api.py       post_simulation(), poll_simulation_progress(), get_alpha_check()...
        │     └── __init__.py      统一公开出口
        │
        ├─ Core/sim/             ← 【业务编排层】
        │     ├── sim_engine.py    任务池切分、并发提交、轮询调度
        │     ├── alpha_manager.py Alpha 批量检索、剪枝、SC/PC 校验调度
        │     ├── validator.py     SC/PC/PPAC 独立检查函数（职责严格分离）
        │     └── sc_engine.py     本地 SC/PPAC 计算引擎（内嵌算法，无外部包依赖）
        │
        ├─ Core/data/            ← 【本地数据层】
        │     ├── catalog_db.py    SQLite CRUD（纯本地，无 HTTP）
        │     ├── data_fetcher.py  ← Shim → Core.api.data_api
        │     └── platform_settings.py ← Shim → Core.api.platform
        │
        ├─ Core/factor/          ← 【因子生成层】
        │     ├── generator/alpha_factory.py  Alpha 表达式组合工厂（纯代数，无 IO）
        │     ├── filter/          表达式过滤器（关键词、指标、语法）
        │     ├── templates/       各类 Alpha 模板（动量、基本面、情绪等）
        │     └── assembly/        宏观重型复合模板
        │
        ├─ Core/constants/       ← 全量算子签名库
        │     └── global_ops.py
        │
        └─ Core/auth/            ← Shim（已废弃，仅保留向前兼容）
              └── auth_lib.py    → Core.api.auth
```

## 严格禁止的跨层调用

| 禁止行为 | 正确替代 |
|---|---|
| 在 `sim/`、`data/`、`factor/` 中 `import requests` | 通过 `Core.api.BrainClient` 发请求 |
| `get_sc_check()` fallback 到平台 `/check` 接口 | 缓存为空时返回 `"no_cache"` |
| `get_pc_check()` 走本地 PPAC 计算 | 优先调用 `/correlations/prod`，仅以 `/check` 单次降级 |
| `get_ppac_check()` fallback 到平台接口 | 缓存为空时返回 `"no_cache"` |
| `auth/auth_lib.py` 中写业务逻辑 | 全部 re-export 至 `Core.api.auth` |

## 向前兼容 Shim 列表

这些文件保留是为了不破坏旧代码，内部只有 `import` 的 re-export：

| Shim 文件 | 实际实现位置 |
|---|---|
| `auth/auth_lib.py` | `Core.api.auth` |
| `data/data_fetcher.py` | `Core.api.data_api` |
| `data/platform_settings.py` | `Core.api.platform` |
