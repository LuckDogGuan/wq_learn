# auth/auth_lib.py — 向前兼容 Shim
# 原有逻辑已迁移至 Core.api.auth，此文件仅保留向前兼容导入。
# 如果您有旧代码导入 from Core.auth.auth_lib import login，无需修改，仍然有效。

from Core.api.auth import login, login_hk, load_config  # noqa: F401
from Core.api.client import API_BASE_URL, PLATFORM_URL   # noqa: F401

__all__ = ["login", "login_hk", "load_config", "API_BASE_URL", "PLATFORM_URL"]