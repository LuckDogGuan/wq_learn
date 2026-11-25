"""源 Alpha 的字段元数据、组合排名、塔分配与 SC 调度。"""

from collections import defaultdict
from datetime import datetime
from functools import cmp_to_key
import re

from Core.api.data_api import get_datafield_metadata
from Core.sim.research_policy import candidate_rank_key
from Core.sim.alpha_manager import (
    allocate_tower_candidate_pool,
    extract_expression_field_ids,
    rank_field_combination_candidates,
)
from hill_climbing.config import (
    PROMOTION_OBSERVABLE_WINDOW, PROMOTION_PARTIAL_MAX_BATCHES,
    PROMOTION_PARTIAL_MAX_HOURS, PROMOTION_PARTIAL_MIN_OBSERVABLE,
    SOURCE_ADMISSION_PROFILE, STAGE_SCORE_VERSION, TOWER_PROMOTION_COHORT_SIZE,
)
from hill_climbing.scoring import compare_candidates, evaluate_stage_candidate


def quarter_key(now=None):
    now = now or datetime.now().astimezone()
    return f'{now.year}-Q{(now.month - 1) // 3 + 1}'


def _compact_metadata(metadata):
    dataset = metadata.get('dataset')
    dataset_id = dataset.get('id') if isinstance(dataset, dict) else None
    return {
        'id': str(metadata.get('id') or ''),
        'dataset_id': str(
            dataset_id or metadata.get('dataset_id') or metadata.get('dataset.id') or 'UNKNOWN'
        ),
        'type': metadata.get('type'),
        'category': metadata.get('category') or metadata.get('category_name'),
    }


def enrich_field_metadata(client, records, catalog=None):
    """只补齐当前候选，已保存字段元数据优先且不重复访问平台。"""
    pending = []
    by_scope = defaultdict(list)
    for record in records:
        expression = record.get('expression') or ''
        field_ids = extract_expression_field_ids(expression)
        record['field_ids'] = field_ids
        settings = record.get('settings') or {}
        scope = (
            str(record.get('instrument_type') or settings.get('instrumentType') or 'EQUITY'),
            str(record.get('region') or settings.get('region') or 'UNKNOWN'),
            str(record.get('universe') or settings.get('universe') or 'UNKNOWN'),
            int(record.get('delay', settings.get('delay', 1))),
        )
        by_scope[scope].append(record)

    for (instrument_type, region, universe, delay), scope_records in by_scope.items():
        saved = {}
        field_ids = []
        for record in scope_records:
            for field_id, metadata in (record.get('field_metadata') or {}).items():
                if isinstance(metadata, dict):
                    saved[field_id] = metadata
            field_ids.extend(record['field_ids'])
        result = get_datafield_metadata(
            client, field_ids, instrument_type, region, universe, delay,
            catalog=saved or catalog,
        )
        resolved = result['metadata']
        for record in scope_records:
            record['field_metadata'] = {
                field_id: _compact_metadata(resolved[field_id])
                for field_id in record['field_ids'] if field_id in resolved
            }
            missing = [
                field_id for field_id in record['field_ids']
                if field_id not in record['field_metadata']
            ]
            if not record['field_ids'] or missing:
                record['status'] = 'PENDING_FIELD_METADATA'
                record['pending_field_ids'] = missing or record['field_ids']
                pending.append(record)
    return pending


_CALL_PATTERN = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')


def source_scope_reason(record):
    """返回源表达式不可进入固定单数据集探针的确定性原因。

    历史源表达式的算子和复杂度属于既有资产，不作为入口拒绝条件；
    禁用算子和新增复杂度只约束优化器新引入的变换。
    """
    metadata = record.get('field_metadata') or {}
    if not record.get('field_ids') or len(metadata) != len(record.get('field_ids') or []):
        return '字段元数据不可观察'
    dataset_ids = {
        str(item.get('dataset_id') or 'UNKNOWN')
        for item in metadata.values() if isinstance(item, dict)
    }
    if 'UNKNOWN' in dataset_ids:
        return '数据集元数据不可观察'
    if len(dataset_ids) != 1:
        return f'源表达式跨{len(dataset_ids)}个数据集'
    return ''


