import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

import pandas as pd

HILL_ROOT = Path(__file__).parents[1] / '代码' / '优化代码' / '爬山代码'
OPTIMIZATION_ROOT = HILL_ROOT.parent
for path in (HILL_ROOT, OPTIMIZATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Core.api.data_api import get_datafield_metadata
from Core.sim.alpha_manager import (
    allocate_tower_candidate_pool,
    build_field_combination_key,
    extract_expression_field_ids,
    rank_field_combination_candidates,
)
from Core.sim import validator
from hill_climbing.source_pipeline import (
    apply_region_category_relative_quality,
    promote_completed_stages,
    source_scope_reason,
)
from hill_climbing.config import (
    STAGE_SCORE_VERSION, TOWER_STAGE1_BATCHES, TOWER_STAGE2_BATCHES,
    TOWER_STAGE3_BATCHES,
)


class FieldCombinationPoolTest(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            'field_a': {'id': 'field_a', 'dataset': {'id': 'dataset_a'}},
            'field_b': {'id': 'field_b', 'dataset_id': 'dataset_b'},
        }

    def test_extract_fields_excludes_operators_parameters_and_groups(self):
        expression = (
            'group_rank(ts_target_tvr_decay(field_a, lambda_min=0.1, '
            'target_tvr=0.2), sector) + vec_avg(field_b)'
        )
        self.assertEqual(
            extract_expression_field_ids(expression),
            ['field_a', 'field_b'],
        )

    def test_order_and_direction_are_part_of_combination_key(self):
        common = {'settings': {'region': 'GLB', 'universe': 'TOP3000', 'delay': 1}}
        ab = build_field_combination_key(
            dict(common, expression='subtract(field_a, field_b)', sharpe=1.0),
            self.metadata,
        )
        ba = build_field_combination_key(
            dict(common, expression='subtract(field_b, field_a)', sharpe=1.0),
            self.metadata,
        )
        negative = build_field_combination_key(
            dict(common, expression='subtract(field_a, field_b)', sharpe=-1.0),
            self.metadata,
        )
        self.assertNotEqual(ab, ba)
        self.assertNotEqual(ab, negative)
        self.assertEqual(ab[3], (('dataset_a', 'field_a'), ('dataset_b', 'field_b')))

    def test_best_per_combination_and_tower_limit(self):
        records = []
        for index in range(14):
            records.append({
                'alpha_id': f'a{index:02d}',
                'expression': f'rank(field_{index})',
                'field_ids': [f'field_{index}'],
                'settings': {'region': 'GLB', 'universe': 'TOP3000', 'delay': 1},
                'fitness': 1.0 + index / 100,
                'sharpe': 1.5,
                'covered_towers': ['GLB/D1/MODEL'],
            })
        metadata = {
            f'field_{index}': {'id': f'field_{index}', 'dataset_id': f'ds{index}'}
            for index in range(14)
        }
        records.append(dict(records[0], alpha_id='weak', fitness=0.5))
        ranked = rank_field_combination_candidates(records, metadata)
        pool = allocate_tower_candidate_pool(ranked, active_limit=12)
        self.assertEqual(len(ranked['winners']), 14)
        self.assertEqual(len(ranked['superseded']), 1)
        self.assertEqual(ranked['winners'][records[0].get('field_combination_key', next(iter(ranked['winners'])))]['alpha_id'], 'a00')
        self.assertEqual(len(pool['active']), 12)
        self.assertEqual(len(pool['reserve']), 2)

    def test_multi_tower_candidate_uses_one_primary_slot(self):
        ranked = rank_field_combination_candidates([{
            'alpha_id': 'multi', 'expression': 'rank(field_a)',
            'settings': {'region': 'GLB', 'universe': 'TOP3000', 'delay': 1},
            'fitness': 1.0, 'sharpe': 1.5,
            'covered_towers': ['GLB/D1/MODEL', 'GLB/D1/ANALYST'],
        }], self.metadata)
        pool = allocate_tower_candidate_pool(ranked)
        self.assertEqual(len(pool['active']), 1)
        self.assertIn(pool['active'][0]['primary_tower'], pool['active'][0]['covered_towers'])
        self.assertEqual(sum(v['active_count'] for v in pool['tower_summary'].values()), 1)


class FieldMetadataTest(unittest.TestCase):
    def test_saved_metadata_has_priority_and_skips_network(self):
        client = Mock()
        saved = {'field_a': {'id': 'field_a', 'dataset_id': 'saved'}}
        result = get_datafield_metadata(
            client, ['field_a'], 'EQUITY', 'GLB', 'TOP3000', 1, catalog=saved
        )
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['metadata']['field_a']['dataset_id'], 'saved')
        client.get.assert_not_called()

    def test_exact_platform_match_is_required(self):
        client = Mock()
        with patch('Core.api.data_api.get_datafields',
                   return_value=pd.DataFrame([{'id': 'field_a_suffix'}])):
            result = get_datafield_metadata(
                client, ['field_a'], 'EQUITY', 'GLB', 'TOP3000', 1, catalog={}
            )
        self.assertEqual(result['status'], 'PENDING_FIELD_METADATA')
        self.assertEqual(result['pending_field_ids'], ['field_a'])


