"""表达式解析和确定性的局部邻域生成。"""

import logging
import re
from difflib import SequenceMatcher

from hill_climbing.config import (
    CANDIDATE_ALL_OPS, CANDIDATE_GROUPS, MAX_FIELD_NEIGHBORS,
    MAX_NEIGHBORS_PER_STEP, OPERATOR_GROUPS,
)
from hill_climbing.expression_utils import (
    _number_candidates, _number_parameter_context, _stable_unique,
)

OPERATOR_ARITY = {
    # 1参数: (field)
    'days_from_last_change': 1, 'rank': 1, 'zscore': 1, 'scale': 1, 'normalize': 1,
    'quantile': 1, 'pasteurize': 1, 'sqrt': 1, 'log': 1, 'sign': 1, 'reverse': 1,
    'inverse': 1, 'abs': 1, 'is_nan': 1, 'not': 1, 'densify': 1,
    'winsorize': 1,  # winsorize(x, std=4) — std有默认值
    'tail': 1,       # tail(x, lower=0, upper=0, newval=0) — 关键字参数有默认值
    # 2参数: (field, lookback) 或 (field, field) 或 (field, group) - 默认
    'last_diff_value': 2,  # last_diff_value(x, d) — 需要lookback
    'ts_corr': 3, 'ts_covariance': 3, 'ts_regression': 3, 'kth_element': 3,
    'add': 2, 'subtract': 2, 'multiply': 2, 'divide': 2, 'power': 2, 'min': 2, 'max': 2,
    'signed_power': 2, 'greater_equal': 2, 'greater': 2, 'less_equal': 2, 'less': 2,
    'equal': 2, 'not_equal': 2, 'and': 2, 'or': 2,
    # 特殊参数 (不参与自动替换)
    'hump': -1, 'ts_target_tvr_decay': -1, 'ts_target_tvr_hump': -1, 'ts_step': -1,
    # 3参数
    'if_else': 3, 'trade_when': 3, 'bucket': 3,  # trade_when(x, y, z) 需要3参数
    'group_mean': 3,        # group_mean(x, weight, group)
    'group_backfill': 3,    # group_backfill(x, group, d, std=4.0)
    'group_cartesian_product': -1,  # 需要Group类型输入，不参与替换
}

IGNORED_TOKENS = {
    'true', 'false', 'nan', 'inf', 'filter', 'driver', 'gaussian', 'uniform', 'cauchy',
    'ignore', 'std', 'k', 'lag', 'rettype', 'scope', 'constant', 'rate', 'limit', 'sigma'
}
IGNORED_TOKENS.update(CANDIDATE_GROUPS)
IGNORED_TOKENS.update(CANDIDATE_ALL_OPS)

