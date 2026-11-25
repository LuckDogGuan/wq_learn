# data/data_fetcher.py — 向前兼容 Shim
# 原有逻辑已迁移至 Core.api.data_api，此文件仅保留向前兼容导入。
# 如果您有旧代码导入 from Core.data.data_fetcher import xxx，无需修改，仍然有效。

from Core.api.data_api import (  # noqa: F401
    get_datasets,
    get_datafields,
    get_vec_fields,
    process_datafields,
)

__all__ = ["get_datasets", "get_datafields", "get_vec_fields", "process_datafields"]