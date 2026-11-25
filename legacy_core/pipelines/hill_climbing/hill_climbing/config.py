"""爬山算法的用户可调配置；修改这里即可，不需要进入优化器实现。"""

import json

# ==================== 用户配置区域 ====================
# 运行模式配置
# RUN_MODE = 1: 重新开始，删除旧的日志和检查点文件
# RUN_MODE = 2: 断点续爬
RUN_MODE = 2

# 支持多个Alpha ID的列表
TARGET_ALPHA_IDS = ['le21nEr7']

# 持续运行模式: True = 自动从平台获取alpha并持续优化; False = 使用固定TARGET_ALPHA_IDS
CONTINUOUS_MODE = True

# 持续模式源 Alpha 筛选。开启塔反补后，仅优化至少关联一个未 PASS 塔的 Alpha。
ENABLE_PYRAMID_BACKFILL = True
# 每轮安全检查点调用一次Core刷新管理器；仅到期时访问平台，不启动后台线程。
ENABLE_SC_PYRAMID_AUTO_REFRESH = True
SC_PYRAMID_REFRESH_HOURS = 6
# 首次运行回看最近 30 个自然日；恢复时包含断点当天，避免漏掉当天晚些创建的 Alpha。
SOURCE_LOOKBACK_DAYS = 30
SOURCE_DATE_OVERLAP_DAYS = 1
# 源 Alpha 基础门槛均为严格大于；等于阈值时不进入后续塔检查和 SC 检查。
SOURCE_SHARPE_MIN = 1.2
SOURCE_FITNESS_MIN = 0.5
# 宽进阶段：已有 SC 必须严格小于 0.5；SC 缺失允许低优先进入探针。
SOURCE_SC_MAX = 0.5
SOURCE_ALLOW_MISSING_SC = True
SOURCE_ADMISSION_PROFILE = "balanced-v3-inherited-operators"
SOURCE_MAX_OPERATOR_CALLS = 5
SOURCE_FORBIDDEN_OPERATORS = frozenset({"add", "multiply", "trade_when"})
# 同时允许未提交和 IS 失败的 REGULAR Alpha 作为可修复的起点。
SOURCE_STATUSES = ("UNSUBMITTED", "IS_FAIL")
# 当前没有可优化源 Alpha 或平台结果不可观察时，等待一小时后再只读检查。
SOURCE_IDLE_SECONDS = 3600
# 日期分页不可观察时，保留成功页 offset，冷却后从失败页继续。
SOURCE_SCAN_RETRY_SECONDS = 300
# 当天只需短周期倒序增量检查；完整分页用于半小时兜底对账。
SOURCE_INCREMENTAL_SCAN_SECONDS = 300
SOURCE_FULL_SCAN_SECONDS = 1800
# Multi-Simulation 的 POST 本身不做隐式重试；明确 429 后冷却 5 分钟，最多重试两次。
MULTI_RATE_LIMIT_WAITS = ()
MULTI_RATE_LIMIT_COOLDOWN_SECONDS = 300
MULTI_MAX_POST_ATTEMPTS = 3  # 首次 POST + 冷却后的 2 次重试
MULTI_RATE_LIMIT_MAX_RETRIES = MULTI_MAX_POST_ATTEMPTS - 1
MULTI_SUBMITTED_ABANDON_AFTER_SECONDS = 1200
# 兼容旧调用；语义已经从“超时重提”改为“超时停止恢复”。
MULTI_SUBMITTED_REPOST_AFTER_SECONDS = MULTI_SUBMITTED_ABANDON_AFTER_SECONDS
OBJECTIVE_VERSION = "hard-gate-distance-v6-immediate-branches"
CODE_VERSION = "hill-climbing-v4.7.8-catalog-priority"
# 字段组合、塔候选池与三阶段 Multi-Simulation 预算。
FIELD_COMBINATION_KEEP_NUM = 1
TOWER_ACTIVE_HILL_LIMIT = 12
TOWER_SC_ATTEMPT_LIMIT = 24
TOWER_STAGE1_BATCHES = 4
TOWER_STAGE2_PROMOTE = 6
TOWER_STAGE2_BATCHES = 4
TOWER_STAGE3_PROMOTE = 3
TOWER_STAGE3_BATCHES = 5
STAGE_BATCH_BUDGETS = {
    1: TOWER_STAGE1_BATCHES,
    2: TOWER_STAGE2_BATCHES,
    3: TOWER_STAGE3_BATCHES,
}
TOWER_PROMOTION_COHORT_SIZE = 12
PROMOTION_OBSERVABLE_WINDOW = 40
PROMOTION_PARTIAL_MIN_OBSERVABLE = 8
PROMOTION_PARTIAL_MAX_BATCHES = 10
PROMOTION_PARTIAL_MAX_HOURS = 24