def build_candidate_pool(client, records, active_limit=12, catalog=None, now=None):
    """建立一组合一赢家、主塔 ACTIVE 和季度 RESERVE 池。"""
    records = list(records)
    pending = enrich_field_metadata(client, records, catalog=catalog)
    pending_ids = {str(record.get('alpha_id') or record.get('id')) for record in pending}
    eligible_records = []
    disabled_scope = []
    for record in records:
        alpha_id = str(record.get('alpha_id') or record.get('id'))
        if alpha_id in pending_ids:
            continue
        reason = source_scope_reason(record)
        if reason:
            record['status'] = 'DISABLED_SCOPE'
            record['status_reason'] = reason
            disabled_scope.append(record)
            continue
        record['admission_profile'] = SOURCE_ADMISSION_PROFILE
        eligible_records.append(record)
    metadata = {}
    for record in eligible_records:
        metadata.update(record.get('field_metadata') or {})
        record['covered_towers'] = list(dict.fromkeys(
            item.get('raw_scope') for item in (record.get('gap_scopes') or [])
            if isinstance(item, dict) and item.get('raw_scope')
        ))
    ranked = rank_field_combination_candidates(eligible_records, metadata, rank_key=candidate_rank_key)
    pool = allocate_tower_candidate_pool(ranked, active_limit=active_limit, rank_key=candidate_rank_key)
    current_quarter = quarter_key(now)
    for bucket in ('active', 'reserve', 'hold_pass', 'superseded', 'pending_metadata'):
        for record in pool.get(bucket, []):
            record['quarter_key'] = current_quarter
    pool['pending_metadata'] = list({
        str(record.get('alpha_id') or record.get('id')): record
        for record in pool['pending_metadata'] + pending
    }.values())
    pool['disabled_scope'] = disabled_scope
    pool['ranked'] = ranked['ranked']
    return pool


def iter_sc_attempts(pool, attempt_limit=24):
    """每塔最多给出 24 次尝试；同组合按排名顺序递补。"""
    attempts = defaultdict(int)
    for active in pool.get('active', []):
        tower = active.get('primary_tower')
        key = active.get('field_combination_key')
        for candidate in pool.get('ranked', {}).get(key, [active]):
            if attempts[tower] >= attempt_limit:
                break
            attempts[tower] += 1
            candidate['primary_tower'] = tower
            candidate['covered_towers'] = active.get('covered_towers', [])
            candidate['pool_status'] = 'ACTIVE'
            yield candidate


def _template_category(record):
    """相对排名沿用模板学习的 Category 口径；冲突或缺失不参与。"""
    tower = str(record.get('primary_tower') or '').strip()
    tower_category = tower.replace('\\', '/').rstrip('/').split('/')[-1].upper() if tower else ''
    metadata = record.get('field_metadata') or {}
    field_categories = set()
    for value in metadata.values():
        if not isinstance(value, dict):
            continue
        category = value.get('category') or value.get('category_name')
        if isinstance(category, dict):
            category = category.get('id') or category.get('name') or category.get('value')
        category = str(category or '').strip().upper()
        if category:
            field_categories.add(category)
    field_categories.discard('')
    if tower_category and field_categories and tower_category not in field_categories:
        return None
    if tower_category:
        return tower_category
    return next(iter(field_categories)) if len(field_categories) == 1 else None


def _percentile(values, value):
    if len(values) < 2:
        return 0.5
    below = sum(item < value for item in values)
    equal = sum(item == value for item in values)
    return (below + max(0, equal - 1) / 2) / (len(values) - 1)


def apply_region_category_relative_quality(records, stage):
    """满8个完整源后写入同 Region×Category 的 Sharpe/P2Y 百分位。"""
    groups = defaultdict(list)
    for record in records:
        if int(record.get('hill_stage') or 1) != stage:
            continue
        stats = dict(record.get('best_stats') or record)
        for key in (
            'relative_quality', 'relative_quality_scope',
            'relative_quality_window', 'relative_quality_count',
        ):
            stats.pop(key, None)
        record['best_stats'] = stats
        if record.get('score_version') != STAGE_SCORE_VERSION:
            continue
        assessment = evaluate_stage_candidate(stats, stage)
        sharpe = stats.get('sharpe')
        p2y = stats.get('sharpe_2y')
        category = _template_category(record)
        settings = record.get('settings') or {}
        region = str(record.get('region') or settings.get('region') or 'UNKNOWN').upper()
        if (
            not category or not assessment['gate']['observable']
            or not isinstance(sharpe, (int, float))
            or not isinstance(p2y, (int, float))
        ):
            continue
        groups[(region, category)].append((record, float(sharpe), float(p2y)))
    for (region, category), items in groups.items():
        if len(items) < 8:
            continue
        sharpes = [item[1] for item in items]
        p2ys = [item[2] for item in items]
        window_kind = 'FULL' if len(items) >= 40 else 'PARTIAL'
        for record, sharpe, p2y in items:
            stats = dict(record.get('best_stats') or record)
            stats['relative_quality'] = (
                _percentile(sharpes, sharpe) + _percentile(p2ys, p2y)
            ) / 2
            stats['relative_quality_scope'] = f'{region}|{category}'
            stats['relative_quality_window'] = window_kind
            stats['relative_quality_count'] = len(items)
            record['best_stats'] = stats
    return records


