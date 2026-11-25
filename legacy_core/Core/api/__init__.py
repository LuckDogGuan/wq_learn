"""
Core/api/__init__.py
统一暴露 api 子包的所有公开接口，方便外部导入。
"""
from Core.api.client import BrainClient, API_BASE_URL, PLATFORM_URL
from Core.api.auth import login, login_hk, load_config
from Core.api.platform import get_day1_universe_map, get_all_valid_scopes
from Core.api.activity_api import (
    evaluate_pyramid_coverage, get_alpha_pyramid_pass_info, get_user_diversity,
    get_pyramid_alphas, get_pyramid_tower_status, get_pyramid_lit_tower_counts,
    get_current_quarter_dates,
)
from Core.api.data_api import (
    get_datasets, get_datafields, get_datafield_metadata,
    get_vec_fields, process_datafields,
)
from Core.api.sim_api import (
    set_alpha_properties, locate_alpha, get_user_alphas, get_user_alphas_page,
    post_multi_simulation, poll_simulation_progress,
    get_alpha_check, get_prod_correlation, get_ppc_value,
    get_alpha_details, check_alpha_submission_status, is_alpha_submitted,
)
from Core.api.alpha_retrieval import (
    AlphaFetchResult, COMPLETE, PARTIAL, PENDING,
    build_alpha_page_url, fetch_alpha_window,
)

__all__ = [
    "BrainClient", "API_BASE_URL", "PLATFORM_URL",
    "login", "login_hk", "load_config",
    "get_day1_universe_map", "get_all_valid_scopes",
    "get_user_diversity",
    "get_alpha_pyramid_pass_info",
    "evaluate_pyramid_coverage",
    "get_pyramid_alphas",
    "get_pyramid_tower_status",
    "get_pyramid_lit_tower_counts",
    "get_current_quarter_dates",
    "get_datasets", "get_datafields", "get_datafield_metadata",
    "get_vec_fields", "process_datafields",
    "set_alpha_properties", "locate_alpha", "get_user_alphas", "get_user_alphas_page",
    "post_multi_simulation", "poll_simulation_progress",
    "get_alpha_check", "get_prod_correlation", "get_ppc_value",
    "get_alpha_details", "check_alpha_submission_status", "is_alpha_submitted",
    "AlphaFetchResult", "COMPLETE", "PARTIAL", "PENDING",
    "build_alpha_page_url", "fetch_alpha_window",
]