class SourceScopeTest(unittest.TestCase):
    @staticmethod
    def record(expression, datasets=('dataset_a',)):
        field_ids = [f'field_{index}' for index in range(len(datasets))]
        return {
            'expression': expression,
            'field_ids': field_ids,
            'field_metadata': {
                field_id: {'id': field_id, 'dataset_id': dataset_id}
                for field_id, dataset_id in zip(field_ids, datasets)
            },
        }

    def test_relative_quality_starts_at_eight_and_is_region_category_scoped(self):
        records = []
        for index in range(8):
            records.append({
                'alpha_id': f'a{index}', 'hill_stage': 1,
                'score_version': STAGE_SCORE_VERSION, 'region': 'USA',
                'primary_tower': 'USA/TOP3000/D1/MODEL',
                'field_metadata': {
                    'f': {'dataset_id': 'demo', 'category': {'id': 'MODEL'}},
                },
                'best_stats': {
                    'sharpe': 1.0 + index / 10, 'fitness': 0.7,
                    'sharpe_2y': 0.9 + index / 10, 'margin': 0.0005,
                    'turnover': 0.2, 'sc': 0.2,
                },
            })
        apply_region_category_relative_quality(records, 1)
        self.assertEqual(records[0]['best_stats']['relative_quality'], 0.0)
        self.assertEqual(records[-1]['best_stats']['relative_quality'], 1.0)
        self.assertEqual(records[-1]['best_stats']['relative_quality_window'], 'PARTIAL')

        conflict = dict(records[0])
        conflict['alpha_id'] = 'conflict'
        conflict['best_stats'] = dict(records[0]['best_stats'])
        conflict['best_stats'].pop('relative_quality', None)
        conflict['field_metadata'] = {'f': {'category': 'ANALYST'}}
        apply_region_category_relative_quality([*records[:7], conflict], 1)
        self.assertNotIn('relative_quality', conflict['best_stats'])

    def test_source_scope_rejects_multi_dataset_and_forbidden_operator(self):
        self.assertIn(
            '跨2个数据集',
            source_scope_reason(self.record(
                'subtract(field_0, field_1)', ('dataset_a', 'dataset_b')
            )),
        )
        # 源表达式的历史算子只做继承基线，不在源入口误拒。
        self.assertEqual(source_scope_reason(self.record('add(field_0, 1)')), '')

    def test_source_scope_keeps_unknown_metadata_pending_and_low_complexity_valid(self):
        pending = self.record('rank(field_0)')
        pending['field_metadata'] = {}
        self.assertIn('不可观察', source_scope_reason(pending))
        self.assertEqual(source_scope_reason(self.record('rank(ts_mean(field_0, 22))')), '')


