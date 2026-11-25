# machine_lib.py — 向前兼容聚合层
# 对外暴露所有子模块功能的统一入口，上层应用无需感知内部路径变化。

# === 新的 API 层 (唯一的网络请求出口) ===
from Core.api.client import BrainClient, API_BASE_URL, PLATFORM_URL
from Core.api.auth import login, login_hk, load_config
from Core.api.platform import get_day1_universe_map, get_all_valid_scopes
from Core.api.activity_api import (
    evaluate_pyramid_coverage, get_alpha_pyramid_pass_info, get_user_diversity,
)
from Core.api.data_api import get_datasets, get_datafields, get_vec_fields, process_datafields
from Core.api.sim_api import (
    set_alpha_properties, locate_alpha, get_user_alphas, get_user_alphas_page,
    post_multi_simulation, poll_simulation_progress,
    get_alpha_check, get_prod_correlation, get_ppc_value,
    get_alpha_details, check_alpha_submission_status, is_alpha_submitted,
)

# === 常量层 ===
from Core.constants.global_ops import (
    basic_ops,
    ts_ops,
    ops_set,
    cap_group,
    asset_group,
    sector_cap_group,
    sector_asset_group,
    vol_group,
    liquidity_group,
    groups,
    chn_group_13,
    chn_group_1,
    chn_group_2,
    hkg_group_13,
    hkg_group_1,
    hkg_group_2,
    twn_group_13,
    twn_group_1,
    twn_group_2,
    usa_group_13,
    usa_group_1,
    usa_group_2,
    usa_group_6,
    asi_group_13,
    asi_group_1,
    jpn_group_1,
    jpn_group_2,
    jpn_group_13,
    kor_group_13,
    kor_group_1,
    kor_group_2,
    eur_group_13,
    eur_group_1,
    eur_group_2,
    glb_group_1,
    glb_group_2,
    glb_group_13,
    amr_group_13,
    open_event_templates,
    exit_events,
    usa_events,
    asi_events,
    eur_events,
    glb_events,
    chn_events,
    kor_events,
    twn_events,
    submission_thresholds,
)

# === 因子工厂 ===
from Core.factor.generator.alpha_factory import (
    ts_factory,
    ts_comp_factory,
    vector_factory,
    twin_field_factory,
    first_order_factory,
    group_factory,
    get_group_second_order_factory,
    trade_when_factory,
)

# === 模拟与业务调度层 ===
from Core.sim.sim_engine import (
    build_sim_payload,
    generate_sim_data,
    load_task_pool,
    multi_simulate,
)
from Core.sim.alpha_manager import (
    extract_expression_field_ids,
    build_field_combination_key,
    rank_field_combination_candidates,
    allocate_tower_candidate_pool,
    get_alphas,
    prune,
    get_sc_value,
    get_pc_value,
    check_submission,
    view_alphas,
)
from Core.sim.validator import (
    invalidate_cache,
    get_sc_check,
    get_ppac_check,
    get_pc_check,
    get_alpha_extended_details,
    is_ppa,
)
from Core.sim.sc_pyramid_refresh import (
    load_sc_pyramid_refresh_state, refresh_sc_pyramid_bundle,
)
from Core.sim.sc_engine import (
    load_data, load_ppac_data, calc_self_corr, calc_ppac,
    DEFAULT_CACHE_DIR, PnlUnavailableError,
)
