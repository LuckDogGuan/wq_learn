import json
import pandas as pd
import time
import logging
import re
import hashlib
import math
import os
import threading
import signal
import sys
from pathlib import Path
from uuid import uuid4
from collections import Counter
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from functools import cmp_to_key
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 复用 Core 的表达式检查、Multi-Simulation、SC 和模板账本。
PACKAGE_DIR = Path(__file__).resolve().parent
HILL_ROOT = PACKAGE_DIR.parent
OPTIMIZATION_ROOT = HILL_ROOT.parent
if str(OPTIMIZATION_ROOT) not in sys.path:
    sys.path.insert(0, str(OPTIMIZATION_ROOT))
SCRIPT_DIR = HILL_ROOT
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from Core.api import login as core_login
from Core.api.data_api import get_datafield_metadata, get_datafields
from Core.api.activity_api import (
    evaluate_pyramid_coverage, get_alpha_pyramid_pass_info, get_user_diversity,
)
from Core.api.sim_api import (
    get_user_alphas_page, post_multi_simulation, poll_simulation_progress,
)
from Core.data.runtime_paths import (
    HILL_CLIMBING_SOURCE_DB_PATH, HILL_CLIMBING_SOURCE_EVENTS_PATH,
    HILL_CLIMBING_SOURCE_STATE_PATH,
    SC_PPA_CACHE_DIR,
)
from Core.factor.filter.expression_checker import batch_verify_expressions
from Core.factor.template_usage import (
    TEMPLATE_LEARNING_VERSION, compose_stage1_template_batch,
    compose_template_batch, load_template_usage, record_template_usage,
    resolve_template_category, select_template_candidates, summarize_template_usage,
)
from Core.factor.templates.risk_and_correlation import (
    optimize_weight_concentration_neutralize,
    optimize_weight_concentration_rank,
    reduce_correlation_by_decay_sweep,
    reduce_correlation_by_delay_signal,
)
from Core.sim.alpha_manager import prune as core_prune
from Core.sim.sc_engine import delete_target_pnl_cache, load_target_pnl_cache
from Core.sim.sc_pyramid_refresh import refresh_sc_pyramid_bundle
from Core.sim.validator import get_pc_check, get_sc_check

from hill_climbing.budget import DailyBacktestBudget, DailyBacktestLimitReached
from hill_climbing.config import *
from hill_climbing.source_pipeline import (
    apply_region_category_relative_quality, build_candidate_pool,
    promote_completed_stages, source_scope_reason,
)
from hill_climbing.state_store import SourceState, SourceStateStore
from hill_climbing.routes import (
    ROUTE_REGISTRY, candidate_route, choose_route, prioritize_route,
)
from hill_climbing.scoring import (
    candidate_rank_key, compare_candidates, evaluate_stage_candidate,
    evaluate_margin_repair_readiness, is_candidate_better,
    margin_repair_rank_key, number,
)

print(f"📧 邮件通知功能: {'已启用' if EMAIL_CONFIG.get('enabled') else '未启用'}")


from hill_climbing.expression_utils import (
    _cache_key, _legacy_cache_key, _multi_batch_key, _normalize_expression,
    _number_candidates, _stable_unique, normalize_simulation_settings,
)

# 运算符参数数量映射 (仅标记非标准签名的算子，默认为2参数: field, lookback/group)
from hill_climbing.smart_expression import IGNORED_TOKENS, SmartExpression
from hill_climbing.runtime import (
    BASE_CHECKPOINT_FILE, BASE_DATASET_CACHE_FILE, BASE_HISTORY_FILE,
    OUTPUT_DIR, RUN_OUTPUT_DIR, SingleInstanceLock, create_run_output_dir, setup_logging,
)


def _core_client(context):
    """生产环境取 Core 客户端；测试替身可直接实现同一接口。"""
    if isinstance(context, OptimizerContext):
        return context.core_client
    return context