def promote_completed_stages(records, stage2_limit=6, stage3_limit=3,
                             cohort_size=TOWER_PROMOTION_COHORT_SIZE):
    """按真实范围的40条可观察窗口晋级，并允许下一阶段门槛快速通道。"""
    records = list(records)
    changed = []
    for stage, complete_status, next_limit in (
        (1, 'STAGE1_COMPLETE', stage2_limit),
        (2, 'STAGE2_COMPLETE', stage3_limit),
    ):
        apply_region_category_relative_quality(records, stage)
        groups = defaultdict(list)
        for record in records:
            if int(record.get('hill_stage') or 1) != stage:
                continue
            metadata = record.get('field_metadata') or {}
            dataset_ids = sorted({
                str(value.get('dataset_id') or 'UNKNOWN')
                for value in metadata.values() if isinstance(value, dict)
            })
            settings = record.get('settings') or {}
            scope = (
                str(record.get('region') or settings.get('region') or 'UNKNOWN'),
                str(record.get('universe') or settings.get('universe') or 'UNKNOWN'),
                int(record.get('delay', settings.get('delay', 1))),
                dataset_ids[0] if len(dataset_ids) == 1 else 'UNKNOWN',
                str(record.get('primary_tower') or 'UNKNOWN'),
            )
            groups[scope].append(record)
        for scope, scope_records in groups.items():
            scope_key = '|'.join(map(str, scope))
            completed = [
                record for record in scope_records
                if record.get('pool_status') == 'ACTIVE'
                and record.get('status') == complete_status
                and record.get('score_version') == STAGE_SCORE_VERSION
                and not (
                    record.get('promotion_window_closed')
                    and int(record.get('promotion_from_stage') or 0) == stage
                )
            ]
            if not completed:
                continue
            ranked = []
            for record in completed:
                stats = record.get('best_stats') or record
                assessment = evaluate_stage_candidate(stats, stage)
                if assessment['gate']['status'] == 'FAIL':
                    record['pool_status'] = 'RESERVE'
                    record['status_reason'] = (
                        f'第{stage}阶段完成但不满足本阶段门槛: '
                        + ','.join(assessment['gate']['failed'])
                    )
                    changed.append(record)
                    continue
                if not assessment['eligible']:
                    continue
                record['stage_score'] = assessment['score']
                record['score_components'] = assessment['components']
                ranked.append(record)
            ranked = sorted(
                ranked,
                key=cmp_to_key(lambda left, right: compare_candidates(
                    left.get('best_stats') or left, left['stage_score'],
                    right.get('best_stats') or right, right['stage_score'], stage,
                )),
                reverse=True,
            )
            window_index = 1 + max([
                int(record.get('promotion_window_index') or 0)
                for record in records
                if record.get('promotion_scope_key') == scope_key
                and record.get('promotion_window_closed')
            ] or [0])
            existing_promoted = [
                record for record in records
                if record.get('promotion_scope_key') == scope_key
                and int(record.get('promotion_from_stage') or 0) == stage
                and int(record.get('promotion_window_index') or 0) == window_index
                and int(record.get('hill_stage') or 1) >= stage + 1
            ]
            window_records = sorted(
                ranked,
                key=lambda record: (
                    str(record.get('optimized_at') or ''),
                    str(record.get('alpha_id') or ''),
                ),
            )
            accounting_records = list({
                str(record.get('alpha_id') or record.get('id')): record
                for record in window_records + existing_promoted
            }.values())
            observable = sum(max(0, int(
                record.get('stage_observable_results')
                if record.get('stage_observable_results') is not None
                else min(8, 8 * max(1, int(record.get('stage_batches_used') or 1)))
            )) for record in accounting_records)
            logical_batches = sum(max(0, int(
                record.get('stage_logical_batches')
                if record.get('stage_logical_batches') is not None
                else record.get('stage_batches_used') or 0
            )) for record in accounting_records)
            timestamps = []
            for record in accounting_records:
                try:
                    timestamps.append(datetime.fromisoformat(
                        record.get('stage_window_started_at')
                        or record.get('optimized_at') or ''
                    ))
                except (TypeError, ValueError):
                    pass
            age_hours = 0.0
            if timestamps:
                now = datetime.now(timestamps[0].tzinfo) if timestamps[0].tzinfo else datetime.now()
                age_hours = max(0.0, (now - min(timestamps)).total_seconds() / 3600)

            promoted = list(existing_promoted)
            for record in ranked:
                if len(promoted) >= next_limit:
                    break
                next_stats = dict(record.get('best_stats') or record)
                if stage + 1 == 3:
                    next_stats['passed'] = True  # 快速通道只检查数字门槛。
                if evaluate_stage_candidate(next_stats, stage + 1)['eligible']:
                    record['hill_stage'] = stage + 1
                    record['status'] = 'ELIGIBLE'
                    record['pool_status'] = 'ACTIVE'
                    record['status_reason'] = f'已满足下一阶段数字门槛，快速晋级第{stage + 1}阶段'
                    record['promotion_fast_lane'] = True
                    record['promotion_window_index'] = window_index
                    record['promotion_scope_key'] = scope_key
                    record['promotion_from_stage'] = stage
                    record['promotion_window_closed'] = False
                    record['stage_batches_used'] = 0
                    record['stage_observable_results'] = 0
                    record['stage_pass_results'] = 0
                    record['stage_logical_batches'] = 0
                    record['stage_window_started_at'] = None
                    promoted.append(record)
                    changed.append(record)

            window_ready = (
                observable >= PROMOTION_OBSERVABLE_WINDOW
                or observable >= PROMOTION_PARTIAL_MIN_OBSERVABLE
                and (
                    logical_batches >= PROMOTION_PARTIAL_MAX_BATCHES
                    or age_hours >= PROMOTION_PARTIAL_MAX_HOURS
                )
            )
            if not window_ready:
                continue
            pass_count = sum(
                int(item.get('stage_pass_results') or 0) for item in accounting_records
            )
            healthy_low, healthy_high = (6, 14) if stage == 1 else (2, 6)
            window_health = (
                'LOW' if pass_count < healthy_low
                else 'HIGH' if pass_count > healthy_high else 'HEALTHY'
            )
            remaining = [record for record in ranked if record not in promoted]
            for record in remaining[:max(0, next_limit - len(promoted))]:
                record['hill_stage'] = stage + 1
                record['status'] = 'ELIGIBLE'
                record['pool_status'] = 'ACTIVE'
                record['status_reason'] = f'观察窗口按硬门槛距离晋级第{stage + 1}阶段'
                record['promotion_fast_lane'] = False
                record['promotion_scope_key'] = scope_key
                record['promotion_from_stage'] = stage
                record['promotion_window_closed'] = False
                record['stage_batches_used'] = 0
                record['stage_observable_results'] = 0
                record['stage_pass_results'] = 0
                record['stage_logical_batches'] = 0
                record['stage_window_started_at'] = None
                promoted.append(record)
                changed.append(record)
            closing_records = list({
                str(record.get('alpha_id') or record.get('id')): record
                for record in accounting_records + promoted
                if int(record.get('hill_stage') or 1) == stage
            }.values())
            for record in closing_records:
                record['promotion_window_index'] = window_index
                record['promotion_window_closed'] = True
                record['promotion_scope_key'] = scope_key
                record['promotion_from_stage'] = stage
                record['promotion_window_observable'] = observable
                record['promotion_window_passes'] = pass_count
                record['promotion_window_health'] = window_health
                if record not in promoted:
                    record['pool_status'] = 'RESERVE'
                    record['status_reason'] = f'第{stage}阶段窗口关闭，进入季度候补池'
                if record not in changed:
                    changed.append(record)
    return changed


# v6: 保留旧名称给外部调用，但观察窗只做报表，不再改变阶段。
def promote_completed_stages(records, stage2_limit=6, stage3_limit=3,
                             cohort_size=TOWER_PROMOTION_COHORT_SIZE):
    """Refresh relative-quality windows without promoting or reserving records."""
    records = list(records)
    apply_region_category_relative_quality(records, 1)
    apply_region_category_relative_quality(records, 2)
    for record in records:
        record['promotion_window_mode'] = 'REPORT_ONLY'
    return []