# 三阶段连续分仅用于同一硬门槛层级内排序。Margin 原始值先乘 10000 转换为 bp。
STAGE_SCORE_VERSION = "stage-v7-test-p2y"
STAGE_SCORE_BOUNDS = {
    "sharpe": (1.4, 3.6),
    "fitness": (0.7, 2.3),
    "sharpe_2y": (1.4, 3.6),
    "margin_bp": (5.0, 50.0),
}
STAGE_SCORE_WEIGHTS = {
    "sharpe": 30.0, "fitness": 20.0, "sharpe_2y": 25.0, "margin": 25.0,
}
STAGE_CORRELATION_PENALTY_WEIGHTS = {"sc": 10.0, "pc": 10.0}
STAGE_SC_LIMIT = 0.4
STAGE_PC_LIMIT = 0.7
STAGE_SCORE_MIN_IMPROVEMENT = 0.5
STAGE_GATES = {
    1: {
        "sharpe": 1.2, "fitness": 0.5, "sharpe_2y": 1.0,
        "margin_bp": 3.0, "turnover_min": 0.03, "turnover_max": 0.80,
        "sc": 0.5,
        "require_platform_pass": False,
    },
    2: {
        "sharpe": 1.4, "fitness": 0.75, "sharpe_2y": 1.3,
        "margin_bp": 6.0, "turnover_min": 0.04, "turnover_max": 0.50,
        "sc": 0.45,
        "require_platform_pass": False,
    },
    3: {
        "sharpe": 1.58, "fitness": 1.0, "sharpe_2y": 1.6,
        "margin_bp": 10.0, "turnover_min": 0.05, "turnover_max": 0.30,
        "sc": 0.4,
        "require_platform_pass": True,
    },
}
STAGE1_GATE_DEFICIT_IMPROVEMENT_MIN = 0.05
STAGE_MAX_IMMEDIATE_BRANCHES = 3
MARGIN_REPAIR_MIN_IMPROVEMENT_BP = 1.0
MARGIN_REPAIR_MAX_BATCHES_PER_STAGE = 2
# 旧调用继续可读；新的候选池固定每组合只保留当前最佳一条。
SOURCE_PRUNE_KEEP_NUM = FIELD_COMBINATION_KEEP_NUM
# 连续 3 个目标 Alpha 的 PnL 均不可用时，暂停请求 PnL 60 秒，避免平台异常时逐条空转。
SOURCE_SC_PNL_FAILURE_LIMIT = 3
SOURCE_SC_PNL_COOLDOWN_SECONDS = 60
# 从配置文件中读取邮箱配置
try:
    with open('email_config.json') as f:
        EMAIL_CONFIG = json.load(f)

except Exception as e:
    # 默认邮箱配置
    EMAIL_CONFIG = {
        'enabled': False,
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,
        'sender': '',
        'password': '',
        'receiver': ''
    }
# 最大并发数设置（卡槽数量）
MAX_CONCURRENT = 2

# 爬山起始位置配置
START_OPTIMIZATION_FROM = {
    'data_field': 0,
    'time_window': 0,
    'number': 0,
    'group': 0,
    'operator': 0
}

# 迭代优化配置
MAX_ITERATIONS = 5
BATCH_SIZE = 8

# 回测预算：真正的爬山只看局部邻域；连续批次没有提升时停止当前位置。
MAX_NEIGHBORS_PER_STEP = 8
MAX_FIELD_NEIGHBORS = 16
MAX_SETTINGS_CANDIDATES = 6
MAX_STALE_BATCHES = 1
MIN_SCORE_IMPROVEMENT = STAGE_SCORE_MIN_IMPROVEMENT
ENABLE_AUTO_REVERSE = False
ALLOW_PLATFORM_PROPERTY_WRITES = False

