"""三阶段候选门槛与相关性递减统一评分。"""

import math

from hill_climbing.config import (
    STAGE_GATES,
    STAGE_CORRELATION_PENALTY_WEIGHTS,
    STAGE_PC_LIMIT,
    STAGE_SCORE_BOUNDS,
    STAGE_SCORE_MIN_IMPROVEMENT,
    STAGE_SCORE_VERSION,
    STAGE_SCORE_WEIGHTS,
)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def score_stage_metrics(stats, stage=1, include_correlations=True):
    """连续分保持0-100，仅作为相同硬门槛层级内的排序信号。"""
    stats = stats if isinstance(stats, dict) else {}
    margin = number(stats.get('margin'))
    values = {
        'sharpe': number(stats.get('sharpe')),
        'fitness': number(stats.get('fitness')),
        'sharpe_2y': number(stats.get('sharpe_2y')),
        'margin_bp': margin * 10000 if margin is not None else None,
    }
    missing = [name for name, value in values.items() if value is None]
    if missing:
        return {
            'status': 'PENDING', 'score': None, 'score_version': STAGE_SCORE_VERSION,
            'components': {}, 'missing': missing,
        }

    components = {}
    for name, value in values.items():
        low, high = STAGE_SCORE_BOUNDS[name]
        progress = math.sqrt(min(1.0, max(0.0, (value - low) / (high - low))))
        weight_name = 'margin' if name == 'margin_bp' else name
        components[weight_name] = STAGE_SCORE_WEIGHTS[weight_name] * progress
    base_score = sum(components.values())
    penalties = {}
    sc_value = number(stats.get('sc'))
    stage = max(1, min(3, int(stage or 1)))
    sc_limit = STAGE_GATES[stage]['sc']
    if include_correlations:
        if sc_value is None:
            return {
                'status': 'PENDING', 'score': None, 'base_score': base_score,
                'score_version': STAGE_SCORE_VERSION, 'components': components,
                'penalties': {}, 'missing': ['sc'], 'margin_bp': values['margin_bp'],
            }
        penalties['sc'] = STAGE_CORRELATION_PENALTY_WEIGHTS['sc'] * (
            max(0.0, sc_value) / sc_limit
        ) ** 2
        pc_value = number(stats.get('pc'))
        if int(stage or 1) >= 3 and pc_value is not None:
            penalties['pc'] = STAGE_CORRELATION_PENALTY_WEIGHTS['pc'] * (
                max(0.0, pc_value) / STAGE_PC_LIMIT
            ) ** 2
    score = max(0.0, base_score - sum(penalties.values()))
    return {
        'status': 'OK', 'score': score, 'base_score': base_score,
        'score_version': STAGE_SCORE_VERSION, 'components': components,
        'penalties': penalties, 'missing': [], 'margin_bp': values['margin_bp'],
    }


def evaluate_stage_gate(stats, stage, include_correlations=True):
    """严格硬门槛，并给出可比较的归一化缺口。"""
    stats = stats if isinstance(stats, dict) else {}
    stage = max(1, min(3, int(stage or 1)))
    gate = STAGE_GATES[stage]
    margin = number(stats.get('margin'))
    values = {
        'sharpe': number(stats.get('sharpe')),
        'fitness': number(stats.get('fitness')),
        'sharpe_2y': number(stats.get('sharpe_2y')),
        'margin_bp': margin * 10000 if margin is not None else None,
        'turnover': number(stats.get('turnover')),
    }
    failed = []
    deficits = {}
    passed_count = 0
    total_count = 0
    for name in ('sharpe', 'fitness', 'sharpe_2y', 'margin_bp'):
        total_count += 1
        value = values[name]
        threshold = gate[name]
        if value is None:
            continue
        if value > threshold:
            passed_count += 1
            deficits[name] = 0.0
        else:
            failed.append(f'{name}<={threshold:g}')
            deficits[name] = max(0.0, (threshold - value) / max(abs(threshold), 1e-12))
    total_count += 1
    turnover = values['turnover']
    if turnover is not None:
        if gate['turnover_min'] < turnover < gate['turnover_max']:
            passed_count += 1
            deficits['turnover'] = 0.0
        elif turnover <= gate['turnover_min']:
            deficits['turnover'] = (gate['turnover_min'] - turnover) / gate['turnover_min']
            failed.append(f"turnover不在({gate['turnover_min']:.0%},{gate['turnover_max']:.0%})")
        else:
            deficits['turnover'] = (turnover - gate['turnover_max']) / gate['turnover_max']
            failed.append(f"turnover不在({gate['turnover_min']:.0%},{gate['turnover_max']:.0%})")
    if gate['require_platform_pass']:
        total_count += 1
        platform_pass = stats.get('passed')
        if platform_pass is True:
            passed_count += 1
            deficits['platform_checks'] = 0.0
        elif platform_pass is False:
            failed.append('platform_checks!=PASS')
            deficits['platform_checks'] = 1.0
        else:
            values['platform_checks'] = None
    if include_correlations:
        total_count += 1
        sc_value = number(stats.get('sc'))
        if sc_value is None:
            values['sc'] = None
        elif sc_value >= gate['sc']:
            failed.append(f"sc>={gate['sc']:g}")
            deficits['sc'] = (sc_value - gate['sc']) / gate['sc']
        else:
            passed_count += 1
            deficits['sc'] = 0.0
    missing = [name for name, value in values.items() if value is None]
    # 已知硬门槛失败具有支配性；主动后置的 SC/PC 缺失不能把失败洗成 PENDING。
    status = 'FAIL' if failed else ('PENDING' if missing else 'PASS')
    return {
        'status': status, 'passed': status == 'PASS',
        'missing': missing, 'failed': failed,
        'gate_level': passed_count, 'gate_total': total_count,
        'gate_deficits': deficits,
        'gate_deficit_total': sum(deficits.values()) + len(missing),
        'observable': not missing,
    }