class SmartExpression:
    def __init__(self, expression, settings, client):
        self.original_expr = expression
        self.settings = settings
        self.client = client
        self.tokens = []
        self.data_fields_cache = {}
        self._parse()

    def _parse(self):
        # 直接使用原始公式解析，确保索引绝对准确
        pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_.]*)|(-?\d+\.?\d*)')
        self.tokens = []
        unique_data_fields_list = []
        seen_fields = set()

        current_idx = 0
        while current_idx < len(self.original_expr):
            match = pattern.search(self.original_expr, current_idx)
            if not match: break
            
            text = match.group()
            start, end = match.span()
            token_type = 'unknown'

            if re.match(r'^-?\d+\.?\d*$', text):
                token_type = 'number'
            elif text in CANDIDATE_ALL_OPS:
                token_type = 'operator'
            elif text in CANDIDATE_GROUPS:
                token_type = 'group'
            elif text.lower() in IGNORED_TOKENS:
                token_type = 'keyword'
            # 识别算子控制参数，防止误当成数据字段优化
            elif text.startswith('lambda_') or text == 'target_tvr' or text.endswith('_tvr'):
                token_type = 'parameter'
            else:
                token_type = 'data_field'
                if text not in seen_fields:
                    unique_data_fields_list.append(text)
                    seen_fields.add(text)

            self.tokens.append({'text': text, 'type': token_type, 'start': start, 'end': end})
            current_idx = end

        # === 智能检测 group_* 函数的分组参数，防止被误当作 data_field 优化 ===
        reclassified_fields = set()
        for token in self.tokens:
            if token['type'] != 'operator' or not token['text'].startswith('group_'):
                continue
            func_end = token['end']
            if func_end >= len(self.original_expr) or self.original_expr[func_end] != '(':
                continue
            # 从开括号后扫描，找第一个 depth=1 的逗号（分隔表达式参数和分组参数）
            depth = 1
            first_comma = -1
            pos = func_end + 1
            while pos < len(self.original_expr) and depth > 0:
                ch = self.original_expr[pos]
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                elif ch == ',' and depth == 1 and first_comma == -1:
                    first_comma = pos
                pos += 1
            if first_comma == -1:
                continue
            # 逗号后的第一个 token 即为分组参数
            for t in self.tokens:
                if t['start'] > first_comma:
                    if t['type'] == 'data_field':
                        # 确认是简单标识符（逗号和此 token 之间没有嵌套调用）
                        between = self.original_expr[first_comma + 1:t['start']].strip()
                        if '(' not in between:
                            logging.info(f"  -> 将 '{t['text']}' 重新分类为 group (它是 {token['text']} 的分组参数)")
                            t['type'] = 'group'
                            reclassified_fields.add(t['text'])
                    break
        # 从数据字段列表中移除已重新分类的字段（仅当该字段所有实例都不再是 data_field 时）
        if reclassified_fields:
            still_data_fields = {t['text'] for t in self.tokens if t['type'] == 'data_field'}
            unique_data_fields_list = [f for f in unique_data_fields_list if f in still_data_fields]

        total_data_instances = len([t for t in self.tokens if t['type'] == 'data_field'])
        logging.info(f"识别到 {len(unique_data_fields_list)} 种数据字段 (共 {total_data_instances} 个优化位置): {unique_data_fields_list}")
        
        for i, field in enumerate(unique_data_fields_list):
            logging.info(f"[{i + 1}/{len(unique_data_fields_list)}] 正在搜索字段 '{field}'...")
            # 先尝试从缓存获取
            cached_cands = self.data_fields_cache.get(field)
            if cached_cands:
                # 获取原始字段类型
                original_field_type = 'UNKNOWN'
                for cached_field in cached_cands:
                    if cached_field.get('id') == field and isinstance(cached_field, dict):
                        original_field_type = cached_field.get('type', 'UNKNOWN')
                        break

                # 根据原始字段类型过滤缓存中的候选字段
                if original_field_type != 'UNKNOWN':
                    filtered_cands = [cand for cand in cached_cands if
                                      isinstance(cand, dict) and cand.get('type') == original_field_type]
                    # 更新缓存
                    self.data_fields_cache[field] = filtered_cands
                    cached_cands = filtered_cands

                # 显示缓存中的候选字段数量和类型信息
                type_counts = {}
                for cand in cached_cands:
                    field_type = cand.get('type', 'UNKNOWN') if isinstance(cand, dict) else 'UNKNOWN'
                    type_counts[field_type] = type_counts.get(field_type, 0) + 1
                type_info = ", ".join([f"{count}个{ftype}" for ftype, count in type_counts.items()])
                logging.info(f"  -> 命中本地缓存: {len(cached_cands)} 个候选字段 ({type_info})")
            else:
                # 缓存中没有则从API获取
                cands = self.client.search_dataset_for_field(field, self.settings)
                if cands:
                    self.data_fields_cache[field] = cands
                    # 显示找到的候选字段数量和类型信息
                    type_counts = {}
                    for cand in cands:
                        field_type = cand.get('type', 'UNKNOWN') if isinstance(cand, dict) else 'UNKNOWN'
                        type_counts[field_type] = type_counts.get(field_type, 0) + 1
                    type_info = ", ".join([f"{count}个{ftype}" for ftype, count in type_counts.items()])
                    logging.info(f"  -> 找到 {len(cands)} 个候选字段 ({type_info})")
                else:
                    logging.warning(f"字段 '{field}' 未找到候选，但将保留其在优化列表中的位置")
                    # 保持 token['type'] = 'data_field' 不变，确保索引稳定性

    def _get_operator_group(self, operator_name):
        """确定运算符属于哪个组"""
        for group_name, operators in OPERATOR_GROUPS.items():
            if operator_name in operators:
                return group_name
        return None

    def generate_neighbors(self, target_type, target_index):
        """生成变体 (回归 v4.4 稳健版)"""
        # 统一处理 time_window 和 number 搜索类型
        actual_search_type = 'number' if target_type == 'time_window' else target_type
        
        # 直接找到所有该类型的 Token
        candidates_indices = []
        for idx, t in enumerate(self.tokens):
            if t['type'] == actual_search_type:
                # 排除算子内部参数 (lambda_, target_tvr)
                if t['text'].startswith('lambda_') or 'tvr' in t['text']:
                    continue
                candidates_indices.append(idx)
        
        if not candidates_indices or target_index >= len(candidates_indices):
            return []

        token_idx = candidates_indices[target_index]
        token = self.tokens[token_idx]
        old_text = token['text']

        pool = []
        if target_type == 'data_field':
            pool = self.data_fields_cache.get(old_text, [])
            if not pool:
                # 策略 1: 原名搜索
                pool = self.client.search_dataset_for_field(old_text, self.settings)
                
                # 策略 2: 剥离后缀模糊搜索
                if not pool and '_' in old_text:
                    parts = old_text.split('_')
                    if len(parts) > 1:
                        short_name = '_'.join(parts[:-1])
                        logging.info(f"  -> 字段 '{old_text}' 搜索无果，尝试前缀搜索: {short_name}")
                        pool = self.client.search_dataset_for_field(short_name, self.settings)
                
                # 策略 3: 通用补救
                if not pool:
                    if 'price' in old_text.lower():
                        pool = self.client.search_dataset_for_field('pv_price', self.settings)
                    elif 'volume' in old_text.lower():
                        pool = self.client.search_dataset_for_field('pv_volume', self.settings)

                if pool: self.data_fields_cache[old_text] = pool
            
            if pool:
                logging.info(f"  -> 找到 {len(pool)} 个候选字段")
            else:
                logging.warning(f"字段 '{old_text}' 仍未找到候选，将跳过优化")
                return []
        elif target_type in ['number', 'time_window']:
            # 特殊处理：固定数值-1不应被替换
            if old_text == '-1':
                logging.info(f"  -> 检测到固定数值 '{old_text}'，不参与优化")
                return []

            pool = _number_candidates(self.original_expr, token['start'], old_text)
            if not pool:
                operator, parameter_index = _number_parameter_context(
                    self.original_expr, token['start']
                )
                logging.info(
                    f"  -> 锁定未知/枚举数字参数: operator={operator}, "
                    f"parameter_index={parameter_index}, value={old_text}"
                )
                return []
        elif target_type == 'group':
            pool = CANDIDATE_GROUPS
        elif target_type == 'operator':
            # 只在同一组内查找替代运算符，并过滤参数签名不兼容的
            operator_group = self._get_operator_group(old_text)
            if operator_group:
                old_arity = OPERATOR_ARITY.get(old_text, 2)
                pool = [op for op in OPERATOR_GROUPS[operator_group]
                        if OPERATOR_ARITY.get(op, 2) == old_arity]
                logging.info(f"  -> 运算符 '{old_text}' 属于 '{operator_group}' 组 (arity={old_arity})，兼容候选: {len(pool)} 个")
            else:
                pool = CANDIDATE_ALL_OPS
                logging.warning(f"  -> 未找到运算符 '{old_text}' 的所属组，将在整个运算符池中查找替代")

        # 处理候选池，确保正确提取字段ID
        processed_pool = []
        for x in pool:
            if isinstance(x, dict):
                processed_pool.append(x['id'])
            else:
                processed_pool.append(str(x))

        # 过滤原值、稳定去重，并让最接近当前值的候选先接受回测。
        filtered_pool = _stable_unique(x for x in processed_pool if x != old_text)

        if target_type in ['number', 'time_window']:
            current_value = float(old_text)
            filtered_pool.sort(key=lambda x: abs(float(x) - current_value))
        elif target_type == 'data_field':
            filtered_pool.sort(
                key=lambda x: SequenceMatcher(None, old_text.lower(), x.lower()).ratio(),
                reverse=True,
            )

        limit = MAX_FIELD_NEIGHBORS if target_type == 'data_field' else MAX_NEIGHBORS_PER_STEP
        if len(filtered_pool) > limit:
            logging.info(f"  -> 局部邻域剪枝: {len(filtered_pool)} -> {limit} 个候选")
            filtered_pool = filtered_pool[:limit]

        if not filtered_pool:
            return []

        results = []
        for cand in filtered_pool:
            new_expr = self.original_expr[:token['start']] + cand + self.original_expr[token['end']:]
            results.append(new_expr)

        return _stable_unique(results)

