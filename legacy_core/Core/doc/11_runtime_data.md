# 11 — Core 运行时数据与工具目录

## 运行时数据统一位置

所有 Core 默认运行时数据统一放在：

```text
Core/runtime_data/
├── catalog.db          # 数据集和字段目录 SQLite 数据库
├── sc_ppa/             # SC/PPA 本地缓存
│   ├── os_alpha_ids.pickle
│   ├── os_alpha_pnls.pickle
│   ├── ppac_alpha_ids.pickle
│   └── target_pnls/      # 仅保存SC严格通过阈值的目标Alpha PnL
├── hill_climbing_source/ # 持续爬山的日期断点与源Alpha事件
│   ├── state.json
│   └── events.jsonl
├── template_usage/       # 模板学习事件与可重建摘要
│   ├── events_v2.jsonl
│   └── summary_v2.csv
├── sc_pyramid_refresh/ # SC参考池与Pyramid统一刷新状态
│   └── state.json
└── logs/               # 后台下载等运行日志
```

路径由 `Core/data/runtime_paths.py` 集中定义：

- `CATALOG_DB_PATH`
- `SC_PPA_CACHE_DIR`
- `RUNTIME_LOG_DIR`
- `TEMPLATE_USAGE_DIR`
- `TEMPLATE_USAGE_EVENTS_PATH`
- `TEMPLATE_USAGE_SUMMARY_PATH`
- `TEMPLATE_USAGE_V2_EVENTS_PATH`
- `TEMPLATE_USAGE_V2_SUMMARY_PATH`
- `TEMPLATE_USAGE_V3_EVENTS_PATH`
- `TEMPLATE_USAGE_V3_SUMMARY_PATH`
- `HILL_CLIMBING_SOURCE_DIR`
- `SC_PYRAMID_REFRESH_DIR`
- `SC_PYRAMID_REFRESH_STATE_PATH`
- `HILL_CLIMBING_SOURCE_STATE_PATH`
- `HILL_CLIMBING_SOURCE_EVENTS_PATH`

`template_usage/events_v3.jsonl` 是经济语义版追加式账本；`summary_v3.csv` 仅汇总正式模板且基线、结果目标指标完整的样本。v2 与更早账本保持只读，不迁移正负表现。以上均属于运行时研究数据，默认由 `.gitignore` 排除，不作为源码提交。

`hill_climbing_source/state.json` 保存最近完整扫描日期和候选当前状态；`events.jsonl` 追加记录发现、塔判断、SC判断、优化、中断与失败。只有 `OPTIMIZED` 才代表已经处理，`PENDING`、`FAILED` 和 `INTERRUPTED` 均保留恢复资格。

因此默认路径不再依赖 PowerShell 或 Python 的当前工作目录。调用方仍可显式传入 `db_path` 或 `cache_dir`，用于测试和特殊任务。

## 目录数据库

`CatalogDB()` 默认打开 `Core/runtime_data/catalog.db`。后台数据同步、数据库检查和清理脚本都应使用该路径；测试专用的 `Core/tests/test_dummy.db` 保持独立。

## SC/PPA 缓存

`sc_engine.DEFAULT_CACHE_DIR` 默认指向 `Core/runtime_data/sc_ppa/`。这里保存 OS Alpha ID、PnL 和 PPA Alpha ID，供本地 SC/PPAC 计算使用。`target_pnls/` 与参考池隔离：只保留 SC 严格通过阈值的目标 PnL，达到阈值后删除。已有缓存已迁移到新目录，文件内容和缓存格式未改变。

## 工具目录

Core 根目录只保留包入口、兼容聚合层和核心配置。原根目录工具已移动但未删除：

```text
Core/tools/
├── manual/
│   ├── check_perms.py    # 会登录并批量模拟，必须人工确认后运行
│   └── test_sim.py       # 单条模拟测试，不属于自动流程
└── maintenance/
    └── rewrite_files.py  # 一次性维护/改写脚本，不属于运行时流程
```

其中 `check_perms.py` 和 `test_sim.py` 可能产生真实平台请求，不能纳入普通单元测试；`rewrite_files.py` 会改写源文件，只能在明确备份和确认目标后使用。

## 保留在 Core 根目录的文件

- `__init__.py`：保留，明确声明 `Core` 为 Python 包。
- `machine_lib.py`：保留，作为向前兼容聚合入口；已有 `alpha_evaluator.py` 使用它。
- `ops.json`：保留，作为算子定义/权限参考数据。
- `README.md`：保留，作为 Core 总入口。

## 尚未迁移的旧调用点

`Core/factor/filter/alpha_evaluator.py` 仍有一处显式写死 `Core/test/catalog.db`。该文件含有历史非法 UTF-8 字节，当前未强行重写，避免破坏原有中文内容；在使用这个旧评估脚本前，应先将其路径改为 `CATALOG_DB_PATH`。