def evaluate_stage_candidate(stats, stage, include_correlations=True):
    scoring = score_stage_metrics(stats, stage, include_correlations)
    gate = evaluate_stage_gate(stats, stage, include_correlations)
    return {**scoring, 'gate': gate, 'eligible': gate['passed'] and scoring['score'] is not None}


def evaluate_margin_repair_readiness(stats, stage):
    """判断是否只剩当前阶段 Margin 数字门槛需要修复。"""
    stats = stats if isinstance(stats, dict) else {}
    stage = max(1, min(3, int(stage or 1)))
    gate = STAGE_GATES[stage]
    values = {
        'sharpe': number(stats.get('sharpe')),
        'fitness': number(stats.get('fitness')),
        'sharpe_2y': number(stats.get('sharpe_2y')),
        'turnover': number(stats.get('turnover')),
        'margin_bp': (
            number(stats.get('margin')) * 10000
            if number(stats.get('margin')) is not None else None
        ),
    }
    missing = [name for name, value in values.items() if value is None]
    non_margin_failed = []
    for name in ('sharpe', 'fitness', 'sharpe_2y'):
        value = values[name]
        if value is not None and value <= gate[name]:
            non_margin_failed.append(f'{name}<={gate[name]:g}')
    turnover = values['turnover']
    turnover_retained = bool(
        turnover is not None
        and gate['turnover_min'] < turnover < gate['turnover_max']
    )
    if turnover is not None and not turnover_retained:
        non_margin_failed.append(
            f"turnover不在({gate['turnover_min']:.0%},{gate['turnover_max']:.0%})"
        )
    margin_bp = values['margin_bp']
    margin_passed = bool(margin_bp is not None and margin_bp > gate['margin_bp'])
    numeric_observable = not missing
    non_margin_passed = numeric_observable and not non_margin_failed
    ready = non_margin_passed and not margin_passed
    return {
        'status': 'READY' if ready else ('PENDING' if missing else 'NOT_READY'),
        'ready': ready,
        'numeric_observable': numeric_observable,
        'non_margin_passed': non_margin_passed,
        'non_margin_failed': non_margin_failed,
        'missing': missing,
        'margin_bp': margin_bp,
        'margin_threshold': gate['margin_bp'],
        'margin_passed': margin_passed,
        'margin_deficit_bp': (
            max(0.0, gate['margin_bp'] - margin_bp)
            if margin_bp is not None else None
        ),
        'turnover_retained': turnover_retained,
        'turnover_midpoint': (gate['turnover_min'] + gate['turnover_max']) / 2,
    }


def margin_repair_rank_key(stats, stage=1):
    """Margin 专项词典序；只在 MARGIN_REPAIR 批次中使用。"""
    readiness = evaluate_margin_repair_readiness(stats, stage)
    margin_bp = readiness['margin_bp']
    turnover = number((stats or {}).get('turnover'))
    midpoint = readiness['turnover_midpoint']
    sc_value = number((stats or {}).get('sc'))
    sharpe = number((stats or {}).get('sharpe'))
    fitness = number((stats or {}).get('fitness'))
    sharpe_2y = number((stats or {}).get('sharpe_2y'))
    return (
        1 if readiness['numeric_observable'] else 0,
        1 if readiness['non_margin_passed'] else 0,
        1 if readiness['margin_passed'] else 0,
        -(readiness['margin_deficit_bp'] if readiness['margin_deficit_bp'] is not None else float('inf')),
        margin_bp if margin_bp is not None else float('-inf'),
        sharpe if sharpe is not None else float('-inf'),
        fitness if fitness is not None else float('-inf'),
        sharpe_2y if sharpe_2y is not None else float('-inf'),
        -abs(turnover - midpoint) if turnover is not None else float('-inf'),
        -sc_value if sc_value is not None else float('-inf'),
    )


def candidate_rank_key(stats, score, stage=1):
    """词典序：硬门槛优先，同层再使用 Region×Category 相对质量。"""
    stats = stats if isinstance(stats, dict) else {}
    gate = evaluate_stage_gate(stats, stage)
    safe_score = number(score)
    relative_quality = number(stats.get('relative_quality'))
    return (
        1 if gate['observable'] else 0,
        gate['gate_level'],
        -gate['gate_deficit_total'],
        relative_quality if relative_quality is not None else float('-inf'),
        safe_score if safe_score is not None else float('-inf'),
        number(stats.get('sharpe')) or float('-inf'),
        number(stats.get('fitness')) or float('-inf'),
        number(stats.get('sharpe_2y')) or float('-inf'),
        number(stats.get('margin')) or float('-inf'),
        -(number(stats.get('turnover')) or float('inf')),
        -(number(stats.get('sc')) or float('inf')),
    )


def is_candidate_better(candidate_stats, candidate_score, current_stats, current_score, stage=1):
    """硬门槛进度优先；连续分不允许跨门槛层级抢占排序。"""
    return candidate_rank_key(candidate_stats, candidate_score, stage) > candidate_rank_key(
        current_stats, current_score, stage
    )


def compare_candidates(left_stats, left_score, right_stats, right_score, stage=1):
    """返回正数表示左候选应排在右候选之前。"""
    if is_candidate_better(left_stats, left_score, right_stats, right_score, stage):
        return 1
    if is_candidate_better(right_stats, right_score, left_stats, left_score, stage):
        return -1
    return 0