# 广度探索预算：最多 8 批，每批 8 条；不足 2 条绝不回退单条接口。
ENABLE_TEMPLATE_EXPLORATION = True
PREFER_ADMIN_TEMPLATES = True
PREFER_CATALOG_TEMPLATES = True  # 用户指定224个模板优先验证；失败范围仍禁止使用。
TEMPLATE_EXPLORATION_LIMIT = 64
TEMPLATE_BATCH_SIZE = 8
TEMPLATE_BREADTH_LIMIT = 40
TEMPLATE_SHAPE_LIMIT = 16

# 候选项配置
# CANDIDATE_DAYS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 22, 60, 64, 120, 128, 252, 256, 512, 720, 900, 1050, 2000]
CANDIDATE_DAYS = [5, 10, 22, 66, 120, 252]
# 仅用于 signed_power/power 的指数；未知数字参数不再盲扫。
CANDIDATE_NUMBERS = [0.5, 1.0, 1.5, 2.0]
CANDIDATE_GROUPS = ['market', 'industry', 'subindustry', 'sector', 'densify(pv13_1l_scibr)']
CANDIDATE_NEUTRALIZATIONS = ["RAM"]
# CANDIDATE_NEUTRALIZATIONS = ["MARKET", "INDUSTRY", "SUBINDUSTRY", "SECTOR", "NONE", "CROWDING", "FAST", "SLOW", "RAM"]

# Simulation Decay：0=不平滑，5=约一周，10=约两周，22=约一月，66=约一季。
CANDIDATE_DECAYS = [0, 5, 10, 22, 66]

# 2.4版本改色逻辑常量
MARGIN_THRESHOLD = 0.000

# 运算符池分类
OPERATOR_GROUPS = {
    'group': [
        'group_rank', 'group_zscore', 'group_neutralize',
        'group_sum', 'group_std_dev', 'group_count',
        'group_scale'
    ],
    'group_special': [
        # 以下操作符参数签名特殊，不参与自动替换
        # group_mean(x, weight, group) — 3参数
        # group_backfill(x, group, d, std=4.0) — 3+参数
        # group_cartesian_product(g1, g2) — 需要Group类型输入
        'group_mean', 'group_backfill', 'group_cartesian_product'
    ],
    'time_series': [
        'ts_rank', 'ts_zscore', 'ts_mean', 'ts_std_dev', 'ts_delta', 'ts_delay',
        'ts_backfill', 'ts_av_diff', 'ts_arg_min', 'ts_arg_max', 'days_from_last_change',
        'ts_quantile', 'ts_scale', 'ts_regression', 'ts_sum', 'ts_decay_linear',
        'ts_covariance', 'ts_count_nans', 'kth_element', 'ts_corr', 'ts_product',
        'last_diff_value', 'ts_ir', 'ts_kurtosis', 'ts_max_diff', 'ts_returns'
    ],
    'time_series_special': [
        # 以下操作符参数签名特殊，不参与自动替换
        # hump(x, hump=0.01) — 关键字参数
        # ts_step(1) — 常量参数，无field/lookback
        # ts_target_tvr_decay/hump — 需要lambda_min/max/target_tvr
        'hump', 'ts_step', 'ts_target_tvr_decay', 'ts_target_tvr_hump'
    ],
    'cross_sectional': [
        'rank', 'zscore', 'scale', 'normalize', 'quantile', 'winsorize'
    ],
    'arithmetic': [
        'subtract', 'divide', 'pasteurize', 'sqrt', 'log',
        'signed_power', 'sign', 'reverse', 'power', 'min', 'max', 'inverse',
        'densify', 'abs'
    ],
    'vector': [
        'vec_avg', 'vec_sum', 'vec_max', 'vec_min','vec_stddev','vec_range'
    ],
    'logical': [
        'greater_equal', 'and', 'or', 'not_equal', 'not', 'greater',
        'less_equal', 'less', 'is_nan', 'if_else', 'equal'
    ],
    'transformational': [
        'tail', 'bucket'
    ]
}

CANDIDATE_ALL_OPS = []
for ops in OPERATOR_GROUPS.values():
    CANDIDATE_ALL_OPS.extend(ops)

# 每个北京时间中午 12:00 开始一个新的回测额度窗口。
# 一条 Multi-Simulation 中有 8 个表达式时计为 8 次，而不是 1 次 HTTP 请求。
DAILY_BACKTEST_LIMIT = 3000
DAILY_BACKTEST_RESET_HOUR = 12