def send_qq_email(subject, content):
    if not EMAIL_CONFIG.get('enabled', False): return
    try:
        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = EMAIL_CONFIG['sender']
        msg["To"] = EMAIL_CONFIG['receiver']
        msg["Subject"] = Header(subject, "utf-8")
        server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
        server.sendmail(EMAIL_CONFIG['sender'], [EMAIL_CONFIG['receiver']], msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

def is_file_older_than_days(file_path, days):
    try:
        file_mtime = os.path.getmtime(file_path)
        file_time = datetime.fromtimestamp(file_mtime)
        return datetime.now() - file_time > timedelta(days=days)
    except: return False

def cleanup_alpha_files(alpha_id):
    files = [
        os.path.join(OUTPUT_DIR, f'{alpha_id}_checkpoint_v4.7.json'),
        os.path.join(OUTPUT_DIR, f'{alpha_id}_history_v4.7.json'),
        os.path.join(OUTPUT_DIR, f'{alpha_id}_dataset_cache_v4.7.json'),
        os.path.join(RUN_OUTPUT_DIR, f'{alpha_id}_hill_climbing_v4.7.log')
    ]
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
                logging.info(f"已清理: {f}")
            except: pass

# 忽略的关键词 (避免被误识别为数据字段)

# ==================== 持续运行模式：辅助函数 ====================
PROCESSED_ALPHAS_FILE = os.path.join(OUTPUT_DIR, 'processed_alphas.json')

def load_processed_alphas():
    """加载已处理的alpha记录"""
    if os.path.exists(PROCESSED_ALPHAS_FILE):
        try:
            with open(PROCESSED_ALPHAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_processed_alpha(alpha_id, expr):
    """保存已处理的alpha记录"""
    data = load_processed_alphas()
    data[alpha_id] = {
        'expr': expr,
        'timestamp': datetime.now().isoformat(),
        'operators': extract_operators(expr)
    }
    with open(PROCESSED_ALPHAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def extract_operators(expr):
    """从表达式中提取使用的运算符列表"""
    ops = []
    for op in CANDIDATE_ALL_OPS:
        if re.search(r'\b' + re.escape(op) + r'\s*\(', expr):
            ops.append(op)
    return sorted(ops)


def introduced_operator_counts(expression, inherited_expression=''):
    """只计算候选相对继承表达式新增的函数调用。"""
    pattern = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')
    candidate = Counter(name.lower() for name in pattern.findall(expression or ''))
    inherited = Counter(
        name.lower() for name in pattern.findall(inherited_expression or '')
    )
    return candidate - inherited


def new_operator_policy_reason(expression, inherited_expression,
                               allowed_operators, max_new_calls=None):
    """历史子树获准继承；仅审查本轮新增算子。"""
    introduced = introduced_operator_counts(expression, inherited_expression)
    introduced_names = set(introduced)
    forbidden = introduced_names & set(SOURCE_FORBIDDEN_OPERATORS)
    if forbidden:
        return '新变换引入项目禁用操作符: ' + ','.join(sorted(forbidden))
    allowed = {str(name).lower() for name in (allowed_operators or ())}
    unavailable = introduced_names - allowed
    if unavailable:
        return '新变换使用当前账户无权限操作符: ' + ','.join(sorted(unavailable))
    limit = SOURCE_MAX_OPERATOR_CALLS if max_new_calls is None else int(max_new_calls)
    if sum(int(value) for value in introduced.values()) > limit:
        return f'新引入操作符数量>{limit}'
    return ''

def extract_expression_structure(expr):
    """提取表达式的结构特征用于多样性比较"""
    operators = set(extract_operators(expr))
    # 计算嵌套深度
    max_depth = 0
    current_depth = 0
    for ch in expr:
        if ch == '(':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif ch == ')':
            current_depth -= 1
    # 提取数据字段
    pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)')
    tokens = pattern.findall(expr)
    data_fields = set()
    for t in tokens:
        if (t not in CANDIDATE_ALL_OPS
                and t.lower() not in IGNORED_TOKENS
                and t not in CANDIDATE_GROUPS):
            data_fields.add(t)
    return {
        'operators': operators,
        'depth': max_depth,
        'data_fields': data_fields,
        'op_count': len(operators)
    }

def calculate_structural_distance(expr1, expr2):
    """计算两个表达式的结构差异度（0=完全相同, 1=完全不同）"""
    s1 = extract_expression_structure(expr1)
    s2 = extract_expression_structure(expr2)
    # 1. 运算符集合Jaccard距离 (权重50%)
    ops_union = s1['operators'] | s2['operators']
    ops_inter = s1['operators'] & s2['operators']
    op_distance = 1.0 - (len(ops_inter) / len(ops_union)) if ops_union else 0.0
    # 2. 数据字段Jaccard距离 (权重30%)
    fields_union = s1['data_fields'] | s2['data_fields']
    fields_inter = s1['data_fields'] & s2['data_fields']
    field_distance = 1.0 - (len(fields_inter) / len(fields_union)) if fields_union else 0.0
    # 3. 嵌套深度差异 (权重20%)
    depth_distance = abs(s1['depth'] - s2['depth']) / max(s1['depth'], s2['depth'], 1)
    return 0.5 * op_distance + 0.3 * field_distance + 0.2 * depth_distance

def select_most_diverse_alpha(candidates, processed_records):
    """从候选alpha中选择与已处理alpha结构差异最大的（maximin策略）

    Args:
        candidates: alpha详情列表, 每个包含 'id' 和 'regular' 字段
        processed_records: dict, 已处理alpha记录 {alpha_id: {expr, ...}}

    Returns:
        结构差异最大的候选alpha dict, 或 None
    """
    if not candidates:
        return None
    if not processed_records:
        return candidates[0]
    processed_exprs = [r.get('expr', '') for r in processed_records.values() if r.get('expr')]
    if not processed_exprs:
        return candidates[0]
    best_candidate = None
    best_min_distance = -1
    for cand in candidates:
        cand_expr = cand.get('regular', '')
        if isinstance(cand_expr, dict):
            cand_expr = cand_expr.get('code', '')
        if not cand_expr:
            continue
        # 计算与所有已处理alpha的最小距离（最近邻距离）
        min_dist = float('inf')
        for pe in processed_exprs:
            dist = calculate_structural_distance(cand_expr, pe)
            min_dist = min(min_dist, dist)
        # 选择最小距离最大的（maximin策略）
        if min_dist > best_min_distance:
            best_min_distance = min_dist
            best_candidate = cand
    if best_candidate:
        logging.info(f"   🎯 选择了结构差异度最大的alpha (距离={best_min_distance:.4f})")
    return best_candidate


def select_immediate_stage_branches(candidates, stage, limit=3):
    """选择不同模板家族的完整 PASS；同表达式或 Alpha ID 只保留一次。"""
    eligible = []
    seen_identity = set()
    for item in candidates or ():
        stats = dict(item.get('stats') or {})
        if item.get('status') not in {'COMPLETE', 'CACHE_HIT', None}:
            continue
        alpha_id = str(item.get('alpha_id') or '').strip()
        expression = str(item.get('expression') or '').strip()
        if not alpha_id or not expression:
            continue
        assessment = evaluate_stage_candidate(stats, int(stage))
        if not assessment.get('eligible'):
            continue
        identity = (alpha_id, _normalize_expression(expression))
        if identity in seen_identity:
            continue
        seen_identity.add(identity)
        eligible.append({**item, 'score': assessment.get('score')})
    eligible.sort(
        key=cmp_to_key(lambda left, right: compare_candidates(
            left.get('stats') or {}, left.get('score'),
            right.get('stats') or {}, right.get('score'), int(stage),
        )),
        reverse=True,
    )
    selected = []
    families = set()
    for item in eligible:
        family = str(item.get('template_family') or item.get('family') or 'UNKNOWN')
        if family in families:
            continue
        families.add(family)
        selected.append(item)
        if len(selected) >= int(limit):
            break
    return selected


def enqueue_immediate_stage_branches(state, parent, branches, stage):
    """把 PASS 分支写回现有 candidates SQLite 载荷，不新增表。"""
    candidates = state.setdefault('candidates', {})
    parent_id = str(parent.get('alpha_id') or '')
    root_id = str(parent.get('root_source_alpha_id') or parent_id)
    created = []
    merged = 0
    active_expressions = {
        _normalize_expression(item.get('expression', ''))
        for item in candidates.values()
        if item.get('immediate_stage_branch') and item.get('pool_status') == 'ACTIVE'
    }
    for branch in branches or ():
        alpha_id = str(branch.get('alpha_id') or '')
        expression = str(branch.get('expression') or '')
        normalized = _normalize_expression(expression)
        if not alpha_id or not normalized:
            continue
        existing = candidates.get(alpha_id)
        if normalized in active_expressions and not (
            existing and str(existing.get('alpha_id')) == alpha_id
        ):
            merged += 1
            continue
        branch_id = hashlib.sha256(
            f'{root_id}|{stage}|{alpha_id}|{normalized}'.encode('utf-8')
        ).hexdigest()[:16]
        payload = dict(parent)
        stats = dict(branch.get('stats') or {})
        payload.update({
            'alpha_id': alpha_id,
            'expression': expression,
            'status': 'ELIGIBLE',
            'status_reason': f'Stage {stage} PASS后立即交接Stage {stage + 1}',
            'pool_status': 'ACTIVE',
            'hill_stage': int(stage) + 1,
            'immediate_stage_branch': True,
            'branch_id': branch_id,
            'parent_source_alpha_id': parent_id,
            'root_source_alpha_id': root_id,
            'branch_family': branch.get('template_family') or 'UNKNOWN',
            'branch_template_id': branch.get('template_id'),
            'branch_variant_id': branch.get('variant_id'),
            'best_stats': stats,
            'sharpe': stats.get('sharpe'),
            'fitness': stats.get('fitness'),
            'stage_batches_used': 0,
            'stage_plan_cursor': 0,
            'stage_post_batches_used': 0,
            'stage_cache_batches_reused': 0,
            'stage_observed_candidates': 0,
            'stage_observable_results': 0,
            'stage_pass_results': 0,
            'stage_logical_batches': 0,
            'stage_branches': [],
            'template_batch': 0,
            'template_batches_executed': 0,
            'margin_batches_executed': 0,
            'attempted_routes': [],
            'active_route': None,
            'promotion_window_closed': False,
            'retry_after': None,
            'retry_kind': 'IMMEDIATE_STAGE_HANDOFF',
            'objective_version': OBJECTIVE_VERSION,
            'score_version': STAGE_SCORE_VERSION,
            'code_version': CODE_VERSION,
        })
        candidates[alpha_id] = payload
        active_expressions.add(normalized)
        created.append(payload)
    return created, merged


SOURCE_STATE_SCHEMA_VERSION = 6
SOURCE_RETRYABLE_STATUSES = {
    'PENDING_DIVERSITY', 'PENDING_PYRAMID', 'PENDING_SC',
}
SOURCE_QUEUE_STATUSES = {'ELIGIBLE', 'INTERRUPTED', 'BLOCKED_INCOMPLETE_BATCH'}
SOURCE_PRE_SC_STATUSES = {'PRE_SC_ELIGIBLE', 'PENDING_SC'}


def _migrate_source_admission(record):
    """按当前宽入口本地重分类；不访问平台，也不把缺失 SC 当失败。"""
    previous_status = record.get('status')
    sharpe = number(record.get('sharpe'))
    fitness = number(record.get('fitness'))
    record.update({
        'admission_profile': SOURCE_ADMISSION_PROFILE,
        'objective_version': OBJECTIVE_VERSION,
        'code_version': CODE_VERSION,
        'retry_after': None,
    })
    if sharpe is None or fitness is None or sharpe <= SOURCE_SHARPE_MIN \
            or fitness <= SOURCE_FITNESS_MIN:
        record['status'] = 'METRIC_REJECTED'
        record['status_reason'] = (
            f'当前宽入口要求Sharpe>{SOURCE_SHARPE_MIN}且Fitness>{SOURCE_FITNESS_MIN}'
        )
        return
    sc_value = number(record.get('sc_value'))
    if previous_status == 'SC_REJECTED' and sc_value is None:
        record['status'] = 'SC_REJECTED'
        record['status_reason'] = '历史SC拒绝记录没有可证实的SC<0.5，不自动恢复'
        record['source_sc_kind'] = 'UNOBSERVED_REJECTED'
        return
    reason = source_scope_reason(record)
    if reason:
        record['status'] = (
            'PENDING_FIELD_METADATA' if '不可观察' in reason else 'DISABLED_SCOPE'
        )
        record['status_reason'] = reason
        return
    if sc_value is not None and sc_value >= SOURCE_SC_MAX:
        record['status'] = 'SC_REJECTED'
        record['status_reason'] = f'已有SC必须严格小于{SOURCE_SC_MAX}'
        record['source_sc_kind'] = 'OBSERVED_REJECTED'
        return
    record['status'] = 'PRE_SC_ELIGIBLE'
    record['status_reason'] = '符合宽入口，等待本地字段组合池分配'
    record['source_sc_kind'] = 'OBSERVED' if sc_value is not None else 'MISSING_ALLOWED'
    record['retry_kind'] = 'ADMISSION_PROFILE_CHANGED'


def _source_now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def _source_expression(alpha):
    expr = alpha.get('regular', '') if isinstance(alpha, dict) else ''
    return expr.get('code', '') if isinstance(expr, dict) else str(expr or '')


def _two_year_sharpe(payload):
    payload = payload if isinstance(payload, dict) else {}
    test = payload.get('test') if isinstance(payload.get('test'), dict) else {}
    return test.get('sharpe')


def _source_json_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _format_core_refresh_result(result):
    """区分本轮刷新结果与 NOT_DUE 返回的上次持久化快照。"""
    not_due = result.get('status') == 'NOT_DUE'
    prefix = '上次' if not_due else '本轮'
    snapshot = '（本轮未刷新） ' if not_due else ' '
    sc_label = 'SC快照' if not_due else 'SC'
    pyramid_label = 'Pyramid快照' if not_due else 'Pyramid'
    return (
        f"🔄 Core刷新结果={result.get('status')}{snapshot}"
        f"{sc_label}={result.get('sc_status')} "
        f"{pyramid_label}={result.get('pyramid_status')} "
        f"参考池={result.get('cached_os_count', 0)} "
        f"{prefix}远端发现={len(result.get('observed_new_os_alpha_ids') or [])} "
        f"{prefix}缓存新增={len(result.get('cached_new_os_alpha_ids') or [])} "
        f"{prefix}PnL失败={len(result.get('failed_pnl_alpha_ids') or [])}"
    )


def _simulation_failure_reason(payload):
    """提取平台终态错误；保留结构但避免日志写入不可序列化对象。"""
    if not isinstance(payload, dict):
        return ''
    for key in ('message', 'error', 'errors'):
        value = payload.get(key)
        if value not in (None, '', [], {}):
            return value if isinstance(value, str) else json.dumps(
                value, ensure_ascii=False, default=str
            )
    return ''


def _default_source_state():
    return {
        'schema_version': SOURCE_STATE_SCHEMA_VERSION,
        'last_complete_scan_date': None,
        'last_incremental_scan_at': None,
        'last_full_scan_at': None,
        'legacy_processed_imported': False,
        'diversity_snapshot_hash': None,
        'diversity_snapshot_time': None,
        'tower_summary': {},
        'scan_resume': None,
        'candidates': {},
    }


def load_source_state(path=None):
    """读取 SQLite 状态；首次启动幂等导入旧 JSON，旧文件保持只读。"""
    legacy_path = Path(path or HILL_CLIMBING_SOURCE_STATE_PATH)
    store_path = HILL_CLIMBING_SOURCE_DB_PATH if path is None else legacy_path
    store = SourceStateStore(store_path)
    state = store.load(_default_source_state(), legacy_path=legacy_path)
    state['schema_version'] = SOURCE_STATE_SCHEMA_VERSION
    state.setdefault('last_complete_scan_date', None)
    state.setdefault('last_incremental_scan_at', None)
    state.setdefault('last_full_scan_at', None)
    state.setdefault('legacy_processed_imported', False)
    state.setdefault('diversity_snapshot_hash', None)
    state.setdefault('diversity_snapshot_time', None)
    state.setdefault('tower_summary', {})
    state.setdefault('scan_resume', None)
    frozen = {'METRIC_REJECTED', 'SKIPPED_ALL_TOWERS_PASS', 'SC_REJECTED', 'OPTIMIZED'}
    for record in state['candidates'].values():
        status = record.get('status')
        if (
            status == 'BLOCKED_INCOMPLETE_BATCH'
            and int(record.get('hill_stage') or 1) == 2
            and int(record.get('stage_batches_used') or 0) <= TOWER_STAGE1_BATCHES
            and record.get('code_version') != CODE_VERSION
        ):
            record['status'] = 'INTERRUPTED'
            record['status_reason'] = '旧版把Stage2预算累计成5批，已改为独立3批并逐批补足'
            record['retry_kind'] = 'STAGE_BATCH_ACCOUNTING_FIXED'
            record['retry_after'] = None
            record['blocked_candidate_pool_fingerprint'] = None
            status = record['status']
        settings = record.get('settings') or {}
        if (
            status == 'PENDING_STAGE_SCORE'
            and int(record.get('hill_stage') or 1) < 3
            and int(record.get('stage_batches_used') or 0) == 0
            and number((record.get('best_stats') or {}).get('sharpe_2y')) is None
            and settings.get('testPeriod') != 'P2Y'
        ):
            record['status'] = 'INTERRUPTED'
            record['status_reason'] = '旧版P2Y设置未进入payload，允许按P2Y刷新基线'
            record['retry_kind'] = 'P2Y_PAYLOAD_FIXED'
            record['retry_after'] = None
            status = record['status']
        admission_migration_statuses = {
            'ELIGIBLE', 'INTERRUPTED', 'PENDING_STAGE_SCORE', 'METRIC_REJECTED',
            'SC_REJECTED', 'PENDING_SC', 'PRE_SC_ELIGIBLE', 'PRUNED_PRE_SC',
            'SKIPPED_PNL_UNAVAILABLE', 'PENDING_FIELD_METADATA',
        }
        if (
            record.get('admission_profile') != SOURCE_ADMISSION_PROFILE
            and status in admission_migration_statuses
            and not (
                status == 'PENDING_STAGE_SCORE'
                and int(record.get('stage_batches_used') or 0) > 0
            )
        ):
            _migrate_source_admission(record)
        stage_statuses = {'STAGE1_COMPLETE', 'STAGE2_COMPLETE', 'STAGE3_COMPLETE'}
        previous_status = (
            record.get('status') if record.get('status') in stage_statuses
            else record.get('previous_stage_status')
        )
        old_stage_qualification = (
            int(record.get('hill_stage') or 1) > 1
            or previous_status in stage_statuses
        )
        if old_stage_qualification and record.get('score_version') != STAGE_SCORE_VERSION:
            saved_stats = dict(record.get('best_stats') or {})
            saved_stats['sharpe_2y'] = None
            record.update({
                'previous_stage_status': previous_status or record.get('status'),
                'status': 'INTERRUPTED',
                'status_reason': '旧版曾把train Sharpe当P2Y；退回Stage 1刷新真实test Sharpe',
                'hill_stage': 1,
                'stage_batches_used': 0,
                'stage_score': None,
                'score_version': STAGE_SCORE_VERSION,
                'best_stats': saved_stats,
                'retry_kind': 'P2Y_SEMANTICS_FIXED',
                'retry_after': None,
                'candidate_pool_fingerprint': None,
                'blocked_candidate_pool_fingerprint': None,
            })
        if record.get('status') in frozen:
            continue
        stored_code_version = record.get('code_version')
        if record.get('status') == 'FAILED' and stored_code_version != CODE_VERSION:
            record['status'] = 'INTERRUPTED'
            record['status_reason'] = '旧版代码异常已在新代码版本修复，允许一次重新验证'
            record['retry_kind'] = 'CODE_VERSION_CHANGED'
            record['retry_after'] = None
        if record.get('status') == 'OPTIMIZING':
            record['status'] = 'INTERRUPTED'
            record['status_reason'] = '进程重启时恢复陈旧的OPTIMIZING断点'
            record['recovered_at'] = _source_now()
        if (
            record.get('status') == 'BUG_BLOCKED'
            and record.get('code_version')
            and record.get('code_version') != CODE_VERSION
        ):
            record['status'] = 'INTERRUPTED'
            record['status_reason'] = '代码版本变化，允许重新验证原代码异常'
            record['retry_kind'] = 'CODE_VERSION_CHANGED'
        if record.get('status') == 'ELIGIBLE' and (
            number(record.get('sharpe')) is None
            or number(record.get('fitness')) is None
            or float(record.get('sharpe')) <= SOURCE_SHARPE_MIN
            or float(record.get('fitness')) <= SOURCE_FITNESS_MIN
        ):
            record['status'] = 'METRIC_REJECTED'
            record['status_reason'] = '旧候选不满足当前Sharpe/Fitness预筛门槛'
        record.setdefault('field_ids', [])
        record.setdefault('field_metadata', {})
        record.setdefault('field_combination_key', None)
        record.setdefault('combination_rank', None)
        record.setdefault('primary_tower', None)
        record.setdefault('covered_towers', [])
        record.setdefault('pool_status', None)
        record.setdefault('pnl_source', None)
        record.setdefault('pnl_cached_at', None)
        record.setdefault('hill_stage', 1)
        record.setdefault('stage_batches_used', 0)
        record.setdefault('quarter_key', None)
        record.setdefault('objective_version', OBJECTIVE_VERSION)
        record.setdefault('code_version', CODE_VERSION)
        record.setdefault('retry_count', 0)
        record.setdefault('retry_kind', None)
        record.setdefault('candidate_pool_fingerprint', None)
        record.setdefault('blocked_candidate_pool_fingerprint', None)
        record.setdefault('stage_observable_results', None)
        record.setdefault('stage_pass_results', None)
        record.setdefault('stage_logical_batches', None)
        record.setdefault('promotion_window_index', None)
        record.setdefault('promotion_window_closed', False)
        record.setdefault('stage_plan_cursor', int(record.get('template_batch') or 0))
        record.setdefault(
            'stage_post_batches_used', int(
                record.get('template_batches_executed')
                if record.get('template_batches_executed') is not None
                else record.get('stage_batches_used') or 0
            )
        )
        record.setdefault('stage_cache_batches_reused', 0)
        record.setdefault(
            'stage_observed_candidates', int(record.get('stage_observable_results') or 0)
        )
        record.setdefault('stage_branches', [])
        if (
            record.get('objective_version') != OBJECTIVE_VERSION
            and record.get('status') in {'STAGE1_COMPLETE', 'STAGE2_COMPLETE', 'STAGE3_COMPLETE'}
        ):
            stats = dict(record.get('best_stats') or {})
            earliest_stage = 1
            if evaluate_stage_candidate(stats, 1).get('eligible'):
                earliest_stage = 2
            if evaluate_stage_candidate(stats, 2).get('eligible'):
                earliest_stage = 3
            record.update({
                'previous_stage_status': record.get('status'),
                'status': 'INTERRUPTED',
                'status_reason': '旧阶段完成状态按完整门槛重新判定；缓存不再冒充POST预算',
                'hill_stage': earliest_stage,
                'stage_batches_used': 0,
                'stage_plan_cursor': 0,
                'stage_post_batches_used': 0,
                'stage_cache_batches_reused': 0,
                'stage_observed_candidates': 0,
                'stage_branches': [],
                'template_batch': 0,
                'template_batches_executed': 0,
                'objective_version': OBJECTIVE_VERSION,
                'code_version': CODE_VERSION,
                'retry_kind': 'STAGE_ACCOUNTING_V6',
                'retry_after': None,
            })
    return state


def save_source_state(state, path=None):
    """增量提交变化候选和元数据，不再全量重写状态 JSON。"""
    store = getattr(state, '_store', None)
    if store is None:
        source_path = Path(path or HILL_CLIMBING_SOURCE_STATE_PATH)
        store_path = HILL_CLIMBING_SOURCE_DB_PATH if path is None else source_path
        store = SourceStateStore(store_path)
    return store.save(state)


def append_source_event(event, path=None, store=None):
    """按稳定事件键写入 SQLite；相同阻塞/PENDING 不重复膨胀。"""
    payload = {'time': _source_now(), **event}
    stable = {
        key: value for key, value in payload.items()
        if key not in {'time', 'updated_at', 'selected_at'}
    }
    event_key = _source_json_hash(stable)
    source_path = HILL_CLIMBING_SOURCE_DB_PATH if path is None else path
    target_store = store or SourceStateStore(source_path)
    return target_store.append_event(
        event_key, event.get('event', 'SOURCE_EVENT'), payload
    )


def persist_multi_batch(batch_key, pending, source_alpha_id=None, stage=1, store=None):
    """把批次恢复身份写入 SQLite；client history 继续作为结果缓存。"""
    if store is None and not source_alpha_id:
        # 独立单元测试/诊断对象没有源队列身份，不能污染真实运行状态库。
        return False
    payload = dict(pending or {})
    payload.setdefault('source_alpha_id', source_alpha_id)
    payload.setdefault('stage', int(stage or 1))
    payload.setdefault('post_attempts', 1 + int(payload.get('retry_count') or 0))
    target_store = store or SourceStateStore(HILL_CLIMBING_SOURCE_DB_PATH)
    target_store.save_batch(batch_key, payload)
    return True


def import_legacy_processed(state, processed_records):
    """一次性兼容旧 processed_alphas.json，不删除用户原文件。"""
    if state.get('legacy_processed_imported'):
        return False
    for alpha_id, legacy in (processed_records or {}).items():
        if alpha_id in state['candidates']:
            continue
        state['candidates'][alpha_id] = {
            'alpha_id': alpha_id,
            'expression': legacy.get('expr', ''),
            'status': 'OPTIMIZED',
            'status_reason': '从旧 processed_alphas.json 兼容导入',
            'optimized_at': legacy.get('timestamp'),
            'operators': legacy.get('operators', []),
            'legacy_imported': True,
        }
    state['legacy_processed_imported'] = True
    return True


def current_sc_cache_token():
    """以 SC 缓存文件元数据标识版本；缓存更新后允许重新筛选。"""
    parts = []
    cache_dir = Path(SC_PPA_CACHE_DIR)
    if cache_dir.exists():
        for path in sorted(cache_dir.glob('*.pickle')):
            try:
                stat = path.stat()
                parts.append((path.name, stat.st_size, stat.st_mtime_ns))
            except OSError:
                continue
    return _source_json_hash(parts)


def source_candidate_sort_key(record, optimized_expressions):
    """缺塔优先；已观察低 SC 优先，SC 缺失进入低优先探针。"""
    expression = record.get('expression', '')
    if expression and optimized_expressions:
        structural_distance = min(
            calculate_structural_distance(expression, processed_expr)
            for processed_expr in optimized_expressions
        )
    else:
        structural_distance = 1.0
    record['structural_distance'] = structural_distance
    gap_count = len(record.get('gap_scopes') or [])
    created = str(record.get('date_created') or '9999-12-31T23:59:59')
    sc_value = record.get('sc_value')
    sc_missing = not isinstance(sc_value, (int, float)) or isinstance(sc_value, bool)
    if sc_missing:
        sc_value = float('inf')
    return (
        0 if record.get('immediate_stage_branch') else 1,
        -int(record.get('hill_stage') or 1),
        -gap_count,
        1 if int(record.get('no_new_candidate_count') or 0) >= 2 else 0,
        1 if sc_missing else 0, sc_value, created,
        -structural_distance, str(record.get('alpha_id') or ''),
    )


def select_next_source_record(state, excluded_ids=None):
    """从持久化队列中选出下一条源 Alpha，不依赖最近 200 条列表。"""
    excluded_ids = {str(value) for value in (excluded_ids or ())}
    records = list(state.get('candidates', {}).values())
    optimized_expressions = [
        item.get('expression', '') for item in records
        if item.get('status') == 'OPTIMIZED' and item.get('expression')
    ]
    now = datetime.now().astimezone()
    queued = []
    for item in records:
        if str(item.get('alpha_id') or '') in excluded_ids:
            continue
        if item.get('status') not in SOURCE_QUEUE_STATUSES:
            continue
        if (
            item.get('status') == 'BLOCKED_INCOMPLETE_BATCH'
            and item.get('candidate_pool_fingerprint')
            == item.get('blocked_candidate_pool_fingerprint')
        ):
            continue
        if item.get('pool_status') not in {None, 'ACTIVE'}:
            continue
        retry_after = item.get('retry_after')
        if retry_after:
            try:
                if datetime.fromisoformat(retry_after) > now:
                    continue
            except (TypeError, ValueError):
                pass
        queued.append(item)
    if not queued:
        return None
    return min(queued, key=lambda item: source_candidate_sort_key(item, optimized_expressions))


def claim_next_source_record(state):
    """优先领取到期待恢复的批次，再原子领取普通源。"""
    store = getattr(state, '_store', None)
    due_batch = store.due_batch() if store is not None else None
    due_source_id = (
        due_batch.get('source_alpha_id') if isinstance(due_batch, dict) else None
    )
    excluded_ids = set()
    while True:
        selected = None
        if due_source_id and str(due_source_id) not in excluded_ids:
            candidate = state.get('candidates', {}).get(str(due_source_id))
            if candidate and candidate.get('status') in SOURCE_QUEUE_STATUSES:
                selected = candidate
        if selected is None:
            selected = select_next_source_record(state, excluded_ids=excluded_ids)
        if selected is None:
            return None
        selected_at = _source_now()
        if store is None:
            selected.update({
                'status': 'OPTIMIZING', 'selected_at': selected_at,
                'select_count': int(selected.get('select_count') or 0) + 1,
            })
            return selected
        claimed = store.atomic_claim(
            selected.get('alpha_id'), SOURCE_QUEUE_STATUSES, selected_at=selected_at
        )
        if claimed is None:
            # 本地快照陈旧时继续尝试下一条，不能因为一次竞争失败空转一小时。
            excluded_ids.add(str(selected.get('alpha_id') or ''))
            continue
        selected.update(claimed)
        if str(selected.get('alpha_id')) == str(due_source_id):
            selected['_due_batch'] = due_batch
        append_source_event({
            'event': 'SOURCE_CLAIMED', 'alpha_id': selected.get('alpha_id'),
            'selected_at': selected_at,
            'due_batch_priority': str(selected.get('alpha_id')) == str(due_source_id),
        }, store=store)
        return selected


def tighten_saved_sc_threshold(state, sc_max=SOURCE_SC_MAX):
    """用已记录的SC值收紧历史队列，不重新下载PnL或计算SC。"""
    changed_ids = []
    eligible_statuses = SOURCE_QUEUE_STATUSES | SOURCE_PRE_SC_STATUSES | {
        'PRUNED_SIMILAR'
    }
    for record in state.get('candidates', {}).values():
        if record.get('status') not in eligible_statuses:
            continue
        sc_value = record.get('sc_value')
        if isinstance(sc_value, bool) or not isinstance(sc_value, (int, float)) \
                or not math.isfinite(float(sc_value)) or float(sc_value) < sc_max:
            continue
        alpha_id = str(record.get('alpha_id') or '').strip()
        update_source_record(
            state, alpha_id, 'SC_REJECTED',
            f'使用账本SC={float(sc_value):.6f}按当前阈值{sc_max}本地收紧；未重新计算SC',
            sc_threshold_applied=sc_max,
        )
        delete_target_pnl_cache(alpha_id, SC_PPA_CACHE_DIR)
        changed_ids.append(alpha_id)
    return changed_ids


def _core_prune_record_ids(candidates, keep_num):
    """把完整候选适配为 Core.prune 输入，并恢复被保留的 Alpha ID。"""
    field_ids = sorted({
        field for record in candidates
        for field in extract_expression_structure(record['expression'])['data_fields']
    })
    core_records = [
        [
            record.get('alpha_id'), record['expression'], float(record['sharpe']),
            None, record.get('fitness'), None, record.get('date_created'),
            (record.get('settings') or {}).get('decay'),
            (record.get('settings') or {}).get('decay'),
        ]
        for record in candidates
    ]
    kept_expression_counts = Counter()
    for direction, direction_records in (
        ('positive', [rec for rec in core_records if rec[2] >= 0]),
        ('negative', [rec for rec in core_records if rec[2] < 0]),
    ):
        if not direction_records:
            continue
        kept_layers = core_prune(
            direction_records, keep_num=keep_num, field_ids=field_ids or None
        )
        kept_expression_counts.update(
            (direction, layer[0]) for layer in kept_layers
        )

    kept_ids = set()
    for record in sorted(
        candidates,
        key=lambda item: (-abs(float(item['sharpe'])), str(item.get('alpha_id') or '')),
    ):
        direction = 'negative' if float(record['sharpe']) < 0 else 'positive'
        expression_key = (direction, record['expression'])
        if kept_expression_counts[expression_key] > 0:
            kept_ids.add(record['alpha_id'])
            kept_expression_counts[expression_key] -= 1
    return kept_ids, field_ids


def prune_source_candidates_before_sc(state, keep_num=SOURCE_PRUNE_KEEP_NUM):
    """先按缺口塔分类，再复用 Core.prune；被剪候选绝不请求PnL或SC。"""
    candidates = [
        record for record in state.get('candidates', {}).values()
        if record.get('status') in SOURCE_PRE_SC_STATUSES
        and record.get('expression')
        and isinstance(record.get('sharpe'), (int, float))
        and not isinstance(record.get('sharpe'), bool)
    ]
    groups = {}
    for record in candidates:
        gap_key = tuple(sorted(
            str(scope.get('raw_scope') or '')
            for scope in record.get('gap_scopes') or []
            if isinstance(scope, dict) and scope.get('raw_scope')
        ))
        if not gap_key:
            gap_key = (
                f"{record.get('region') or 'UNKNOWN'}/"
                f"D{record.get('delay')}/PYRAMID_DISABLED",
            )
        groups.setdefault(gap_key, []).append(record)

    kept_ids = set()
    all_field_ids = set()
    for group_records in groups.values():
        group_kept_ids, field_ids = _core_prune_record_ids(group_records, keep_num)
        kept_ids.update(group_kept_ids)
        all_field_ids.update(field_ids)

    prune_time = _source_now()
    for record in candidates:
        if record['alpha_id'] in kept_ids:
            record.update({
                'pre_sc_prune_keep_num': keep_num,
                'pre_sc_pruned_at': prune_time,
            })
            continue
        update_source_record(
            state, record['alpha_id'], 'PRUNED_PRE_SC',
            f'获取SC前Core.prune剪枝：同缺口塔及字段组合仅保留Top {keep_num}',
            pre_sc_prune_keep_num=keep_num,
            pre_sc_pruned_at=prune_time,
        )
    return {
        'before': len(candidates), 'kept': len(kept_ids),
        'pruned': len(candidates) - len(kept_ids), 'groups': len(groups),
        'field_ids': sorted(all_field_ids),
    }


def prune_source_queue(state, keep_num=SOURCE_PRUNE_KEEP_NUM):
    """复用 Core.prune 剪掉同字段组合中的弱候选，并保留完整 Alpha 记录。

    Core 的输入是 get_alphas 风格列表，输出只有 ``[表达式, 推荐Decay]``；这里按
    Sharpe 正负方向分别调用，避免相同表达式的返回名额映射到错误方向，再恢复 Alpha ID。
    """
    candidates = [
        record for record in state.get('candidates', {}).values()
        if record.get('status') in {'ELIGIBLE', 'PRUNED_SIMILAR'}
        and record.get('expression')
        and isinstance(record.get('sharpe'), (int, float))
    ]
    if not candidates:
        return {'before': 0, 'kept': 0, 'pruned': 0, 'field_ids': []}

    kept_ids, field_ids = _core_prune_record_ids(candidates, keep_num)

    prune_time = _source_now()
    for record in candidates:
        alpha_id = record['alpha_id']
        prune_fields = sorted(extract_expression_structure(record['expression'])['data_fields'])
        if alpha_id in kept_ids:
            if record.get('status') == 'PRUNED_SIMILAR':
                update_source_record(
                    state, alpha_id, 'ELIGIBLE',
                    f'Core.prune重新选入：同字段组合Top {keep_num}',
                    prune_keep_num=keep_num, prune_fields=prune_fields,
                    pruned_at=prune_time,
                )
            else:
                record.update({
                    'prune_keep_num': keep_num, 'prune_fields': prune_fields,
                    'pruned_at': prune_time,
                })
        elif record.get('status') != 'PRUNED_SIMILAR':
            update_source_record(
                state, alpha_id, 'PRUNED_SIMILAR',
                f'Core.prune剪枝：同字段组合仅保留Sharpe最强Top {keep_num}',
                prune_keep_num=keep_num, prune_fields=prune_fields,
                pruned_at=prune_time,
            )

    return {
        'before': len(candidates), 'kept': len(kept_ids),
        'pruned': len(candidates) - len(kept_ids), 'field_ids': field_ids,
    }


def update_source_record(state, alpha_id, status, reason='', **fields):
    """更新候选当前状态，并把每次状态迁移追加到账本。"""
    record = state.setdefault('candidates', {}).setdefault(alpha_id, {'alpha_id': alpha_id})
    previous_status = record.get('status')
    record.update(fields)
    record.update({
        'alpha_id': alpha_id,
        'status': status,
        'status_reason': reason,
        'updated_at': _source_now(),
    })
    append_source_event({
        'event': 'SOURCE_STATUS',
        'alpha_id': alpha_id,
        'previous_status': previous_status,
        'status': status,
        'reason': reason,
        'record': record,
    })
    return record

def test_diversity_functions():
    """测试表达式结构多样性相关函数"""
    print("=" * 50)
    print("🧪 开始测试表达式结构多样性函数")
    print("=" * 50)

    # Test 1: extract_operators
    expr1 = "signed_power(group_rank(ts_zscore(divide(field1, field2), 66), industry), 1.5)"
    ops1 = extract_operators(expr1)
    assert 'signed_power' in ops1, f"应包含 signed_power, 实际: {ops1}"
    assert 'group_rank' in ops1, f"应包含 group_rank, 实际: {ops1}"
    assert 'ts_zscore' in ops1, f"应包含 ts_zscore, 实际: {ops1}"
    assert 'divide' in ops1, f"应包含 divide, 实际: {ops1}"
    print(f"✅ Test 1 PASS: extract_operators -> {ops1}")

    # Test 2: extract_expression_structure
    s1 = extract_expression_structure(expr1)
    assert s1['depth'] == 4, f"深度应为4, 实际: {s1['depth']}"
    assert 'field1' in s1['data_fields'], f"应包含 field1, 实际: {s1['data_fields']}"
    print(f"✅ Test 2 PASS: structure -> ops={len(s1['operators'])}, depth={s1['depth']}, fields={s1['data_fields']}")

    # Test 3: 相同表达式距离=0
    dist_same = calculate_structural_distance(expr1, expr1)
    assert dist_same == 0.0, f"相同表达式距离应为0, 实际: {dist_same}"
    print(f"✅ Test 3 PASS: 相同表达式距离 = {dist_same}")

    # Test 4: 不同表达式距离>0
    expr2 = "rank(ts_mean(close, 22))"
    dist_diff = calculate_structural_distance(expr1, expr2)
    assert dist_diff > 0, f"不同表达式距离应>0, 实际: {dist_diff}"
    print(f"✅ Test 4 PASS: 不同表达式距离 = {dist_diff:.4f}")

    # Test 5: 结构差异更大的距离更大
    expr3 = "if_else(ts_delta(vol, 10), rank(ret), reverse(rank(ret)))"
    dist_e1_e2 = calculate_structural_distance(expr1, expr2)
    dist_e1_e3 = calculate_structural_distance(expr1, expr3)
    print(f"   expr1 vs expr2 距离: {dist_e1_e2:.4f}")
    print(f"   expr1 vs expr3 距离: {dist_e1_e3:.4f}")
    print(f"✅ Test 5 PASS: 结构距离计算合理")

    # Test 6: select_most_diverse_alpha
    candidates = [
        {'id': 'a1', 'regular': expr1},
        {'id': 'a2', 'regular': expr2},
        {'id': 'a3', 'regular': expr3},
    ]
    processed = {
        'p1': {'expr': expr1, 'operators': extract_operators(expr1)}
    }
    selected = select_most_diverse_alpha(candidates, processed)
    assert selected is not None
    assert selected['id'] != 'a1', "不应选择与已处理结构相同的alpha"
    print(f"✅ Test 6 PASS: 选择了结构差异最大的 alpha: {selected['id']}")

    # Test 7: 空已处理记录时选择第一个
    selected_empty = select_most_diverse_alpha(candidates, {})
    assert selected_empty is not None
    assert selected_empty['id'] == 'a1'
    print(f"✅ Test 7 PASS: 空处理记录时选择第一个: {selected_empty['id']}")

    # Test 8: 无候选时返回None
    result = select_most_diverse_alpha([], processed)
    assert result is None
    print(f"✅ Test 8 PASS: 无候选时返回 None")

    # Test 9: 多候选多已处理时选择最不相似的
    many_candidates = [
        {'id': 'c1', 'regular': 'signed_power(group_rank(ts_zscore(divide(f1, f2), 66), industry), 1.5)'},
        {'id': 'c2', 'regular': 'rank(ts_mean(close, 22))'},
        {'id': 'c3', 'regular': 'if_else(ts_delta(vol, 10), rank(ret), reverse(rank(ret)))'},
        {'id': 'c4', 'regular': 'signed_power(group_rank(ts_zscore(divide(f3, f4), 44), sector), 2.0)'},
    ]
    many_processed = {
        'p1': {'expr': expr1},
        'p2': {'expr': 'signed_power(group_rank(ts_rank(divide(fA, fB), 120), subindustry), 1.0)'}
    }
    selected_div = select_most_diverse_alpha(many_candidates, many_processed)
    print(f"✅ Test 9 PASS: 从4个候选中选择了: {selected_div['id']}")

    print("=" * 50)
    print("🎉 所有测试通过！")
    print("=" * 50)
    return True

# ==================== 持续运行模式：辅助函数结束 ====================

class OptimizerContext:
    def _signal_handler(self, signum, frame):
        # 用户要求 Ctrl+C 直接杀死进程；不等待 PC、429 或任何收尾循环。
        try:
            sys.stderr.write("\n🛑 Ctrl+C：立即终止爬山进程。下次启动将读取已落盘断点。\n")
            sys.stderr.flush()
        finally:
            os._exit(130)

    def __init__(self, alpha_id=None):
        self.alpha_id = alpha_id
        self.auth_lock = threading.Lock()
        self.stop_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)

        self.core_client = self._sign_in()
        # 保留 sess 属性兼容旧代码；网络请求仍统一经过 Core BrainClient。
        self.sess = self.core_client.session
        self.history = self._load_history()
        self.dataset_cache = self._load_dataset_cache()
        self.last_auth_time = time.time()
        self._available_operators = None
        self._field_metadata_cache = {}
        self.sc_status = {}

    def _sign_in(self):
        """复用 Core 登录：自动查找 Password/config.yaml，不重复管理凭据。"""
        print("🔑 正在使用 Core.api.login() 登录...")
        client = core_login()
        if getattr(client, '_authenticated_at', None) is None:
            raise RuntimeError("❌ Core 登录未成功，请检查 Password/config.yaml 或平台认证响应")
        return client

    def _load_history(self):
        history_file = BASE_HISTORY_FILE if not self.alpha_id else os.path.join(OUTPUT_DIR, f'{self.alpha_id}_history_v4.7.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def _load_dataset_cache(self):
        cache_file = BASE_DATASET_CACHE_FILE if not self.alpha_id else os.path.join(OUTPUT_DIR, f'{self.alpha_id}_dataset_cache_v4.7.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_history(self):
        history_file = BASE_HISTORY_FILE if not self.alpha_id else os.path.join(OUTPUT_DIR, f'{self.alpha_id}_history_v4.7.json')
        with open(history_file, 'w') as f: json.dump(self.history, f)

    def save_dataset_cache(self):
        cache_file = BASE_DATASET_CACHE_FILE if not self.alpha_id else os.path.join(OUTPUT_DIR, f'{self.alpha_id}_dataset_cache_v4.7.json')
        with open(cache_file, 'w') as f: json.dump(self.dataset_cache, f)

    def get_available_operators(self):
        """每次进程只读取一次当前账户算子权限；失败保持 UNKNOWN。"""
        if self._available_operators is not None:
            return self._available_operators
        resp = self.core_client.get('/operators', timeout=30)
        if not resp or resp.status_code != 200:
            return None
        try:
            payload = resp.json()
            rows = payload.get('results', []) if isinstance(payload, dict) else payload
            self._available_operators = {
                row.get('name') for row in rows if isinstance(row, dict) and row.get('name')
            }
        except (TypeError, ValueError):
            return None
        return self._available_operators or None

    def get_field_metadata(self, field_name, settings):
        """读取源字段的官方类型和数据集；缓存严格包含研究范围。"""
        scope = (
            settings.get('instrumentType', 'EQUITY'), settings.get('region', 'USA'),
            str(settings.get('delay', 1)), settings.get('universe', 'TOP3000'), field_name,
        )
        if scope in self._field_metadata_cache:
            return self._field_metadata_cache[scope]
        result = get_datafield_metadata(
            self.core_client, [field_name], scope[0], scope[1], scope[3], int(scope[2]),
            catalog=self._field_metadata_cache,
        )
        match = result.get('metadata', {}).get(field_name)
        if not isinstance(match, dict):
            return None
        dataset = match.get('dataset') or {}
        result = {
            'id': field_name,
            'type': match.get('type', 'UNKNOWN'),
            'dataset_id': dataset.get('id', 'UNKNOWN'),
        }
        self._field_metadata_cache[scope] = result
        return result

    def get_alpha_details(self, alpha_id):
        resp = self.core_client.get(f'/alphas/{alpha_id}', timeout=30)
        if resp and resp.status_code == 200:
            return resp.json()
        elif resp:
            logging.error(f"❌ 获取详情失败: Alpha {alpha_id} | 状态码: {resp.status_code} | 响应: {resp.text[:100]}")
        else:
            logging.error(f"❌ 获取详情异常: Alpha {alpha_id} | 请求无返回")
        return None


    def search_dataset_for_field(self, field_name, settings):
        search_scope = {
            'instrumentType': settings.get('instrumentType', 'EQUITY'),
            'region': settings.get('region', 'USA'),
            'delay': str(settings.get('delay', 1)),
            'universe': settings.get('universe', 'TOP3000')
        }
        # 同名字段在不同 Region/Universe 下的可用候选不同，不能跨范围复用。
        cache_key = '|'.join([
            search_scope['instrumentType'], search_scope['region'],
            search_scope['delay'], search_scope['universe'], field_name,
        ])
        if cache_key in self.dataset_cache:
            logging.info(f"  -> 命中本地缓存: {len(self.dataset_cache[cache_key])} 个候选")
            return self.dataset_cache[cache_key]

        try:
            frame = get_datafields(
                self.core_client,
                instrument_type=search_scope['instrumentType'],
                region=search_scope['region'], delay=int(search_scope['delay']),
                universe=search_scope['universe'], search=field_name,
            )
            results = frame.to_dict('records')
            target_dataset_id = None
            original_field_type = 'UNKNOWN'

            for item in results:
                if item['id'] == field_name:
                    original_field_type = item.get('type', 'UNKNOWN')
                    target_dataset_id = item['dataset']['id']
                    break

            if not target_dataset_id and results:
                target_dataset_id = results[0]['dataset']['id']
                original_field_type = results[0].get('type', 'UNKNOWN')

            if not target_dataset_id: return []

            dataset_frame = get_datafields(
                self.core_client,
                instrument_type=search_scope['instrumentType'],
                region=search_scope['region'], delay=int(search_scope['delay']),
                universe=search_scope['universe'], dataset_id=target_dataset_id,
            )
            candidates = [
                {'id': item['id'], 'type': item.get('type', original_field_type)}
                for item in dataset_frame.to_dict('records')
                if item.get('id') and item.get('id') != field_name
            ]

            self.dataset_cache[cache_key] = candidates
            self.save_dataset_cache()
            return candidates
        except Exception as e:
            logging.error(f"搜索字段异常: {e}")
            return []

    def check_factory_shape(self, alpha_id):
        """
        增强版厂字型检查：整合年度统计与 PNL 详情
        """
        try:
            # 低成本优先：有效本地 target_pnls 存在时先做平坦/异常曲线预筛，
            # 并禁止为同一 Alpha 再下载 PnL。
            cached_pnl = load_target_pnl_cache(alpha_id, SC_PPA_CACHE_DIR)
            if not cached_pnl.empty:
                local_records = [
                    [str(index), value]
                    for index, value in cached_pnl[alpha_id].items()
                ]
                if not self._check_consecutive_pnl_values(alpha_id, local_records):
                    return True

            # 1. 检查年度统计 (Yearly Stats)
            url_yearly = f"/alphas/{alpha_id}/recordsets/yearly-stats"
            json_yearly = None
            for _ in range(3):
                resp = self.core_client.get(url_yearly, timeout=30)
                if resp and resp.status_code == 200 and resp.text.strip():
                    try:
                        temp = resp.json()
                        if temp.get('records'):
                            json_yearly = temp
                            break
                    except: pass
                time.sleep(2)

            if json_yearly:
                records = json_yearly.get('records', [])
                non_zero_sharpe_count = sum(1 for r in records if len(r) > 6 and r[6] is not None and abs(float(r[6])) > 1e-6)
                if non_zero_sharpe_count > 0 and non_zero_sharpe_count < 8:
                    logging.info(f"  🟣 [厂字型] 有效年份不足 8 年 ({non_zero_sharpe_count})")
                    return True

            # 2. 本地没有有效缓存时才读取平台 PnL。
            if not cached_pnl.empty:
                return False
            url_pnl = f"/alphas/{alpha_id}/recordsets/pnl"
            for _ in range(3):
                resp_pnl = self.core_client.get(url_pnl, timeout=30)
                if resp_pnl and resp_pnl.status_code == 200:
                    data_pnl = resp_pnl.json().get('records', [])
                    if data_pnl:
                        if not self._check_consecutive_pnl_values(alpha_id, data_pnl):
                            return True
                        break
                time.sleep(2)

            return False

        except Exception as e:
            logging.error(f"增强厂字型检查异常: {e}")
            return False



    def _check_consecutive_pnl_values(self, alpha_id, data, required_streak=250):
        """
        检查是否有连续 required_streak 天的相同非零值 (厂字型核心特征)
        """
        if not data or len(data) < required_streak:
            return True # 数据不足，视为通过

        pnl_values = [row[1] for row in data if len(row) >= 2]
        if not pnl_values: return True
        
        if all(v == 0 for v in pnl_values):
            return False # 全 0 也是无效

        # 检查末端稳定性 (从后往前查)
        end_streak_count = 0
        end_streak_value = pnl_values[-1]
        for i in range(len(pnl_values)-1, -1, -1):
            if pnl_values[i] == end_streak_value:
                end_streak_count += 1
            else:
                break
        
        if end_streak_count >= required_streak:
            logging.info(f"  🟣 [厂字型] 末端连续 {end_streak_count} 天数值相同: {end_streak_value}")
            return False

        # 检查全局连续性
        curr_count = 0
        curr_val = None
        for v in pnl_values:
            if v != 0:
                if v == curr_val:
                    curr_count += 1
                else:
                    curr_val = v
                    curr_count = 1
            else:
                curr_val = None
                curr_count = 0
            
            if curr_count >= required_streak:
                logging.info(f"  🟣 [厂字型] 全局检测到连续 {curr_count} 天相同非零值")
                return False
        return True



class AsyncOptimizer:
    def _signal_handler(self, signum, frame):
        # BrainClient 和优化器都注册同一种硬退出行为，避免初始化顺序影响 Ctrl+C。
        try:
            sys.stderr.write("\n🛑 Ctrl+C：立即终止爬山进程。下次启动将读取已落盘断点。\n")
            sys.stderr.flush()
        finally:
            os._exit(130)

    def __init__(self, alpha_id=None):
        self.alpha_id = alpha_id
        self.auth_lock = threading.Lock() # 添加登录锁
        self.score_lock = threading.Lock() # 恢复分数锁
        self.stop_requested = False # 优雅退出标志位
        
        # 注册信号处理器 (防止重复注册或报错)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
        except Exception:
            pass

        # 在模式1下，先删除旧文件
        if RUN_MODE == 1:
            print("🧹 正在清理旧的日志和检查点文件...")
            self._cleanup_old_files()
        else:
            # RUN_MODE=2 过去没有初始化 INFO 日志，导致持续模式看起来像“卡住”。
            setup_logging(alpha_id)

        budget = self._ensure_backtest_budget().snapshot()
        logging.info(
            f"🧮 每日回测额度: 已用={budget['used']}，剩余={budget['remaining']}，"
            f"上限={budget['limit']}，重置={budget['reset_at']}"
        )

        print("🔑 正在尝试登录 WorldQuant Brain 平台...")
        self.client = OptimizerContext(alpha_id)
        print("🔓 登录成功！")
        
        # Core.get_sc_check 自主管理统一缓存；不再在热路径下载一份重复 OS 池。
        self.os_pool = None

        self.best_expr = None
        self.best_score = -9999
        self.best_base_score = -9999  # 新增：记录不含 PC 奖惩的基础分数
        self.settings = None
        self.history_cache = {}
        self.best_alpha_id = None  # 添加跟踪最佳Alpha ID的属性
        self.initial_score = None  # 添加初始分数属性
        self.initial_alpha_id = None  # 添加初始Alpha ID属性
        self.source_expression = None
        self.source_record = {}
        self.baseline_refresh_status = 'NOT_REQUIRED'
        self.baseline_alpha_id = None
        self.best_pc = None  # 记录当前最优解的 PC 值 (None表示尚未获取)
        self.best_stats = {}  # 记录最优解的详细统计指标
        self.score_components = {}
        self.score_penalties = {}
        self.score_version = STAGE_SCORE_VERSION
        self.hill_stage = 1 if CONTINUOUS_MODE else 3
        self.research_metrics = Counter()
        self._research_metric_seen = {}
        self._last_reported_parent_count = 0
        self._stage_result_seen = set()
        self.stage_observable_results = 0
        self.stage_pass_results = 0
        self.stage_pass_candidates = []
        # 新增：记录当前优化位置（包括字段和批次）
        self.current_position = {
            'data_field': START_OPTIMIZATION_FROM['data_field'],
            'time_window': START_OPTIMIZATION_FROM['time_window'],
            'number': START_OPTIMIZATION_FROM['number'],
            'group': START_OPTIMIZATION_FROM['group'],
            'operator': START_OPTIMIZATION_FROM['operator'],
            'batch_offset': 0,  # 批次偏移量
            'template_batch': 0,  # 广度模板探索批次（0～8）
            'neutralization': 0,  # 中性化参数优化位置
            'decay': 0,  # 衰减参数优化位置
            'template_batches_executed': 0,
            'stage_plan_cursor': 0,
            'stage_post_batches_used': 0,
            'stage_cache_batches_reused': 0,
            'stage_observed_candidates': 0,
            'stage_branches': [],
            'margin_batches_executed': 0,
            'attempted_routes': [],
            'active_route': None,
            'candidate_pool_fingerprint': None,
        }

    def _cleanup_old_files(self):
        """清理旧的检查点和日志文件"""
        logging.info(f"清理旧文件 (扫描目录: {OUTPUT_DIR})...")
        patterns = [r'.*_v4\.[67]\.json$', r'.*_v4\.[67]\.log$', r'checkpoint.*\.json$', r'history.*\.json$']
        try:
            for fname in os.listdir(OUTPUT_DIR):
                if any(re.match(p, fname) for p in patterns):
                    full_path = os.path.join(OUTPUT_DIR, fname)
                    if is_file_older_than_days(full_path, 2):
                        try:
                            # 尝试关闭句柄
                            for handler in logging.root.handlers[:]:
                                handler.close()
                                logging.root.removeHandler(handler)
                            os.remove(full_path)
                            logging.info(f"已删除旧文件: {full_path}")
                        except: pass
        except Exception as e:
            logging.warning(f"清理文件时出错: {e}")

        # 重新初始化日志配置
        setup_logging(self.alpha_id)

    def _assess_stats(self, stats):
        return evaluate_stage_candidate(stats, getattr(self, 'hill_stage', 3))

    def _metric(self, name, amount=1):
        metrics = getattr(self, 'research_metrics', None)
        if metrics is None:
            metrics = Counter()
            self.research_metrics = metrics
        metrics[name] += amount

    def _metric_once(self, name, key, amount=1):
        seen = getattr(self, '_research_metric_seen', None)
        if seen is None:
            seen = {}
            self._research_metric_seen = seen
        bucket = seen.setdefault(name, set())
        if key in bucket:
            return False
        bucket.add(key)
        self._metric(name, amount)
        return True

    def _post_cooldown_snapshot(self):
        budget = self._ensure_backtest_budget()
        method = getattr(budget, 'post_cooldown_snapshot', None)
        snapshot = method() if callable(method) else None
        return snapshot if isinstance(snapshot, dict) else {
            'active': False, 'retry_after': None, 'remaining_seconds': 0.0,
        }

    def _log_research_metrics(self):
        metrics = getattr(self, 'research_metrics', Counter())
        parents = metrics.get('logical_parent_batches', 0)
        if not parents or parents % 10 or parents == getattr(
            self, '_last_reported_parent_count', 0
        ):
            return
        self._last_reported_parent_count = parents
        candidates = metrics.get('candidate_slots', 0)
        core_observable = metrics.get('core_observable_candidates', 0)
        p2y_observable = metrics.get('p2y_observable_candidates', 0)
        gate_observable = metrics.get('gate_observable_candidates', 0)
        improvements = metrics.get('gate_improvements', 0)
        budget = self._ensure_backtest_budget().snapshot()
        network_metrics = getattr(
            _core_client(self.client), 'request_metrics', {}
        ) or {}
        state_store = getattr(self, 'source_state_store', None)
        scheduler_counts = (
            state_store.operational_counts() if state_store is not None else {}
        )
        per_thousand = (
            1000 * metrics.get('stage3_full_pass', 0) / candidates if candidates else 0.0
        )
        logging.info(
            '📊 每10逻辑父批结果报表 | 逻辑批=%s 实际POST=%s 额度=%s/%s '
            '核心/P2Y/全门槛观察率=%.1f%%/%.1f%%/%.1f%% '
            'Stage1/2/3 PASS-FAIL-PENDING=%s/%s/%s 硬门槛缺口改善率=%.1f%% '
            '缓存命中=%s 重复调度=%s 跳过SC=%s 快速晋级=%s '
            '429/10054/401/全局冷却=%s/%s/%s/%s '
            'Stage3完整通过=%s 每千回测完整通过=%.3f',
            parents, metrics.get('actual_post_attempts', 0), budget['used'], budget['limit'],
            min(100.0, 100 * core_observable / max(1, candidates)),
            min(100.0, 100 * p2y_observable / max(1, candidates)),
            min(100.0, 100 * gate_observable / max(1, candidates)),
            '/'.join(str(metrics.get(f'stage1_gate_{status}', 0))
                     for status in ('pass', 'fail', 'pending')),
            '/'.join(str(metrics.get(f'stage2_gate_{status}', 0))
                     for status in ('pass', 'fail', 'pending')),
            '/'.join(str(metrics.get(f'stage3_gate_{status}', 0))
                     for status in ('pass', 'fail', 'pending')),
            100 * improvements / max(1, gate_observable), metrics.get('cache_hits', 0),
            metrics.get('duplicate_schedules', 0), metrics.get('skipped_sc_requests', 0),
            metrics.get('fast_lane_promotions', 0), metrics.get('rate_limits', 0),
            network_metrics.get('connection_resets', metrics.get('connection_resets', 0)),
            network_metrics.get('auth_401', metrics.get('auth_401', 0)),
            metrics.get('global_cooldowns', 0),
            metrics.get('stage3_full_pass', 0), per_thousand,
        )
        logging.info(
            '🧭 SQLite调度去重 | 唯一源=%s 唯一批次=%s 源领取=%s 重复领取=%s '
            '连续无新候选源=%s 批次POST累计=%s 不足8阻塞=%s 只读未观察=%s '
            '唯一候选=%s',
            scheduler_counts.get('unique_sources', 0),
            scheduler_counts.get('unique_batches', 0),
            scheduler_counts.get('source_selections', 0),
            scheduler_counts.get('repeat_source_selections', 0),
            scheduler_counts.get('no_new_candidate_sources', 0),
            scheduler_counts.get('batch_post_attempts', 0),
            scheduler_counts.get('incomplete_batches', 0),
            scheduler_counts.get('read_only_unobserved', 0),
            len(getattr(self, '_research_metric_seen', {}).get('candidate_slots', set())),
        )
        logging.info(
            '🧪 Stage1分批 | B1/B2/B3/B4运行=%s/%s/%s/%s '
            'PASS批=%s/%s/%s/%s 立即交接1→2/2→3=%s/%s '
            '分支创建/合并=%s/%s 缓存命中=%s',
            *(metrics.get(f'stage1_batch_{index}_runs', 0) for index in range(1, 5)),
            *(metrics.get(f'stage1_batch_{index}_pass_batches', 0) for index in range(1, 5)),
            metrics.get('stage1_to_stage2_immediate', 0),
            metrics.get('stage2_to_stage3_immediate', 0),
            metrics.get('stage_branches_created', 0),
            metrics.get('stage_branch_merges', 0),
            metrics.get('cache_hits', 0),
        )
        events = load_template_usage()
        latest = {}
        for event in events:
            if event.get('template_learning_version') != TEMPLATE_LEARNING_VERSION:
                continue
            key = event.get('candidate_key') or '|'.join((
                str(event.get('run_id') or ''), str(event.get('template_id') or ''),
                str(event.get('variant_id') or ''),
            ))
            latest[key] = event
        complete_events = [
            event for event in latest.values()
            if event.get('status') in {'COMPLETE', 'CACHE_HIT'}
            and number(event.get('sharpe')) is not None
            and number(event.get('sharpe_2y')) is not None
        ]
        quality_groups = {}
        for event in complete_events:
            quality_groups.setdefault((
                str(event.get('region') or 'UNKNOWN'),
                str(event.get('category') or 'UNKNOWN'),
            ), []).append(event)

        def quantile(values, fraction):
            ordered = sorted(values)
            if not ordered:
                return None
            position = (len(ordered) - 1) * fraction
            lower = int(math.floor(position))
            upper = int(math.ceil(position))
            if lower == upper:
                return ordered[lower]
            return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

        for (region, category), group in sorted(quality_groups.items()):
            sharpes = [number(item.get('sharpe')) for item in group]
            p2ys = [number(item.get('sharpe_2y')) for item in group]
            logging.info(
                '📈 模板范围 %s×%s 完整=%s | Sharpe P25/P50/P75/均值=%.3f/%.3f/%.3f/%.3f '
                '| P2Y P25/P50/P75/均值=%.3f/%.3f/%.3f/%.3f',
                region, category, len(group),
                quantile(sharpes, .25), quantile(sharpes, .5), quantile(sharpes, .75),
                sum(sharpes) / len(sharpes),
                quantile(p2ys, .25), quantile(p2ys, .5), quantile(p2ys, .75),
                sum(p2ys) / len(p2ys),
            )
        template_rows = summarize_template_usage(summary_path=None)
        for role in ('SIGNAL_BUILD', 'STABILITY_CONTROL', 'MARGIN_REPAIR', 'FINAL_REPAIR'):
            rows = [row for row in template_rows if row.get('template_role') == role]
            complete = sum(int(row.get('complete_count') or 0) for row in rows)
            improved = sum(int(row.get('improved_count') or 0) for row in rows)
            retained = sum(int(row.get('retained_gate_count') or 0) for row in rows)
            best = next((row for row in rows if row.get('template_state') in {
                'CHAMPION', 'PROMISING',
            }), None)
            logging.info(
                '🧩 模板角色 %s | 完整=%s 改善率=%.1f%% 保门槛率=%.1f%% '
                '最佳=%s@%s 参数=%s',
                role, complete, 100 * improved / max(1, complete),
                100 * retained / max(1, complete),
                (best or {}).get('template_id', 'NONE'),
                (best or {}).get('template_version', '-'),
                (best or {}).get('resolved_params', '{}'),
            )
        logging.info(
            '🧾 正式模板额度占比=%.1f%% SC/PC修复成功=%s/%s '
            '字段/权限/PENDING拒绝=%s/%s/%s',
            min(100.0, 100 * metrics.get('formal_template_simulated_slots', 0) / max(1, candidates)),
            metrics.get('sc_repair_success', 0), metrics.get('pc_repair_success', 0),
            metrics.get('template_field_rejected', 0),
            metrics.get('template_permission_rejected', 0),
            metrics.get('template_pending', 0),
        )
        margin_events = [
            event for event in latest.values()
            if event.get('repair_goal') == 'MARGIN'
            and event.get('status') in {'COMPLETE', 'CACHE_HIT'}
            and number(event.get('margin_bp_delta')) is not None
        ]
        margin_deltas = [number(event.get('margin_bp_delta')) for event in margin_events]
        retained = sum(event.get('non_margin_gates_retained') is True for event in margin_events)
        crossed = sum(event.get('margin_threshold_crossed') is True for event in margin_events)
        logging.info(
            '🛠️ Margin修复 | Ready S1/S2/S3=%s/%s/%s 批次=%s 完整=%s '
            '跨门槛=%s 非Margin保留率=%.1f%% Δbp P25/P50/P75=%s/%s/%s '
            '换手失效=%s Stage3数字通过后SC请求=%s',
            metrics.get('stage1_margin_repair_ready', 0),
            metrics.get('stage2_margin_repair_ready', 0),
            metrics.get('stage3_margin_repair_ready', 0),
            metrics.get('margin_repair_batches', 0), len(margin_events), crossed,
            100 * retained / max(1, len(margin_events)),
            self._score_text(quantile(margin_deltas, .25), '.2f'),
            self._score_text(quantile(margin_deltas, .5), '.2f'),
            self._score_text(quantile(margin_deltas, .75), '.2f'),
            metrics.get('margin_turnover_invalid', 0),
            metrics.get('stage3_numeric_pass_sc_requests', 0),
        )

    @staticmethod
    def _stats_from_details(details, existing=None):
        details = details if isinstance(details, dict) else {}
        is_stats = details.get('is') if isinstance(details.get('is'), dict) else {}
        checks = is_stats.get('checks') if isinstance(is_stats.get('checks'), list) else []
        platform_pass = (
            True if checks and all(check.get('result') == 'PASS' for check in checks)
            else False if any(check.get('result') == 'FAIL' for check in checks)
            else None
        )
        stats = dict(existing or {})
        stats.update({
            'sharpe': is_stats.get('sharpe'),
            'fitness': is_stats.get('fitness'),
            'margin': is_stats.get('margin'),
            'turnover': is_stats.get('turnover'),
            'sharpe_2y': _two_year_sharpe(details),
            'passed': platform_pass,
            'check_failures': [
                check.get('name') or check.get('message') or 'UNKNOWN'
                for check in checks if check.get('result') != 'PASS'
            ],
        })
        return stats

    def _apply_score(self, result):
        """统一重算新旧缓存；门槛状态不再把可比较的连续分数归零。"""
        if not isinstance(result, dict):
            return result
        assessment = self._assess_stats(result.get('stats', {}))
        result['quality_score'] = assessment.get('score')
        result['score'] = assessment.get('score')
        result['score_version'] = STAGE_SCORE_VERSION
        result['score_components'] = assessment.get('components', {})
        result['score_penalties'] = assessment.get('penalties', {})
        result['stage_gate'] = assessment.get('gate', {})
        gate = result['stage_gate']
        result['gate_status'] = gate.get('status', 'PENDING')
        scoring_missing = assessment.get('missing', []) or []
        result['score_status'] = (
            'OK' if number(assessment.get('score')) is not None
            else 'PENDING_SC' if scoring_missing == ['sc']
            else 'PENDING_METRICS'
        )
        stats = result.get('stats', {}) or {}
        margin_route = evaluate_margin_repair_readiness(
            stats, getattr(self, 'hill_stage', 1)
        )
        if margin_route.get('ready'):
            repair_route = 'MARGIN_REPAIR'
        elif (
            margin_route.get('non_margin_passed')
            and margin_route.get('margin_passed')
            and number(stats.get('sc')) is None
        ):
            repair_route = 'SC_REPAIR'
        elif (
            int(getattr(self, 'hill_stage', 1)) >= 3
            and number(stats.get('sc')) is not None
            and number(stats.get('pc')) is None
        ):
            repair_route = 'PC_REPAIR'
        else:
            repair_route = 'NONE'
        result['repair_route'] = repair_route
        result['candidate_status'] = (
            'FAIL' if gate.get('failed')
            else 'PASS' if gate.get('passed')
            else 'PENDING'
        )
        return result

    @staticmethod
    def _score_text(value, spec='.4f'):
        value = number(value)
        return format(value, spec) if value is not None else 'PENDING'

    def _set_refreshed_baseline(self, result):
        """用首批原表达式的 P2Y 结果建立可比较基线。"""
        if not isinstance(result, dict) or result.get('status') not in {
            None, 'COMPLETE', 'CACHE_HIT'
        }:
            pending_status = (
                'PENDING_RATE_LIMIT'
                if getattr(self, 'template_retry_after', None)
                else 'RESULTS_UNOBSERVED'
            )
            self.baseline_refresh_status = pending_status
            self.current_position['baseline_refresh_status'] = pending_status
            return False
        stats = dict(result.get('stats') or {})
        source_sc = number((getattr(self, 'source_record', {}) or {}).get('sc_value'))
        if number(stats.get('sc')) is None and source_sc is not None:
            stats['sc'] = source_sc
            stats['sc_status'] = 'SC_REUSED_SOURCE'
        scored = self._apply_score({**result, 'stats': stats})
        if number(stats.get('sharpe_2y')) is None or number(scored.get('score')) is None:
            self.baseline_refresh_status = 'PENDING_STAGE_SCORE'
            self.current_position['baseline_refresh_status'] = self.baseline_refresh_status
            return False
        with self.score_lock:
            self.best_expr = self.source_expression
            self.best_alpha_id = scored.get('alpha_id') or self.best_alpha_id
            self.baseline_alpha_id = self.best_alpha_id
            self.initial_alpha_id = self.best_alpha_id
            self.best_stats = stats
            self.best_score = scored['score']
            self.best_base_score = scored['score']
            self.initial_score = scored['score']
            self.score_components = scored.get('score_components', {})
            self.score_penalties = scored.get('score_penalties', {})
            self.score_version = STAGE_SCORE_VERSION
        result.update(scored)
        self.baseline_refresh_status = 'COMPLETE'
        self.current_position['baseline_refresh_status'] = 'COMPLETE'
        self.current_position['baseline_alpha_id'] = self.baseline_alpha_id
        logging.info(
            f'🧭 P2Y基线刷新完成: Alpha={self.baseline_alpha_id} '
            f'Score={self._score_text(self.initial_score)}'
        )
        return True

    def _target_metrics_complete(self, stats, target_metrics):
        required = {
            name for name in (target_metrics or ())
            if name in {'sharpe', 'fitness', 'sharpe_2y', 'margin', 'turnover', 'sc', 'pc'}
        }
        return bool(required) and all(number((stats or {}).get(name)) is not None for name in required)

    def _gate_progress_improved(self, stats, candidate=None):
        """只比较完整目标指标；缺指标变成有值本身不是模板改善。"""
        baseline = getattr(self, 'template_baseline_gate', {}) or {}
        baseline_stats = getattr(self, 'template_baseline_stats', {}) or {}
        targets = (candidate or {}).get('target_metrics') or (
            'sharpe', 'fitness', 'sharpe_2y', 'margin', 'turnover', 'sc'
        )
        if not (
            self._target_metrics_complete(baseline_stats, targets)
            and self._target_metrics_complete(stats, targets)
        ):
            return False
        gate = evaluate_stage_candidate(
            stats, getattr(self, 'hill_stage', 1)
        ).get('gate', {})
        if not gate.get('observable'):
            return False
        current_level = int(gate.get('gate_level') or 0)
        baseline_level = int(baseline.get('gate_level') or 0)
        if current_level > baseline_level:
            return True
        if current_level != baseline_level:
            return False
        deficit = number(gate.get('gate_deficit_total'))
        baseline_deficit = number(baseline.get('gate_deficit_total'))
        if (
            deficit is not None and baseline_deficit is not None
            and baseline_deficit - deficit >= STAGE1_GATE_DEFICIT_IMPROVEMENT_MIN
        ):
            return True
        if baseline_deficit != 0 or deficit != 0:
            return False
        def delta(name, reverse=False):
            before = number(baseline_stats.get(name))
            after = number(stats.get(name))
            if before is None or after is None:
                return float('-inf')
            return before - after if reverse else after - before

        improvements = {
            'sharpe': delta('sharpe'), 'fitness': delta('fitness'),
            'sharpe_2y': delta('sharpe_2y'), 'margin': delta('margin'),
            'sc': delta('sc', reverse=True), 'pc': delta('pc', reverse=True),
        }
        thresholds = {
            'sharpe': 0.05, 'fitness': 0.05, 'sharpe_2y': 0.05,
            'margin': 0.0001, 'sc': 0.02, 'pc': 0.03,
        }
        return any(
            name in targets and improvements[name] >= threshold
            for name, threshold in thresholds.items()
        )

    def _retains_previous_gates(self, stats):
        """候选不能以破坏已经通过的门槛换取另一项改善。"""
        baseline = getattr(self, 'template_baseline_gate', {}) or {}
        gate = evaluate_stage_candidate(
            stats, getattr(self, 'hill_stage', 1)
        ).get('gate', {})
        if not gate.get('observable'):
            return False
        baseline_deficits = baseline.get('gate_deficits', {}) or {}
        result_deficits = gate.get('gate_deficits', {}) or {}
        return (
            int(gate.get('gate_level') or 0) >= int(baseline.get('gate_level') or 0)
            and all(
                result_deficits.get(name, 1.0) == 0
                for name, value in baseline_deficits.items() if value == 0
            )
        )

    def _passes_final_correlations(self, result):
        """第三阶段只把明确SC/PC合格者作为新的最佳解。"""
        if getattr(self, 'hill_stage', 3) < 3:
            return True
        stats = result.get('stats', {})
        alpha_id = result.get('alpha_id')
        sc_value = number(stats.get('sc'))
        if sc_value is None:
            sc_value = get_sc_check(_core_client(self.client), alpha_id) if alpha_id else None
            stats['sc'] = sc_value
        sc_value = number(sc_value)
        if sc_value is None or sc_value >= STAGE_SC_LIMIT:
            return False
        pc_value = number(stats.get('pc'))
        if pc_value is None:
            pc_value = get_pc_check(
                _core_client(self.client), alpha_id, max_attempts=40,
                should_stop=lambda: self.stop_requested,
            ) if alpha_id else None
            stats['pc'] = pc_value
        pc_value = number(pc_value)
        passed = pc_value is not None and pc_value < STAGE_PC_LIMIT
        if passed and alpha_id:
            seen = getattr(self, '_stage3_pass_ids', set())
            if alpha_id not in seen:
                seen.add(alpha_id)
                self._stage3_pass_ids = seen
                self._metric('stage3_full_pass')
        return passed

    def _is_better_result(self, result):
        result = self._apply_score(result)
        gate_passed = result.get('stage_gate', {}).get('passed')
        if getattr(self, 'hill_stage', 3) >= 3 and gate_passed and not self._passes_final_correlations(result):
            return False
        result = self._apply_score(result)
        candidate_score = result.get('score')
        current_assessment = self._assess_stats(self.best_stats)
        current_score = current_assessment.get('score')
        if current_assessment.get('eligible') and getattr(self, 'hill_stage', 3) >= 3:
            current_result = {'alpha_id': self.best_alpha_id, 'stats': self.best_stats}
            if self._passes_final_correlations(current_result):
                current_scored = self._apply_score(current_result)
                current_score = current_scored['score']
        better = is_candidate_better(
            result.get('stats', {}), candidate_score, self.best_stats, current_score,
            getattr(self, 'hill_stage', 1),
        )
        return better

    def _adopt_result(self, expression, result, alpha_id, settings=None):
        if result.get('status') not in {'COMPLETE', 'CACHE_HIT', None}:
            return False
        if not self._is_better_result(result):
            return False
        with self.score_lock:
            self.best_expr = expression
            self.best_score = result['score']
            self.best_base_score = result['score']
            self.best_alpha_id = result.get('alpha_id') or self.best_alpha_id
            self.best_stats = result.get('stats', {})
            self.best_pc = self.best_stats.get('pc')
            self.score_components = result.get('score_components', {})
            self.score_penalties = result.get('score_penalties', {})
            if settings is not None:
                self.settings = settings
        self.save_checkpoint(alpha_id)
        return True

    def _select_batch_challenger(self, items):
        """SC后排序；第三阶段只对仍可能上位者按序查询PC。"""
        ordered = sorted(items, key=lambda item: (
            number(item[1].get('score'))
            if number(item[1].get('score')) is not None else float('-inf')
        ), reverse=True)
        if getattr(self, 'hill_stage', 3) < 3:
            return max(
                ordered,
                key=cmp_to_key(lambda left, right: compare_candidates(
                    left[1].get('stats', {}), left[1].get('score', 0),
                    right[1].get('stats', {}), right[1].get('score', 0),
                    getattr(self, 'hill_stage', 1),
                )),
            )
        best = None
        for expression, result in ordered:
            if best and result.get('score', 0) <= best[1].get('score', 0) - STAGE_SCORE_MIN_IMPROVEMENT:
                break
            if not self._passes_final_correlations(result):
                continue
            result = self._apply_score(result)
            if best is None or compare_candidates(
                result.get('stats', {}), result.get('score', 0),
                best[1].get('stats', {}), best[1].get('score', 0),
                getattr(self, 'hill_stage', 1),
            ) > 0:
                best = (expression, result)
        return best

    def load_checkpoint(self, alpha_id):
        """为特定Alpha ID加载检查点"""
        checkpoint_file = os.path.join(OUTPUT_DIR, f'{alpha_id}_checkpoint_v4.7.json')
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    
                    # 强校验：比对 initial_alpha_id 而不是当前最优 alpha_id
                    # 这样即使爬山过程中 ID 变了，只要是同一个起始任务，就能续爬
                    saved_initial_id = data.get('initial_alpha_id')
                    
                    # 兼容旧版 checkpoint (如果没有 initial_alpha_id，尝试用 alpha_id 兜底，但可能会误判)
                    if not saved_initial_id:
                        saved_initial_id = data.get('alpha_id')

                    if saved_initial_id != alpha_id:
                        logging.warning(f"⚠️ 检查点初始 ID ({saved_initial_id}) 与目标 ID ({alpha_id}) 不匹配，将重置进度！")
                        return False

                    self.best_expr = data['expr']
                    self.best_score = data['score']
                    self.best_base_score = data.get('base_score', self.best_score)
                    self.settings = normalize_simulation_settings(data['settings'])
                    self.best_alpha_id = data.get('alpha_id', None)
                    self.initial_score = data.get('initial_score', None)
                    self.initial_alpha_id = data.get('initial_alpha_id', None)
                    self.source_expression = data.get('source_expression') or data.get('expr')
                    self.baseline_refresh_status = data.get(
                        'baseline_refresh_status',
                        data.get('current_position', {}).get(
                            'baseline_refresh_status', 'NOT_REQUIRED'
                        ),
                    )
                    self.baseline_alpha_id = data.get('baseline_alpha_id')
                    self.best_pc = data.get('best_pc', None) # 加载保存的 PC 值
                    self.best_stats = data.get('best_stats', {})
                    self.score_components = data.get('score_components', {})
                    self.score_penalties = data.get('score_penalties', {})
                    self.score_version = data.get('score_version')
                    # 加载当前优化位置（包括字段和批次）
                    self.current_position = data.get('current_position', self.current_position)
                    self.current_position.setdefault(
                        'stage_plan_cursor', int(self.current_position.get('template_batch') or 0)
                    )
                    self.current_position.setdefault(
                        'stage_post_batches_used', int(
                            self.current_position.get('template_batches_executed') or 0
                        )
                    )
                    self.current_position.setdefault('stage_cache_batches_reused', 0)
                    self.current_position.setdefault('stage_observed_candidates', 0)
                    self.current_position.setdefault('stage_branches', [])
                    saved_stage = int(data.get('hill_stage') or 1)
                    if saved_stage != int(getattr(self, 'hill_stage', saved_stage)):
                        self.current_position.update({
                            'template_batch': 0,
                            'template_batches_executed': 0,
                            'stage_plan_cursor': 0,
                            'stage_post_batches_used': 0,
                            'stage_cache_batches_reused': 0,
                            'stage_observed_candidates': 0,
                            'stage_branches': [],
                            'margin_batches_executed': 0,
                            'attempted_routes': [],
                            'active_route': None,
                            'candidate_pool_fingerprint': None,
                            'blocked_candidate_pool_fingerprint': None,
                            'probe_stopped_no_improvement': False,
                            'stage_settled_candidate_exhausted': False,
                        })
                        self.baseline_refresh_status = 'NOT_REQUIRED'
                        self.current_position['baseline_refresh_status'] = 'NOT_REQUIRED'
                        logging.info(
                            f'阶段从Stage {saved_stage}切换到Stage {self.hill_stage}；'
                            '仅重置阶段批次位置，保留当前最佳Alpha和完整指标。'
                        )
                    if self.score_version != STAGE_SCORE_VERSION:
                        self.best_stats = dict(self.best_stats or {})
                        self.best_stats['sharpe_2y'] = None
                        self.best_score = None
                        self.best_base_score = None
                        self.initial_score = None
                        self.baseline_refresh_status = 'REQUIRED'
                        self.current_position.update({
                            'template_batch': 0,
                            'template_batches_executed': 0,
                            'stage_plan_cursor': 0,
                            'stage_post_batches_used': 0,
                            'stage_cache_batches_reused': 0,
                            'stage_observed_candidates': 0,
                            'stage_branches': [],
                            'margin_batches_executed': 0,
                            'attempted_routes': [],
                            'active_route': None,
                            'candidate_pool_fingerprint': None,
                            'blocked_candidate_pool_fingerprint': None,
                            'baseline_refresh_status': 'REQUIRED',
                        })
                        logging.warning(
                            '旧检查点P2Y口径不可比较；保留表达式但清空阶段分，'
                            '从原式test Sharpe刷新基线。'
                        )
                    logging.info(f"断点续传: Score={self.best_score}, Alpha ID={self.best_alpha_id}, PC={self.best_pc}")
                    return True
            except Exception as e:
                logging.error(f"加载检查点失败: {e}")
                pass
        return False

    def save_checkpoint(self, alpha_id):
        """为特定Alpha ID保存检查点"""
        checkpoint_file = os.path.join(OUTPUT_DIR, f'{alpha_id}_checkpoint_v4.7.json')
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'expr': self.best_expr,
                'score': self.best_score,
                'base_score': self.best_base_score,
                'settings': self.settings,
                'alpha_id': self.best_alpha_id,
                'best_pc': self.best_pc, # 保存当前 PC 值
                'best_stats': self.best_stats,
                'score_version': STAGE_SCORE_VERSION,
                'score_components': self.score_components,
                'score_penalties': self.score_penalties,
                'objective_version': OBJECTIVE_VERSION,
                'code_version': CODE_VERSION,
                'gate_level': self._assess_stats(self.best_stats).get('gate', {}).get('gate_level'),
                'gate_deficits': self._assess_stats(self.best_stats).get('gate', {}).get('gate_deficits', {}),
                'candidate_pool_fingerprint': self.current_position.get('candidate_pool_fingerprint'),
                'hill_stage': getattr(self, 'hill_stage', 3),
                'target_alpha_ids': TARGET_ALPHA_IDS,
                'initial_score': self.initial_score,
                'initial_alpha_id': self.initial_alpha_id, # <--- 核心修复：必须存这个！
                'source_expression': self.source_expression,
                'baseline_refresh_status': self.baseline_refresh_status,
                'baseline_alpha_id': self.baseline_alpha_id,
                'admission_profile': SOURCE_ADMISSION_PROFILE,
                'current_position': self.current_position
            }, f)





    def evaluate_batch(self, expr_list, settings=None, force_run=()):
        """通过 Core Multi-Simulation 评估严格 8 条表达式。"""
        uses_default_settings = settings is None
        if settings is None:
            settings = self.settings
        settings = normalize_simulation_settings(settings)
        if uses_default_settings or self.settings is None:
            self.settings = settings

        force_keys = {_cache_key(expr, settings) for expr in force_run}
        to_run = []
        results = {}
        pending_batches = self.client.history.setdefault('__pending_multi__', {})
        pending_expression_keys = {
            _cache_key(expr, settings)
            for pending in pending_batches.values()
            if isinstance(pending, dict) and pending.get('settings') == settings
            for expr in pending.get('expressions', [])
        }

        seen_keys = set()
        for expr in expr_list:
            # 核心修复：缓存键应包含 settings 以支持参数优化回测
            h = _cache_key(expr, settings)
            if h in seen_keys:
                logging.info(f"  -> 跳过批内等价表达式: {expr}")
                continue
            seen_keys.add(h)
            
            if h not in force_keys and h in self.client.history and h not in pending_expression_keys:
                self._metric('cache_hits')
                cached_data = self.client.history[h]
                if isinstance(cached_data, dict):
                    results[expr] = self._apply_score(dict(cached_data))
                    if results[expr].get('status') in {None, 'COMPLETE'}:
                        results[expr]['status'] = 'CACHE_HIT'
                else:
                    # 兼容旧版本
                    results[expr] = {'score': cached_data, 'url': 'Legacy Cache Hit'}
                continue

            # 兼容并迁移 v4.7 旧缓存键，避免升级后把同一公式重跑一遍。
            legacy_h = _legacy_cache_key(expr, settings)
            if (
                h not in force_keys
                and h not in pending_expression_keys
                and legacy_h in self.client.history
            ):
                cached_data = self.client.history[legacy_h]
                self.client.history[h] = cached_data
                results[expr] = self._apply_score(dict(cached_data)) if isinstance(cached_data, dict) else {
                    'score': cached_data, 'url': 'Legacy Cache Hit'
                }
                if isinstance(results[expr], dict) and results[expr].get('status') in {None, 'COMPLETE'}:
                    results[expr]['status'] = 'CACHE_HIT'
                continue

            to_run.append(expr)

        if not to_run: return results

        # expression_checker 是语法门槛，不代表字段/权限/性能通过。
        checked = batch_verify_expressions(to_run)
        valid = []
        for expr, check in zip(to_run, checked):
            if check.get('valid'):
                valid.append(expr)
            else:
                results[expr] = {
                    'score': 0, 'url': '', 'alpha_id': None,
                    'status': 'LOCAL_REJECTED',
                    'stats': {'passed': False, 'validation_errors': check.get('errors', [])},
                }

        for start in range(0, len(valid), TEMPLATE_BATCH_SIZE):
            batch = valid[start:start + TEMPLATE_BATCH_SIZE]
            if len(batch) != TEMPLATE_BATCH_SIZE:
                logging.info(f"  -> DEFERRED_INCOMPLETE_BATCH: {len(batch)}/8")
                for expr in batch:
                    results[expr] = {
                        'score': 0, 'url': '', 'alpha_id': None,
                        'status': 'DEFERRED_INCOMPLETE_BATCH',
                        'stats': {'passed': False},
                    }
                continue

            payloads = [
                {'type': 'REGULAR', 'settings': dict(settings), 'regular': expr}
                for expr in batch
            ]
            batch_key = _multi_batch_key(batch, settings)
            self._metric_once('logical_parent_batches', batch_key)
            for expr in batch:
                self._metric_once('candidate_slots', f'{batch_key}|{_normalize_expression(expr)}')
            pending = pending_batches.get(batch_key)
            has_pending = isinstance(pending, dict)
            if has_pending:
                persist_multi_batch(
                    batch_key, pending,
                    getattr(self, 'initial_alpha_id', None),
                    getattr(self, 'hill_stage', 1),
                    getattr(self, 'source_state_store', None),
                )
            location = pending.get('location') if has_pending else None
            retrying_rate_limit = False
            if has_pending and pending.get('status') == 'SUBMITTED':
                try:
                    created_at = datetime.fromisoformat(pending.get('created_at'))
                    now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
                    pending_age = (now - created_at).total_seconds()
                except (TypeError, ValueError):
                    pending_age = 0
                if pending_age >= MULTI_SUBMITTED_REPOST_AFTER_SECONDS:
                    logging.warning(
                        f'Multi-Simulation断点已超过{MULTI_SUBMITTED_REPOST_AFTER_SECONDS // 60}分钟，'
                        f'停止恢复且绝不重新 POST；保留 RESULTS_UNOBSERVED: {location}'
                    )
                    pending.update({
                        'status': 'RESULTS_UNOBSERVED',
                        'retry_kind': 'STALE_LOCATION',
                        'observed_at': datetime.now().astimezone().isoformat(timespec='seconds'),
                    })
                    persist_multi_batch(
                        batch_key, pending,
                        getattr(self, 'initial_alpha_id', None),
                        getattr(self, 'hill_stage', 1),
                        getattr(self, 'source_state_store', None),
                    )
                    location = None
                    self.client.save_history()
            if has_pending and pending.get('status') == 'PENDING_RATE_LIMIT':
                retry_after = pending.get('retry_after')
                try:
                    retry_at = datetime.fromisoformat(retry_after)
                except (TypeError, ValueError):
                    retry_at = None
                retry_count = int(pending.get('retry_count') or 0)
                if retry_count >= MULTI_RATE_LIMIT_MAX_RETRIES:
                    pending.update({
                        'status': 'RESULTS_UNOBSERVED',
                        'retry_kind': 'RATE_LIMIT_EXHAUSTED',
                        'retry_after': None,
                    })
                    persist_multi_batch(
                        batch_key, pending,
                        getattr(self, 'initial_alpha_id', None),
                        getattr(self, 'hill_stage', 1),
                        getattr(self, 'source_state_store', None),
                    )
                    self.client.save_history()
                elif retry_at and retry_at > datetime.now().astimezone():
                    self.template_retry_after = retry_after
                else:
                    retrying_rate_limit = True
                    has_pending = False
                    logging.info('⏯️ Multi-Simulation 限频冷却结束，续跑同一批8条。')
            if has_pending:
                self._metric('duplicate_schedules')
                logging.info(
                    f"只读恢复已有 Multi-Simulation: "
                    f"{location or pending.get('status', 'RESULTS_UNOBSERVED')}"
                )
            else:
                global_cooldown = self._post_cooldown_snapshot()
                if global_cooldown['active']:
                    self.template_retry_after = global_cooldown['retry_after']
                    logging.warning(
                        '⏸️ 账户级429冷却中，禁止创建新的 Multi-Simulation；'
                        f"恢复时间={global_cooldown['retry_after']}"
                    )
                    for expr in batch:
                        results[expr] = {
                            'score': None, 'url': '', 'alpha_id': None,
                            'status': 'PENDING',
                            'stats': {'passed': None, 'retry_kind': 'GLOBAL_RATE_LIMIT'},
                        }
                    continue
                action = '重试提交' if retrying_rate_limit else '首次提交'
                logging.info(
                    f"{action} Multi-Simulation: 1个父任务 × {len(batch)}个并发子模拟 "
                    f"({settings.get('neutralization', 'NONE')}/{settings.get('decay', 0)})"
                )
                if retrying_rate_limit:
                    logging.info('🧮 复用该批首次提交前的额度预扣，不重复计数。')
                else:
                    budget = self._ensure_backtest_budget().reserve(len(batch))
                    logging.info(
                        f"🧮 回测额度已预扣 {len(batch)}："
                        f"已用={budget['used']}/{budget['limit']}，"
                        f"剩余={budget['remaining']}，重置={budget['reset_at']}"
                    )
                submission = None
                self._metric('actual_post_attempts')
                try:
                    submission = post_multi_simulation(
                        _core_client(self.client), payloads, return_metadata=True,
                        rate_limit_waits=MULTI_RATE_LIMIT_WAITS,
                    )
                except Exception as exc:
                    logging.warning(f"Multi-Simulation 提交异常: {exc}")
                submission = submission if isinstance(submission, dict) else {}
                location = submission.get('location')
                status_code = submission.get('status_code')
                retry_after = None
                prior_retry_count = int((pending or {}).get('retry_count') or 0)
                retry_count = prior_retry_count + (1 if retrying_rate_limit else 0)
                pending_status = 'SUBMITTED' if location else 'RESULTS_UNOBSERVED'
                if status_code == 429:
                    self._metric('rate_limits')
                    record_cooldown = getattr(
                        self._ensure_backtest_budget(), 'record_post_rate_limit', None
                    )
                    cooldown = record_cooldown(
                        MULTI_RATE_LIMIT_COOLDOWN_SECONDS
                    ) if callable(record_cooldown) else None
                    if not isinstance(cooldown, dict):
                        cooldown = {
                            'retry_after': (
                                datetime.now().astimezone()
                                + timedelta(seconds=MULTI_RATE_LIMIT_COOLDOWN_SECONDS)
                            ).isoformat(timespec='seconds')
                        }
                    self._metric('global_cooldowns')
                    if retrying_rate_limit and retry_count >= MULTI_RATE_LIMIT_MAX_RETRIES:
                        pending_status = 'RESULTS_UNOBSERVED'
                    else:
                        retry_after = cooldown['retry_after']
                        pending_status = 'PENDING_RATE_LIMIT'
                        self.template_retry_after = retry_after
                pending_batches[batch_key] = {
                    'status': pending_status,
                    'location': location,
                    'expressions': list(batch),
                    'settings': dict(settings),
                    'created_at': (pending or {}).get('created_at') or datetime.now().isoformat(),
                    'retry_after': retry_after,
                    'status_code': status_code,
                    'budget_reserved': True,
                    'retry_count': retry_count,
                    'retry_kind': (
                        'RATE_LIMIT_EXHAUSTED' if pending_status == 'RESULTS_UNOBSERVED'
                        and status_code == 429 else 'RATE_LIMIT' if status_code == 429 else None
                    ),
                    'code_version': CODE_VERSION,
                    'source_alpha_id': getattr(self, 'initial_alpha_id', None),
                    'stage': int(getattr(self, 'hill_stage', 1)),
                    'post_attempts': 1 + retry_count,
                }
                persist_multi_batch(
                    batch_key, pending_batches[batch_key],
                    getattr(self, 'initial_alpha_id', None),
                    getattr(self, 'hill_stage', 1),
                    getattr(self, 'source_state_store', None),
                )
                self.client.save_history()
                if location:
                    logging.info(f"已记录 Multi-Simulation 断点: {location}")
                elif status_code == 429 and pending_status == 'PENDING_RATE_LIMIT':
                    logging.warning(
                        f'Multi-Simulation 明确限频；保留同批断点，'
                        f'冷却至 {retry_after} 后续跑。'
                    )
                elif status_code == 429:
                    logging.warning(
                        'Multi-Simulation 已达到两次冷却重试上限；转为 RESULTS_UNOBSERVED，'
                        '后续仅允许只读对账。'
                    )
                else:
                    logging.warning(
                        "Multi-Simulation 提交结果不可观察；已记录批次哈希，重启不会重复 POST。"
                    )
            if not location:
                result_status = (
                    'PENDING' if (pending_batches.get(batch_key) or {}).get('status')
                    == 'PENDING_RATE_LIMIT' else 'RESULTS_UNOBSERVED'
                )
                for expr in batch:
                    results[expr] = {
                        'score': None, 'url': '', 'alpha_id': None,
                        'status': result_status, 'stats': {'passed': False},
                    }
                continue

            parent = poll_simulation_progress(
                _core_client(self.client), location, timeout=900,
                should_stop=lambda: self.client.stop_requested,
            )
            children = parent.get('children', []) if isinstance(parent, dict) else []
            parent_status = str(parent.get('status') or '').upper() if isinstance(parent, dict) else ''
            terminal_parent_statuses = {
                'COMPLETE', 'COMPLETED', 'WARNING', 'ERROR', 'FAILED', 'CANCELLED',
            }
            if parent_status not in terminal_parent_statuses or not children:
                result_status = 'PENDING' if parent_status == 'INTERRUPTED' else 'RESULTS_UNOBSERVED'
                parent_reason = _simulation_failure_reason(parent)
                for expr in batch:
                    results[expr] = {
                        'score': 0, 'url': location, 'alpha_id': None,
                        'status': result_status,
                        'failure_reason': parent_reason,
                        'stats': {
                            'passed': False, 'parent_status': parent_status or 'UNOBSERVED',
                        },
                    }
                continue

            all_observed = True
            history_changed = False
            child_status_counts = Counter()
            for index, expr in enumerate(batch):
                child = children[index] if index < len(children) else None
                payload, child_url = self._read_multi_child(child)
                child_status = str((payload or {}).get('status') or '').upper()
                child_status_counts[child_status or 'UNOBSERVED'] += 1
                details = self._multi_child_details(payload)
                if details and details.get('is', {}).get('sharpe') is not None:
                    self._process_result(details, expr, child_url or location, results, settings)
                    results[expr]['status'] = 'COMPLETE'
                    result_key = f'{getattr(self, "hill_stage", 1)}|{results[expr].get("alpha_id") or batch_key + "|" + _normalize_expression(expr)}'
                    self._metric_once('core_observable_candidates', result_key)
                    assessment = self._assess_stats(results[expr].get('stats', {}))
                    gate_status = str(
                        assessment.get('gate', {}).get('status') or 'PENDING'
                    ).lower()
                    new_gate_status = self._metric_once(
                        f'stage{getattr(self, "hill_stage", 1)}_gate_{gate_status}',
                        result_key,
                    )
                    if number(results[expr].get('stats', {}).get('sharpe_2y')) is not None:
                        self._metric_once('p2y_observable_candidates', result_key)
                    if assessment.get('gate', {}).get('observable'):
                        if self._metric_once('gate_observable_candidates', result_key):
                            self.stage_observable_results += 1
                    if assessment.get('gate', {}).get('passed') and new_gate_status:
                        self.stage_pass_results += 1
                elif child_status in {'ERROR', 'FAILED', 'CANCELLED'}:
                    result_status = 'CANCELLED' if child_status == 'CANCELLED' else 'FAILED'
                    reason = _simulation_failure_reason(payload) or f'child status={child_status}'
                    result = {
                        'score': 0, 'url': child_url or location, 'alpha_id': None,
                        'status': result_status, 'negative_cache': result_status == 'FAILED',
                        'terminal_status': child_status, 'failure_reason': reason,
                        'stats': {
                            'passed': False, 'parent_status': parent_status,
                            'child_status': child_status, 'failure_reason': reason,
                        },
                    }
                    results[expr] = result
                    if result_status == 'FAILED':
                        self.client.history[_cache_key(expr, settings)] = result
                        history_changed = True
                    logging.warning(
                        f'  -> child[{index + 1}] {result_status}: {child_status} - {reason}'
                    )
                else:
                    all_observed = False
                    results[expr] = {
                        'score': 0, 'url': child_url or location, 'alpha_id': None,
                        'status': 'RESULTS_UNOBSERVED',
                        'stats': {
                            'passed': False, 'parent_status': parent_status,
                            'child_status': child_status or 'UNOBSERVED',
                        },
                    }
            if all_observed:
                persist_multi_batch(
                    batch_key,
                    {
                        **(pending_batches.get(batch_key) or {}),
                        'status': 'COMPLETE', 'retry_after': None,
                        'source_alpha_id': getattr(self, 'initial_alpha_id', None),
                        'stage': int(getattr(self, 'hill_stage', 1)),
                    },
                    getattr(self, 'initial_alpha_id', None),
                    getattr(self, 'hill_stage', 1),
                    getattr(self, 'source_state_store', None),
                )
                pending_batches.pop(batch_key, None)
                history_changed = True
                if any(item.get('status') in {'FAILED', 'CANCELLED'} for item in results.values()):
                    self.template_retry_after = datetime.now().astimezone().isoformat(timespec='seconds')
            if history_changed:
                self.client.save_history()
            logging.info(
                f'Multi-Simulation 终态汇总: parent={parent_status} '
                f'children={dict(child_status_counts)} all_observed={all_observed}'
            )
            self._log_research_metrics()

        return results

    def _read_multi_child(self, child):
        """只读获取 multi-sim 子任务原始载荷，不丢失 ERROR/CANCELLED 信息。"""
        if not child:
            return None, ''
        child_url = child if isinstance(child, str) else (
            child.get('location') or child.get('url') or child.get('self') or ''
        )
        if (
            isinstance(child, dict) and not child_url
            and not child.get('alpha') and not child.get('is')
        ):
            child_url = child.get('id') or ''
        payload = child if isinstance(child, dict) else None
        if child_url:
            payload = poll_simulation_progress(
                _core_client(self.client), child_url, timeout=900,
                should_stop=lambda: self.client.stop_requested,
            )
        return payload if isinstance(payload, dict) else None, child_url

    def _multi_child_details(self, payload):
        """仅在子任务给出 Alpha ID 时读取统计详情。"""
        if not isinstance(payload, dict):
            return None
        alpha_id = payload.get('alpha')
        if not alpha_id and payload.get('is'):
            alpha_id = payload.get('id')
        if not alpha_id:
            return None
        return self.client.get_alpha_details(alpha_id)

    def _resolve_multi_child(self, child):
        """兼容原调用：返回 Alpha 详情和子任务 URL。"""
        payload, child_url = self._read_multi_child(child)
        return self._multi_child_details(payload), child_url

    def _process_result(self, res, expr, location, results_dict=None, settings=None):
        """处理单个结果"""
        current_settings = settings if settings is not None else self.settings
        
        # --- 补救逻辑加强：如果 res 只是个 simulation 对象或报表缺失，通过 ID 强制取回 ---
        if res and ('is' not in res or res['is'].get('sharpe') is None):
            aid = res.get('alpha') or res.get('id')
            if aid and len(aid) > 5: # 简单的 ID 合法性检查
                logging.info(f"   🔎 [强力取回] 报表缺失或不完整，通过 Alpha ID {aid} 直接查询详情...")
                # 循环重试几次，因为平台生成报表可能需要一点时间
                for attempt in range(5):
                    details = self.client.get_alpha_details(aid)
                    if details and 'is' in details and details['is'].get('sharpe') is not None:
                        res = details
                        logging.info(f"   ✅ [取回成功] 已成功拿回 Alpha {aid} 的统计数据。")
                        break
                    time.sleep(2)
        # --------------------------------------------------------------------------

        score = 0
        stats_dict = {'sharpe': 0, 'fitness': 0, 'margin': 0}
        alpha_id = None

        if res and 'is' in res:
            alpha_id = res['id']  # 获取Alpha ID
            is_stats = res['is']
            # 缺键与显式 None 都是不可观察，不能用 0 伪装成数字门槛失败。
            sharpe = is_stats.get('sharpe')
            fitness = is_stats.get('fitness')
            margin = is_stats.get('margin')
            turnover = is_stats.get('turnover')

            if any(value is None for value in (sharpe, fitness, margin, turnover)):
                logging.warning("  -> 回测核心指标不完整，当前评分版本保持PENDING语义")

            checks = is_stats.get('checks') if isinstance(is_stats.get('checks'), list) else []
            is_passed = (
                True if checks and all(c.get('result') == 'PASS' for c in checks)
                else False if any(c.get('result') == 'FAIL' for c in checks)
                else None
            )

            two_year_sharpe = _two_year_sharpe(res)
            cheap_stats = {
                'sharpe': sharpe, 'fitness': fitness, 'margin': margin,
                'turnover': turnover, 'sharpe_2y': two_year_sharpe,
                # 便宜数字预筛不把 Stage 3 平台总检查作为获取 SC 的前置条件。
                'passed': True,
            }
            cheap_gate = evaluate_stage_candidate(
                cheap_stats, getattr(self, 'hill_stage', 1),
                include_correlations=False,
            ).get('gate', {})

            # 厂型/年份/PnL/相关性均后置；数字门槛已明确失败或P2Y缺失时不请求。
            if cheap_gate.get('passed') and is_passed and self.client.check_factory_shape(alpha_id):
                logging.info(f"  🟣 检测到厂字型Alpha: {alpha_id}")
                factory_result = {
                    'score': 0,
                    'url': location,
                    'stats': {
                        'sharpe': 0, 'fitness': 0, 'margin': 0,
                        'passed': False, 'factory_shape': True,
                    },
                    'alpha_id': alpha_id,
                }
                if results_dict is not None:
                    results_dict[expr] = factory_result
                self.client.history[_cache_key(expr, current_settings)] = factory_result
                self.client.save_history()
                return 0

            # --- [相关性校准与定色] ---
            sc_val = None
            pc_val_from_name = None
            is_newly_colored = False
            
            if alpha_id and cheap_gate.get('passed'):
                try:
                    logging.info(f"   [本地SC检查] Alpha {alpha_id} 正在计算 SC...")
                    sc_val = get_sc_check(_core_client(self.client), alpha_id)
                except Exception as e:
                    logging.warning(f"SC处理失败: {e}")
            elif cheap_gate.get('failed'):
                self._metric('skipped_sc_requests')
                logging.info(
                    '   [SC后置] 基础数字门槛已失败，跳过SC/PnL请求: '
                    + ','.join(cheap_gate.get('failed') or [])
                )
            else:
                self._metric('skipped_sc_requests')
                logging.info('   [SC后置] P2Y或核心指标尚不可观察，跳过SC/PnL请求。')

            # 三阶段统一评分：核心分固定，SC/PC越大相关性扣分越多。
            stats_dict = {
                'sharpe': sharpe, 'fitness': fitness, 'margin': margin, 
                'passed': is_passed, 'sc': sc_val, 'pc': pc_val_from_name,
                'sc_status': (
                    getattr(self.client, 'sc_status', {}).get(alpha_id, sc_val)
                    if sc_val is not None else 'SC_SKIPPED_BASIC_GATE'
                    if cheap_gate.get('failed') else 'SC_SKIPPED_PENDING_METRICS'
                ),
                'turnover': turnover, 'sharpe_2y': two_year_sharpe,
                'check_failures': [
                    check.get('name') or check.get('message') or 'UNKNOWN'
                    for check in checks if check.get('result') != 'PASS'
                ],
                'is_newly_colored': is_newly_colored
            }
            scored = self._apply_score({'stats': stats_dict})
            score = scored['score']
            final_score = score
            gate = scored['stage_gate']
            components = scored['score_components']
            penalties = scored.get('score_penalties', {})
            score_text = f'{score:.2f}' if number(score) is not None else 'PENDING'
            logging.info(
                f"   [{STAGE_SCORE_VERSION}评分] 阶段={getattr(self, 'hill_stage', 3)} "
                f"门槛={gate.get('status')} "
                f"Sharpe分={components.get('sharpe', 0):.2f} "
                f"Fitness分={components.get('fitness', 0):.2f} "
                f"Margin分={components.get('margin', 0):.2f} "
                f"SC扣分={penalties.get('sc', 0):.2f} "
                f"PC扣分={penalties.get('pc', 0):.2f} 总分={score_text}"
            )
            if not gate.get('passed'):
                logging.info(
                    f"   [阶段门槛未通过] missing={gate.get('missing', [])} "
                    f"failed={gate.get('failed', [])}"
                )

            # 将结果存入结果字典
            if results_dict is not None:
                results_dict[expr] = {
                    'score': score,
                    'url': location,
                    'stats': stats_dict,
                    'alpha_id': alpha_id,
                    'status': 'COMPLETE',
                    'score_version': STAGE_SCORE_VERSION,
                    'score_components': components,
                    'score_penalties': penalties,
                    'stage_gate': gate,
                    'gate_status': scored.get('gate_status'),
                    'score_status': scored.get('score_status'),
                    'repair_route': scored.get('repair_route'),
                    'candidate_status': scored.get('candidate_status'),
                }

            # 优化终端显示
            status_icon = "⚪"
            color_code = "\033[90m" # 默认灰色
            if is_passed:
                if (
                    (sc_val is not None and sc_val >= STAGE_SC_LIMIT)
                    or not isinstance(margin, (int, float))
                    or margin < MARGIN_THRESHOLD
                ):
                    status_icon = "🔵"
                    color_code = "\033[94m" # 蓝色
                else:
                    status_icon = "🟢"
                    color_code = "\033[92m" # 绿色
            
            logging.info(f"{color_code}--------------------------------------------------")
            final_score_text = f'{final_score:.4f}' if number(final_score) is not None else 'PENDING'
            logging.info(f"{status_icon} Alpha ID: {alpha_id} | Score: {final_score_text}")
            metric_text = lambda value, spec: format(value, spec) if isinstance(value, (int, float)) else 'PENDING'
            logging.info(
                f"   Sharpe: {metric_text(sharpe, '.2f')} | "
                f"Fitness: {metric_text(fitness, '.2f')} | "
                f"Margin: {metric_text(margin, '.4f')} | "
                f"TO: {metric_text(turnover, '.2%')}"
            )

            if (
                gate.get('passed')
                and number(final_score) is not None
                and number(getattr(self, 'best_base_score', None)) is not None
            ):
                difference = final_score - self.best_base_score
                if difference >= STAGE_SCORE_MIN_IMPROVEMENT:
                    logging.info(f"   🎉 阶段分达到上位幅度 (+{difference:.2f})")
                elif abs(difference) < STAGE_SCORE_MIN_IMPROVEMENT:
                    logging.info("   阶段分差小于0.5，将按Margin/2Y Sharpe/Turnover比较")
            logging.info(f"{color_code}--------------------------------------------------\033[0m")

        else:
            logging.warning(f"  [异常] 无法获取结果或统计数据!")
            logging.warning(f"  URL: {location}")
            logging.warning(f"  Response: {res}")
            logging.warning("-" * 20)

            # 无法获取结果的Alpha分数设为0，不参与比较
            score = 0.0
            stats_dict = {'sharpe': 0, 'fitness': 0, 'margin': 0, 'passed': False}

        # 保存到历史记录 (核心修复：缓存键应包含 settings，值包含完整信息)
        h = _cache_key(expr, current_settings)
        
        # 存入完整结果包
        self.client.history[h] = {
            'score': score,
            'url': location,
            'stats': stats_dict,
            'alpha_id': alpha_id,
            'status': 'COMPLETE' if alpha_id else 'RESULTS_UNOBSERVED',
            'score_version': STAGE_SCORE_VERSION,
            'score_components': (
                results_dict.get(expr, {}).get('score_components', {})
                if results_dict is not None else {}
            ),
            'score_penalties': (
                results_dict.get(expr, {}).get('score_penalties', {})
                if results_dict is not None else {}
            ),
            'stage_gate': (
                results_dict.get(expr, {}).get('stage_gate', {})
                if results_dict is not None else {}
            ),
            'gate_status': (
                results_dict.get(expr, {}).get('gate_status', 'PENDING')
                if results_dict is not None else 'PENDING'
            ),
            'score_status': (
                results_dict.get(expr, {}).get('score_status', 'PENDING_METRICS')
                if results_dict is not None else 'PENDING_METRICS'
            ),
            'repair_route': (
                results_dict.get(expr, {}).get('repair_route', 'NONE')
                if results_dict is not None else 'NONE'
            ),
        }
        self.client.save_history()

        return score

    def _template_scope(self, fields):
        primary = fields[0] if fields else {}
        source = getattr(self, 'source_record', {}) or {}
        category = resolve_template_category(
            source.get('primary_tower'),
            [field.get('category') or field.get('category_name') for field in fields],
        )
        return {
            'template_learning_version': TEMPLATE_LEARNING_VERSION,
            'region': self.settings.get('region', 'UNKNOWN'),
            'category': category['category'],
            'category_source': category['category_source'],
            'category_status': category['status'],
            'universe': self.settings.get('universe', 'UNKNOWN'),
            'delay': self.settings.get('delay', 'UNKNOWN'),
            'dataset_id': primary.get('dataset_id', 'UNKNOWN'),
            'field_type': primary.get('type', 'UNKNOWN'),
            'stage': int(getattr(self, 'hill_stage', 1)),
        }

    def _record_template_candidate(self, run_id, alpha_id, candidate, status,
                                   result=None, reason=''):
        result = result or {}
        stats = result.get('stats', {})
        fields = candidate.get('field_metadata', [])
        if not fields or any(
            str(field.get('dataset_id') or 'UNKNOWN') == 'UNKNOWN'
            for field in fields if isinstance(field, dict)
        ):
            source_metadata = (getattr(self, 'source_record', {}) or {}).get(
                'field_metadata', {}
            )
            source_fields = [
                value for value in source_metadata.values()
                if isinstance(value, dict) and value.get('dataset_id') not in {None, 'UNKNOWN'}
            ] if isinstance(source_metadata, dict) else []
            if source_fields:
                fields = source_fields
        scope = self._template_scope(fields)
        score = result.get('score')
        score_delta = (
            score - self.initial_score
            if isinstance(score, (int, float)) and isinstance(self.initial_score, (int, float))
            else None
        )
        assessment = evaluate_stage_candidate(stats, getattr(self, 'hill_stage', 1))
        gate = assessment.get('gate', {})
        baseline_gate = getattr(self, 'template_baseline_gate', {})
        deficit = gate.get('gate_deficit_total')
        baseline_deficit = baseline_gate.get('gate_deficit_total')
        gate_deficit_delta = (
            baseline_deficit - deficit
            if isinstance(deficit, (int, float)) and isinstance(baseline_deficit, (int, float))
            else None
        )
        sharpe_2y = stats.get('sharpe_2y')
        sc_value = stats.get('sc')
        final_gate = evaluate_stage_candidate(stats, 3).get('gate', {})
        pc_value = number(stats.get('pc'))
        baseline_deficits = baseline_gate.get('gate_deficits', {}) or {}
        result_deficits = gate.get('gate_deficits', {}) or {}
        target_metrics = candidate.get('target_metrics', ())
        baseline_metrics = dict(getattr(self, 'template_baseline_stats', {}) or {})
        baseline_metrics_complete = self._target_metrics_complete(
            baseline_metrics, target_metrics
        )
        result_metrics_complete = self._target_metrics_complete(stats, target_metrics)
        target_metric_deltas = {}
        for name in target_metrics:
            before = number(baseline_metrics.get(name))
            after = number(stats.get(name))
            if before is None or after is None:
                target_metric_deltas[name] = None
            elif name in {'sc', 'pc'}:
                target_metric_deltas[name] = before - after
            else:
                target_metric_deltas[name] = after - before
        observable_target_deltas = [
            value for value in target_metric_deltas.values()
            if isinstance(value, (int, float))
        ]
        retained_previous_gates = (
            baseline_metrics_complete and result_metrics_complete
            and gate.get('observable') and baseline_gate.get('observable')
            and
            gate.get('gate_level', 0) >= baseline_gate.get('gate_level', 0)
            and all(
                result_deficits.get(name, 1.0) == 0
                for name, value in baseline_deficits.items() if value == 0
            )
        )
        hard_pass = bool(
            final_gate.get('passed') and pc_value is not None and pc_value < STAGE_PC_LIMIT
        )
        validation = candidate.get('local_validation') or {}
        margin_evidence = (
            self._margin_repair_effect(stats)
            if candidate.get('role') == 'MARGIN_REPAIR'
            else {}
        )
        event = {
            **scope,
            'run_id': run_id,
            'candidate_key': candidate.get('candidate_key'),
            'source_alpha_id': alpha_id,
            'template_id': candidate.get('template_id', 'UNKNOWN'),
            'template_state': candidate.get('template_state', 'PROBATION'),
            'template_module': candidate.get('module'),
            'template_function': candidate.get('function'),
            'source_kind': candidate.get('source_kind'),
            'source_post_id': candidate.get('source_post_id'),
            'source_url': candidate.get('source_url'),
            'source_relation': candidate.get('source_relation'),
            'source_section': candidate.get('source_section'),
            'source_author': candidate.get('source_author'),
            'source_line': candidate.get('source_line'),
            'template_attempt_count': candidate.get('template_attempt_count', 0),
            'template_version': candidate.get('template_version'),
            'template_family': candidate.get('family'),
            'candidate_origin': candidate.get('candidate_origin', 'LOCAL_PROBE'),
            'template_class': candidate.get('template_class'),
            'supported_categories': candidate.get('supported_categories', ()),
            'economic_hypothesis': candidate.get('economic_hypothesis', ''),
            'semantic_requirements': candidate.get('semantic_requirements', ()),
            'semantic_match_evidence': candidate.get('semantic_match_evidence', ()),
            'input_mode': candidate.get('input_mode'),
            'horizon_days': candidate.get('horizon_days', ()),
            'economic_thesis_id': candidate.get('economic_thesis_id'),
            'template_role': candidate.get('role'),
            'repair_goal': candidate.get('repair_goal'),
            'repair_family': candidate.get('repair_family'),
            'hu_ge_variant': candidate.get('hu_ge_variant'),
            'target_metrics': target_metrics,
            'variant_id': candidate.get('variant_id'),
            'resolved_params': candidate.get('resolved_params') or candidate.get('params', {}),
            'operator_family': candidate.get('family'),
            'fields': candidate.get('fields', []),
            'parameters': candidate.get('params', {}),
            'expression': candidate.get('expression'),
            'expression_hash': candidate.get('expression_hash'),
            'operators': candidate.get('operators', []),
            'neutralization': self.settings.get('neutralization'),
            'decay': self.settings.get('decay'),
            'local_valid': validation.get('valid'),
            'validation_errors': validation.get('errors', []),
            'live_operator_check': 'PASS' if candidate.get('eligible') else 'REJECTED',
            'multi_simulation_url': result.get('url'),
            'alpha_id': result.get('alpha_id'),
            'sharpe': stats.get('sharpe'),
            'fitness': stats.get('fitness'),
            'margin': stats.get('margin'),
            'turnover': stats.get('turnover'),
            'sharpe_2y': sharpe_2y,
            'sc': sc_value,
            'sc_status': stats.get('sc_status'),
            'checks': stats.get('checks') or stats.get('platform_checks') or [],
            'overfit_status': stats.get('overfit_status'),
            'robust_status': stats.get('robust_status'),
            'strict_overfit_status': stats.get('strict_overfit_status'),
            'score': score,
            'score_delta': score_delta,
            'objective_version': OBJECTIVE_VERSION,
            'gate_level': gate.get('gate_level'),
            'gate_deficits': gate.get('gate_deficits', {}),
            'gate_deficit_total': deficit,
            'gate_deficit_delta': gate_deficit_delta,
            'gate_improved': bool(result.get('gate_improved')),
            'baseline_metrics': baseline_metrics,
            'result_metrics': dict(stats or {}),
            'target_metric_deltas': target_metric_deltas,
            'target_improvement_value': (
                max(observable_target_deltas) if observable_target_deltas else None
            ),
            'baseline_metrics_complete': baseline_metrics_complete,
            'result_metrics_complete': result_metrics_complete,
            'source_gate_level': baseline_gate.get('gate_level'),
            'result_gate_level': gate.get('gate_level'),
            'retained_previous_gates': retained_previous_gates,
            'became_best': bool(result.get('became_best')),
            'hard_pass': hard_pass,
            'status': status,
            'failure_reason': (
                result.get('failure_reason') or reason or candidate.get('reason', '')
            ),
            'formal_batch_id': candidate.get('formal_batch_id'),
            'low_recheck_cycle': candidate.get('low_recheck_cycle', 0),
            **margin_evidence,
        }
        metric_key = candidate.get('candidate_key') or '|'.join((
            str(run_id), str(candidate.get('template_id')), str(candidate.get('variant_id')),
        ))
        is_formal = candidate.get('candidate_origin') == 'FORMAL_TEMPLATE'
        if is_formal and status == 'GENERATED':
            self._metric_once('formal_template_slots', metric_key)
        if is_formal and status in {'COMPLETE', 'CACHE_HIT'}:
            self._metric_once('formal_template_complete', metric_key)
            if status == 'COMPLETE':
                self._metric_once('formal_template_simulated_slots', metric_key)
            role = str(candidate.get('role') or 'UNKNOWN').lower()
            self._metric_once(f'template_role_{role}_complete', metric_key)
            effective_improvement = (
                event.get('margin_effective_improvement') is True
                if candidate.get('role') == 'MARGIN_REPAIR'
                else event.get('gate_improved') and event.get('retained_previous_gates')
            )
            if effective_improvement:
                self._metric_once(f'template_role_{role}_improved', metric_key)
                baseline_stats = getattr(self, 'template_baseline_stats', {}) or {}
                baseline_sc = number(baseline_stats.get('sc'))
                result_sc = number(stats.get('sc'))
                baseline_pc = number(baseline_stats.get('pc'))
                result_pc = number(stats.get('pc'))
                if baseline_sc is not None and result_sc is not None and result_sc < baseline_sc:
                    self._metric_once('sc_repair_success', metric_key)
                if baseline_pc is not None and result_pc is not None and result_pc < baseline_pc:
                    self._metric_once('pc_repair_success', metric_key)
        if status == 'FIELD_REJECTED':
            self._metric_once('template_field_rejected', metric_key)
        elif status == 'LIVE_REJECTED':
            self._metric_once('template_permission_rejected', metric_key)
        elif str(status).startswith('PENDING') or status == 'RESULTS_UNOBSERVED':
            self._metric_once('template_pending', metric_key)
        # v4 只保存正式结果。生成事件和局部探针已由运行日志/批次状态覆盖，
        # 不再逐条写入高体积模板表现账本。
        if not is_formal or status == 'GENERATED':
            return
        if status in {'LOCAL_REJECTED', 'LIVE_REJECTED', 'FIELD_REJECTED'}:
            reject_key = (run_id, status, str(reason or candidate.get('reason', '')))
            seen = getattr(self, '_template_rejection_seen', set())
            if reject_key in seen:
                return
            seen.add(reject_key)
            self._template_rejection_seen = seen
            event['status'] = 'AGGREGATED_REJECTED'
            event['template_id'] = 'AGGREGATED_REJECTED'
            event['expression'] = None
        record_template_usage(event, refresh_summary=False)

    def _adopt_template_result(self, expression, result, alpha_id):
        """模板与局部爬山共用当前门槛、相关性评分和上位规则。"""
        return self._adopt_result(expression, result, alpha_id)

    def _remember_stage_pass_candidate(self, candidate, result):
        """记住当前阶段的完整 PASS；稍后按家族去重后立即交接。"""
        if not isinstance(result, dict) or result.get('status') not in {
            None, 'COMPLETE', 'CACHE_HIT'
        }:
            return False
        alpha_id = result.get('alpha_id')
        expression = candidate.get('expression')
        stats = dict(result.get('stats') or {})
        assessment = evaluate_stage_candidate(stats, int(getattr(self, 'hill_stage', 1)))
        if not alpha_id or not expression or not assessment.get('eligible'):
            return False
        normalized = _normalize_expression(expression)
        remembered = getattr(self, 'stage_pass_candidates', None)
        if remembered is None:
            remembered = []
            self.stage_pass_candidates = remembered
        duplicate = any(
            str(item.get('alpha_id')) == str(alpha_id)
            or _normalize_expression(item.get('expression', '')) == normalized
            for item in remembered
        )
        if duplicate:
            self._metric('stage_branch_merges')
            return False
        remembered.append({
            'alpha_id': str(alpha_id),
            'expression': expression,
            'stats': stats,
            'score': assessment.get('score'),
            'template_id': candidate.get('template_id'),
            'template_family': candidate.get('family') or candidate_route(candidate),
            'candidate_origin': candidate.get('candidate_origin'),
            'variant_id': candidate.get('variant_id'),
            'status': result.get('status') or 'CACHE_HIT',
        })
        return True

    def _adopt_margin_result(self, expression, result, alpha_id):
        """Margin 路由只比较联合门槛安全的 Margin 专项词典序。"""
        if result.get('status') not in {'COMPLETE', 'CACHE_HIT', None}:
            return False
        result = self._apply_score(result)
        if margin_repair_rank_key(
            result.get('stats', {}), getattr(self, 'hill_stage', 1)
        ) <= margin_repair_rank_key(
            getattr(self, 'best_stats', {}), getattr(self, 'hill_stage', 1)
        ):
            return False
        with self.score_lock:
            self.best_expr = expression
            self.best_score = result.get('score')
            self.best_base_score = result.get('score')
            self.best_alpha_id = result.get('alpha_id') or self.best_alpha_id
            self.best_stats = result.get('stats', {})
            self.best_pc = self.best_stats.get('pc')
            self.score_components = result.get('score_components', {})
            self.score_penalties = result.get('score_penalties', {})
        self.save_checkpoint(alpha_id)
        return True

    def _margin_repair_effect(self, stats):
        """返回 Margin 改善证据；高 Margin 但换手失效不算成功。"""
        stage = int(getattr(self, 'hill_stage', 1))
        before = getattr(self, 'template_baseline_stats', {}) or {}
        before_ready = evaluate_margin_repair_readiness(before, stage)
        after_ready = evaluate_margin_repair_readiness(stats, stage)
        before_bp = before_ready.get('margin_bp')
        after_bp = after_ready.get('margin_bp')
        delta_bp = (
            after_bp - before_bp
            if before_bp is not None and after_bp is not None else None
        )
        retained = bool(after_ready.get('non_margin_passed'))
        crossed = bool(
            before_bp is not None and after_bp is not None
            and before_bp <= after_ready['margin_threshold'] < after_bp
        )
        effective = bool(
            before_ready.get('ready')
            and retained
            and after_ready.get('turnover_retained')
            and delta_bp is not None
            and (crossed or delta_bp >= MARGIN_REPAIR_MIN_IMPROVEMENT_BP)
        )
        return {
            'margin_repair_ready_before': bool(before_ready.get('ready')),
            'non_margin_gates_retained': retained,
            'margin_bp_before': before_bp,
            'margin_bp_after': after_bp,
            'margin_bp_delta': delta_bp,
            'margin_threshold': after_ready.get('margin_threshold'),
            'margin_threshold_crossed': crossed,
            'turnover_before': number(before.get('turnover')),
            'turnover_after': number((stats or {}).get('turnover')),
            'turnover_retained': bool(after_ready.get('turnover_retained')),
            'sc_retained_if_observed': (
                True if number(before.get('sc')) is None
                else number((stats or {}).get('sc')) is not None
                and number((stats or {}).get('sc')) <= number(before.get('sc'))
            ),
            'margin_effective_improvement': effective,
        }

    def _make_margin_candidate(self, template_id, expression, fields,
                               allowed_operators, family, params=None,
                               hypothesis='', hu_ge_variant=None,
                               inherits_source=True):
        normalized = _normalize_expression(expression)
        operators = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', expression)
        validation = batch_verify_expressions([expression])[0]
        inherited_expression = self.best_expr if inherits_source else ''
        reason = new_operator_policy_reason(
            expression, inherited_expression, allowed_operators
        )
        if not reason and not validation.get('valid'):
            reason = '; '.join(str(item) for item in validation.get('errors', []))
        params = dict(params or {})
        expression_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
        return {
            'template_id': template_id,
            'module': __name__, 'function': family, 'family': family,
            'tier': 2, 'kind': 'margin_repair', 'params': params,
            'expression': expression, 'expression_hash': expression_hash,
            'template_version': CODE_VERSION,
            'variant_id': hashlib.sha256(
                json.dumps({'template': template_id, 'params': params}, sort_keys=True).encode('utf-8')
            ).hexdigest()[:16],
            'resolved_params': params,
            'role': 'MARGIN_REPAIR',
            'repair_goal': 'MARGIN',
            'repair_family': family,
            'hu_ge_variant': hu_ge_variant,
            'target_metrics': ('sharpe', 'fitness', 'sharpe_2y', 'margin', 'turnover'),
            'template_class': 'ECONOMIC_SIGNAL' if hu_ge_variant else 'STATISTICAL_CONTROL',
            'economic_hypothesis': hypothesis,
            'operators': operators,
            'fields': [field.get('id') for field in fields],
            'field_type': '+'.join(sorted({str(field.get('type', 'UNKNOWN')) for field in fields})),
            'dataset_id': '+'.join(sorted({str(field.get('dataset_id', 'UNKNOWN')) for field in fields})),
            'eligible': not reason, 'reason': reason,
            'local_validation': validation, 'field_metadata': fields,
            'candidate_origin': 'FORMAL_TEMPLATE',
            'template_state': 'PROBATION',
            'selection_bucket': 'CHALLENGER',
        }

    def _margin_repair_candidates(self, parser, fields, allowed_operators,
                                  formal_candidates, round_number=1):
        """组成固定 2局部+2效率+2分布+2经济关系 的 Margin 批次。"""
        source = self.best_expr
        stage = int(getattr(self, 'hill_stage', 1))
        readiness = evaluate_margin_repair_readiness(self.best_stats, stage)
        if not readiness.get('ready'):
            return []
        candidates = []
        seen = set()

        def append(candidate):
            key = candidate.get('expression_hash')
            if candidate.get('eligible') and key and key not in seen:
                seen.add(key)
                candidates.append(candidate)

        local_pool = self._probe_neighborhood_candidates(
            parser, fields, allowed_operators, limit=8
        )
        local_pool = [item for item in local_pool if '.time_window.' in item['template_id']]
        offset = 0 if round_number == 1 else 2
        for index, item in enumerate(local_pool[offset:offset + 2], 1):
            append(self._make_margin_candidate(
                f'margin.local_window.r{round_number}.{index}', item['expression'],
                fields, allowed_operators, 'LOCAL_WINDOW', item.get('params'),
                '相邻窗口在保持经济方向的同时寻找更高单位换手收益。',
            ))

        turnover = number(self.best_stats.get('turnover'))
        if turnover is not None and turnover > readiness['turnover_midpoint']:
            values = (2, 5) if round_number == 1 else (5, 10)
            expressions = [(f'ts_decay_linear({source}, {d})', {'d': d}) for d in values]
            family = 'TURNOVER_DECAY'
        else:
            values = (22, 66) if round_number == 1 else (66, 120)
            expressions = [(f'ts_av_diff({source}, {d})', {'d': d}) for d in values]
            family = 'ACTIVE_RETURN'
        for expression, params in expressions:
            append(self._make_margin_candidate(
                f'margin.{family.lower()}.d{params["d"]}', expression, fields,
                allowed_operators, family, params,
                '按当前换手位置平衡有效收益与交易频率。',
            ))

        failures = ' '.join(str(item) for item in self.best_stats.get('check_failures', ())).upper()
        has_concentration = any(token in failures for token in ('CONCENTRATED', 'WEIGHT', 'LONG_TAIL'))
        if has_concentration:
            std = 4 if round_number == 1 else 3
            group = 'subindustry' if round_number == 1 else 'industry'
            distribution_specs = (
                (f'winsorize({source}, std={std})', 'DISTRIBUTION_WINSORIZE', {'std': std}),
                (f'group_neutralize({source}, {group})', 'DISTRIBUTION_NEUTRALIZE', {'group': group}),
            )
            for expression, family, params in distribution_specs:
                append(self._make_margin_candidate(
                    f'margin.{family.lower()}.{round_number}', expression, fields,
                    allowed_operators, family, params,
                    '只有存在集中度证据时才改变信号分布。',
                ))
        else:
            for index, item in enumerate(local_pool[offset + 2:offset + 4], 1):
                append(self._make_margin_candidate(
                    f'margin.local_distribution_fallback.r{round_number}.{index}',
                    item['expression'], fields, allowed_operators,
                    'LOCAL_WINDOW_FALLBACK', item.get('params'),
                    '没有集中度证据时继续使用保方向局部窗口。',
                ))

        hu_target = 120 if round_number == 1 else 252
        hu_candidates = [
            item for item in formal_candidates
            if str(item.get('template_id', '')).startswith('hu_ge.series2_')
            and int((item.get('resolved_params') or item.get('params') or {}).get('d', 0)) == hu_target
        ]
        for item in hu_candidates[:2]:
            value = dict(item)
            value.update({
                'role': 'MARGIN_REPAIR', 'repair_goal': 'MARGIN',
                'repair_family': 'HU_GE_RELATION',
                'hu_ge_variant': item.get('template_id'),
                'candidate_origin': 'FORMAL_TEMPLATE',
                'target_metrics': ('sharpe', 'fitness', 'sharpe_2y', 'margin', 'turnover'),
            })
            append(value)

        fallback = [
            item for item in [*local_pool, *formal_candidates]
            if item.get('template_state') not in {'LOW_PRIORITY', 'DISABLED_SCOPE'}
        ]
        for item in fallback:
            if len(candidates) >= TEMPLATE_BATCH_SIZE:
                break
            value = self._make_margin_candidate(
                f'margin.fallback.{item.get("template_id")}', item['expression'], fields,
                allowed_operators, 'FALLBACK', item.get('resolved_params') or item.get('params'),
                item.get('economic_hypothesis', '同范围合法候选补位。'),
                inherits_source=False,
            )
            append(value)
        return candidates[:TEMPLATE_BATCH_SIZE] if len(candidates) >= TEMPLATE_BATCH_SIZE else []

    def _adaptive_template_candidates(self, completed, allowed_operators, fields):
        """为第 8 批生成有序候选池，调用方再按缓存状态选满固定8条。"""
        ranked = sorted(
            ((expr, data) for expr, data in completed.items()
             if data.get('status') in {'COMPLETE', 'CACHE_HIT'}),
            key=lambda item: (
                number(item[1].get('score'))
                if number(item[1].get('score')) is not None else float('-inf')
            ), reverse=True,
        )
        if not ranked:
            return []
        builders = (
            ('corr_decay2', lambda expr: reduce_correlation_by_decay_sweep(expr, 2)),
            ('corr_decay5', lambda expr: reduce_correlation_by_decay_sweep(expr, 5)),
            ('corr_decay10', lambda expr: reduce_correlation_by_decay_sweep(expr, 10)),
            ('corr_neutral_industry', lambda expr: optimize_weight_concentration_neutralize(expr, 'industry')),
            ('corr_neutral_subindustry', lambda expr: optimize_weight_concentration_neutralize(expr, 'subindustry')),
            ('corr_rank', optimize_weight_concentration_rank),
            ('corr_delay1', lambda expr: reduce_correlation_by_delay_signal(expr, 1)),
            ('corr_delay2', lambda expr: reduce_correlation_by_delay_signal(expr, 2)),
        )
        candidates = []
        seen = set()
        for base_expression, _ in ranked[:3]:
            for suffix, builder in builders:
                expression = builder(base_expression)
                operators = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', expression)
                if new_operator_policy_reason(
                    expression, base_expression, allowed_operators
                ):
                    continue
                check = batch_verify_expressions([expression])[0]
                expression_hash = hashlib.sha256(_normalize_expression(expression).encode('utf-8')).hexdigest()[:16]
                if not check.get('valid') or expression_hash in seen:
                    continue
                seen.add(expression_hash)
                candidates.append({
                    'template_id': f'adaptive.{suffix}',
                    'module': __name__, 'function': suffix, 'family': 'adaptive',
                    'tier': 3, 'kind': 'adaptive', 'params': {},
                    'expression': expression, 'expression_hash': expression_hash,
                    'template_version': 'builtin-v1', 'operators': operators,
                    'variant_id': expression_hash,
                    'resolved_params': {},
                    'role': 'FINAL_REPAIR',
                    'target_metrics': ('sharpe', 'fitness', 'sharpe_2y', 'margin', 'sc', 'pc'),
                    'fields': [field.get('id') for field in fields],
                    'field_type': fields[0].get('type', 'UNKNOWN'),
                    'dataset_id': fields[0].get('dataset_id', 'UNKNOWN'),
                    'local_validation': check, 'eligible': True, 'reason': '',
                    'field_metadata': fields,
                    'candidate_origin': 'ADAPTIVE_REPAIR',
                })
        return candidates

    def _probe_neighborhood_candidates(self, parser, fields, allowed_operators, limit=7):
        """生成与原式同字段、同骨架的近邻；不足部分再由模板池补齐。"""
        candidates = []
        seen = {_normalize_expression(
            getattr(self, 'source_expression', None) or self.best_expr
        )}
        inherited_expression = getattr(self, 'source_expression', None) or self.best_expr
        for target_type in ('time_window', 'operator', 'group'):
            position_count = len([
                token for token in parser.tokens
                if token.get('type') == ('number' if target_type == 'time_window' else target_type)
            ])
            for position in range(position_count):
                for expression in parser.generate_neighbors(target_type, position):
                    normalized = _normalize_expression(expression)
                    operators = re.findall(
                        r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', expression
                    )
                    operator_names = {name.lower() for name in operators}
                    has_group_input = any(
                        str(field.get('type', '')).upper() in {'GROUP', 'CATEGORY'}
                        for field in fields
                    )
                    if (
                        normalized in seen
                        or new_operator_policy_reason(
                            expression, inherited_expression, allowed_operators
                        )
                        or ('densify' in operator_names and not has_group_input)
                    ):
                        continue
                    seen.add(normalized)
                    candidates.append({
                        'template_id': f'probe.neighbor.{target_type}.{position}',
                        'module': __name__, 'function': 'local_probe_neighbor',
                        'family': 'local_neighborhood', 'tier': 0,
                        'kind': 'probe_neighbor', 'params': {
                            'target_type': target_type, 'position': position,
                        },
                        'expression': expression,
                        'expression_hash': hashlib.sha256(
                            normalized.encode('utf-8')
                        ).hexdigest()[:16],
                        'template_version': CODE_VERSION,
                        'variant_id': hashlib.sha256(
                            json.dumps({
                                'target_type': target_type, 'position': position,
                                'expression': normalized,
                            }, sort_keys=True).encode('utf-8')
                        ).hexdigest()[:16],
                        'resolved_params': {
                            'target_type': target_type, 'position': position,
                        },
                        'role': (
                            'SIGNAL_BUILD' if int(getattr(self, 'hill_stage', 1)) == 1
                            else 'STABILITY_CONTROL'
                        ),
                        'target_metrics': ('sharpe', 'fitness', 'sharpe_2y', 'margin'),
                        'operators': operators,
                        'fields': [field.get('id') for field in fields],
                        'field_type': fields[0].get('type', 'UNKNOWN'),
                        'dataset_id': fields[0].get('dataset_id', 'UNKNOWN'),
                        'eligible': True, 'reason': '', 'field_metadata': fields,
                        'candidate_origin': 'LOCAL_PROBE',
                    })
                    if len(candidates) >= limit:
                        return candidates
        return candidates

    def _template_calibration_due(self, scope, alpha_id):
        """每个 Region×Category 的第 7 个完整 Stage1 源获得一次模板校准批。"""
        sources = {
            str(event.get('source_alpha_id') or '')
            for event in load_template_usage()
            if event.get('template_learning_version') == TEMPLATE_LEARNING_VERSION
            and str(event.get('region')) == str(scope.get('region'))
            and str(event.get('category')) == str(scope.get('category'))
            and int(event.get('stage') or 0) == 1
            and str(event.get('template_id', '')).startswith('probe.neighbor.')
            and event.get('status') == 'COMPLETE'
        }
        sources.discard('')
        if not sources:
            state = load_source_state()
            for record in (state.get('candidates', {}) or {}).values():
                if int(record.get('hill_stage') or 1) != 1:
                    continue
                if int(record.get('stage_batches_used') or 0) < 1:
                    continue
                settings = record.get('settings') or {}
                region = record.get('region') or settings.get('region')
                tower = str(record.get('primary_tower') or '')
                category = tower.replace('\\', '/').rstrip('/').split('/')[-1].upper()
                if (
                    str(region) == str(scope.get('region'))
                    and category == str(scope.get('category')).upper()
                ):
                    sources.add(str(record.get('alpha_id') or ''))
            sources.discard('')
            sources.add(str(alpha_id))
        return str(alpha_id) in sources and len(sources) > 0 and len(sources) % 7 == 0

    def run_template_exploration(self, alpha_id, parser):
        """首轮广度阶段：40 个模板骨架 + 16 个形态 + 8 个自适应补充。"""
        if not ENABLE_TEMPLATE_EXPLORATION or self.stop_requested:
            return False
        self.template_pending_status = None
        allowed_operators = self.client.get_available_operators()
        if not allowed_operators:
            logging.warning('模板探索 PENDING：实时算子权限不可观察，不创建回测。')
            return False

        field_ids = _stable_unique(
            token['text'] for token in parser.tokens if token['type'] == 'data_field'
        )
        if not 1 <= len(field_ids) <= 2:
            logging.warning(
                f'模板探索已阻止：源表达式包含 {len(field_ids)} 个字段，'
                '固定边界要求1至2个字段；不创建回测。'
            )
            self.template_blocked_status = 'DISABLED_SCOPE'
            return False
        fields = []
        for field_id in field_ids:
            metadata = self.client.get_field_metadata(field_id, self.settings)
            if metadata:
                fields.append(metadata)
        if len(fields) != len(field_ids):
            logging.warning('模板探索 PENDING：源字段官方元数据不可观察，不创建回测。')
            self.template_pending_status = 'PENDING_FIELD_METADATA'
            return False
        if len({field.get('dataset_id') for field in fields}) > 1:
            logging.warning('模板探索已阻止：源表达式跨数据集，不创建回测。')
            self.template_blocked_status = 'DISABLED_SCOPE'
            return False

        scope = self._template_scope(fields)
        if scope.get('category_status') != 'OK':
            self.template_pending_status = scope.get('category_status')
            logging.warning(
                '模板学习范围 PENDING：主塔 Category 与字段 Category 缺失或冲突；不创建回测。'
            )
            return False
        stage = int(getattr(self, 'hill_stage', 1))
        if stage == 3 and not PREFER_CATALOG_TEMPLATES:
            numeric_state = evaluate_margin_repair_readiness(self.best_stats, 3)
            pc_value = number((getattr(self, 'best_stats', {}) or {}).get('pc'))
            if pc_value is None:
                pc_value = number(getattr(self, 'best_pc', None))
                if pc_value is not None:
                    self.best_stats['pc'] = pc_value
            sc_value = number((getattr(self, 'best_stats', {}) or {}).get('sc'))
            numeric_passed = bool(
                numeric_state.get('non_margin_passed')
                and numeric_state.get('margin_passed')
            )
            if numeric_passed and sc_value is None:
                sc_value = number(get_sc_check(
                    _core_client(self.client), self.best_alpha_id
                ) if self.best_alpha_id else None)
                self.best_stats['sc'] = sc_value
                self._metric('stage3_numeric_pass_sc_requests')
                if sc_value is None:
                    self.template_pending_status = 'PENDING_SC'
                    logging.warning('Stage 3 数字门槛已通过但SC不可观察；保持PENDING，不创建盲目修复批次。')
                    return False
            if numeric_passed and sc_value is not None and sc_value < STAGE_SC_LIMIT:
                if pc_value is None:
                    self.template_pending_status = 'PENDING_PC'
                    logging.warning('Stage 3 数值PC不可观察；不创建盲目相关性修复批次。')
                    return False
                if pc_value < STAGE_PC_LIMIT:
                    self.current_position['template_batch'] = int(
                        getattr(self, 'stage_target_batches', 3)
                    )
                    logging.info('Stage 3 基础门槛及SC/PC已通过；直接结算，不追加模板变形。')
                    return True
        role = (
            'SIGNAL_BUILD' if stage == 1
            else 'STABILITY_CONTROL' if stage == 2
            else 'FINAL_REPAIR'
        )
        context = {
            **scope,
            'fields': fields,
            'expression': self.best_expr,
            'allowed_operators': allowed_operators,
            'template_role': role,
            'prefer_admin_templates': PREFER_ADMIN_TEMPLATES,
            'prefer_catalog_templates': PREFER_CATALOG_TEMPLATES,
        }
        selected, rejected = select_template_candidates(
            context, TEMPLATE_EXPLORATION_LIMIT, include_rejected=True
        )
        attempted_routes = list(self.current_position.get('attempted_routes') or [])
        active_route = choose_route(
            stage, self._assess_stats(self.best_stats).get('gate', {}), attempted_routes
        )
        selected = prioritize_route(selected, active_route, prefer_catalog=PREFER_CATALOG_TEMPLATES)
        for candidate in selected:
            candidate['optimization_route'] = candidate_route(candidate)
        template_candidates = list(selected)

        def _candidate_has_complete_cache(candidate):
            cached = self.client.history.get(
                _cache_key(candidate['expression'], self.settings)
            )
            return bool(
                isinstance(cached, dict)
                and cached.get('alpha_id')
                and cached.get('status') in {None, 'COMPLETE', 'CACHE_HIT'}
            )

        def _fill_stage_group(primary, fallback, active_slots=TEMPLATE_BATCH_SIZE):
            """Keep cached evidence, but fill POST slots only from the same plan group."""
            group = []
            seen = set()
            active_count = 0
            for candidate in [*primary, *fallback]:
                expression_hash = candidate.get('expression_hash')
                if expression_hash in seen:
                    continue
                seen.add(expression_hash)
                group.append(candidate)
                if not _candidate_has_complete_cache(candidate):
                    active_count += 1
                if active_count >= active_slots:
                    break
            return group

        def _active_group_size(group):
            return sum(not _candidate_has_complete_cache(item) for item in group)

        self.current_position['active_route'] = active_route
        logging.info(f'🧭 Stage {stage} 本轮优化路由: {active_route}')
        margin_context = {**context, 'template_role': 'MARGIN_REPAIR'}
        margin_formal, margin_rejected = select_template_candidates(
            margin_context, TEMPLATE_EXPLORATION_LIMIT, include_rejected=True
        )
        rejected.extend(margin_rejected)
        if stage == 3:
            pc_value = number((getattr(self, 'best_stats', {}) or {}).get('pc'))
            if pc_value is None:
                pc_value = number(getattr(self, 'best_pc', None))
            if pc_value is None:
                pc_blind = [
                    item for item in selected
                    if str(item.get('template_id', '')).startswith('structure.pc_')
                ]
                for item in pc_blind:
                    item['reason'] = '数值PC不可观察，不运行PC结构重塑模板'
                rejected.extend(pc_blind)
                selected = [item for item in selected if item not in pc_blind]
        formal_batch = compose_template_batch(selected, TEMPLATE_BATCH_SIZE)
        formal_hashes = {item.get('expression_hash') for item in formal_batch}
        remaining_formal = [
            item for item in selected if item.get('expression_hash') not in formal_hashes
        ]
        stage1_second_primary = compose_stage1_template_batch(
            template_candidates, TEMPLATE_BATCH_SIZE
        )
        stage1_second_primary_hashes = {
            item.get('expression_hash') for item in stage1_second_primary
        }
        stage1_second = _fill_stage_group(
            stage1_second_primary,
            [item for item in template_candidates
             if item.get('expression_hash') not in stage1_second_primary_hashes],
        )
        stage1_second_hashes = {
            item.get('expression_hash') for item in stage1_second
        }
        stage1_third_pool = [
            item for item in template_candidates
            if item.get('expression_hash') not in stage1_second_hashes
        ]
        stage1_third_primary = compose_stage1_template_batch(
            stage1_third_pool, TEMPLATE_BATCH_SIZE
        )
        stage1_third_primary_hashes = {
            item.get('expression_hash') for item in stage1_third_primary
        }
        stage1_third = _fill_stage_group(
            stage1_third_primary,
            [item for item in stage1_third_pool
             if item.get('expression_hash') not in stage1_third_primary_hashes],
        )
        stage1_used_hashes = stage1_second_hashes | {
            item.get('expression_hash') for item in stage1_third
        }
        stage1_fourth_pool = [
            item for item in template_candidates
            if item.get('expression_hash') not in stage1_used_hashes
        ]
        stage1_fourth_primary = compose_template_batch(
            stage1_fourth_pool, TEMPLATE_BATCH_SIZE
        )
        stage1_fourth_primary_hashes = {
            item.get('expression_hash') for item in stage1_fourth_primary
        }
        stage1_fourth = _fill_stage_group(
            stage1_fourth_primary,
            [item for item in stage1_fourth_pool
             if item.get('expression_hash') not in stage1_fourth_primary_hashes],
        )
        margin_ready_now = evaluate_margin_repair_readiness(
            getattr(self, 'best_stats', {}), stage
        ).get('ready')
        needs_baseline_refresh = (
            getattr(self, 'hill_stage', 1) == 1
            and int(self.current_position.get('stage_plan_cursor', 0)) == 0
            and number(getattr(self, 'initial_score', None)) is None
        )
        second = []
        third = []
        stage2_third = []
        if needs_baseline_refresh:
            source_expression = getattr(self, 'source_expression', None) or self.best_expr
            normalized = _normalize_expression(source_expression)
            baseline_cache_key = _cache_key(source_expression, self.settings)
            baseline_cached_result = self.client.history.get(baseline_cache_key)
            baseline_cache_complete = bool(
                isinstance(baseline_cached_result, dict)
                and baseline_cached_result.get('alpha_id')
                and number((baseline_cached_result.get('stats') or {}).get('sharpe_2y')) is not None
            )
            baseline_candidate = {
                'template_id': 'baseline.refresh_p2y',
                'module': __name__, 'function': 'refresh_source_baseline',
                'family': 'baseline', 'tier': 0, 'kind': 'baseline_refresh',
                'params': {}, 'expression': source_expression,
                'expression_hash': hashlib.sha256(
                    normalized.encode('utf-8')
                ).hexdigest()[:16],
                'template_version': CODE_VERSION,
                'variant_id': hashlib.sha256(
                    f'{CODE_VERSION}|baseline'.encode('utf-8')
                ).hexdigest()[:16],
                'resolved_params': {},
                'role': 'SIGNAL_BUILD',
                'target_metrics': ('sharpe', 'fitness', 'sharpe_2y', 'margin'),
                'operators': re.findall(
                    r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', source_expression
                ),
                'fields': [field.get('id') for field in fields],
                'field_type': fields[0].get('type', 'UNKNOWN'),
                'dataset_id': fields[0].get('dataset_id', 'UNKNOWN'),
                'eligible': True, 'reason': '', 'field_metadata': fields,
                'candidate_origin': 'BASELINE',
                'force_run': not baseline_cache_complete,
            }
            local_pool = self._probe_neighborhood_candidates(
                parser, fields, allowed_operators,
                limit=TEMPLATE_BATCH_SIZE * 3,
            )
            local_neighbors = _fill_stage_group(
                local_pool[:8 if baseline_cache_complete else 7],
                local_pool[8 if baseline_cache_complete else 7:],
                active_slots=8 if baseline_cache_complete else 7,
            )
            neighbor_hashes = {
                item['expression_hash'] for item in local_neighbors
            }
            used = {
                item.get('expression_hash')
                for item in [*stage1_second, *stage1_third, *stage1_fourth]
            }
            selected = [
                baseline_candidate, *local_neighbors,
                *stage1_second, *stage1_third, *stage1_fourth,
                *[item for item in selected if item.get('expression_hash') not in used],
            ]
            self.baseline_refresh_status = 'REQUIRED'
            self.current_position['baseline_refresh_status'] = 'REQUIRED'
            logging.info(
                f'🧭 首批固定结构：P2Y基线（完整缓存可复用）+ 邻域候选；'
                f'本地同骨架近邻={len(local_neighbors)}。'
            )
        elif stage == 1:
            local_pool = self._probe_neighborhood_candidates(
                parser, fields, allowed_operators, limit=TEMPLATE_BATCH_SIZE * 3
            )
            local_neighbors = _fill_stage_group(
                local_pool[:TEMPLATE_BATCH_SIZE],
                local_pool[TEMPLATE_BATCH_SIZE:],
            )
            used = {
                item.get('expression_hash')
                for item in [*stage1_second, *stage1_third, *stage1_fourth]
            }
            selected = [
                *local_neighbors, *stage1_second, *stage1_third, *stage1_fourth,
                *[item for item in selected if item.get('expression_hash') not in used],
            ]
        elif stage == 2:
            local_neighbors = self._probe_neighborhood_candidates(
                parser, fields, allowed_operators, limit=TEMPLATE_BATCH_SIZE
            )
            stage2_third = compose_template_batch(
                remaining_formal, TEMPLATE_BATCH_SIZE
            )
            used_hashes = {
                item.get('expression_hash')
                for item in [*formal_batch, *local_neighbors, *stage2_third]
            }
            selected = [
                *formal_batch, *local_neighbors, *stage2_third,
                *[item for item in remaining_formal
                  if item.get('expression_hash') not in used_hashes],
            ]
        else:
            second = compose_template_batch(remaining_formal, TEMPLATE_BATCH_SIZE)
            second_hashes = {item.get('expression_hash') for item in second}
            third = compose_template_batch([
                item for item in remaining_formal
                if item.get('expression_hash') not in second_hashes
            ], TEMPLATE_BATCH_SIZE)
            used_hashes = {
                item.get('expression_hash')
                for item in [*formal_batch, *second, *third]
            }
            selected = [
                *formal_batch, *second, *third,
                *[item for item in remaining_formal
                  if item.get('expression_hash') not in used_hashes],
            ]
        if not PREFER_CATALOG_TEMPLATES and not needs_baseline_refresh and margin_ready_now and stage in {2, 3}:
            margin_batch = self._margin_repair_candidates(
                parser, fields, allowed_operators, margin_formal, round_number=1
            )
            if len(margin_batch) != TEMPLATE_BATCH_SIZE:
                self.template_blocked_status = 'BLOCKED_INCOMPLETE_MARGIN_BATCH'
                logging.warning(
                    f'MARGIN_REPAIR_READY 但专项候选只有 {len(margin_batch)}/8；不POST。'
                )
                return False
            selected = [*margin_batch, *selected]
            self._metric(f'stage{stage}_margin_repair_ready')
            logging.info('🛠️ MARGIN_REPAIR_READY：下一批使用2+2+2+2专项候选。')
        if PREFER_CATALOG_TEMPLATES:
            # 优先在各阶段验证224模板；原有P2Y基线如必需仍占一席，不能伪造基线。
            catalog_pool = [item for item in template_candidates if item.get('catalog_status') == 'LOCAL_PASS_UNVALIDATED']
            if catalog_pool:
                baselines = [item for item in selected if item.get('kind') == 'baseline_refresh']
                preferred = [*baselines, *catalog_pool]
                used = {item.get('expression_hash') for item in preferred}
                selected = [*preferred, *[item for item in selected if item.get('expression_hash') not in used]]
                logging.info('224目录优先：阶段%s、合法目录候选%s，首批优先使用目录函数。', stage, len(catalog_pool))
        baseline_stats = getattr(self, 'best_stats', {})
        baseline_score = getattr(self, 'best_score', None)
        self.template_baseline_stats = dict(baseline_stats or {})
        self.template_baseline_gate = self._assess_stats(baseline_stats).get('gate', {})
        probe_baseline_key = candidate_rank_key(
            baseline_stats, baseline_score, getattr(self, 'hill_stage', 1)
        )[:3]
        completed = {}
        terminal_cached = []
        reusable_selected = []
        pending_batches = self.client.history.get('__pending_multi__', {})
        pending_expression_keys = {
            _cache_key(expression, self.settings)
            for pending in pending_batches.values()
            if isinstance(pending, dict) and pending.get('settings') == self.settings
            for expression in pending.get('expressions', [])
        } if isinstance(pending_batches, dict) else set()
        for candidate in selected:
            if PREFER_ADMIN_TEMPLATES:
                from Core.factor.templates.disabled_templates import blocked_reason
                disabled_reason = blocked_reason(candidate, context)
                if disabled_reason:
                    # 覆盖局部探针/专项补位，差模板只保全代码，不进入轮动。
                    candidate['reason'] = disabled_reason
                    rejected.append(candidate)
                    logging.info('跳过日志差模板 %s：%s', candidate.get('template_id'), disabled_reason)
                    continue
            cached = self.client.history.get(_cache_key(candidate['expression'], self.settings))
            if isinstance(cached, dict) and cached.get('negative_cache'):
                terminal_cached.append(candidate)
            else:
                reusable_selected.append(candidate)
        if terminal_cached:
            logging.info(
                f'⏭️ 跳过 {len(terminal_cached)} 条已确认终态失败表达式，'
                '使用后续模板补齐固定批次。'
            )
        # 在切成 8 条之前二次校验；失效项由后续候选自然补位。
        secondary_checks = batch_verify_expressions([
            candidate['expression'] for candidate in reusable_selected
        ]) if reusable_selected else []
        secondary_valid = []
        for candidate, check in zip(reusable_selected, secondary_checks):
            if check.get('valid'):
                candidate['local_validation'] = check
                secondary_valid.append(candidate)
            else:
                candidate['reason'] = '; '.join(check.get('errors') or ['二次本地校验失败'])
                rejected.append(candidate)
        reusable_selected = secondary_valid
        breadth_limit = (
            max(TEMPLATE_BREADTH_LIMIT, STAGE_BATCH_BUDGETS.get(1, 4) * 16)
            if stage == 1 else TEMPLATE_BREADTH_LIMIT
        )
        breadth = [item for item in reusable_selected if item.get('kind') != 'shape'][:breadth_limit]
        shapes = [item for item in reusable_selected if item.get('kind') == 'shape'][:TEMPLATE_SHAPE_LIMIT]
        reusable_selected = breadth + shapes
        pool_fingerprint = _source_json_hash({
            'settings': self.settings,
            'expressions': [_normalize_expression(item['expression']) for item in reusable_selected],
            'template_variants': [
                (item.get('template_id'), item.get('template_version'), item.get('variant_id'))
                for item in reusable_selected
            ],
            'route_registry': {
                name: (route.get('status'), tuple(route.get('stages') or ()))
                for name, route in sorted(ROUTE_REGISTRY.items())
            },
            'objective_version': OBJECTIVE_VERSION,
            'score_version': STAGE_SCORE_VERSION,
            'code_version': CODE_VERSION,
            'template_learning_version': TEMPLATE_LEARNING_VERSION,
        })
        self.current_position['candidate_pool_fingerprint'] = pool_fingerprint
        if self.current_position.get('blocked_candidate_pool_fingerprint') == pool_fingerprint:
            self.template_blocked_status = 'BLOCKED_INCOMPLETE_BATCH'
            logging.warning('候选池指纹未变化，保持 BLOCKED_INCOMPLETE_BATCH，不重复调度。')
            return False

        # 缓存结果与新表达式分开组批：完整缓存批直接重算新评分且不 POST；
        # 新表达式仍必须凑满固定 8 条，不能因混入缓存而提交 1..7 条。
        completed_cached = []
        active_selected = []
        for candidate in reusable_selected:
            cache_key = _cache_key(candidate['expression'], self.settings)
            cached = self.client.history.get(cache_key)
            cached_p2y_ready = number((cached.get('stats') or {}).get('sharpe_2y')) is not None if isinstance(cached, dict) else False
            if (
                isinstance(cached, dict) and cached.get('alpha_id')
                and cached.get('status') in {None, 'COMPLETE', 'CACHE_HIT'}
                and cache_key not in pending_expression_keys
                and (candidate.get('kind') != 'baseline_refresh' or cached_p2y_ready)
            ):
                completed_cached.append(candidate)
                completed[candidate['expression']] = cached
            else:
                active_selected.append(candidate)
        active_batches = [
            active_selected[index:index + TEMPLATE_BATCH_SIZE]
            for index in range(0, len(active_selected), TEMPLATE_BATCH_SIZE)
            if len(active_selected[index:index + TEMPLATE_BATCH_SIZE]) == TEMPLATE_BATCH_SIZE
        ]
        if completed_cached:
            logging.info(
                f'♻️ 发现 {len(completed_cached)} 条完整缓存表达式，'
                '逐条重算当前阶段门槛（不重复POST、不占批次预算）。'
            )
        cached_baseline = next(
            (
                completed.get(item['expression']) for item in completed_cached
                if item.get('kind') == 'baseline_refresh'
            ),
            None,
        )
        if cached_baseline is not None and self._set_refreshed_baseline(cached_baseline):
            baseline_stats = self.best_stats
            baseline_score = self.best_score
            self.template_baseline_stats = dict(baseline_stats or {})
            self.template_baseline_gate = self._assess_stats(baseline_stats).get('gate', {})
        run_id = f"{alpha_id}-{uuid4().hex[:10]}"

        for candidate in completed_cached:
            result = dict(completed[candidate['expression']])
            result['status'] = 'CACHE_HIT'
            if candidate.get('kind') != 'baseline_refresh':
                margin_evidence = (
                    self._margin_repair_effect(result.get('stats', {}))
                    if candidate.get('role') == 'MARGIN_REPAIR' else {}
                )
                result.update(margin_evidence)
                result['gate_improved'] = (
                    margin_evidence.get('margin_effective_improvement', False)
                    if candidate.get('role') == 'MARGIN_REPAIR'
                    else (
                        self._gate_progress_improved(result.get('stats', {}), candidate)
                        and self._retains_previous_gates(result.get('stats', {}))
                    )
                )
                result['became_best'] = (
                    self._adopt_margin_result(candidate['expression'], result, alpha_id)
                    if candidate.get('role') == 'MARGIN_REPAIR'
                    else self._adopt_template_result(candidate['expression'], result, alpha_id)
                )
            candidate['field_metadata'] = fields
            candidate['candidate_key'] = f"{run_id}|{candidate['expression_hash']}|cache"
            self._remember_stage_pass_candidate(candidate, result)
            self._record_template_candidate(
                run_id, alpha_id, candidate, 'CACHE_HIT', result=result
            )
            self._metric('cache_hits')
        self.current_position['stage_cache_batches_reused'] = (
            int(self.current_position.get('stage_cache_batches_reused') or 0)
            + len(completed_cached) // TEMPLATE_BATCH_SIZE
        )
        cached_limit = STAGE_MAX_IMMEDIATE_BRANCHES if stage == 1 else 1
        cached_immediate = select_immediate_stage_branches(
            getattr(self, 'stage_pass_candidates', []), stage, cached_limit
        )
        if stage < 3 and cached_immediate:
            target = int(getattr(self, 'stage_target_batches', 1))
            self.current_position['stage_branches'] = cached_immediate
            self.current_position['template_batch'] = target
            self.current_position['stage_plan_cursor'] = target
            self._metric(f'stage{stage}_to_stage{stage + 1}_immediate')
            logging.info(
                f'♻️ 缓存中已有 {len(cached_immediate)} 条 Stage {stage} PASS分支；'
                f'不新建POST，立即交接 Stage {stage + 1}。'
            )
            self.save_checkpoint(alpha_id)
            return True

        for candidate in rejected:
            candidate['field_metadata'] = fields
            reason = candidate.get('reason', '')
            status = 'LOCAL_REJECTED'
            if '权限' in reason:
                status = 'LIVE_REJECTED'
            elif '字段' in reason:
                status = 'FIELD_REJECTED'
            candidate['candidate_key'] = f"{run_id}|{candidate.get('template_id')}|rejected"
            self._record_template_candidate(run_id, alpha_id, candidate, status, reason=reason)

        stage_target = int(getattr(self, 'stage_target_batches', 8))
        start_batch = int(self.current_position.get('stage_post_batches_used', 0))
        remaining_breadth_batches = max(0, stage_target - start_batch)
        # Margin 路由是“当前逻辑批次”的替代项，不是阶段开头新增的历史批次。
        # 恢复到 template_batch>0 时仍必须先取列表首个 Margin 批，不能按旧位置跳过它；
        # batch_index 继续从 start_batch 计数，因此不会扩大阶段预算。
        batches = active_batches[:remaining_breadth_batches]
        if remaining_breadth_batches and not batches:
            if active_selected and all(
                _cache_key(item['expression'], self.settings) in pending_expression_keys
                for item in active_selected
            ):
                self.template_pending_status = 'RESULTS_UNOBSERVED'
                logging.warning(
                    '当前未缓存候选均属于已有平台断点；只读对账，'
                    '不用缓存表达式重新POST。'
                )
                return False
            if completed_cached:
                self.current_position['template_batch'] = stage_target
                self.current_position['stage_plan_cursor'] = stage_target
                self.current_position['stage_settled_candidate_exhausted'] = True
                logging.info(
                    '候选池只有完整缓存且已无新的8条批次；'
                    '按当前门槛结算，实际POST预算不增加。'
                )
                self.save_checkpoint(alpha_id)
                return True
            if int(self.current_position.get('stage_post_batches_used') or 0) > 0:
                logging.info(
                    '当前阶段已完成至少一个完整批次，后续候选不足8条；'
                    '使用当前最佳结果结算，不预判未来批次。'
                )
                self.current_position['template_batch'] = stage_target
                self.current_position['stage_plan_cursor'] = stage_target
                self.current_position['stage_settled_candidate_exhausted'] = True
                self.save_checkpoint(alpha_id)
                return True
            self.current_position['blocked_candidate_pool_fingerprint'] = pool_fingerprint
            self.template_blocked_status = 'BLOCKED_INCOMPLETE_BATCH'
            logging.warning(
                'BLOCKED_INCOMPLETE_BATCH：第一批无法补足固定8条；候选池变化前不重试。'
            )
            self.save_checkpoint(alpha_id)
            return False
        for relative_index, batch in enumerate(batches):
            batch_index = start_batch + relative_index
            if self.stop_requested:
                continue
            if len(batch) != TEMPLATE_BATCH_SIZE:
                for candidate in batch:
                    candidate['field_metadata'] = fields
                    candidate['candidate_key'] = f"{run_id}|{candidate['expression_hash']}"
                    self._record_template_candidate(
                        run_id, alpha_id, candidate, 'DEFERRED_INCOMPLETE_BATCH',
                        reason=f'批次不足固定8条（{len(batch)}/8），未调用模拟接口',
                    )
                summarize_template_usage()
                self.save_checkpoint(alpha_id)
                return False
            for candidate in batch:
                candidate['field_metadata'] = fields
                candidate['candidate_key'] = f"{run_id}|{candidate['expression_hash']}"
                if candidate.get('candidate_origin') == 'FORMAL_TEMPLATE':
                    candidate['formal_batch_id'] = f'{run_id}:{batch_index}'
                self._record_template_candidate(run_id, alpha_id, candidate, 'GENERATED')
            batch_expressions = [candidate['expression'] for candidate in batch]
            forced_expressions = [
                candidate['expression'] for candidate in batch
                if candidate.get('force_run')
            ]
            results = (
                self.evaluate_batch(batch_expressions, force_run=forced_expressions)
                if forced_expressions else self.evaluate_batch(batch_expressions)
            )
            baseline_candidate = next(
                (item for item in batch if item.get('kind') == 'baseline_refresh'), None
            )
            baseline_ready = True
            if baseline_candidate is not None:
                baseline_result = results.get(baseline_candidate['expression'])
                baseline_ready = self._set_refreshed_baseline(baseline_result)
                if baseline_ready:
                    baseline_stats = self.best_stats
                    baseline_score = self.best_score
                    self.template_baseline_stats = dict(baseline_stats or {})
                    self.template_baseline_gate = self._assess_stats(
                        baseline_stats
                    ).get('gate', {})
                    probe_baseline_key = candidate_rank_key(
                        baseline_stats, baseline_score,
                        getattr(self, 'hill_stage', 1),
                    )[:3]
            for candidate in batch:
                expression = candidate['expression']
                result = results.get(expression, {
                    'status': 'RESULTS_UNOBSERVED', 'score': 0,
                    'stats': {'passed': False}, 'alpha_id': None, 'url': '',
                })
                if result.get('status') is None:
                    result['status'] = 'CACHE_HIT'
                margin_evidence = (
                    self._margin_repair_effect(result.get('stats', {}))
                    if candidate.get('role') == 'MARGIN_REPAIR' else {}
                )
                result.update(margin_evidence)
                result['gate_improved'] = (
                    margin_evidence.get('margin_effective_improvement', False)
                    if candidate.get('role') == 'MARGIN_REPAIR'
                    else (
                        baseline_ready
                        and candidate.get('kind') != 'baseline_refresh'
                        and self._gate_progress_improved(result.get('stats', {}), candidate)
                        and self._retains_previous_gates(result.get('stats', {}))
                    )
                )
                if result['gate_improved']:
                    self._metric('gate_improvements')
                became_best = False
                if baseline_ready and candidate.get('kind') != 'baseline_refresh':
                    became_best = (
                        self._adopt_margin_result(expression, result, alpha_id)
                        if candidate.get('role') == 'MARGIN_REPAIR'
                        else self._adopt_template_result(expression, result, alpha_id)
                    )
                result['became_best'] = became_best
                self._remember_stage_pass_candidate(candidate, result)
                self._record_template_candidate(
                    run_id, alpha_id, candidate, result['status'], result=result,
                    reason='' if result['status'] in {'COMPLETE', 'CACHE_HIT'} else result['status'],
                )
                completed[expression] = result
            summarize_template_usage()
            if not baseline_ready:
                pending_status = (
                    self.baseline_refresh_status
                    if (
                        str(self.baseline_refresh_status).startswith('PENDING')
                        or self.baseline_refresh_status == 'RESULTS_UNOBSERVED'
                    )
                    else 'PENDING_STAGE_SCORE'
                )
                self.template_pending_status = pending_status
                self.current_position['baseline_refresh_status'] = pending_status
                self.save_checkpoint(alpha_id)
                logging.warning(
                    f'原表达式基线尚不可比较；首批保持 {pending_status}，'
                    '不虚构基线、不执行晋级。'
                )
                return False
            batch_complete = all(
                results.get(candidate['expression'], {}).get('status') in {'COMPLETE', 'CACHE_HIT'}
                and results.get(candidate['expression'], {}).get('alpha_id')
                for candidate in batch
            )
            if not batch_complete:
                terminal_count = sum(
                    results.get(candidate['expression'], {}).get('status') in {'FAILED', 'CANCELLED'}
                    for candidate in batch
                )
                if terminal_count:
                    logging.warning(
                        f'模板第 {batch_index + 1} 批含 {terminal_count} 条终态失败/取消；'
                        '失败表达式已缓存，本批不推进，下轮由后续模板补齐。'
                    )
                else:
                    logging.warning(
                        f"模板第 {batch_index + 1} 批未完整观察到8条结果；"
                        "保留平台断点并停止后续回测。"
                    )
                self.save_checkpoint(alpha_id)
                return False
            self.current_position['stage_plan_cursor'] = batch_index + 1
            self.current_position['template_batch'] = batch_index + 1
            self.current_position['stage_post_batches_used'] = int(
                self.current_position.get('stage_post_batches_used') or 0
            ) + 1
            self.current_position['template_batches_executed'] = int(
                self.current_position.get('stage_post_batches_used') or 0
            )
            observed_keys = {
                str(results.get(candidate['expression'], {}).get('alpha_id'))
                for candidate in batch
                if results.get(candidate['expression'], {}).get('alpha_id')
                and results.get(candidate['expression'], {}).get('status') in {
                    'COMPLETE', 'CACHE_HIT', None,
                }
            }
            self.current_position['stage_observed_candidates'] = int(
                self.current_position.get('stage_observed_candidates') or 0
            ) + len(observed_keys)
            stage = int(getattr(self, 'hill_stage', 1))
            if stage == 1:
                self._metric(f'stage1_batch_{batch_index + 1}_runs')
                if any(
                    evaluate_stage_candidate(
                        results.get(candidate['expression'], {}).get('stats', {}), 1
                    ).get('eligible')
                    for candidate in batch
                ):
                    self._metric(f'stage1_batch_{batch_index + 1}_pass_batches')
            attempted_routes = list(self.current_position.get('attempted_routes') or [])
            for route_name in (candidate_route(candidate) for candidate in batch):
                if route_name not in attempted_routes:
                    attempted_routes.append(route_name)
            self.current_position['attempted_routes'] = attempted_routes
            next_batch_position = relative_index + 1
            if next_batch_position < len(batches) and stage != 1:
                next_route = choose_route(
                    stage, self._assess_stats(self.best_stats).get('gate', {}),
                    attempted_routes,
                )
                best_position = min(
                    range(next_batch_position, len(batches)),
                    key=lambda position: sum(
                        candidate_route(candidate) != next_route
                        for candidate in batches[position]
                    ),
                )
                batches[next_batch_position], batches[best_position] = (
                    batches[best_position], batches[next_batch_position]
                )
                self.current_position['active_route'] = next_route
                logging.info(
                    f'🧭 Stage {stage} 下一批按最新最大缺口切换到未尝试路由: '
                    f'{next_route}'
                )
            margin_batch = bool(batch) and all(
                candidate.get('role') == 'MARGIN_REPAIR' for candidate in batch
            )
            margin_batch_success = margin_batch and any(
                results.get(candidate['expression'], {}).get('margin_effective_improvement')
                for candidate in batch
            )
            if margin_batch:
                self.current_position['margin_batches_executed'] = int(
                    self.current_position.get('margin_batches_executed') or 0
                ) + 1
                self._metric('margin_repair_batches')
                for candidate in batch:
                    evidence = results.get(candidate['expression'], {})
                    if evidence.get('margin_effective_improvement'):
                        self._metric('margin_repair_complete_improvements')
                    if evidence.get('margin_threshold_crossed'):
                        self._metric('margin_threshold_crossed')
                    if evidence.get('turnover_retained') is False:
                        self._metric('margin_turnover_invalid')
            self.save_checkpoint(alpha_id)
            immediate_limit = STAGE_MAX_IMMEDIATE_BRANCHES if stage == 1 else 1
            immediate = select_immediate_stage_branches(
                getattr(self, 'stage_pass_candidates', []), stage, immediate_limit
            )
            if stage < 3 and immediate:
                self.current_position['stage_branches'] = immediate
                self.current_position['template_batch'] = stage_target
                self.current_position['stage_plan_cursor'] = stage_target
                self._metric(f'stage{stage}_to_stage{stage + 1}_immediate')
                logging.info(
                    f'⚡ Stage {stage} 出现 {len(immediate)} 条去重PASS分支；'
                    f'立即交接 Stage {stage + 1}，停止本阶段剩余批次。'
                )
                self.save_checkpoint(alpha_id)
                return True
            batch_improved = any(
                item.get('gate_improved') for item in results.values()
            )
            margin_batches_used = int(
                self.current_position.get('margin_batches_executed') or 0
            )
            route_ready = evaluate_margin_repair_readiness(
                getattr(self, 'best_stats', {}), stage
            ).get('ready')
            may_schedule_margin = (
                next_batch_position < len(batches)
                and route_ready
                and margin_batches_used < MARGIN_REPAIR_MAX_BATCHES_PER_STAGE
                and (not margin_batch or margin_batch_success)
                and (stage != 1 or batch_index >= 1)
            )
            if may_schedule_margin:
                self.template_baseline_stats = dict(self.best_stats or {})
                self.template_baseline_gate = self._assess_stats(
                    self.template_baseline_stats
                ).get('gate', {})
                margin_round = margin_batches_used + 1
                next_margin_batch = self._margin_repair_candidates(
                    parser, fields, allowed_operators, margin_formal,
                    round_number=margin_round,
                )
                if len(next_margin_batch) != TEMPLATE_BATCH_SIZE:
                    self.template_blocked_status = 'BLOCKED_INCOMPLETE_MARGIN_BATCH'
                    self.save_checkpoint(alpha_id)
                    logging.warning(
                        f'Margin第 {margin_round} 批只有 {len(next_margin_batch)}/8 条；不POST。'
                    )
                    return False
                batches[next_batch_position] = next_margin_batch
                self._metric(f'stage{stage}_margin_repair_ready')
                logging.info(
                    f'🛠️ 下一批切换为 Margin 专项第 {margin_round} 批；'
                    '仍占用当前阶段既有预算。'
                )
            calibration_due = (
                stage == 1 and batch_index == 0
                and self._template_calibration_due(scope, alpha_id)
            )
            next_formal_missing = not may_schedule_margin and (
                stage == 1 and batch_index == 0
                and batch_index + 1 < stage_target
                and _active_group_size(stage1_second) != TEMPLATE_BATCH_SIZE
            ) or (
                stage == 2 and batch_index == 1 and batch_improved
                and len(stage2_third) != TEMPLATE_BATCH_SIZE
            ) or (
                stage == 3 and batch_index == 0 and batch_improved
                and len(second) != TEMPLATE_BATCH_SIZE
            ) or (
                stage == 3 and batch_index == 1 and batch_improved
                and len(third) != TEMPLATE_BATCH_SIZE
            )
            if next_formal_missing:
                self.template_blocked_status = 'BLOCKED_INCOMPLETE_TEMPLATE_BATCH'
                self.current_position['blocked_candidate_pool_fingerprint'] = pool_fingerprint
                self.save_checkpoint(alpha_id)
                logging.warning(
                    f'Stage {stage} 下一正式模板批不足8条；不POST、不跨角色补齐。'
                )
                return False
            should_stop = (
                (stage == 1 and batch_index >= 1 and not batch_improved)
                or (stage == 2 and batch_index >= 1 and not batch_improved)
                or (stage == 3 and not batch_improved)
            ) and not may_schedule_margin
            if should_stop:
                if calibration_due:
                    logging.info(
                        '🧪 本范围已完成7个Stage 1首批，虽无局部改善仍执行一次正式模板校准批。'
                    )
                    continue
                logging.info(
                    f'🧪 Stage {stage} 当前决策批未减少硬门槛缺口或破坏已有门槛；'
                    '停止本阶段后续批次。'
                )
                self.current_position['template_batch'] = stage_target
                self.current_position['stage_plan_cursor'] = stage_target
                self.current_position['probe_stopped_no_improvement'] = True
                self.save_checkpoint(alpha_id)
                return True

        if batches and len(batches) < remaining_breadth_batches:
            logging.info(
                '当前阶段候选只够已执行批次；使用当前最佳结果结算，'
                '不因尚未发生的未来批次阻塞。'
            )
            self.current_position['template_batch'] = stage_target
            self.current_position['stage_settled_candidate_exhausted'] = True
            self.save_checkpoint(alpha_id)

        if stage_target >= 8 and self.current_position.get('template_batch', 0) < 8 and not self.stop_requested:
            adaptive_pool = self._adaptive_template_candidates(completed, allowed_operators, fields)
            adaptive_cached = []
            adaptive_active = []
            adaptive_failed = 0
            for candidate in adaptive_pool:
                if PREFER_ADMIN_TEMPLATES:
                    from Core.factor.templates.disabled_templates import blocked_reason
                    if blocked_reason(candidate, context):
                        continue
                cached = self.client.history.get(_cache_key(candidate['expression'], self.settings))
                if isinstance(cached, dict) and cached.get('negative_cache'):
                    adaptive_failed += 1
                elif (
                    isinstance(cached, dict) and cached.get('alpha_id')
                    and cached.get('status') in {None, 'COMPLETE', 'CACHE_HIT'}
                ):
                    adaptive_cached.append(candidate)
                else:
                    adaptive_active.append(candidate)
            if adaptive_failed:
                logging.info(f'⏭️ 第 8 批跳过 {adaptive_failed} 条终态失败自适应表达式。')
            adaptive = (
                adaptive_cached[:TEMPLATE_BATCH_SIZE]
                if len(adaptive_cached) >= TEMPLATE_BATCH_SIZE
                else adaptive_active[:TEMPLATE_BATCH_SIZE]
            )
            if len(adaptive) == TEMPLATE_BATCH_SIZE:
                results = self.evaluate_batch([candidate['expression'] for candidate in adaptive])
                for candidate in adaptive:
                    candidate['candidate_key'] = f"{run_id}|{candidate['expression_hash']}"
                    result = results.get(candidate['expression'], {
                        'status': 'RESULTS_UNOBSERVED', 'score': 0,
                        'stats': {'passed': False}, 'alpha_id': None, 'url': '',
                    })
                    if result.get('status') is None:
                        result['status'] = 'CACHE_HIT'
                    became_best = self._adopt_template_result(candidate['expression'], result, alpha_id)
                    result['became_best'] = became_best
                    self._record_template_candidate(
                        run_id, alpha_id, candidate, result['status'], result=result,
                        reason='' if result['status'] in {'COMPLETE', 'CACHE_HIT'} else result['status'],
                    )
                summarize_template_usage()
                adaptive_complete = all(
                    results.get(candidate['expression'], {}).get('status') in {'COMPLETE', 'CACHE_HIT'}
                    and results.get(candidate['expression'], {}).get('alpha_id')
                    for candidate in adaptive
                )
                if not adaptive_complete:
                    logging.warning('模板第 8 批未完整观察到8条结果；保留断点。')
                    self.save_checkpoint(alpha_id)
                    return False
            else:
                logging.warning(
                    f'第 8 批只有 {len(adaptive)}/8 条自适应候选；保留断点，不冒充完成。'
                )
                self.save_checkpoint(alpha_id)
                return False
            self.current_position['template_batch'] = 8
            self.save_checkpoint(alpha_id)
        summarize_template_usage()
        return self.current_position.get('template_batch', 0) >= stage_target

    def optimize_single_alpha(self, alpha_id):
        """优化单个Alpha - 异步版本"""
        logging.info(f"开始异步优化 Alpha ID: {alpha_id}")

        # 续爬也需要当前详情来判断 Region 对应的设置候选。
        details = self.client.get_alpha_details(alpha_id)
        if not details:
            logging.error(f"无法获取 Alpha {alpha_id} 的详情")
            return 'PENDING'

        # 为每个Alpha ID使用单独的检查点文件
        if not self.load_checkpoint(alpha_id):
            logging.info(f"初始化目标 Alpha: {alpha_id}")
            self.settings = normalize_simulation_settings(details['settings'])
            regular = details['regular']
            self.best_expr = regular if isinstance(regular, str) else regular['code']
            self.source_expression = self.best_expr
            self.best_alpha_id = alpha_id  # 设置初始Alpha ID
            self.initial_alpha_id = alpha_id  # 设置初始Alpha ID

            # 只从指标重算；旧 PASS/PC/SC 奖励不再进入基础分。
            initial_stats = self._stats_from_details(details)
            source_sc = number((getattr(self, 'source_record', {}) or {}).get('sc_value'))
            initial_stats['sc'] = (
                source_sc if source_sc is not None else
                None if CONTINUOUS_MODE else get_sc_check(_core_client(self.client), alpha_id)
            )
            initial_result = self._apply_score({
                'status': 'COMPLETE', 'alpha_id': alpha_id, 'stats': initial_stats,
            })
            if initial_result.get('score') is None:
                gate = initial_result.get('stage_gate', {})
                self.best_stats = initial_stats
                self.best_score = None
                self.best_base_score = None
                self.initial_score = None
                self.score_components = initial_result.get('score_components', {})
                self.score_penalties = initial_result.get('score_penalties', {})
                self.score_version = STAGE_SCORE_VERSION
                self.baseline_refresh_status = 'REQUIRED'
                self.current_position['baseline_refresh_status'] = 'REQUIRED'
                self.save_checkpoint(alpha_id)
                logging.warning(
                    '初始评分缺少 %s；首批将用原表达式刷新P2Y基线，不记为代码失败。',
                    ','.join(gate.get('missing') or initial_result.get('missing') or ['unknown']),
                )
            else:
                with self.score_lock:
                    self.best_stats = initial_stats
                    self.best_score = initial_result['score']
                    self.best_base_score = initial_result['score']
                    self.initial_score = initial_result['score']
                    self.score_components = initial_result['score_components']
                    self.score_penalties = initial_result.get('score_penalties', {})
                    self.score_version = STAGE_SCORE_VERSION
                self.baseline_refresh_status = 'NOT_REQUIRED'
                self.current_position['baseline_refresh_status'] = 'NOT_REQUIRED'
            if initial_result.get('score') is not None:
                gate = initial_result['stage_gate']
                logging.info(
                    f"[{STAGE_SCORE_VERSION}初始评分] 阶段={self.hill_stage} 门槛={gate.get('status')} "
                    f"Sharpe分={self.score_components.get('sharpe', 0):.2f} "
                    f"Fitness分={self.score_components.get('fitness', 0):.2f} "
                    f"Margin分={self.score_components.get('margin', 0):.2f} "
                    f"SC扣分={self.score_penalties.get('sc', 0):.2f} "
                    f"PC扣分={self.score_penalties.get('pc', 0):.2f} "
                    f"总分={self.best_score:.2f}"
                )

            self.save_checkpoint(alpha_id)

        self.source_expression = getattr(self, 'source_expression', None) or (
            details['regular'] if isinstance(details['regular'], str)
            else details['regular']['code']
        )

        if self.score_version != STAGE_SCORE_VERSION:
            score_details = details
            if self.best_alpha_id and self.best_alpha_id != alpha_id:
                score_details = self.client.get_alpha_details(self.best_alpha_id) or details
            self.best_stats = self._stats_from_details(score_details, self.best_stats)
            source_sc = number((getattr(self, 'source_record', {}) or {}).get('sc_value'))
            if number(self.best_stats.get('sc')) is None:
                self.best_stats['sc'] = source_sc
            migrated = self._apply_score({
                'status': 'COMPLETE', 'alpha_id': self.best_alpha_id,
                'stats': self.best_stats,
            })
            if migrated.get('score') is None:
                self.best_score = None
                self.best_base_score = None
                self.initial_score = None
                self.score_components = migrated.get('score_components', {})
                self.score_penalties = migrated.get('score_penalties', {})
                self.score_version = STAGE_SCORE_VERSION
                self.baseline_refresh_status = 'REQUIRED'
                self.current_position['baseline_refresh_status'] = 'REQUIRED'
                self.save_checkpoint(alpha_id)
                logging.warning('旧检查点评分仍缺指标；首批将刷新原表达式P2Y基线。')
            else:
                self.best_score = migrated['score']
                self.best_base_score = migrated['score']
                self.initial_score = migrated['score']
                self.score_components = migrated['score_components']
                self.score_penalties = migrated.get('score_penalties', {})
                self.score_version = STAGE_SCORE_VERSION
                self.baseline_refresh_status = 'NOT_REQUIRED'
                self.current_position['baseline_refresh_status'] = 'NOT_REQUIRED'
                logging.info(
                    f"♻️ 旧检查点已按{STAGE_SCORE_VERSION}重算: "
                    f"门槛={migrated['stage_gate'].get('status')} "
                    f"总分={self.best_score:.2f}"
                )
            self.save_checkpoint(alpha_id)

        logging.info("=" * 50)
        logging.info(f"初始公式: {self.best_expr}")
        logging.info(
            f"初始分数: \033[97m{self._score_text(self.initial_score)}\033[0m "
            f"(ID: {self.initial_alpha_id})"
        )
        logging.info(
            f"当前最优分数: \033[97m{self._score_text(self.best_score)}\033[0m "
            f"(ID: {self.best_alpha_id})"
        )
        logging.info("=" * 50)

        parser = SmartExpression(self.best_expr, self.settings, self.client)

        # 持续模式严格分为 2、追加 3、再追加 3 个批次；每批固定 8 条。
        stage_target = int(getattr(self, 'stage_target_batches', 8))
        if self.current_position.get('template_batch', 0) < stage_target:
            template_complete = self.run_template_exploration(alpha_id, parser)
            if not template_complete or self.current_position.get('template_batch', 0) < stage_target:
                logging.info('模板批次仍为 PENDING，本轮不进入传统局部爬山。')
                return (
                    getattr(self, 'template_pending_status', None)
                    or getattr(self, 'template_blocked_status', None)
                    or 'PENDING'
                )
            parser = SmartExpression(self.best_expr, self.settings, self.client)
        if hasattr(self, 'stage_target_batches'):
            logging.info(
                f'✅ Stage {getattr(self, "hill_stage", 1)} 预算到达 '
                f'{stage_target} 批，本阶段停止；'
                '持续模式不再追加传统局部爬山批次。'
            )
            return 'COMPLETE'

        # 1. 优化数据字段 (Data Field)
        n_data = len([t for t in parser.tokens if t['type'] == 'data_field'])
        if self.current_position['data_field'] < n_data:
            logging.info(f">>> 开始优化数据字段 (共 {n_data} 个位置)")
            for i in range(self.current_position['data_field'], n_data):
                if self.stop_requested: 
                    logging.info("🛑 [外层中断] 停止优化数据字段")
                    break
                self._optimize_step(parser, 'data_field', i, alpha_id)
                self.current_position['data_field'] = i + 1
                self.save_checkpoint(alpha_id)

        # 2. 优化数值 (Number/TimeWindow - 回归 v4.4 稳健顺序)
        parser = SmartExpression(self.best_expr, self.settings, self.client)
        # 找到所有非 lambda/tvr 参数的数字 Token
        n_nums = len([t for t in parser.tokens if t['type'] == 'number' 
                     and not t['text'].startswith('lambda_') 
                     and 'tvr' not in t['text']])
        
        if self.current_position['number'] < n_nums:
            logging.info(f">>> 开始按顺序优化所有数值位置 (共 {n_nums} 个)")
            for i in range(self.current_position['number'], n_nums):
                if self.stop_requested: 
                    logging.info("🛑 [外层中断] 停止优化数值位置")
                    break
                # 注意：统一使用 'number' 类型调用步进优化，generate_neighbors 内部会自适应处理
                self._optimize_step(parser, 'number', i, alpha_id)
                self.current_position['number'] = i + 1
                self.save_checkpoint(alpha_id)

        # 4. 优化分组 (Group)
        parser = SmartExpression(self.best_expr, self.settings, self.client)
        n_groups = len([t for t in parser.tokens if t['type'] == 'group'])
        if self.current_position['group'] < n_groups:
            logging.info(f">>> 开始优化分组 (共 {n_groups} 个位置)")
            for i in range(self.current_position['group'], n_groups):
                if self.stop_requested: 
                    logging.info("🛑 [外层中断] 停止优化分组")
                    break
                self._optimize_step(parser, 'group', i, alpha_id)
                self.current_position['group'] = i + 1
                self.save_checkpoint(alpha_id)

        # 5. 优化运算符 (Operator)
        parser = SmartExpression(self.best_expr, self.settings, self.client)
        n_ops = len([t for t in parser.tokens if t['type'] == 'operator'])
        if self.current_position['operator'] < n_ops:
            logging.info(f">>> 开始优化运算符 (共 {n_ops} 个位置)")
            for i in range(self.current_position['operator'], n_ops):
                if self.stop_requested: 
                    logging.info("🛑 [外层中断] 停止优化运算符")
                    break
                self._optimize_step(parser, 'operator', i, alpha_id)
                self.current_position['operator'] = i + 1
                self.save_checkpoint(alpha_id)
    
        if details.get('region') in ['ASI', 'EUR', 'GLB', 'USA']:
            CANDIDATE_NEUTRALIZATIONS.append("REVERSION_AND_MOMENTUM")
            CANDIDATE_NEUTRALIZATIONS.append("STATISTICAL")
            CANDIDATE_NEUTRALIZATIONS.append("CROWDING")
            CANDIDATE_NEUTRALIZATIONS.append("FAST")
            CANDIDATE_NEUTRALIZATIONS.append("SLOW")
            CANDIDATE_NEUTRALIZATIONS.append("SLOW_AND_FAST")

        if details.get('region')  in ['ASI', 'EUR', 'GLB']:

            CANDIDATE_NEUTRALIZATIONS.append("COUNTRY")

        # Multi-Simulation要求每批固定8条；不同settings不能安全混入同一批。
        # neutralization/decay 已由表达式模板扫频覆盖，这里不再伪装成单条设置优化。
        logging.info('⏭️ 设置参数单条扫频已停用；使用固定8条表达式模板完成Decay/中性化探索')

        logging.info(" ")
        logging.info("\033[93m" + "╔════════════════════ Alpha 优化报告 ════════════════════╗" + "\033[0m")
        logging.info(
            f" 🏁 初始 Alpha: {self.initial_alpha_id}  -->  "
            f"Score: {self._score_text(self.initial_score)}"
        )
        logging.info(
            f" 🏆 最终 Alpha: {self.best_alpha_id}  -->  "
            f"Score: {self._score_text(self.best_score)}"
        )
        initial_score = number(self.initial_score)
        best_score = number(self.best_score)
        improvement = (
            best_score - initial_score
            if best_score is not None and initial_score is not None else None
        )
        logging.info(
            f" 📈 分数提升: \033[92m{self._score_text(improvement, '+.4f')}\033[0m"
        )
        
        # 提取详细结果
        final_details = self.client.get_alpha_details(self.best_alpha_id)
        final_is_passed = False
        final_stats_str = "未知"
        if final_details and 'is' in final_details:
            final_is_passed = not any(c.get('result') == 'FAIL' for c in final_details['is'].get('checks', []))
            st = final_details['is']
            final_stats_str = (
                f"Sharpe: {self._score_text(st.get('sharpe'), '.2f')} | "
                f"Fitness: {self._score_text(st.get('fitness'), '.2f')} | "
                f"Margin: {self._score_text(st.get('margin'), '.4f')}"
            )
        
        status_text = "\033[92m通过 (Pass) ✅\033[0m" if final_is_passed else "\033[91m未通过 (Fail) ❌\033[0m"
        logging.info(f" 🛡️ 检查结果: {status_text}")
        logging.info(f" 📊 核心指标: {final_stats_str}")
        logging.info(f" 📄 最终表达式: \033[97m{self.best_expr}\033[0m")
        logging.info("\033[93m" + "╚════════════════════════════════════════════════════════╝" + "\033[0m")
        logging.info(" ")

        # 发送完成通知邮件
        if EMAIL_CONFIG.get('enabled', False):
            # 获取初始Alpha和最终Alpha的通过状态
            initial_details = self.client.get_alpha_details(self.initial_alpha_id) if self.initial_alpha_id else None
            final_details = self.client.get_alpha_details(self.best_alpha_id) if self.best_alpha_id else None
            
            initial_passed = False
            final_passed = False
            
            if initial_details and 'is' in initial_details and 'checks' in initial_details['is']:
                checks = initial_details['is']['checks']
                if checks and not any(c.get('result') == 'FAIL' for c in checks):
                    initial_passed = True
                    
            if final_details and 'is' in final_details and 'checks' in final_details['is']:
                checks = final_details['is']['checks']
                if checks and not any(c.get('result') == 'FAIL' for c in checks):
                    final_passed = True
            
            subject = f"Alpha {alpha_id} 回测任务已完成"
            
            # 提取最终详细统计
            final_stats = "未知"
            if final_details and 'is' in final_details:
                st = final_details['is']
                final_stats = (
                    f"Sharpe: {self._score_text(st.get('sharpe'), '.2f')}, "
                    f"Fitness: {self._score_text(st.get('fitness'), '.2f')}, "
                    f"Margin: {self._score_text(st.get('margin'), '.4f')}, "
                    f"TO: {self._score_text(st.get('turnover'), '.2%')}"
                )

            content = f"""您的 Alpha {alpha_id} 回测任务已经全部完成！

🏁 初始 Alpha: {self.initial_alpha_id} | 分数: {self._score_text(self.initial_score)}
🏆 最终 Alpha: {self.best_alpha_id} | 分数: {self._score_text(self.best_score)}
📈 总计提升: {self._score_text(improvement, '+.4f')}
✅ 是否通过检查: {'通过 (Pass)' if final_is_passed else '未通过 (Fail)'}
✨ 最终指标: {final_stats}
📄 最终表达式: {self.best_expr}

详细结果请查看日志文件: {os.path.join(RUN_OUTPUT_DIR, f"{alpha_id}_hill_climbing_v4.7.log")}
"""
            send_qq_email(subject, content)

        return 'COMPLETE'

    def _optimize_step(self, parser, type_name, index, alpha_id):
        """同步优化单个步骤 (恢复 v4.3 逻辑)"""
        start_step_score = self.best_score

        if self.best_expr != parser.original_expr:
            parser = SmartExpression(self.best_expr, self.settings, self.client)

        neighbors = parser.generate_neighbors(type_name, index)
        if not neighbors: return

        logging.info(
            f"正在优化 {type_name} 第 {index + 1} 个位置，共 {len(neighbors)} 个候选项... "
            f"(当前基准: {self._score_text(self.best_score)})")

        current_batch_size = min(BATCH_SIZE, len(neighbors))

        # 从检查点中存储的批次偏移量开始处理
        start_batch = self.current_position.get('batch_offset', 0)

        stale_batches = 0
        for i in range(start_batch, len(neighbors), current_batch_size):
            score_before_batch = self.best_score
            batch = neighbors[i:i + current_batch_size]
            batch_index = i // current_batch_size + 1
            total_batches = (len(neighbors) - 1) // current_batch_size + 1
            logging.info(f"  > 处理批次 {batch_index}/{total_batches} (本批 {len(batch)} 个)... [位置: {type_name} 第 {index + 1} 个]")

            results = self.evaluate_batch(batch)

            if not results: continue

            eligible_results = [
                (expr, data) for expr, data in results.items()
                if data.get('status') in {'COMPLETE', 'CACHE_HIT', None}
                and data.get('stage_gate', {}).get('passed')
            ]
            if eligible_results:
                challenger = self._select_batch_challenger(eligible_results)
                if challenger:
                    best_in_batch_expr, best_in_batch_data = challenger
                    adopted = self._adopt_result(best_in_batch_expr, best_in_batch_data, alpha_id)
                    logging.info(
                        f"   [相关性递减上位] 候选={best_in_batch_data.get('alpha_id')} "
                        f"总分={best_in_batch_data.get('score', 0):.2f} 是否上位={'是' if adopted else '否'}"
                    )

            # 更新进度
            self.current_position['batch_offset'] = i + len(batch)
            self.save_checkpoint(alpha_id)

            if self.best_score > score_before_batch + MIN_SCORE_IMPROVEMENT:
                stale_batches = 0
            else:
                stale_batches += 1
                if stale_batches >= MAX_STALE_BATCHES:
                    remaining = max(0, len(neighbors) - i - len(batch))
                    logging.info(
                        f"  -> 当前位置连续 {stale_batches} 个局部批次无提升，"
                        f"提前停止剩余 {remaining} 个候选。"
                    )
                    break

            # 优雅退出检查点
            if self.stop_requested:
                logging.info("🛑 优雅退出：当前 Batch 及收尾工作已完成，进度已保存。")
                return

        # 重置批次偏移量
        self.current_position['batch_offset'] = 0
        self.save_checkpoint(alpha_id)

        # 阶段性总结
        total_improvement = (
            self.best_score - self.initial_score
            if number(self.best_score) is not None and number(self.initial_score) is not None
            else None
        )
        step_improvement = (
            self.best_score - start_step_score
            if number(self.best_score) is not None and number(start_step_score) is not None
            else None
        )
        
        # 格式化指标详情
        stats_msg = "暂无详细指标"
        pass_status = "未知"
        display_pc = f"{self.best_pc:.4f}" if self.best_pc is not None else "待获取/跳过"
        if self.best_stats:
            s = self.best_stats
            pass_status = "通过 ✅" if s.get('passed') else "失败 ❌"
            sc_val = f"{s.get('sc'):.4f}" if isinstance(s.get('sc'), (int, float)) else s.get('sc', '未计算')
            stats_msg = (f"Sharpe: {s.get('sharpe', 0):.2f} | Fitness: {s.get('fitness', 0):.2f} | "
                         f"Margin: {s.get('margin', 0):.4f} | SC: {sc_val} | PC: {display_pc}")

        logging.info(" ")
        logging.info(f"\033[95m" + "=" * 20 + f" [位置优化总结: {type_name} 第 {index + 1} 个位置] " + "=" * 20 + "\033[0m")
        logging.info(f"  🚩 初始 Alpha ID: {self.initial_alpha_id}")
        logging.info(f"  🏆 当前最优 Alpha: {self.best_alpha_id}")
        logging.info(
            f"  💰 当前总分: \033[97m{self._score_text(self.best_score)}\033[0m "
            f"(基础分: {self._score_text(self.best_base_score)})"
        )
        logging.info(f"  📈 本次位置提升: \033[92m{self._score_text(step_improvement, '+.4f')}\033[0m")
        logging.info(f"  🚀 累计总提升: \033[92m{self._score_text(total_improvement, '+.4f')}\033[0m")
        logging.info(f"  🛡️ 检查状态: {pass_status}")
        logging.info(f"  📊 详细指标: {stats_msg}")
        logging.info(f"  📝 当前最佳公式: \033[90m{self.best_expr}\033[0m")
        logging.info(f"\033[95m" + "=" * 75 + "\033[0m")
        logging.info(" ")

    def _print_optimization_summary(self, type_name, count):
        """打印位置优化总结"""
        # 计算阶段提升
        # 注意：这里需要记录进入该阶段时的分数，但由于状态分散，我们简化为计算当前总分与初始分的差值
        # 或者更准确地，我们应该在 _optimize_step 外部记录 start_score，但这需要改动接口。
        # 鉴于日志主要是为了看进度，我们打印当前最优状态即可。
        
        # 格式化指标详情
        stats_msg = "暂无详细指标"
        pass_status = "未知"
        display_pc = f"{self.best_pc:.4f}" if self.best_pc is not None else "待获取/跳过"
        if self.best_stats:
            s = self.best_stats
            pass_status = "通过 ✅" if s.get('passed') else "失败 ❌"
            sc_val = f"{s.get('sc'):.4f}" if isinstance(s.get('sc'), (int, float)) else s.get('sc', '未计算')
            stats_msg = (f"Sharpe: {s.get('sharpe', 0):.2f} | Fitness: {s.get('fitness', 0):.2f} | "
                         f"Margin: {s.get('margin', 0):.4f} | SC: {sc_val} | PC: {display_pc}")

        logging.info(" ")
        logging.info(f"\033[95m" + "=" * 20 + f" [位置优化总结: {type_name} (共 {count} 个位置)] " + "=" * 20 + "\033[0m")
        logging.info(f"  🚩 初始 Alpha ID: {self.initial_alpha_id}")
        logging.info(f"  🏆 当前最优 Alpha: {self.best_alpha_id}")
        logging.info(
            f"  💰 当前总分: \033[97m{self._score_text(self.best_score)}\033[0m "
            f"(基础分: {self._score_text(self.best_base_score)})"
        )
        # logging.info(f"  📈 本次位置提升: ...") # 由于跨越多个位置，这里不好计算单次提升，暂略
        total_improvement = (
            self.best_score - self.initial_score
            if number(self.best_score) is not None and number(self.initial_score) is not None
            else None
        )
        logging.info(f"  🚀 累计总提升: \033[92m{self._score_text(total_improvement, '+.4f')}\033[0m")
        logging.info(f"  🛡️ 检查状态: {pass_status}")
        logging.info(f"  📊 详细指标: {stats_msg}")
        logging.info(f"  📝 当前最佳公式: \033[90m{self.best_expr}\033[0m")
        logging.info(f"\033[95m" + "=" * 75 + "\033[0m")
        logging.info(" ")

    def run(self):
        """运行所有Alpha的异步优化"""
        # 模式1: 强制重新开始，无视时间直接删除所有旧文件
        if RUN_MODE == 1:
            logging.info("运行模式1: 强制重新开始，正在清理所有历史文件...")
            patterns = [r'.*_v4\.[67]\.json$', r'.*_v4\.[67]\.log$', r'checkpoint.*\.json$', r'history.*\.json$']
            try:
                for fname in os.listdir(OUTPUT_DIR):
                    if any(re.match(p, fname) for p in patterns):
                        full_path = os.path.join(OUTPUT_DIR, fname)
                        try:
                            # 尝试关闭句柄
                            for handler in logging.root.handlers[:]:
                                handler.close()
                                logging.root.removeHandler(handler)
                            os.remove(full_path)
                            logging.info(f"已强制删除: {full_path}")
                        except: pass
            except Exception as e:
                logging.warning(f"清理文件时出错: {e}")
            
            # 重新初始化日志 (因为刚才可能把自己的日志文件都删了)
            setup_logging()
        else:
            # 模式2或其他: 仅清理过期的
            self._cleanup_old_files()
        
        try:
            # 根据运行模式决定是否删除旧文件（模式2的情况）
            if RUN_MODE == 2:
                logging.info("运行模式2: 断点续爬模式")
                logging.info("将直接加载现有检查点")
                # 原有的自动清理逻辑已移除，严格执行续爬
                pass

            # 逐个优化Alpha
            for alpha_id in TARGET_ALPHA_IDS:
                try:
                    # 为每个Alpha创建独立的日志记录器
                    setup_logging(alpha_id)
                    
                    # 重置优化位置 (确保包含所有阶段的独立计数器)
                    self.current_position = {
                        'data_field': START_OPTIMIZATION_FROM.get('data_field', 0),
                        'group': START_OPTIMIZATION_FROM.get('group', 0),
                        'time_window': START_OPTIMIZATION_FROM.get('time_window', 0),
                        'number': START_OPTIMIZATION_FROM.get('number', 0),
                        'operator': START_OPTIMIZATION_FROM.get('operator', 0),
                        'batch_offset': 0,
                        'template_batch': 0,
                        'neutralization': 0,
                        'decay': 0
                    }
                    
                    # 迭代优化，直到最佳Alpha ID与起始Alpha ID相同
                    current_alpha_id = alpha_id
                    iteration_count = 0
                    
                    while True:
                        iteration_count += 1
                        logging.info(f"开始第 {iteration_count} 轮异步迭代优化，起始Alpha ID: {current_alpha_id}")
                        
                        # 执行单轮异步优化
                        self.optimize_single_alpha(current_alpha_id)
                        
                        # 检查最佳Alpha ID是否与起始Alpha ID相同
                        if self.best_alpha_id == current_alpha_id or iteration_count >= MAX_ITERATIONS:
                            logging.info(f"异步迭代优化完成，总共进行了 {iteration_count} 轮优化")
                            logging.info(f"最终最佳Alpha ID: {self.best_alpha_id}")
                            break
                        else:
                            # 使用最佳Alpha ID作为下一轮的起始点
                            current_alpha_id = self.best_alpha_id
                            logging.info(f"本轮异步优化结束，最佳Alpha ID为 {current_alpha_id}，将继续下一轮优化")
                            
                            # 重置优化器状态以准备下一轮优化
                            self.reset_optimizer_state()
                            
                except DailyBacktestLimitReached as exc:
                    logging.warning(f"⏸️ {exc}；固定 Alpha 模式已保存断点并停止。")
                    return
                except KeyboardInterrupt:
                    logging.info(f"异步优化 Alpha {alpha_id} 时被用户中断。")
                    raise
                except Exception as e:
                    logging.error(f"异步优化 Alpha {alpha_id} 时发生错误: {e}")
                    continue

            logging.info("========== 所有 Alpha 异步优化完成 ==========")

            # 发送总体完成通知邮件
            if EMAIL_CONFIG.get('enabled', False):
                # 获取所有Alpha的通过状态
                passed_info = []
                for alpha_id in TARGET_ALPHA_IDS:
                    alpha_details = self.client.get_alpha_details(alpha_id) if alpha_id else None
                    is_passed = False
                    if alpha_details and 'is' in alpha_details and 'checks' in alpha_details['is']:
                        checks = alpha_details['is']['checks']
                        if checks and not any(c.get('result') == 'FAIL' for c in checks):
                            is_passed = True
                    passed_info.append(f"Alpha {alpha_id}: {'通过' if is_passed else '未通过'}")
                
                subject = "所有 Alpha 异步回测任务已完成"
                passed_text = '\n'.join(passed_info)
                log_paths = [
                    os.path.join(RUN_OUTPUT_DIR, f'{alpha_id}_hill_climbing_v4.7.log')
                    for alpha_id in TARGET_ALPHA_IDS
                ]
                content = f"""您的所有 Alpha 异步回测任务已经全部完成！

优化的 Alpha IDs: {TARGET_ALPHA_IDS}
检查通过情况:
{passed_text}

详细结果请查看各Alpha对应日志文件: {log_paths}
"""
                send_qq_email(subject, content)

        except KeyboardInterrupt:
            logging.info("异步程序已被用户中断。")
        except Exception as e:
            logging.error(f"异步运行过程中发生未预期的错误: {e}")
            # 发送错误通知邮件
            if EMAIL_CONFIG.get('enabled', False):
                subject = "Alpha 异步回测任务出现错误"
                content = f"您的 Alpha 异步回测任务在运行过程中出现错误：{str(e)}"
                send_qq_email(subject, content)

    def reset_optimizer_state(self):
        """重置优化器状态以准备下一轮迭代"""
        # 重置当前优化位置
        self.current_position = {
            'data_field': START_OPTIMIZATION_FROM.get('data_field', 0),
            'group': START_OPTIMIZATION_FROM.get('group', 0),
            'time_window': START_OPTIMIZATION_FROM.get('time_window', 0),
            'number': START_OPTIMIZATION_FROM.get('number', 0),
            'operator': START_OPTIMIZATION_FROM.get('operator', 0),
            'batch_offset': 0,
            'template_batch': 0,
            'neutralization': 0,
            'decay': 0,
            'template_batches_executed': 0,
            'stage_plan_cursor': 0,
            'stage_post_batches_used': 0,
            'stage_cache_batches_reused': 0,
            'stage_observed_candidates': 0,
            'stage_branches': [],
            'margin_batches_executed': 0,
            'attempted_routes': [],
            'active_route': None,
        }
        
        # 重置初始分数和ID为当前最佳值，因为下一轮将以当前最佳为起点
        self.initial_score = self.best_score
        self.initial_alpha_id = self.best_alpha_id
        
        # 保存检查点
        if self.best_alpha_id:
            self.save_checkpoint(self.best_alpha_id)

    def _source_stop_requested(self):
        return bool(self.stop_requested or getattr(self.client, 'stop_requested', False))

    def _ensure_backtest_budget(self):
        """兼容通过 ``__new__`` 构造的旧测试与外部调用。"""
        budget = getattr(self, 'backtest_budget', None)
        if budget is None:
            budget = DailyBacktestBudget(
                limit=DAILY_BACKTEST_LIMIT,
                reset_hour=DAILY_BACKTEST_RESET_HOUR,
            )
            self.backtest_budget = budget
        return budget

    def _wait_source_idle(self, seconds):
        """分段等待，使 Ctrl+C 不必等完整的一小时。"""
        end = time.time() + max(0, seconds)
        while time.time() < end:
            if self._source_stop_requested():
                raise KeyboardInterrupt
            time.sleep(min(1.0, end - time.time()))

    def _wait_for_budget_reset(self, snapshot):
        """等待到北京时间额度重置点；等待期间仍可立即 Ctrl+C。"""
        reset_at = datetime.fromisoformat(snapshot["reset_at"])
        seconds = max(
            1.0,
            (reset_at - datetime.now().astimezone()).total_seconds() + 1.0,
        )
        logging.warning(
            f"⏸️ 每日回测额度不足：已用={snapshot['used']}/{snapshot['limit']}，"
            f"剩余={snapshot['remaining']}；将在 {snapshot['reset_at']} 自动恢复"
        )
        self._wait_source_idle(seconds)

    @staticmethod
    def _source_filter_hash():
        return _source_json_hash({
            'pyramid_backfill': ENABLE_PYRAMID_BACKFILL,
            'sharpe_min': SOURCE_SHARPE_MIN,
            'fitness_min': SOURCE_FITNESS_MIN,
            'sc_max': SOURCE_SC_MAX,
            'allow_missing_sc': SOURCE_ALLOW_MISSING_SC,
            'admission_profile': SOURCE_ADMISSION_PROFILE,
            'source_operator_policy': 'INHERITED_ALLOWED_NEW_INTRODUCTIONS_RESTRICTED',
            'statuses': SOURCE_STATUSES,
            'stage_score_version': STAGE_SCORE_VERSION,
            'stage1_gate': STAGE_GATES[1],
        })

    @staticmethod
    def _source_record_as_alpha(record):
        return {
            'id': record.get('alpha_id'),
            'regular': record.get('expression', ''),
            'dateCreated': record.get('date_created'),
            'status': record.get('platform_status'),
            'settings': record.get('settings') or {},
            'is': {
                'sharpe': record.get('sharpe'),
                'fitness': record.get('fitness'),
                'margin': record.get('margin'),
                'turnover': record.get('turnover'),
            },
            'test': {'sharpe': record.get('sharpe_2y')},
        }

    def _screen_source_alpha(self, alpha, state, diversity_payload,
                             diversity_hash, filter_hash, defer_sc=False):
        """先按指标和塔分类；批量扫描可延迟SC到Core剪枝之后。"""
        alpha_id = str(alpha.get('id') or '').strip()
        if not alpha_id:
            append_source_event({'event': 'SOURCE_SKIPPED', 'reason': '缺少Alpha ID'})
            return None
        expression = _source_expression(alpha)
        stats = alpha.get('is') if isinstance(alpha.get('is'), dict) else {}
        settings = alpha.get('settings') if isinstance(alpha.get('settings'), dict) else {}
        test_stats = alpha.get('test') if isinstance(alpha.get('test'), dict) else {}
        sharpe_2y = test_stats.get('sharpe')
        logging.info(
            f"   🔎 筛选源 Alpha {alpha_id}: "
            f"创建时间={alpha.get('dateCreated') or '未知'} "
            f"Sharpe={stats.get('sharpe')} Fitness={stats.get('fitness')}"
        )
        base_fields = {
            'expression': expression,
            'date_created': alpha.get('dateCreated'),
            'platform_status': alpha.get('status'),
            'sharpe': stats.get('sharpe'),
            'fitness': stats.get('fitness'),
            'margin': stats.get('margin'),
            'turnover': stats.get('turnover'),
            'sharpe_2y': sharpe_2y,
            'region': settings.get('region'),
            'universe': settings.get('universe'),
            'delay': settings.get('delay'),
            'settings': settings,
            'filter_hash': filter_hash,
            'source_sharpe_min': SOURCE_SHARPE_MIN,
            'source_fitness_min': SOURCE_FITNESS_MIN,
            'source_sc_max': SOURCE_SC_MAX,
            'source_allow_missing_sc': SOURCE_ALLOW_MISSING_SC,
            'admission_profile': SOURCE_ADMISSION_PROFILE,
            'source_sc_kind': 'MISSING_ALLOWED',
            'pyramid_backfill_enabled': ENABLE_PYRAMID_BACKFILL,
            'source_statuses': list(SOURCE_STATUSES),
        }
        if not expression:
            return update_source_record(
                state, alpha_id, 'METRIC_REJECTED', '缺少REGULAR表达式', **base_fields
            )

        # 列表接口通常只有Sharpe/Fitness；这里只做廉价预筛，完整阶段门槛
        # 在可观察的回测结果上执行，避免为数千条源Alpha逐一请求详情。
        sharpe = number(stats.get('sharpe'))
        fitness = number(stats.get('fitness'))
        if (
            sharpe is None or fitness is None
            or sharpe <= SOURCE_SHARPE_MIN or fitness <= SOURCE_FITNESS_MIN
        ):
            return update_source_record(
                state, alpha_id, 'METRIC_REJECTED',
                f'Sharpe必须>{SOURCE_SHARPE_MIN}且Fitness必须>{SOURCE_FITNESS_MIN}',
                **base_fields,
            )

        coverage = {'status': 'HAS_GAP', 'scopes': [], 'gap_scopes': []}
        if ENABLE_PYRAMID_BACKFILL:
            logging.info(f'      🗼 查询关联塔: {alpha_id}')
            pyramid_info = get_alpha_pyramid_pass_info(_core_client(self.client), alpha_id)
            coverage = evaluate_pyramid_coverage(diversity_payload, pyramid_info)
            logging.info(
                f"      🗼 塔判断={coverage.get('status')} "
                f"关联={len(coverage.get('scopes') or [])} "
                f"缺口={len(coverage.get('gap_scopes') or [])}"
            )
            scope_text = ', '.join(
                f"{scope.get('raw_scope')}={scope.get('check')}"
                for scope in coverage.get('scopes') or []
            ) or '无可观察关联塔'
            gap_text = ', '.join(
                str(scope.get('raw_scope'))
                for scope in coverage.get('gap_scopes') or []
            ) or '无'
            logging.info(f'      🗼 关联塔明细: {scope_text}')
            logging.info(f'      🗼 待反补塔: {gap_text}')
            base_fields.update({
                'pyramid_status': pyramid_info.get('status'),
                'pyramid_categories': pyramid_info.get('categories', []),
                'pyramid_scopes': coverage.get('scopes', []),
                'gap_scopes': coverage.get('gap_scopes', []),
                'diversity_snapshot_hash': diversity_hash,
                'diversity_checked_at': _source_now(),
            })
            if coverage['status'] == 'PENDING':
                return update_source_record(
                    state, alpha_id, 'PENDING_PYRAMID', coverage.get('reason', ''),
                    **base_fields,
                )
            if coverage['status'] == 'ALL_PASS':
                return update_source_record(
                    state, alpha_id, 'SKIPPED_ALL_TOWERS_PASS', coverage.get('reason', ''),
                    **base_fields,
                )
        else:
            base_fields.update({
                'pyramid_status': 'DISABLED', 'pyramid_categories': [],
                'pyramid_scopes': [], 'gap_scopes': [],
                'diversity_snapshot_hash': None,
            })

        if defer_sc:
            return update_source_record(
                state, alpha_id, 'PRE_SC_ELIGIBLE',
                '指标与塔缺口符合要求，等待获取SC前Core剪枝', **base_fields,
            )
        return self._screen_source_sc(state, alpha_id, base_fields)

    def _screen_source_sc(self, state, alpha_id, base_fields):
        """只对Core剪枝保留项下载PnL并计算SC。"""
        base_fields = {
            key: value for key, value in dict(base_fields).items()
            if key not in {'alpha_id', 'status', 'status_reason', 'updated_at'}
        }
        logging.info(f'      📐 开始本地 SC 检查: {alpha_id}')
        pnl_cache_hit = not load_target_pnl_cache(alpha_id, SC_PPA_CACHE_DIR).empty
        if pnl_cache_hit:
            logging.info(f'      PNL_CACHE_HIT: {alpha_id}')
            append_source_event({'event': 'PNL_CACHE_HIT', 'alpha_id': alpha_id})
        now = datetime.now().astimezone()
        circuit_until = getattr(self, '_sc_pnl_circuit_open_until', None)
        if circuit_until and now < circuit_until:
            retry_after = circuit_until.isoformat(timespec='seconds')
            logging.warning(
                f'      ⏭️ 平台PnL短路保护中，暂不请求该Alpha；恢复时间={retry_after}'
            )
            base_fields.update({
                'sc_status': 'deferred_platform_pnl',
                'sc_checked_at': _source_now(),
                'sc_cache_token': current_sc_cache_token(),
                'sc_retry_after': retry_after,
            })
            return update_source_record(
                state, alpha_id, 'PENDING_SC',
                '连续PnL空响应触发平台短路保护，本条尚未实际检查', **base_fields,
            )
        if circuit_until:
            self._sc_pnl_circuit_open_until = None
            self._sc_pnl_consecutive_failures = 0

        sc_value = get_sc_check(
            _core_client(self.client), alpha_id, cache_pnl_below=SOURCE_SC_MAX,
            alpha_result=self._source_record_as_alpha({**base_fields, 'alpha_id': alpha_id}),
        )
        logging.info(f'      📐 本地 SC 结果: {sc_value}')
        sc_token = current_sc_cache_token()
        base_fields.update({
            'sc_status': sc_value,
            'sc_checked_at': _source_now(),
            'sc_cache_token': sc_token,
            'pnl_source': 'LOCAL_CACHE' if pnl_cache_hit else 'REMOTE_DOWNLOAD',
        })
        valid_sc = (
            isinstance(sc_value, (int, float)) and not isinstance(sc_value, bool)
            and math.isfinite(float(sc_value))
        )
        if sc_value == 'pnl_unavailable':
            base_fields['pnl_source'] = 'UNAVAILABLE'
            append_source_event({'event': 'PNL_UNAVAILABLE', 'alpha_id': alpha_id})
            failure_count = getattr(self, '_sc_pnl_consecutive_failures', 0) + 1
            self._sc_pnl_consecutive_failures = failure_count
            base_fields['sc_pnl_unavailable_count'] = int(
                (state.get('candidates', {}).get(alpha_id, {}).get(
                    'sc_pnl_unavailable_count', 0
                ) or 0) + 1
            )
            if failure_count >= SOURCE_SC_PNL_FAILURE_LIMIT:
                self._sc_pnl_circuit_open_until = (
                    datetime.now().astimezone()
                    + timedelta(seconds=SOURCE_SC_PNL_COOLDOWN_SECONDS)
                )
                logging.warning(
                    f'      🧯 连续{failure_count}个Alpha的PnL不可用，'
                    f'后续PnL请求短路{SOURCE_SC_PNL_COOLDOWN_SECONDS}秒'
                )
            return update_source_record(
                state, alpha_id, 'SKIPPED_PNL_UNAVAILABLE',
                '平台连续3次返回空PnL，按配置直接跳过；不计为因子质量失败',
                **base_fields,
            )
        self._sc_pnl_consecutive_failures = 0
        if not valid_sc:
            if not pnl_cache_hit:
                base_fields['pnl_source'] = 'UNAVAILABLE'
                append_source_event({'event': 'PNL_UNAVAILABLE', 'alpha_id': alpha_id})
            return update_source_record(
                state, alpha_id, 'PENDING_SC', f'本地SC不可观察: {sc_value}', **base_fields
            )
        base_fields['sc_value'] = float(sc_value)
        if sc_value >= SOURCE_SC_MAX:
            append_source_event({'event': 'PNL_CACHE_DELETED', 'alpha_id': alpha_id})
            return update_source_record(
                state, alpha_id, 'SC_REJECTED', f'本地SC必须严格小于{SOURCE_SC_MAX}',
                **base_fields,
            )
        if not pnl_cache_hit:
            append_source_event({'event': 'PNL_DOWNLOADED', 'alpha_id': alpha_id})
        base_fields['pnl_cached_at'] = _source_now()
        return update_source_record(
            state, alpha_id, 'ELIGIBLE', '指标、塔缺口和本地SC均符合源Alpha要求',
            **base_fields,
        )

    def _source_record_needs_screening(self, record, diversity_hash,
                                       sc_cache_token, filter_hash):
        """只重试尚未完成指标/塔分类的源 Alpha。

        diversity/sc/filter 哈希继续保存在记录中用于审计，但它们的变化不再
        推翻已经完成的筛选结果。PRE_SC_ELIGIBLE/PENDING_SC 已保存塔分类，
        重启后直接进入剪枝/SC，不再查询塔接口。
        """
        status = str(record.get('status') or '').strip().upper()
        classification_pending = SOURCE_RETRYABLE_STATUSES - {'PENDING_SC'}
        return not status or status == 'DISCOVERED' or status in classification_pending

    def _prune_and_screen_pre_sc(self, state):
        """按官方字段组合建立塔候选池，再按组合顺序执行有限次SC。"""
        locally_rejected_ids = tighten_saved_sc_threshold(state)
        if locally_rejected_ids:
            logging.info(
                f'📐 塔分类后先用账本SC筛除={len(locally_rejected_ids)}；'
                f'阈值={SOURCE_SC_MAX}，未重新计算SC'
            )
        candidate_statuses = SOURCE_PRE_SC_STATUSES | {
            'PRUNED_PRE_SC', 'ELIGIBLE', 'RESERVE', 'SUPERSEDED',
            'SKIPPED_PNL_UNAVAILABLE', 'PENDING_FIELD_METADATA',
        }
        candidates = [
            record for record in state.get('candidates', {}).values()
            if record.get('status') in candidate_statuses
            and record.get('expression')
            and not record.get('immediate_stage_branch')
        ]
        pool = build_candidate_pool(
            _core_client(self.client), candidates, active_limit=TOWER_ACTIVE_HILL_LIMIT
        )
        for bucket, pool_status in (
            ('active', 'ACTIVE'), ('reserve', 'RESERVE'),
            ('hold_pass', 'HOLD_PASS'), ('superseded', 'SUPERSEDED'),
        ):
            for candidate in pool.get(bucket, []):
                alpha_id = str(candidate.get('alpha_id') or candidate.get('id') or '')
                if alpha_id in state.get('candidates', {}):
                    state['candidates'][alpha_id].update(candidate)
                    state['candidates'][alpha_id]['pool_status'] = pool_status
        for candidate in pool.get('pending_metadata', []):
            alpha_id = str(candidate.get('alpha_id') or candidate.get('id') or '')
            if alpha_id in state.get('candidates', {}):
                state['candidates'][alpha_id].update(candidate)
                state['candidates'][alpha_id]['status'] = 'PENDING_FIELD_METADATA'
        for candidate in pool.get('disabled_scope', []):
            alpha_id = str(candidate.get('alpha_id') or candidate.get('id') or '')
            if alpha_id in state.get('candidates', {}):
                state['candidates'][alpha_id].update(candidate)
                state['candidates'][alpha_id]['status'] = 'DISABLED_SCOPE'

        summary = {
            'before': len(candidates),
            'kept': len(pool.get('active', [])),
            'reserve': len(pool.get('reserve', [])),
            'superseded': len(pool.get('superseded', [])),
            'pending_metadata': len(pool.get('pending_metadata', [])),
            'disabled_scope': len(pool.get('disabled_scope', [])),
            'tower_summary': pool.get('tower_summary', {}),
        }
        state['tower_summary'] = summary['tower_summary']
        logging.info(
            f"🗂️ 字段组合塔池: 候选={summary['before']}，ACTIVE={summary['kept']}，"
            f"RESERVE={summary['reserve']}，SUPERSEDED={summary['superseded']}，"
            f"PENDING_FIELD_METADATA={summary['pending_metadata']}，"
            f"DISABLED_SCOPE={summary['disabled_scope']}"
        )
        save_source_state(state)

        observed = 0
        missing = 0
        for candidate in pool.get('active', []):
            alpha_id = str(candidate.get('alpha_id') or candidate.get('id') or '')
            record = state.get('candidates', {}).get(alpha_id)
            if not record:
                continue
            sc_value = number(record.get('sc_value'))
            if sc_value is not None and sc_value >= SOURCE_SC_MAX:
                update_source_record(
                    state, alpha_id, 'SC_REJECTED',
                    f'已有SC必须严格小于{SOURCE_SC_MAX}',
                    source_sc_kind='OBSERVED_REJECTED', admission_profile=SOURCE_ADMISSION_PROFILE,
                )
                continue
            source_sc_kind = 'OBSERVED' if sc_value is not None else 'MISSING_ALLOWED'
            observed += int(sc_value is not None)
            missing += int(sc_value is None)
            update_source_record(
                state, alpha_id, 'ELIGIBLE',
                '宽入口已通过；SC缺失允许低优先探针' if sc_value is None
                else '宽入口及账本SC均通过',
                source_sc_kind=source_sc_kind,
                admission_profile=SOURCE_ADMISSION_PROFILE,
                retry_after=None,
            )
        logging.info(
            f'📐 源SC仅使用账本/本地缓存：已观察可领取={observed}，'
            f'缺失低优先可领取={missing}；扫描阶段未下载PnL。'
        )
        save_source_state(state)
        return summary

    def _scan_source_candidates(self, state, diversity_payload, diversity_hash):
        """按自然日扫描并持久化候选；任一分页失败都不推进该日断点。"""
        today = datetime.now().date()
        earliest = today - timedelta(days=max(0, SOURCE_LOOKBACK_DAYS - 1))
        last_complete_raw = state.get('last_complete_scan_date')
        try:
            last_complete = datetime.strptime(last_complete_raw, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            last_complete = None
        if last_complete:
            overlap = max(0, int(SOURCE_DATE_OVERLAP_DAYS) - 1)
            start_date = max(earliest, last_complete - timedelta(days=overlap))
        else:
            start_date = earliest

        now = datetime.now().astimezone()

        def timestamp_due(raw_value, interval_seconds):
            try:
                previous = datetime.fromisoformat(raw_value)
                if previous.tzinfo is None:
                    previous = previous.astimezone()
            except (TypeError, ValueError):
                return True
            return (now - previous).total_seconds() >= interval_seconds

        resume = state.get('scan_resume')
        resume = resume if isinstance(resume, dict) else {}
        try:
            resume_date = datetime.strptime(resume.get('date'), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            resume_date = None
        if resume_date and earliest <= resume_date <= today:
            start_date = resume_date


        # 当天已经完成过全量扫描时，不再每轮从 offset=0 重扫全部分页。
        # 5分钟倒序看最新页；每30分钟仍走一次原有全量逻辑进行兜底对账。
        if not resume and last_complete == today and not timestamp_due(
            state.get('last_full_scan_at'), SOURCE_FULL_SCAN_SECONDS
        ):
            if not timestamp_due(
                state.get('last_incremental_scan_at'), SOURCE_INCREMENTAL_SCAN_SECONDS
            ):
                logging.info('⏭️ 当天增量扫描尚未到期，跳过重复分页请求。')
                return True

            date_text = today.isoformat()
            filter_hash = self._source_filter_hash()
            logging.info(f'🆕 当天倒序增量扫描: {date_text}')
            known_ids = set(state.get('candidates', {}))
            new_count = 0
            returned_count = 0
            offset = 0
            while offset < 1000:
                page = get_user_alphas_page(
                    _core_client(self.client), date_text, date_text,
                    SOURCE_SHARPE_MIN, SOURCE_FITNESS_MIN,
                    statuses=SOURCE_STATUSES, offset=offset, limit=100,
                    descending=True,
                )
                if page is None:
                    logging.warning('⚠️ 当天增量页不可观察；保留原完整断点。')
                    return False
                rows = page.get('results') or []
                returned_count += len(rows)
                reached_known = False
                for alpha in rows:
                    alpha_id = str(alpha.get('id') or '').strip()
                    if not alpha_id:
                        continue
                    if alpha_id in known_ids:
                        reached_known = True
                        continue
                    known_ids.add(alpha_id)
                    new_count += 1
                    update_source_record(
                        state, alpha_id, 'DISCOVERED', '当天倒序增量扫描发现源Alpha',
                        expression=_source_expression(alpha),
                        date_created=alpha.get('dateCreated'),
                    )
                    self._screen_source_alpha(
                        alpha, state, diversity_payload, diversity_hash, filter_hash,
                        defer_sc=True,
                    )
                offset += len(rows)
                if reached_known or not rows or len(rows) < 100:
                    break
                if isinstance(page.get('count'), int) and offset >= page['count']:
                    break
            state['last_incremental_scan_at'] = now.isoformat(timespec='seconds')
            save_source_state(state)
            logging.info(f'✅ 当天增量扫描完成: 返回={returned_count}，新增={new_count}')
            if new_count:
                self._prune_and_screen_pre_sc(state)
            return True

        logging.info(
            f'📆 本轮日期范围: {start_date.isoformat()} -> {today.isoformat()} '
            f'(上次完整断点: {last_complete_raw or "无"})'
        )

        filter_hash = self._source_filter_hash()
        sc_cache_token = current_sc_cache_token()

        locally_rejected_ids = tighten_saved_sc_threshold(state)
        if locally_rejected_ids:
            logging.info(
                f'📐 当前SC阈值={SOURCE_SC_MAX}，仅使用账本已有SC本地收紧='
                f'{len(locally_rejected_ids)}；未下载PnL、未重算SC'
            )
            save_source_state(state)

        history_records = list(state.get('candidates', {}).values())
        history_status_counts = Counter(
            str(record.get('status') or 'NO_STATUS') for record in history_records
        )
        # 先按状态分桶。明确终态及已进入优化队列的记录全部冻结；只有尚未完成
        # 判断的 DISCOVERED/PENDING 记录进入重试队列。
        rescreen_records = [
            record for record in history_records
            if self._source_record_needs_screening(
                record, diversity_hash, sc_cache_token, filter_hash
            )
        ]
        logging.info(
            f'🗂️ 历史候选分类={dict(sorted(history_status_counts.items()))}'
        )
        logging.info(
            f'♻️ 历史候选={len(history_records)}，已筛选冻结='
            f'{len(history_records) - len(rescreen_records)}，'
            f'仅重试DISCOVERED/PENDING={len(rescreen_records)}'
        )
        for index, record in enumerate(rescreen_records, 1):
            if self._source_stop_requested():
                raise KeyboardInterrupt
            logging.info(
                f'   ♻️ 重筛 [{index}/{len(rescreen_records)}] '
                f'{record.get("alpha_id")} ({record.get("status")})'
            )
            self._screen_source_alpha(
                self._source_record_as_alpha(record), state,
                diversity_payload, diversity_hash, filter_hash, defer_sc=True,
            )
            save_source_state(state)

        retry_after = resume.get('retry_after')
        try:
            retry_at = datetime.fromisoformat(retry_after)
        except (TypeError, ValueError):
            retry_at = None
        if retry_at and retry_at > datetime.now().astimezone():
            logging.warning(
                f"⏸️ 日期分页冷却中: date={resume.get('date')} "
                f"offset={resume.get('offset', 0)} retry_after={retry_after}"
            )
            self._prune_and_screen_pre_sc(state)
            return False

        scan_date = start_date
        while scan_date <= today:
            if self._source_stop_requested():
                raise KeyboardInterrupt
            date_text = scan_date.isoformat()
            logging.info(f'📅 扫描源 Alpha 日期: {date_text}')
            is_resume_day = resume.get('date') == date_text
            offset = int(resume.get('offset') or 0) if is_resume_day else 0
            descending = bool(resume.get('descending')) if is_resume_day else False
            target_count = resume.get('target_count') if is_resume_day else None
            day_alpha_ids = set(resume.get('alpha_ids') or []) if is_resume_day else set()
            if offset:
                order_text = 'DESC' if descending else 'ASC'
                logging.info(f'   ♻️ 从分页断点继续: order={order_text} offset={offset}')
            page_failed = False
            failure_reason = None
            while True:
                order_text = 'DESC' if descending else 'ASC'
                logging.info(
                    f'   📄 请求分页 order={order_text}, offset={offset}, limit=100'
                )
                page = get_user_alphas_page(
                    _core_client(self.client), date_text, date_text,
                    SOURCE_SHARPE_MIN, SOURCE_FITNESS_MIN,
                    statuses=SOURCE_STATUSES, offset=offset, limit=100,
                    descending=descending,
                )
                if page is None:
                    page_failed = True
                    failure_reason = '平台分页请求或响应不可观察'
                    break
                results = page['results']
                if isinstance(page.get('count'), int):
                    target_count = page['count']
                logging.info(
                    f'   📄 分页返回={len(results)}，'
                    f'该日平台总数={target_count if target_count is not None else "未知"}'
                )
                for alpha in sorted(
                    results, key=lambda item: (
                        str(item.get('dateCreated') or ''), str(item.get('id') or '')
                    )
                ):
                    alpha_id = str(alpha.get('id') or '').strip()
                    if not alpha_id:
                        continue
                    day_alpha_ids.add(alpha_id)
                    existing = state.get('candidates', {}).get(alpha_id)
                    if existing and not self._source_record_needs_screening(
                        existing, diversity_hash, current_sc_cache_token(), filter_hash
                    ):
                        continue
                    if not existing:
                        update_source_record(
                            state, alpha_id, 'DISCOVERED', '按日期扫描发现源Alpha',
                            expression=_source_expression(alpha),
                            date_created=alpha.get('dateCreated'),
                        )
                    self._screen_source_alpha(
                        alpha, state, diversity_payload, diversity_hash, filter_hash,
                        defer_sc=True,
                    )
                    save_source_state(state)
                count = page.get('count')
                offset += len(results)
                state['scan_resume'] = {
                    'date': date_text,
                    'offset': offset,
                    'descending': descending,
                    'target_count': target_count,
                    'alpha_ids': sorted(day_alpha_ids),
                    'retry_after': None,
                }
                save_source_state(state)
                if isinstance(target_count, int) and len(day_alpha_ids) >= target_count:
                    break
                if offset >= 1000:
                    if not descending:
                        descending = True
                        offset = 0
                        logging.info(
                            f'   ↕️ 总数={target_count}超过正序窗口，切换倒序补齐尾部'
                        )
                        continue
                    page_failed = True
                    failure_reason = (
                        f'正序和倒序各1000条后仍未覆盖平台总数={target_count}'
                    )
                    break
                if not results or len(results) < 100:
                    break
                if isinstance(count, int) and offset >= count:
                    break

            if page_failed:
                retry_after = (
                    datetime.now().astimezone()
                    + timedelta(seconds=SOURCE_SCAN_RETRY_SECONDS)
                ).isoformat(timespec='seconds')
                state['scan_resume'] = {
                    'date': date_text,
                    'offset': offset,
                    'descending': descending,
                    'target_count': target_count,
                    'alpha_ids': sorted(day_alpha_ids),
                    'retry_after': retry_after,
                }
                append_source_event({
                    'event': 'SOURCE_SCAN_PENDING', 'date': date_text,
                    'offset': offset, 'descending': descending,
                    'retry_after': retry_after, 'reason': failure_reason,
                })
                logging.warning(
                    f'⚠️ {date_text} 分页未完整；保留 order='
                    f'{"DESC" if descending else "ASC"} offset={offset}，'
                    f'{SOURCE_SCAN_RETRY_SECONDS}秒后从该页继续'
                )
                self._prune_and_screen_pre_sc(state)
                save_source_state(state)
                return False

            state['last_complete_scan_date'] = date_text
            state['scan_resume'] = None
            status_counts = {}
            for alpha_id in day_alpha_ids:
                status = state.get('candidates', {}).get(alpha_id, {}).get('status', 'UNRECORDED')
                status_counts[status] = status_counts.get(status, 0) + 1
            logging.info(
                f'✅ {date_text} 扫描完成: 唯一Alpha={len(day_alpha_ids)}，状态={status_counts}'
            )
            append_source_event({
                'event': 'SOURCE_SCAN_COMPLETE', 'date': date_text,
                'unique_alpha_count': len(day_alpha_ids),
            })
            save_source_state(state)
            scan_date += timedelta(days=1)
        state['last_full_scan_at'] = now.isoformat(timespec='seconds')
        state['last_incremental_scan_at'] = state['last_full_scan_at']
        save_source_state(state)
        self._prune_and_screen_pre_sc(state)
        return True

    def run_continuous(self):
        """按日期、塔缺口和本地 SC 选择源 Alpha，并持续执行现有爬山。"""
        global CANDIDATE_NEUTRALIZATIONS
        original_neutralizations = CANDIDATE_NEUTRALIZATIONS.copy()
        logging.info(f'📂 正在读取源 Alpha 状态: {HILL_CLIMBING_SOURCE_STATE_PATH}')
        source_state = load_source_state()
        self.source_state_store = getattr(source_state, '_store', None)
        logging.info(
            f'📂 状态读取完成: 日期断点={source_state.get("last_complete_scan_date") or "无"}，'
            f'历史候选={len(source_state.get("candidates", {}))}'
        )
        if import_legacy_processed(source_state, load_processed_alphas()):
            save_source_state(source_state)
        for record in source_state.get('candidates', {}).values():
            if record.get('status') == 'OPTIMIZING':
                update_source_record(
                    source_state, record['alpha_id'], 'INTERRUPTED',
                    '上次进程在优化中结束，恢复为可继续状态',
                )
        save_source_state(source_state)

        round_count = 0
        logging.info('🔄 进入未点亮塔优先的持续运行模式...')
        while True:
            round_count += 1
            self.stop_requested = False
            self.client.stop_requested = False
            logging.info(f"\n{'='*60}")
            logging.info(f'🔄 持续运行模式 - 第 {round_count} 轮')
            logging.info(f"{'='*60}")
            budget = self._ensure_backtest_budget().snapshot()
            logging.info(
                f"🧮 当前回测额度: 已用={budget['used']}/{budget['limit']}，"
                f"剩余={budget['remaining']}，重置={budget['reset_at']}"
            )
            if budget['remaining'] < 2:
                self._wait_for_budget_reset(budget)
                continue
            CANDIDATE_NEUTRALIZATIONS.clear()
            CANDIDATE_NEUTRALIZATIONS.extend(original_neutralizations)

            due_batch = (
                self.source_state_store.due_batch()
                if self.source_state_store is not None else None
            )
            if isinstance(due_batch, dict):
                due_expressions = list(due_batch.get('expressions') or [])
                due_settings = due_batch.get('settings')
                due_fingerprint = due_batch.get('batch_fingerprint')
                if len(due_expressions) != TEMPLATE_BATCH_SIZE or not due_settings:
                    due_batch.update({
                        'status': 'RESULTS_UNOBSERVED',
                        'retry_kind': 'INVALID_RECOVERY_PAYLOAD',
                        'retry_after': None,
                    })
                    self.source_state_store.save_batch(due_fingerprint, due_batch)
                    logging.warning(
                        '已有批次恢复载荷不完整，转 RESULTS_UNOBSERVED；不重新POST。'
                    )
                    continue
                batch_key = _multi_batch_key(
                    due_expressions, normalize_simulation_settings(due_settings)
                )
                pending_batches = self.client.history.setdefault('__pending_multi__', {})
                pending_batches.setdefault(batch_key, {
                    key: value for key, value in due_batch.items()
                    if key != 'batch_fingerprint'
                })
                self.initial_alpha_id = due_batch.get('source_alpha_id')
                self.hill_stage = int(due_batch.get('stage') or 1)
                logging.info(
                    '♻️ 调度器优先只读恢复SQLite已有Location批次；'
                    '恢复完成前禁止领取新源或生成新父任务。'
                )
                recovered = self.evaluate_batch(
                    due_expressions, settings=due_settings
                )
                recovery_complete = all(
                    recovered.get(expression, {}).get('status') in {
                        'COMPLETE', 'CACHE_HIT'
                    }
                    and recovered.get(expression, {}).get('alpha_id')
                    for expression in due_expressions
                )
                if recovery_complete:
                    logging.info('✅ SQLite已有Location批次只读恢复完成。')
                else:
                    logging.info('⏸️ SQLite已有批次仍不可观察；本轮不创建新父任务。')
                    self._wait_source_idle(min(SOURCE_IDLE_SECONDS, 60))
                continue

            diversity_payload = {}
            diversity_hash = 'PYRAMID_FILTER_DISABLED'
            refresh_result = None
            if ENABLE_SC_PYRAMID_AUTO_REFRESH:
                logging.info(
                    f'🔄 Core刷新检查: SC参考池周期={SC_PYRAMID_REFRESH_HOURS}小时'
                )
                refresh_result = refresh_sc_pyramid_bundle(
                    _core_client(self.client), interval_hours=SC_PYRAMID_REFRESH_HOURS
                )
                logging.info(_format_core_refresh_result(refresh_result))
                logging.info(
                    f"⏰ 下次SC刷新={refresh_result.get('next_due_at') or '待定'} "
                    f"刷新失败重试={refresh_result.get('retry_after') or '无'} "
                    f"PnL补偿重试={refresh_result.get('failed_pnl_retry_at') or '无'}"
                )
                if refresh_result.get('status') == 'PENDING':
                    append_source_event({
                        'event': 'SC_PYRAMID_REFRESH_PENDING',
                        'status': 'PENDING',
                        'reason': refresh_result.get('reason'),
                        'retry_after': refresh_result.get('retry_after'),
                    })
                    save_source_state(source_state)
                    retry_at = refresh_result.get('retry_after')
                    try:
                        wait_seconds = max(
                            1, min(
                                SOURCE_IDLE_SECONDS,
                                (datetime.fromisoformat(retry_at)
                                 - datetime.now().astimezone()).total_seconds(),
                            ),
                        )
                    except (TypeError, ValueError):
                        wait_seconds = min(SOURCE_IDLE_SECONDS, 300)
                    logging.warning(
                        f"⚠️ Core刷新不可观察，本轮暂停选源，约{wait_seconds:.0f}秒后重试"
                    )
                    self._wait_source_idle(wait_seconds)
                    continue
                diversity_payload = refresh_result.get('diversity_payload') or {}
                diversity_hash = (
                    refresh_result.get('diversity_coverage_hash')
                    or _source_json_hash(diversity_payload)
                )
            elif ENABLE_PYRAMID_BACKFILL:
                logging.info('🗼 自动刷新已关闭，直接读取当前 Pyramid diversity...')
                diversity_payload = get_user_diversity(_core_client(self.client))
                diversity_hash = _source_json_hash(diversity_payload)

            if ENABLE_PYRAMID_BACKFILL:
                if not isinstance(diversity_payload.get('alphas'), list):
                    append_source_event({
                        'event': 'SOURCE_SCAN_PENDING',
                        'status': 'PENDING_DIVERSITY',
                        'reason': '用户diversity响应不可观察，本轮不把查询失败误判为缺塔',
                    })
                    save_source_state(source_state)
                    logging.warning('⚠️ diversity 查询不可观察，本轮不选择源 Alpha')
                    self._wait_source_idle(min(SOURCE_IDLE_SECONDS, 300))
                    continue
                rows = diversity_payload.get('alphas', [])
                model_row = next((
                    row for row in rows
                    if str(row.get('region') or '').upper() == 'GBR'
                    and row.get('delay') == 1
                    and str((row.get('dataCategory') or {}).get('id') or '').lower() == 'model'
                ), None)
                model_diversity = (model_row or {}).get('dataDiversity') or {}
                logging.info(
                    f"🗼 GBR/D1/MODEL: "
                    f"状态={model_diversity.get('check') or 'MISSING'} "
                    f"limit={model_diversity.get('limit')} "
                    f"alphaCount={(model_row or {}).get('alphaCount')}"
                )
                if source_state.get('diversity_snapshot_hash') != diversity_hash:
                    source_state['diversity_snapshot_hash'] = diversity_hash
                    source_state['diversity_snapshot_time'] = _source_now()
                    append_source_event({
                        'event': 'DIVERSITY_SNAPSHOT',
                        'snapshot_hash': diversity_hash,
                        'payload_hash': (refresh_result or {}).get('diversity_payload_hash'),
                        'tower_row_count': len(rows),
                    })
                    save_source_state(source_state)

            logging.info('🔍 开始按日期扫描并筛选源 Alpha...')
            scan_complete = self._scan_source_candidates(
                source_state, diversity_payload, diversity_hash
            )
            logging.info(f'🔍 日期扫描阶段结束: complete={scan_complete}')
            # 40条窗口只更新相对质量和健康报表，不再控制Stage交接。
            candidate_records = source_state.get('candidates', {}).values()
            apply_region_category_relative_quality(candidate_records, 1)
            apply_region_category_relative_quality(candidate_records, 2)
            save_source_state(source_state)
            cooldown = self._post_cooldown_snapshot()
            if cooldown['active']:
                logging.warning(
                    f"⏸️ 账户级429冷却中，暂停全部新POST至 {cooldown['retry_after']}"
                )
                self._wait_source_idle(max(1, cooldown['remaining_seconds']))
                continue
            selected = claim_next_source_record(source_state)
            if not selected:
                logging.info('⏳ 当前没有通过指标、塔缺口和SC筛选的源 Alpha，稍后重查...')
                self._wait_source_idle(SOURCE_IDLE_SECONDS)
                continue

            selected_id = selected['alpha_id']
            selected_expr = selected.get('expression', '')
            hill_stage = int(selected.get('hill_stage') or 1)
            self.stage_target_batches = STAGE_BATCH_BUDGETS[hill_stage]
            self.hill_stage = hill_stage
            attempts = int(selected.get('attempts') or 0) + 1
            selected.update({
                'attempts': attempts,
                'structural_distance': selected.get('structural_distance'),
            })
            save_source_state(source_state)
            logging.info(f'✅ 本轮选中 Alpha: {selected_id}')
            logging.info(f"   缺塔数量: {len(selected.get('gap_scopes') or [])} | SC: {selected.get('sc_value')}")
            logging.info(f'   表达式: {selected_expr}')

            try:
                setup_logging(selected_id)
                self.current_position = {
                    'data_field': 0, 'group': 0, 'time_window': 0,
                    'number': 0, 'operator': 0, 'batch_offset': 0,
                    'template_batch': 0, 'neutralization': 0, 'decay': 0,
                    'template_batches_executed': 0,
                    'stage_plan_cursor': 0,
                    'stage_post_batches_used': 0,
                    'stage_cache_batches_reused': 0,
                    'stage_observed_candidates': 0,
                    'stage_branches': [],
                    'margin_batches_executed': 0,
                    'attempted_routes': [],
                    'active_route': None,
                    'candidate_pool_fingerprint': None,
                    'baseline_refresh_status': 'NOT_REQUIRED',
                    'baseline_alpha_id': None,
                }
                self.best_expr = None
                self.best_score = -9999
                self.best_base_score = -9999
                self.settings = None
                self.best_alpha_id = None
                self.template_retry_after = None
                self.template_pending_status = None
                self.template_blocked_status = None
                self.initial_score = None
                self.initial_alpha_id = None
                self.source_expression = selected_expr
                self.source_record = dict(selected)
                self.baseline_refresh_status = 'NOT_REQUIRED'
                self.baseline_alpha_id = None
                self.best_pc = None
                self.best_stats = {}
                self.score_components = {}
                self.score_penalties = {}
                self.score_version = STAGE_SCORE_VERSION
                self.stage_observable_results = 0
                self.stage_pass_results = 0
                self.stage_pass_candidates = []
                self._stage_result_seen = set()

                current_alpha_id = selected_id
                iteration_count = 0
                optimization_outcome = 'PENDING'
                while True:
                    iteration_count += 1
                    logging.info(
                        f'🔁 第 {round_count} 轮 - 第 {iteration_count} 次迭代, '
                        f'Alpha: {current_alpha_id}'
                    )
                    optimization_outcome = self.optimize_single_alpha(current_alpha_id)
                    if self._source_stop_requested():
                        raise KeyboardInterrupt
                    if optimization_outcome in {
                        'BLOCKED_INCOMPLETE_BATCH',
                        'BLOCKED_INCOMPLETE_TEMPLATE_BATCH',
                        'BLOCKED_INCOMPLETE_MARGIN_BATCH',
                    }:
                        update_source_record(
                            source_state, selected_id, optimization_outcome,
                            '当前阶段的合法同角色候选无法补足固定8条；候选池变化前不重试',
                            candidate_pool_fingerprint=self.current_position.get(
                                'candidate_pool_fingerprint'
                            ),
                            blocked_candidate_pool_fingerprint=self.current_position.get(
                                'candidate_pool_fingerprint'
                            ),
                            objective_version=OBJECTIVE_VERSION,
                            code_version=CODE_VERSION,
                            retry_kind='DETERMINISTIC_CANDIDATE_POOL',
                            no_new_candidate_count=int(
                                selected.get('no_new_candidate_count') or 0
                            ) + 1,
                        )
                        save_source_state(source_state)
                        break
                    if optimization_outcome == 'DISABLED_SCOPE':
                        update_source_record(
                            source_state, selected_id, 'DISABLED_SCOPE',
                            '源表达式不符合单数据集或低复杂度固定边界，未创建回测',
                            retry_after=None,
                            admission_profile=SOURCE_ADMISSION_PROFILE,
                            objective_version=OBJECTIVE_VERSION,
                            code_version=CODE_VERSION,
                        )
                        save_source_state(source_state)
                        break
                    if (
                        str(optimization_outcome).startswith('PENDING')
                        or optimization_outcome == 'RESULTS_UNOBSERVED'
                    ):
                        logging.warning(
                            '⏸️ 模板批次仍为 PENDING；保留当前源 Alpha 和检查点，'
                            '不标记阶段完成。'
                        )
                        break
                    if not self.best_alpha_id:
                        raise RuntimeError('优化结束但没有可观察的最佳 Alpha ID')
                    if hasattr(self, 'stage_target_batches') or self.best_alpha_id == current_alpha_id or iteration_count >= MAX_ITERATIONS:
                        logging.info(
                            f'✅ 迭代优化完成, 共 {iteration_count} 轮, '
                            f'最终Alpha: {self.best_alpha_id}'
                        )
                        break
                    current_alpha_id = self.best_alpha_id
                    logging.info(f'🔁 最佳Alpha已变更为 {current_alpha_id}, 继续下一轮迭代')
                    self.reset_optimizer_state()

                if optimization_outcome in {
                    'BLOCKED_INCOMPLETE_BATCH',
                    'BLOCKED_INCOMPLETE_TEMPLATE_BATCH',
                    'BLOCKED_INCOMPLETE_MARGIN_BATCH',
                }:
                    logging.info(f'💾 源 Alpha {selected_id} 已确定性阻塞；不进入定时重试队列。')
                    continue

                if optimization_outcome == 'DISABLED_SCOPE':
                    logging.info(f'💾 源 Alpha {selected_id} 已标记 DISABLED_SCOPE。')
                    continue

                if (
                    str(optimization_outcome).startswith('PENDING')
                    or optimization_outcome == 'RESULTS_UNOBSERVED'
                ):
                    missing_stage_score = optimization_outcome == 'PENDING_STAGE_SCORE'
                    results_unobserved = optimization_outcome == 'RESULTS_UNOBSERVED'
                    category_pending = optimization_outcome in {
                        'PENDING_CATEGORY', 'PENDING_CATEGORY_CONFLICT', 'PENDING_PC',
                    }
                    retry_after = None if missing_stage_score or results_unobserved or category_pending else (
                        getattr(self, 'template_retry_after', None) or (
                            datetime.now().astimezone()
                            + timedelta(seconds=MULTI_RATE_LIMIT_COOLDOWN_SECONDS)
                        ).isoformat(timespec='seconds')
                    )
                    pending_status = (
                        'PENDING_STAGE_SCORE' if missing_stage_score
                        else 'RESULTS_UNOBSERVED' if results_unobserved
                        else optimization_outcome if category_pending
                        else 'INTERRUPTED'
                    )
                    update_source_record(
                        source_state, selected_id, pending_status,
                        '必要指标或模板批次结果待观察，保留源 Alpha 和优化检查点',
                        retry_after=retry_after,
                        retry_count=int(selected.get('retry_count') or 0) + 1,
                        retry_kind=(
                            'MISSING_STAGE_SCORE' if missing_stage_score
                            else 'RATE_LIMIT' if optimization_outcome == 'PENDING_RATE_LIMIT'
                            else 'PLATFORM_UNOBSERVED'
                        ),
                        objective_version=OBJECTIVE_VERSION,
                        code_version=CODE_VERSION,
                        hill_stage=hill_stage,
                        stage_batches_used=self.current_position.get(
                            'stage_post_batches_used', 0
                        ),
                        stage_plan_cursor=self.current_position.get('stage_plan_cursor', 0),
                        stage_post_batches_used=self.current_position.get(
                            'stage_post_batches_used', 0
                        ),
                        stage_cache_batches_reused=self.current_position.get(
                            'stage_cache_batches_reused', 0
                        ),
                        stage_observed_candidates=self.current_position.get(
                            'stage_observed_candidates', 0
                        ),
                        admission_profile=SOURCE_ADMISSION_PROFILE,
                        baseline_refresh_status=self.baseline_refresh_status,
                        baseline_alpha_id=self.baseline_alpha_id,
                        source_sc_kind=selected.get('source_sc_kind'),
                    )
                    save_source_state(source_state)
                    logging.info(
                        f'💾 源 Alpha {selected_id} 保持 {pending_status}'
                        f'{f"，重试时间={retry_after}" if retry_after else ""}'
                    )
                    continue

                final_assessment = self._assess_stats(self.best_stats)
                final_gate = final_assessment['gate']
                if final_gate['status'] == 'PENDING':
                    complete_status = 'PENDING_STAGE_SCORE'
                    complete_reason = '阶段预算完成但必要指标缺失: ' + ','.join(final_gate['missing'])
                elif not final_assessment['eligible']:
                    complete_status = f'STAGE{hill_stage}_REJECTED'
                    complete_reason = '阶段门槛未通过: ' + ','.join(final_gate['failed'])
                elif hill_stage == 3:
                    final_result = {'alpha_id': self.best_alpha_id, 'stats': self.best_stats}
                    if not self._passes_final_correlations(final_result):
                        complete_status = 'STAGE3_REJECTED'
                        complete_reason = '最终SC/PC未明确通过'
                    else:
                        final_result = self._apply_score(final_result)
                        self.best_score = final_result['score']
                        self.best_base_score = final_result['score']
                        self.score_components = final_result['score_components']
                        self.score_penalties = final_result['score_penalties']
                        complete_status = 'OPTIMIZED'
                        complete_reason = '第3阶段门槛及SC/PC明确通过'
                else:
                    complete_status = f'STAGE{hill_stage}_COMPLETE'
                    complete_reason = f'第{hill_stage}阶段批量预算明确完成且门槛通过'
                update_source_record(
                    source_state, selected_id, complete_status,
                    complete_reason,
                    optimized_at=_source_now(), final_alpha_id=self.best_alpha_id,
                    final_expression=self.best_expr, iteration_count=iteration_count,
                    hill_stage=hill_stage,
                    stage_batches_used=self.current_position.get(
                        'stage_post_batches_used', 0
                    ),
                    stage_plan_cursor=self.current_position.get('stage_plan_cursor', 0),
                    stage_post_batches_used=self.current_position.get(
                        'stage_post_batches_used', 0
                    ),
                    stage_cache_batches_reused=self.current_position.get(
                        'stage_cache_batches_reused', 0
                    ),
                    stage_observed_candidates=self.current_position.get(
                        'stage_observed_candidates', 0
                    ),
                    stage_score=self.best_score,
                    score_version=STAGE_SCORE_VERSION,
                    objective_version=OBJECTIVE_VERSION,
                    code_version=CODE_VERSION,
                    gate_level=final_gate.get('gate_level'),
                    gate_deficits=final_gate.get('gate_deficits', {}),
                    candidate_pool_fingerprint=self.current_position.get(
                        'candidate_pool_fingerprint'
                    ),
                    score_components=self.score_components,
                    score_penalties=self.score_penalties,
                    best_stats=self.best_stats,
                    stage_gate=final_gate,
                    admission_profile=SOURCE_ADMISSION_PROFILE,
                    baseline_refresh_status=self.baseline_refresh_status,
                    baseline_alpha_id=self.baseline_alpha_id,
                    source_sc_kind=selected.get('source_sc_kind'),
                    stage_observable_results=self.stage_observable_results,
                    stage_pass_results=self.stage_pass_results,
                    stage_logical_batches=self.current_position.get(
                        'stage_plan_cursor', 0
                    ),
                    stage_window_started_at=selected.get('selected_at') or _source_now(),
                    no_new_candidate_count=0,
                )
                if complete_status == f'STAGE{hill_stage}_COMPLETE' and hill_stage < 3:
                    branch_limit = STAGE_MAX_IMMEDIATE_BRANCHES if hill_stage == 1 else 1
                    branch_candidates = select_immediate_stage_branches(
                        self.current_position.get('stage_branches')
                        or getattr(self, 'stage_pass_candidates', []),
                        hill_stage, branch_limit,
                    )
                    created, merged = enqueue_immediate_stage_branches(
                        source_state,
                        source_state.get('candidates', {}).get(selected_id, selected),
                        branch_candidates,
                        hill_stage,
                    )
                    self._metric('stage_branches_created', len(created))
                    self._metric('stage_branch_merges', merged)
                    for branch in created:
                        append_source_event({
                            'event': 'IMMEDIATE_STAGE_HANDOFF',
                            'source_alpha_id': selected_id,
                            'alpha_id': branch.get('alpha_id'),
                            'branch_id': branch.get('branch_id'),
                            'from_stage': hill_stage,
                            'to_stage': hill_stage + 1,
                            'template_family': branch.get('branch_family'),
                        }, store=getattr(source_state, '_store', None))
                save_source_state(source_state)
                logging.info(f'💾 源 Alpha {selected_id} 已记录为 {complete_status}')

            except DailyBacktestLimitReached as exc:
                update_source_record(
                    source_state, selected_id, 'INTERRUPTED',
                    '每日回测额度不足，保留候选和现有优化检查点',
                    retry_after=exc.reset_at,
                )
                save_source_state(source_state)
                self._wait_for_budget_reset(exc.snapshot)
                continue
            except KeyboardInterrupt:
                update_source_record(
                    source_state, selected_id, 'INTERRUPTED',
                    '用户中断，保留候选和现有优化检查点',
                )
                save_source_state(source_state)
                logging.info('🛑 当前源 Alpha 已记录为 INTERRUPTED，未冒充已处理')
                raise
            except SystemExit:
                update_source_record(
                    source_state, selected_id, 'INTERRUPTED',
                    '系统退出，保留候选和现有优化检查点',
                )
                save_source_state(source_state)
                raise
            except Exception as exc:
                update_source_record(
                    source_state, selected_id, 'BUG_BLOCKED',
                    f'优化异常: {type(exc).__name__}: {exc}',
                    retry_after=None,
                    retry_count=int(selected.get('retry_count') or 0) + 1,
                    retry_kind='CODE_EXCEPTION',
                    objective_version=OBJECTIVE_VERSION,
                    code_version=CODE_VERSION,
                )
                save_source_state(source_state)
                logging.exception(f'❌ 优化 Alpha {selected_id} 时出错')
                self._wait_source_idle(10)
                continue

            logging.info(f'🎉 第 {round_count} 轮完成\n')


def _run_main_loop():
    """启动爬山程序；保留原入口的持续重启语义。"""
    print("==================================================")
    print("🚀 脚本已启动")
    print("==================================================")

    # 外层永不停止的重启循环
    restart_count = 0
    while True:
        restart_count += 1
        try:
            if restart_count > 1:
                print(f"\n🔄 第 {restart_count} 次自动重启 (等待30秒)...")
                time.sleep(30)

            print("🔑 正在初始化优化器...")
            optimizer = AsyncOptimizer()
            print("✅ 初始化成功，开始执行优化任务...")

            if CONTINUOUS_MODE:
                optimizer.run_continuous()
            else:
                optimizer.run()

            # 非持续模式run()正常结束后退出
            if not CONTINUOUS_MODE:
                break
        except KeyboardInterrupt:
            print("\n🛑 用户按下 Ctrl+C")
            print("   当前状态已保存，程序停止；下次启动将从日期和优化断点恢复。")
            break

        except SystemExit:
            print("\n🛑 收到系统退出信号，程序终止")
            break

        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")
            import traceback
            traceback.print_exc()
            if CONTINUOUS_MODE:
                print(f"   持续模式下将在60秒后自动重启...")
                time.sleep(60)
            else:
                break


def main():
    """保持原启动命令不变，并防止多个进程重复领取同一源或批次。"""
    instance_lock = SingleInstanceLock()
    if not instance_lock.acquire():
        print('🛑 已有全自动爬山实例正在运行；本进程不领取源 Alpha，也不创建回测。')
        return
    try:
        _run_main_loop()
    finally:
        instance_lock.release()


if __name__ == '__main__':
    main()
