# data/platform_settings.py — 向前兼容 Shim
# 原有逻辑已迁移至 Core.api.platform，此文件仅保留向前兼容导入。
# 如果您有旧代码导入 from Core.data.platform_settings import xxx，无需修改，仍然有效。

from Core.api.platform import get_day1_universe_map, get_all_valid_scopes  # noqa: F401

__all__ = ["get_day1_universe_map", "get_all_valid_scopes"]
