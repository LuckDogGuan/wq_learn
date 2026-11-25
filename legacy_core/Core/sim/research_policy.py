"""显式选用的历史研究排序策略；不代表全局筛选标准或提交通过保证。"""
import math

def candidate_rank_key(record):
    metrics = record.get('is') or {}
    def number(name, default=-math.inf):
        value = record.get(name, metrics.get(name, default))
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default
    observed = str(record.get('status') or '').upper() not in {
        'PENDING', 'PENDING_FIELD_METADATA', 'PENDING_SC', 'RESULTS_UNOBSERVED'
    }
    turnover = number('turnover')
    sharpe_2y = number('sharpe_2y')
    sc_value = number('sc_value', math.inf)
    computed_hard_passes = sum((
        number('sharpe') > 1.58,
        number('fitness') > 1.0,
        number('margin') > 0.001,
        0.05 < turnover < 0.30,
        sharpe_2y > 1.6,
        sc_value < 0.4,
    ))
    hard_passes = record.get(
        'hard_gate_pass_count', record.get('hard_pass_count', computed_hard_passes)
    )
    turnover_score = -abs(turnover - 0.175) if math.isfinite(turnover) else -math.inf
    created = str(record.get('date_created') or record.get('dateCreated') or '')
    return (
        int(observed), int(hard_passes or 0), number('fitness'), number('sharpe'),
        number('margin'), turnover_score, -sc_value,
        created, str(record.get('alpha_id') or record.get('id') or ''),
    )

submission_thresholds = {
    # 基础门槛 (Basic Metrics)
    "is_sharpe": 1.58,           # 基础夏普率门槛：严格过滤噪音。风险中性化后允许放宽至 > 1.0，否则需 > 1.58。
    "is_fitness": 1.0,           # 适应度 (Fitness)：衡量经换手率折损后的真实收益能力。中性化后需 > 0.7，常规需 > 1.0。
    "turnover_min": 0.05,        # 最小换手率 (5%)：过滤长达几年不调仓的“单点过拟合”死水因子。
    "turnover_max": 0.30,        # 最大换手率 (30%)：限制极高频操作，极高频会导致真实交易摩擦成本剧增。
    "margin_bp": 10.0,           # 利润空间 (Margin in bp)：最低必须 > 10bp，用于覆盖实盘交易的滑点。
    "op_count_max": 6,           # 操作符数量 (Complexity)：严禁表达式过度臃肿(大于6层)，防止“刻舟求剑”式数据挖掘过拟合。
    
    # 核心相关性约束 (Correlation Constraints)
    # 相关性衡量了挖掘出的信号是否真正提供了“独占的增量价值”。
    "self_corr_max": 0.70,       # 最大自相关性 (Self-Correlation)：Alpha 在时间推移中不得与自身过去历史表现高度线性相关。
    "prod_corr_max": 0.70,       # 生产相关性 (PROD Correlation)：与平台上所有已经投入实盘(PROD)的因子的相关性必须 < 0.7。
    "power_pool_corr_max": 0.70  # 动力池相关性 (PPC)：特定因子必须与 Power Pool (核心资金池) 内的因子保持低相关。
}