class ValidatorAlphaResultTest(unittest.TestCase):
    def test_get_sc_check_forwards_existing_alpha_result(self):
        details = {'settings': {'region': 'GLB'}}
        with patch.object(validator, '_ensure_sc_cache'), patch.object(
            validator, '_sc_rets', pd.DataFrame({'os': [0.0, 1.0]})
        ), patch.object(validator, '_sc_ids', {'GLB': ['os']}), patch.object(
            validator, 'calc_self_corr', return_value=0.2
        ) as calc:
            value = validator.get_sc_check(Mock(), 'target', 0.4, alpha_result=details)
        self.assertEqual(value, 0.2)
        self.assertIs(calc.call_args.kwargs['alpha_result'], details)


class StagePromotionTest(unittest.TestCase):
    def test_stage_budgets_are_32_plus_32_plus_40(self):
        self.assertEqual(TOWER_STAGE1_BATCHES * 8, 32)
        self.assertEqual(TOWER_STAGE2_BATCHES * 8, 32)
        self.assertEqual(TOWER_STAGE3_BATCHES * 8, 40)

    def test_observation_window_is_reporting_only(self):
        records = [
            {
                'alpha_id': f'a{index}', 'primary_tower': 'TOWER',
                'pool_status': 'ACTIVE', 'hill_stage': 1,
                'status': 'STAGE1_COMPLETE', 'stage_score': float(index),
                'score_version': STAGE_SCORE_VERSION,
                'promotion_window_closed': True, 'promotion_from_stage': 0,
                'stage_batches_used': 2, 'stage_observable_results': 16,
                'best_stats': {
                    'sharpe': 1.7 + index / 10, 'fitness': 1.0 + index / 10,
                    'margin': 0.001 + index / 10000, 'sharpe_2y': 1.7,
                    'turnover': 0.2, 'passed': False, 'sc': 0.2,
                },
            }
            for index in range(8)
        ]
        records[0]['status'] = 'PENDING_STAGE_SCORE'
        promote_completed_stages(records)
        self.assertEqual(sum(r['hill_stage'] == 2 for r in records), 0)
        self.assertTrue(all(r.get('promotion_window_mode') == 'REPORT_ONLY' for r in records))
        self.assertEqual(sum(r['pool_status'] == 'RESERVE' for r in records), 0)
        self.assertEqual(records[0]['status'], 'PENDING_STAGE_SCORE')

    def test_observation_window_never_mutates_stage(self):
        records = [
            {'alpha_id': f's3-{i}', 'primary_tower': 'T', 'hill_stage': 3,
             'pool_status': 'ACTIVE', 'status': 'ELIGIBLE'} for i in range(3)
        ] + [
            {'alpha_id': f's2-{i}', 'primary_tower': 'T', 'hill_stage': 2,
             'pool_status': 'ACTIVE', 'status': 'STAGE2_COMPLETE'} for i in range(3)
        ] + [
            {
                'alpha_id': f'late-{i}', 'primary_tower': 'T', 'hill_stage': 1,
                'pool_status': 'ACTIVE', 'status': 'STAGE1_COMPLETE',
                'score_version': STAGE_SCORE_VERSION,
                'best_stats': {
                    'sharpe': 2.0, 'fitness': 1.1, 'margin': 0.001,
                    'sharpe_2y': 1.8, 'turnover': 0.2, 'sc': 0.2,
                },
            } for i in range(6)
        ]
        promote_completed_stages(records)
        self.assertEqual(sum(r['hill_stage'] >= 2 for r in records), 6)
        self.assertTrue(all(r['pool_status'] == 'ACTIVE' for r in records[-6:]))
        self.assertTrue(all(r.get('promotion_window_mode') == 'REPORT_ONLY' for r in records))


if __name__ == '__main__':
    unittest.main()
