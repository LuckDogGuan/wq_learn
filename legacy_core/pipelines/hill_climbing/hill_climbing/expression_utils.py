"""表达式缓存键、稳定去重和数字参数角色判断。"""

import hashlib
import json
import re

from hill_climbing.config import CANDIDATE_DAYS, CANDIDATE_NUMBERS


def _stable_unique(items):
    """按原顺序去重，避免 set 打乱局部搜索顺序。"""
    return list(dict.fromkeys(items))


def _normalize_expression(expr):
    """FASTEXPR 空白不影响语义；缓存时折叠空白以识别等价表达式。"""
    return re.sub(r'\s+', '', expr or '')


def normalize_simulation_settings(settings):
    """返回稳定的 P2Y 设置副本；调用方传入对象不被原地修改。"""
    normalized = dict(settings or {})
    normalized['testPeriod'] = 'P2Y'
    return normalized


def _cache_key(expr, settings):
    payload = {
        'expr': _normalize_expression(expr),
        'settings': normalize_simulation_settings(settings),
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()


def _legacy_cache_key(expr, settings):
    payload = {'expr': expr, 'settings': settings or {}}
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()


def _multi_batch_key(expressions, settings):
    """Multi-Simulation 断点键：保留表达式顺序，确保子任务映射稳定。"""
    payload = {
        'expressions': [_normalize_expression(expr) for expr in expressions],
        'settings': normalize_simulation_settings(settings),
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()


_DAY_PARAMETER_INDEX = {
    'ts_mean': {1}, 'ts_rank': {1}, 'ts_zscore': {1}, 'ts_std_dev': {1},
    'ts_delta': {1}, 'ts_delay': {1}, 'ts_backfill': {1}, 'ts_av_diff': {1},
    'ts_arg_min': {1}, 'ts_arg_max': {1}, 'ts_quantile': {1}, 'ts_sum': {1},
    'ts_decay_linear': {1}, 'ts_count_nans': {1}, 'ts_product': {1},
    'last_diff_value': {1}, 'ts_ir': {1}, 'ts_kurtosis': {1},
    'ts_max_diff': {1}, 'ts_returns': {1}, 'ts_corr': {2},
    'ts_covariance': {2}, 'ts_regression': {2}, 'group_backfill': {2},
}


def _number_parameter_context(expression, number_start):
    """返回数字所在的最近函数和零基参数位置；无法判断时返回 (None, None)。"""
    stack = []
    for index, char in enumerate(expression[:number_start]):
        if char == '(':
            match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*$', expression[:index])
            stack.append({'operator': match.group(1) if match else None, 'commas': 0})
        elif char == ')' and stack:
            stack.pop()
        elif char == ',' and stack:
            stack[-1]['commas'] += 1
    if not stack:
        return None, None
    return stack[-1]['operator'], stack[-1]['commas']


def _number_candidates(expression, number_start, old_text):
    """按参数角色给候选；未知角色锁定，避免把指数/rettype 当天数。"""
    operator, parameter_index = _number_parameter_context(expression, number_start)
    if parameter_index in _DAY_PARAMETER_INDEX.get(operator, set()):
        return [str(value) for value in CANDIDATE_DAYS]
    if operator in {'signed_power', 'power'} and parameter_index == 1:
        return [str(value) for value in CANDIDATE_NUMBERS]
    if operator == 'ts_regression' and parameter_index == 3:
        return ['0', '1']  # lag 只测试当期和滞后一期。
    # rettype、k、scale、阈值和无法识别的数字保持源值。
    return []
