import base64
import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests


HILL_ROOT = Path(__file__).parents[1] / '代码' / '优化代码' / '爬山代码'
OPTIMIZATION_ROOT = HILL_ROOT.parent
for path in (HILL_ROOT, OPTIMIZATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Core.api.client import BrainClient
from hill_climbing.expression_utils import (
    _cache_key, _multi_batch_key, normalize_simulation_settings,
)
from hill_climbing.config import STAGE_BATCH_BUDGETS
from hill_climbing.routes import ROUTE_REGISTRY, choose_route

with redirect_stdout(io.StringIO()):
    hill = importlib.import_module('hill_climbing.optimizer')

_TEST_RUNTIME = tempfile.TemporaryDirectory()
hill.HILL_CLIMBING_SOURCE_DB_PATH = Path(_TEST_RUNTIME.name) / 'source_state_v6.sqlite3'


class P2YSettingsTest(unittest.TestCase):
    def test_stage_batch_budgets_are_independent(self):
        self.assertEqual(STAGE_BATCH_BUDGETS, {1: 2, 2: 4, 3: 5})

    def test_route_registry_keeps_unavailable_and_ai_modes_dormant(self):
        self.assertEqual(ROUTE_REGISTRY['filter']['status'], 'UNAVAILABLE')
        self.assertEqual(ROUTE_REGISTRY['gvn']['status'], 'UNAVAILABLE')
        self.assertEqual(ROUTE_REGISTRY['ai']['status'], 'DISABLED_BY_POLICY')
        self.assertEqual(ROUTE_REGISTRY['robust_sharpe']['status'], 'DIAGNOSTIC_ONLY')

    def test_later_stage_chooses_untried_route_for_largest_deficit(self):
        gate = {'gate_deficits': {'sharpe_2y': 0.4, 'turnover': 0.1}}
        self.assertEqual(choose_route(2, gate, ()), 'stable')
        self.assertNotEqual(choose_route(2, gate, ('stable',)), 'stable')

    def test_margin_bp_deficit_routes_to_turnover_margin_controls(self):
        gate = {'gate_deficits': {'margin_bp': 0.6, 'sharpe_2y': 0.1}}
        self.assertEqual(choose_route(3, gate, ()), 'smooth')

    def test_new_operator_policy_grandfathers_source_tree_only(self):
        inherited = 'trade_when(field > 0, add(rank(field), 1), -1)'
        allowed = {'rank', 'zscore'}
        self.assertEqual(
            hill.new_operator_policy_reason(
                f'zscore({inherited})', inherited, allowed
            ),
            '',
        )
        self.assertIn(
            '禁用操作符',
            hill.new_operator_policy_reason(
                f'add({inherited}, 1)', inherited, allowed
            ),
        )

    def test_payload_cache_and_batch_identity_force_p2y_without_mutating_input(self):
        original = {'region': 'GBR', 'testPeriod': 'P0Y'}
        normalized = normalize_simulation_settings(original)
        self.assertEqual(normalized['testPeriod'], 'P2Y')
        self.assertEqual(original['testPeriod'], 'P0Y')
        self.assertEqual(
            _cache_key('rank(field)', original),
            _cache_key('rank(field)', normalized),
        )
        self.assertEqual(
            _multi_batch_key(['rank(field)'], original),
            _multi_batch_key(['rank(field)'], normalized),
        )

    def test_multi_simulation_payload_is_p2y(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = MagicMock(stop_requested=False, history={})
        optimizer.settings = {'region': 'GBR', 'testPeriod': 'P0Y'}
        optimizer.stop_requested = False
        budget = MagicMock()
        budget.post_cooldown_snapshot.return_value = {'active': False}
        budget.reserve.return_value = {
            'used': 8, 'remaining': 2992, 'limit': 3000, 'reset_at': 'later',
        }
        budget.record_post_rate_limit.return_value = {
            'retry_after': '2099-01-01T00:00:00+08:00',
        }
        optimizer._ensure_backtest_budget = MagicMock(return_value=budget)
        expressions = [f'rank(ts_delay(field, {index + 1}))' for index in range(8)]
        with patch.object(
            hill, 'batch_verify_expressions',
            return_value=[{'valid': True} for _ in expressions],
        ), patch.object(
            hill, 'post_multi_simulation',
            return_value={'location': None, 'status_code': 429},
        ) as post_mock:
            optimizer.evaluate_batch(expressions)
        payloads = post_mock.call_args.args[1]
        self.assertTrue(all(item['settings']['testPeriod'] == 'P2Y' for item in payloads))

    def test_old_stage2_cumulative_block_is_reactivated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text(json.dumps({
                'candidates': {'source': {
                    'alpha_id': 'source', 'status': 'BLOCKED_INCOMPLETE_BATCH',
                    'hill_stage': 2, 'stage_batches_used': 1,
                    'code_version': 'hill-climbing-v4.7.2',
                    'admission_profile': hill.SOURCE_ADMISSION_PROFILE,
                }},
            }), encoding='utf-8')
            record = hill.load_source_state(path)['candidates']['source']
        self.assertEqual(record['status'], 'INTERRUPTED')
        self.assertEqual(record['retry_kind'], 'P2Y_SEMANTICS_FIXED')
        self.assertEqual(record['hill_stage'], 1)


class ExpensiveCheckOrderingTest(unittest.TestCase):
    def test_basic_gate_failure_skips_sc_and_pnl_path(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = MagicMock(history={}, sc_status={})
        optimizer.settings = {'region': 'GBR'}
        optimizer.hill_stage = 1
        result = {
            'id': 'alpha1',
            'is': {
                'sharpe': 1.0, 'fitness': 1.0, 'margin': 0.001,
                'turnover': 0.2, 'checks': [{'result': 'PASS'}],
            },
            'train': {'sharpe': 1.5},
        }
        output = {}
        with patch.object(hill, 'get_sc_check') as sc_mock:
            optimizer._process_result(result, 'rank(field)', '/simulations/1', output)
        sc_mock.assert_not_called()
        optimizer.client.check_factory_shape.assert_not_called()
        self.assertEqual(
            output['rank(field)']['stats']['sc_status'],
            'SC_SKIPPED_BASIC_GATE',
        )


class NetworkStateMachineTest(unittest.TestCase):
    def test_post_connection_reset_is_never_retried(self):
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError('10054')
        client = BrainClient(session=session)
        with patch('Core.api.client.time.sleep') as sleep_mock:
            self.assertIsNone(client.post('/simulations'))
        self.assertEqual(session.request.call_count, 1)
        sleep_mock.assert_not_called()

    def test_get_connection_reset_has_exactly_three_attempts(self):
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError('10054')
        client = BrainClient(session=session)
        with patch('Core.api.client.time.sleep') as sleep_mock:
            self.assertIsNone(client.get('/alphas/example'))
        self.assertEqual(session.request.call_count, 3)
        retry_waits = [call.args[0] for call in sleep_mock.call_args_list if call.args[0] >= 2]
        self.assertEqual(retry_waits, [2.0, 5.0])

    def test_jwt_exp_schedules_refresh_five_minutes_early(self):
        session = requests.Session()
        payload = base64.urlsafe_b64encode(json.dumps({'exp': 2000}).encode()).decode().rstrip('=')
        session.cookies.set('t', f'a.{payload}.b')
        client = BrainClient(session=session)
        with patch('Core.api.client.time.time', return_value=1000), patch(
            'Core.api.client.time.monotonic', return_value=50
        ):
            client.mark_authenticated()
        self.assertEqual(client._auth_refresh_at, 750)

    def test_failed_proactive_refresh_keeps_single_401_recovery(self):
        session = MagicMock()
        failed_proactive = MagicMock(status_code=500, headers={})
        unauthorized = MagicMock(status_code=401, headers={})
        successful_auth = MagicMock(status_code=201, headers={})
        success = MagicMock(status_code=200, headers={})
        session.request.side_effect = [
            failed_proactive, unauthorized, successful_auth, success,
        ]
        client = BrainClient(session=session)
        client._auth_refresh_at = 0
        with patch('Core.api.client.time.sleep'):
            self.assertIs(client.get('/alphas/example'), success)
        self.assertEqual(session.request.call_count, 4)


if __name__ == '__main__':
    unittest.main()
