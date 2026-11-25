# 07 — `Core/data/` 本地数据层

## 职责

`Core/data/` 负责本地 SQLite 数据库的 CRUD 操作。本层**不包含任何 HTTP 调用**。

默认数据库位置为 `Core/runtime_data/catalog.db`，由 `Core.data.runtime_paths` 集中定义，不再依赖启动时的当前工作目录。

---

## `catalog_db.py` — CatalogDB

### 数据库设计

每个 Region + Universe 组合对应一张独立的数据库表，命名规则：
```
datafields_{REGION}_{UNIVERSE}
```

例如：`datafields_USA_TOP3000`、`datafields_CHN_CHNALL`

**物理隔离原则**：不同 Region/Universe 的数据绝对不合并到同一张表，防止数据污染。

### 主要方法

```python
class CatalogDB:
    def __init__(self, db_path)
    def ensure_table(region, universe)        # 确保表存在（自动建表）
    def upsert_datafields(df, region, universe)  # 批量 upsert（有则更新，无则插入）
    def query_factors(region, universe, search=None) -> pd.DataFrame  # 按条件查询
    def fetch_all_scopes(skip_datasets, skip_fields)  # 拉取所有 Region/Universe 数据
```

### `fetch_all_scopes()` 网络调用说明

此方法是 `CatalogDB` 中**唯一涉及网络的方法**，通过 `Core.api` 调用：
```python
from Core.api import login, get_day1_universe_map
client = login()
day1_map = get_day1_universe_map(client)
```
- 每 3 小时自动重新 `login()`。
- 支持 `skip_datasets` / `skip_fields` 参数跳过已有数据。

---

## Shim 文件

以下文件**不含业务逻辑**，只做 re-export 保持向前兼容：

### `data_fetcher.py`
```python
from Core.api.data_api import get_datasets, get_datafields, get_vec_fields, process_datafields
```

### `platform_settings.py`
```python
from Core.api.platform import get_day1_universe_map, get_all_valid_scopes
```
