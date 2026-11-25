"""状态落盘与 PnL 不可观察分支的独立测试；不访问平台、不创建回测。"""

import importlib.util
import io
import json
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "代码" / "优化代码" / "爬山代码" / "hill_climbing" / "optimizer.py"
SPEC = importlib.util.spec_from_file_location("hill_climbing_resilience", SCRIPT)
hill = importlib.util.module_from_spec(SPEC)
with redirect_stdout(io.StringIO()):
    SPEC.loader.exec_module(hill)

_TEST_RUNTIME = tempfile.TemporaryDirectory()
hill.HILL_CLIMBING_SOURCE_DB_PATH = Path(_TEST_RUNTIME.name) / "source_state_v6.sqlite3"

from Core.sim import sc_engine, validator


class EmptyResponse:
    status_code = 200
    text = ""

    def __bool__(self):
        return True


class HillClimbingResilienceTest(unittest.TestCase):
    def test_immediate_stage_branches_are_family_distinct_and_capped(self):
        stats = {
            "sharpe": 1.5, "fitness": 0.8, "sharpe_2y": 1.4,
            "margin": 0.0007, "turnover": 0.2, "sc": 0.3,
        }
        items = [
            {"alpha_id": "a1", "expression": "rank(f1)", "stats": stats,
             "status": "COMPLETE", "template_family": "rank"},
            {"alpha_id": "a2", "expression": "rank(f2)", "stats": stats,
             "status": "COMPLETE", "template_family": "rank"},
            {"alpha_id": "a3", "expression": "ts_rank(f1,22)", "stats": stats,
             "status": "COMPLETE", "template_family": "time"},
            {"alpha_id": "a4", "expression": "ts_zscore(f1,66)", "stats": stats,
             "status": "COMPLETE", "template_family": "zscore"},
            {"alpha_id": "a5", "expression": "winsorize(f1,std=4)", "stats": stats,
             "status": "COMPLETE", "template_family": "distribution"},
        ]
        selected = hill.select_immediate_stage_branches(items, 1, 3)
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({item["template_family"] for item in selected}), 3)

    def test_immediate_branch_payload_resets_next_stage_accounting(self):
        state = {"candidates": {"source": {
            "alpha_id": "source", "expression": "rank(f1)", "pool_status": "ACTIVE",
            "settings": {"region": "USA", "testPeriod": "P2Y"},
        }}}
        branch = {
            "alpha_id": "child", "expression": "ts_rank(f1,22)",
            "template_family": "time", "template_id": "stage0.time_series_rank",
            "stats": {"sharpe": 1.5, "fitness": 0.8, "sharpe_2y": 1.4,
                      "margin": 0.0007, "turnover": 0.2, "sc": 0.3},
        }
        created, merged = hill.enqueue_immediate_stage_branches(
            state, state["candidates"]["source"], [branch], 1
        )
        self.assertEqual((len(created), merged), (1, 0))
        child = state["candidates"]["child"]
        self.assertEqual(child["hill_stage"], 2)
        self.assertEqual(child["stage_post_batches_used"], 0)
        self.assertTrue(child["immediate_stage_branch"])

    def test_single_expression_settings_sweep_is_not_exposed(self):
        self.assertFalse(hasattr(hill.AsyncOptimizer, '_optimize_settings_param'))

    def test_p2y_uses_test_sharpe_only(self):
        self.assertEqual(hill._two_year_sharpe({
            'train': {'sharpe': 0.0}, 'test': {'sharpe': 2.0},
        }), 2.0)
        self.assertIsNone(hill._two_year_sharpe({'train': {'sharpe': 3.0}}))

    def test_nan_sc_never_passes_final_correlation_gate(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 3
        optimizer.client = Mock()
        with patch.object(hill, 'get_sc_check', return_value=math.nan), patch.object(
            hill, 'get_pc_check'
        ) as pc_mock:
            self.assertFalse(optimizer._passes_final_correlations({
                'alpha_id': 'nan-sc', 'stats': {'sc': math.nan, 'pc': 0.1},
            }))
        pc_mock.assert_not_called()

    def test_pc_boundary_is_strictly_below_point_seven(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 3
        optimizer.client = Mock()
        self.assertFalse(optimizer._passes_final_correlations({
            'alpha_id': 'pc-line', 'stats': {'sc': 0.2, 'pc': 0.7},
        }))
        self.assertTrue(optimizer._passes_final_correlations({
            'alpha_id': 'pc-below', 'stats': {'sc': 0.2, 'pc': 0.699},
        }))

    def test_valid_stage_three_candidate_replaces_stronger_ineligible_baseline(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 3
        optimizer.best_score = 100.0
        optimizer.best_alpha_id = 'bad-base'
        optimizer.best_stats = {
            'sharpe': 4.0, 'fitness': 3.0, 'margin': 0.01,
            'sharpe_2y': 3.0, 'turnover': 0.2, 'passed': False, 'sc': 0.1,
        }
        candidate = {
            'alpha_id': 'valid', 'status': 'COMPLETE',
            'stats': {
                'sharpe': 1.8, 'fitness': 1.1, 'margin': 0.0012,
                'sharpe_2y': 1.8, 'turnover': 0.2, 'passed': True,
                'sc': 0.2, 'pc': 0.2,
            },
        }
        self.assertTrue(optimizer._is_better_result(candidate))

    def test_ineligible_initial_alpha_keeps_its_continuous_score(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 1
        result = optimizer._apply_score({
            'stats': {
                'sharpe': 1.20, 'fitness': 0.8, 'margin': 0.0015,
                'sharpe_2y': 1.5, 'turnover': 0.2, 'passed': False,
                'sc': 0.1,
            },
        })
        self.assertEqual(result['stage_gate']['status'], 'FAIL')
        self.assertGreater(result['score'], 0)

    def test_apply_score_exposes_distinct_gate_score_and_repair_states(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 2
        result = optimizer._apply_score({'stats': {
            'sharpe': 1.5, 'fitness': 0.8, 'sharpe_2y': 1.4,
            'margin': 0.0005, 'turnover': 0.2, 'sc': None,
        }})
        self.assertEqual(result['gate_status'], 'FAIL')
        self.assertEqual(result['score_status'], 'PENDING_SC')
        self.assertEqual(result['candidate_status'], 'FAIL')
        self.assertEqual(result['repair_route'], 'MARGIN_REPAIR')

    def test_missing_numeric_metric_remains_pending_instead_of_zero_failure(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 1
        result = optimizer._apply_score({'stats': {
            'sharpe': 1.5, 'fitness': 0.8, 'sharpe_2y': 1.4,
            'margin': None, 'turnover': 0.2, 'sc': None,
        }})
        self.assertEqual(result['gate_status'], 'PENDING')
        self.assertEqual(result['score_status'], 'PENDING_METRICS')
        self.assertEqual(result['candidate_status'], 'PENDING')
        self.assertEqual(result['repair_route'], 'NONE')

    def test_margin_effect_requires_non_margin_and_turnover_retention(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 3
        optimizer.template_baseline_stats = {
            'sharpe': 1.7, 'fitness': 1.1, 'sharpe_2y': 1.7,
            'margin': 0.0008, 'turnover': 0.2,
        }
        safe = optimizer._margin_repair_effect({
            'sharpe': 1.7, 'fitness': 1.1, 'sharpe_2y': 1.7,
            'margin': 0.0011, 'turnover': 0.2,
        })
        unsafe = optimizer._margin_repair_effect({
            'sharpe': 1.7, 'fitness': 1.1, 'sharpe_2y': 1.7,
            'margin': 0.0020, 'turnover': 0.01,
        })
        self.assertTrue(safe['margin_effective_improvement'])
        self.assertTrue(safe['margin_threshold_crossed'])
        self.assertFalse(unsafe['margin_effective_improvement'])

    def test_margin_batch_is_fixed_two_plus_two_plus_two_plus_two(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 2
        optimizer.best_expr = 'rank(field_a)'
        optimizer.best_stats = {
            'sharpe': 1.5, 'fitness': 0.8, 'sharpe_2y': 1.4,
            'margin': 0.0005, 'turnover': 0.30, 'check_failures': [],
        }
        local_pool = [{
            'template_id': f'probe.time_window.{window}',
            'expression': f'rank(ts_mean(field_a, {window}))',
            'params': {'d': window}, 'eligible': True,
            'expression_hash': f'local-{window}',
        } for window in (5, 10, 22, 66, 120, 252)]
        optimizer._probe_neighborhood_candidates = Mock(return_value=local_pool)
        formal = [{
            'template_id': template_id,
            'expression': expression,
            'resolved_params': {'d': 120, **extra},
            'eligible': True, 'expression_hash': expression_hash,
            'template_state': 'PROBATION',
        } for template_id, expression, expression_hash, extra in (
            (
                'hu_ge.series2_residual_stddev',
                'ts_std_dev(ts_regression(field_a, field_b, 120, lag=0, rettype=6), 120)',
                'hu-residual', {},
            ),
            (
                'hu_ge.series2_beta_lagged',
                'ts_regression(field_a, field_b, 120, lag=5, rettype=2)',
                'hu-beta', {'lag': 5},
            ),
        )]
        fields = [
            {'id': 'field_a', 'type': 'MATRIX', 'dataset_id': 'model1',
             'description': 'analyst earnings estimate revision'},
            {'id': 'field_b', 'type': 'MATRIX', 'dataset_id': 'model1',
             'description': 'analyst earnings estimate dispersion'},
        ]
        allowed = {
            'rank', 'ts_mean', 'ts_decay_linear', 'ts_av_diff',
            'ts_regression', 'ts_std_dev',
        }

        candidates = optimizer._margin_repair_candidates(
            Mock(), fields, allowed, formal, round_number=1,
        )

        self.assertEqual(len(candidates), 8)
        families = [item['repair_family'] for item in candidates]
        self.assertEqual(families.count('LOCAL_WINDOW'), 2)
        self.assertEqual(families.count('TURNOVER_DECAY'), 2)
        self.assertEqual(families.count('LOCAL_WINDOW_FALLBACK'), 2)
        self.assertEqual(families.count('HU_GE_RELATION'), 2)
        self.assertTrue(all(item['candidate_origin'] == 'FORMAL_TEMPLATE' for item in candidates))

    def test_not_due_refresh_log_labels_persisted_counts_as_previous(self):
        message = hill._format_core_refresh_result({
            "status": "NOT_DUE", "sc_status": "REFRESHED",
            "pyramid_status": "REFRESHED", "cached_os_count": 65,
            "observed_new_os_alpha_ids": ["a", "b"],
            "cached_new_os_alpha_ids": ["a", "b"],
            "failed_pnl_alpha_ids": [],
        })

        self.assertIn("本轮未刷新", message)
        self.assertIn("上次远端发现=2", message)
        self.assertIn("上次缓存新增=2", message)
        self.assertNotIn("本轮缓存新增=2", message)

    @staticmethod
    def _template_optimizer(results):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.client.get_available_operators.return_value = {"rank"}
        optimizer.client.get_field_metadata.return_value = {
            "id": "field_a", "type": "MATRIX", "dataset_id": "dataset_a",
            "category": "MODEL",
        }
        optimizer.stop_requested = False
        optimizer.settings = {"region": "USA", "universe": "TOP3000", "delay": 1}
        optimizer.best_expr = "rank(field_a)"
        optimizer.source_expression = optimizer.best_expr
        optimizer.source_record = {
            "sc_value": 0.2,
            "primary_tower": "USA/TOP3000/D1/MODEL",
        }
        optimizer.initial_score = 1.0
        optimizer.best_score = 1.0
        optimizer.best_stats = {
            "sharpe": 1.3, "fitness": 0.6, "margin": 0.0004,
            "sharpe_2y": 1.1, "turnover": 0.2, "sc": 0.2,
        }
        optimizer.hill_stage = 1
        optimizer.current_position = {"template_batch": 0}
        optimizer.stage_target_batches = 1
        optimizer.evaluate_batch = Mock(return_value=results)
        optimizer._record_template_candidate = Mock()
        optimizer._adopt_template_result = Mock(return_value=False)
        optimizer.save_checkpoint = Mock()
        return optimizer

    @staticmethod
    def _template_candidates(count=8):
        return [{
            "template_id": f"template_{index}", "kind": "breadth",
            "expression": f"rank(ts_delay(field_a, {index + 1}))",
            "expression_hash": f"hash_{index}", "eligible": True,
        } for index in range(count)]

    def test_template_batch_only_advances_after_eight_observed_results(self):
        candidates = self._template_candidates()
        results = {
            candidate["expression"]: {
                "status": (
                    "COMPLETE" if index < 6 else
                    "RESULTS_UNOBSERVED" if index == 6 else
                    "DEFERRED_INCOMPLETE_BATCH"
                ),
                "alpha_id": f"alpha{index}" if index < 6 else None,
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates)
        }
        optimizer = self._template_optimizer(results)
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertFalse(complete)
        self.assertEqual(optimizer.current_position["template_batch"], 0)

    def test_template_batch_accepts_complete_and_valid_cache_hits(self):
        candidates = self._template_candidates()
        results = {
            candidate["expression"]: {
                "status": "COMPLETE" if index < 4 else "CACHE_HIT",
                "alpha_id": f"alpha{index}", "score": 0,
                "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates)
        }
        optimizer = self._template_optimizer(results)
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        self.assertEqual(optimizer.current_position["template_batch"], 1)

    def test_stage1_seventh_complete_source_runs_calibration_batch(self):
        candidates = self._template_candidates(16)
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates)
        }
        optimizer = self._template_optimizer(results)
        optimizer.stage_target_batches = 2
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])
        with (
            patch.object(hill, "select_template_candidates", return_value=(candidates, [])),
            patch.object(optimizer, "_template_calibration_due", return_value=True),
        ):
            self.assertTrue(optimizer.run_template_exploration("source_a", parser))
        self.assertEqual(optimizer.evaluate_batch.call_count, 2)
        self.assertEqual(optimizer.current_position["template_batch"], 2)

    def test_stage3_missing_numeric_pc_does_not_generate_repair_batch(self):
        optimizer = self._template_optimizer({})
        optimizer.hill_stage = 3
        optimizer.stage_target_batches = 3
        optimizer.best_stats = {
            "sharpe": 1.7, "fitness": 1.1, "sharpe_2y": 1.7,
            "margin": 0.0012, "turnover": 0.2, "sc": 0.2,
            "passed": True, "pc": None,
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])
        with patch.object(hill, "select_template_candidates") as select:
            self.assertFalse(optimizer.run_template_exploration("source_a", parser))
        self.assertEqual(optimizer.template_pending_status, "PENDING_PC")
        optimizer.evaluate_batch.assert_not_called()
        select.assert_not_called()

    def test_stage3_numeric_pass_requests_sc_even_when_platform_check_failed(self):
        optimizer = self._template_optimizer({})
        optimizer.hill_stage = 3
        optimizer.stage_target_batches = 3
        optimizer.best_alpha_id = 'candidate'
        optimizer.best_stats = {
            'sharpe': 1.7, 'fitness': 1.1, 'sharpe_2y': 1.7,
            'margin': 0.0012, 'turnover': 0.2, 'sc': None,
            'passed': False, 'pc': None,
        }
        parser = Mock(tokens=[{'type': 'data_field', 'text': 'field_a'}])
        with (
            patch.object(hill, 'get_sc_check', return_value=0.2) as sc,
            patch.object(hill, 'select_template_candidates') as select,
        ):
            self.assertFalse(optimizer.run_template_exploration('source_a', parser))
        sc.assert_called_once()
        self.assertEqual(optimizer.template_pending_status, 'PENDING_PC')
        select.assert_not_called()

    def test_stage2_runs_formal_and_local_before_deciding_third_batch(self):
        formal = self._template_candidates(16)
        local = [
            {**candidate, "template_id": f"probe.neighbor.{index}",
             "expression": f"rank(ts_mean(field_a, {index + 30}))",
             "expression_hash": f"local-{index}", "kind": "probe_neighbor"}
            for index, candidate in enumerate(self._template_candidates(8))
        ]
        all_candidates = [*formal[:8], *local, *formal[8:16]]
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}", "score": 0,
                "stats": {
                    "sharpe": 1.5, "fitness": 0.8, "sharpe_2y": 1.4,
                    "margin": 0.0007, "turnover": 0.2, "sc": 0.3,
                }, "url": "",
            }
            for index, candidate in enumerate(all_candidates)
        }
        optimizer = self._template_optimizer(results)
        optimizer.hill_stage = 2
        optimizer.stage_target_batches = 3
        optimizer.best_stats = {
            "sharpe": 1.5, "fitness": 0.8, "sharpe_2y": 1.4,
            "margin": 0.0007, "turnover": 0.2, "sc": 0.3,
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])
        with (
            patch.object(hill, "select_template_candidates", return_value=(formal, [])),
            patch.object(optimizer, "_probe_neighborhood_candidates", return_value=local),
        ):
            self.assertTrue(optimizer.run_template_exploration("source_a", parser))
        self.assertEqual(optimizer.evaluate_batch.call_count, 1)
        self.assertEqual(optimizer.current_position["template_batch"], 3)
        self.assertEqual(len(optimizer.current_position["stage_branches"]), 1)

    def test_full_cached_batch_is_reused_instead_of_becoming_pending(self):
        candidates = self._template_candidates(16)
        results = {
            candidate["expression"]: {
                "status": "CACHE_HIT", "alpha_id": f"cached{index}",
                "score": 0, "stats": {"passed": False}, "url": "cached",
            }
            for index, candidate in enumerate(candidates)
        }
        optimizer = self._template_optimizer(results)
        optimizer.stage_target_batches = 2
        optimizer.client.history = {
            hill._cache_key(candidate["expression"], optimizer.settings): result
            for candidate, result in zip(candidates, results.values())
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        self.assertEqual(optimizer.current_position["template_batch"], 2)
        self.assertEqual(optimizer.evaluate_batch.call_count, 0)
        self.assertEqual(optimizer.current_position.get("stage_post_batches_used", 0), 0)

    def test_pending_batch_members_are_not_misclassified_as_complete_cache(self):
        candidates = self._template_candidates(16)
        results = {
            candidate["expression"]: {
                "status": "CACHE_HIT", "alpha_id": f"cached{index}",
                "score": 0, "stats": {"passed": False}, "url": "cached",
            }
            for index, candidate in enumerate(candidates)
        }
        optimizer = self._template_optimizer(results)
        optimizer.client.history = {
            hill._cache_key(candidate["expression"], optimizer.settings): result
            for candidate, result in zip(candidates, results.values())
        }
        pending_expressions = [candidate["expression"] for candidate in candidates[:2]]
        optimizer.client.history["__pending_multi__"] = {
            "pending": {
                "settings": optimizer.settings,
                "expressions": pending_expressions,
                "status": "RESULTS_UNOBSERVED",
            }
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertFalse(complete)
        self.assertEqual(optimizer.template_pending_status, "RESULTS_UNOBSERVED")
        optimizer.evaluate_batch.assert_not_called()

    def test_continuous_pending_does_not_mark_stage_complete(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.stop_requested = False
        optimizer.template_retry_after = "2099-01-01T00:00:00+08:00"
        budget = Mock()
        budget.snapshot.side_effect = [
            {"used": 0, "remaining": 3000, "limit": 3000,
             "reset_at": "2099-01-01T12:00:00+08:00"},
            RuntimeError("stop"),
        ]
        optimizer._ensure_backtest_budget = Mock(return_value=budget)
        optimizer._scan_source_candidates = Mock(return_value=True)
        optimizer.optimize_single_alpha = Mock(return_value="PENDING")
        optimizer._source_stop_requested = Mock(return_value=False)
        state = hill._default_source_state()
        state["candidates"]["source_a"] = {
            "alpha_id": "source_a", "expression": "rank(field_a)",
            "status": "ELIGIBLE", "hill_stage": 1, "gap_scopes": [],
            "pool_status": "ACTIVE",
        }

        with (
            patch.object(hill, "ENABLE_SC_PYRAMID_AUTO_REFRESH", False),
            patch.object(hill, "ENABLE_PYRAMID_BACKFILL", False),
            patch.object(hill, "load_source_state", return_value=state),
            patch.object(hill, "load_processed_alphas", return_value={}),
            patch.object(hill, "import_legacy_processed", return_value=False),
            patch.object(hill, "save_source_state"),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "promote_completed_stages"),
            patch.object(hill, "setup_logging"),
            self.assertRaisesRegex(RuntimeError, "stop"),
        ):
            optimizer.run_continuous()

        record = state["candidates"]["source_a"]
        self.assertEqual(record["status"], "INTERRUPTED")
        self.assertIsNotNone(record["retry_after"])
        self.assertEqual(record["stage_batches_used"], 0)

    def test_interrupted_source_waits_until_retry_after(self):
        state = hill._default_source_state()
        state["candidates"]["source_a"] = {
            "alpha_id": "source_a", "expression": "rank(field_a)",
            "status": "INTERRUPTED", "pool_status": "ACTIVE",
            "retry_after": "2099-01-01T00:00:00+08:00",
        }

        self.assertIsNone(hill.select_next_source_record(state))

    def test_explicit_429_keeps_same_batch_and_does_not_reserve_twice(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.client.history = {}
        optimizer.settings = {"region": "GBR", "universe": "TOP3000", "delay": 1}
        optimizer.stop_requested = False
        budget = Mock()
        budget.reserve.return_value = {
            "used": 8, "remaining": 2992, "limit": 3000,
            "reset_at": "2026-08-26T12:00:00+08:00",
        }
        optimizer._ensure_backtest_budget = Mock(return_value=budget)
        expressions = [f"rank(ts_delay(field_a, {index + 1}))" for index in range(8)]

        with (
            patch.object(
                hill, "batch_verify_expressions",
                return_value=[{"valid": True} for _ in expressions],
            ),
            patch.object(
                hill, "post_multi_simulation",
                return_value={
                    "location": None, "status_code": 429,
                    "retry_after": None, "response_observed": True,
                },
            ) as post_mock,
        ):
            first = optimizer.evaluate_batch(expressions)
            second = optimizer.evaluate_batch(expressions)

        self.assertEqual({item["status"] for item in first.values()}, {"PENDING"})
        self.assertEqual({item["status"] for item in second.values()}, {"PENDING"})
        self.assertEqual(post_mock.call_count, 1)
        budget.reserve.assert_called_once_with(8)
        pending = next(iter(optimizer.client.history["__pending_multi__"].values()))
        self.assertEqual(pending["status"], "PENDING_RATE_LIMIT")
        self.assertTrue(pending["budget_reserved"])

    def test_429_allows_three_posts_total_then_becomes_unobserved(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.client.history = {}
        optimizer.settings = {"region": "GBR", "universe": "TOP3000", "delay": 1}
        optimizer.stop_requested = False
        budget = Mock()
        budget.reserve.return_value = {
            "used": 8, "remaining": 2992, "limit": 3000,
            "reset_at": "2026-08-26T12:00:00+08:00",
        }
        optimizer._ensure_backtest_budget = Mock(return_value=budget)
        expressions = [f"rank(ts_delay(field_a, {index + 1}))" for index in range(8)]
        with (
            patch.object(hill, "batch_verify_expressions",
                         return_value=[{"valid": True} for _ in expressions]),
            patch.object(hill, "post_multi_simulation",
                         return_value={"location": None, "status_code": 429}) as post_mock,
        ):
            optimizer.evaluate_batch(expressions)
            pending = next(iter(optimizer.client.history["__pending_multi__"].values()))
            pending["retry_after"] = "2020-01-01T00:00:00+08:00"
            second = optimizer.evaluate_batch(expressions)
            pending = next(iter(optimizer.client.history["__pending_multi__"].values()))
            pending["retry_after"] = "2020-01-01T00:00:00+08:00"
            third = optimizer.evaluate_batch(expressions)
            fourth = optimizer.evaluate_batch(expressions)

        self.assertEqual(post_mock.call_count, 3)
        budget.reserve.assert_called_once_with(8)
        self.assertEqual({item["status"] for item in second.values()}, {"PENDING"})
        self.assertEqual({item["status"] for item in third.values()}, {"RESULTS_UNOBSERVED"})
        self.assertEqual({item["status"] for item in fourth.values()}, {"RESULTS_UNOBSERVED"})
        pending = next(iter(optimizer.client.history["__pending_multi__"].values()))
        self.assertEqual(pending["retry_count"], 2)
        self.assertEqual(pending["retry_kind"], "RATE_LIMIT_EXHAUSTED")

    def test_secondary_validation_backfills_seven_of_eight_from_ninth_candidate(self):
        candidates = self._template_candidates(9)
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}",
                "score": 1.0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates[1:])
        }
        optimizer = self._template_optimizer(results)
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])
        checks = [{"valid": False, "errors": ["bad"]}] + [
            {"valid": True} for _ in range(8)
        ]
        with (
            patch.object(hill, "select_template_candidates", return_value=(candidates, [])),
            patch.object(hill, "batch_verify_expressions", return_value=checks),
        ):
            self.assertTrue(optimizer.run_template_exploration("source_a", parser))
        submitted = optimizer.evaluate_batch.call_args.args[0]
        self.assertEqual(submitted, [item["expression"] for item in candidates[1:]])

    def test_missing_initial_score_returns_pending_without_format_exception(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock()
        optimizer.client.get_alpha_details.return_value = {
            "id": "source", "settings": {"region": "USA", "universe": "TOP3000", "delay": 1},
            "regular": {"code": "rank(field_a)"},
            "is": {"sharpe": 1.3, "fitness": 1.0, "margin": 0.001,
                   "turnover": 0.2, "checks": []},
            "train": {},
        }
        optimizer.score_lock = hill.threading.Lock()
        optimizer.hill_stage = 1
        optimizer.current_position = {"template_batch": 0}
        optimizer.score_version = hill.STAGE_SCORE_VERSION
        optimizer.source_record = {"sc_value": 0.2}
        optimizer.stop_requested = False
        optimizer.stage_target_batches = 2
        optimizer.template_pending_status = "PENDING_STAGE_SCORE"
        with (
            patch.object(optimizer, "load_checkpoint", return_value=False),
            patch.object(optimizer, "save_checkpoint"),
            patch.object(hill, "SmartExpression", return_value=Mock()) as parser_mock,
            patch.object(optimizer, "run_template_exploration", return_value=False) as probe_mock,
        ):
            self.assertEqual(optimizer.optimize_single_alpha("source"), "PENDING_STAGE_SCORE")
        parser_mock.assert_called_once()
        probe_mock.assert_called_once()
        self.assertIsNone(optimizer.best_score)

    def test_missing_p2y_first_probe_is_source_plus_seven_neighbors(self):
        source_expression = "rank(ts_mean(field_a, 22))"
        neighbors = [
            f"rank(ts_mean(field_a, {window}))"
            for window in (20, 24, 18, 26, 15, 30, 10)
        ]
        expressions = [source_expression, *neighbors]
        complete_stats = {
            "sharpe": 1.3, "fitness": 0.6, "margin": 0.0004,
            "sharpe_2y": 1.1, "turnover": 0.2, "sc": 0.2,
            "passed": False,
        }
        results = {
            expression: {
                "status": "COMPLETE", "alpha_id": f"alpha-{index}",
                "score": None, "stats": dict(complete_stats), "url": "",
            }
            for index, expression in enumerate(expressions)
        }
        optimizer = self._template_optimizer(results)
        optimizer.client.get_available_operators.return_value = {"rank", "ts_mean"}
        optimizer.best_expr = source_expression
        optimizer.source_expression = source_expression
        optimizer.initial_score = None
        optimizer.best_score = None
        optimizer.best_base_score = None
        optimizer.best_alpha_id = "source"
        optimizer.initial_alpha_id = "source"
        optimizer.score_lock = hill.threading.Lock()
        optimizer.baseline_refresh_status = "REQUIRED"
        parser = Mock(tokens=[
            {"type": "operator", "text": "rank"},
            {"type": "operator", "text": "ts_mean"},
            {"type": "data_field", "text": "field_a"},
            {"type": "number", "text": "22"},
        ])
        parser.generate_neighbors.side_effect = lambda kind, position: (
            neighbors if kind == "time_window" and position == 0 else []
        )
        with (
            patch.object(hill, "select_template_candidates", return_value=([], [])),
            patch.object(
                hill, "batch_verify_expressions",
                side_effect=lambda items: [{"valid": True} for _ in items],
            ),
        ):
            self.assertTrue(optimizer.run_template_exploration("source", parser))

        submitted = optimizer.evaluate_batch.call_args.args[0]
        self.assertEqual(submitted, expressions)
        self.assertEqual(
            optimizer.evaluate_batch.call_args.kwargs["force_run"], [source_expression]
        )
        self.assertEqual(optimizer.baseline_refresh_status, "COMPLETE")
        self.assertEqual(optimizer.baseline_alpha_id, "alpha-0")
        self.assertIsNotNone(optimizer.initial_score)

    def test_complete_p2y_baseline_cache_is_reused_and_eight_neighbors_run(self):
        source_expression = "rank(ts_mean(field_a, 22))"
        neighbors = [f"rank(ts_mean(field_a, {window}))" for window in range(30, 38)]
        complete_stats = {
            "sharpe": 1.3, "fitness": 0.6, "margin": 0.0004,
            "sharpe_2y": 1.1, "turnover": 0.2, "sc": 0.2, "passed": False,
        }
        neighbor_results = {
            expression: {
                "status": "COMPLETE", "alpha_id": f"neighbor-{index}",
                "score": 1.0, "stats": dict(complete_stats), "url": "",
            }
            for index, expression in enumerate(neighbors)
        }
        optimizer = self._template_optimizer(neighbor_results)
        optimizer.client.get_available_operators.return_value = {"rank", "ts_mean"}
        optimizer.best_expr = optimizer.source_expression = source_expression
        optimizer.initial_score = optimizer.best_score = None
        optimizer.best_base_score = None
        optimizer.best_alpha_id = optimizer.initial_alpha_id = "source"
        optimizer.score_lock = hill.threading.Lock()
        optimizer.client.history = {
            hill._cache_key(source_expression, optimizer.settings): {
                "status": "COMPLETE", "alpha_id": "baseline-cached", "score": 1.0,
                "stats": dict(complete_stats), "url": "cached",
            }
        }
        parser = Mock(tokens=[
            {"type": "operator", "text": "rank"},
            {"type": "operator", "text": "ts_mean"},
            {"type": "data_field", "text": "field_a"},
            {"type": "number", "text": "22"},
        ])
        parser.generate_neighbors.side_effect = lambda kind, position: (
            neighbors if kind == "time_window" and position == 0 else []
        )
        with (
            patch.object(hill, "select_template_candidates", return_value=([], [])),
            patch.object(
                hill, "batch_verify_expressions",
                side_effect=lambda items: [{"valid": True} for _ in items],
            ),
        ):
            self.assertTrue(optimizer.run_template_exploration("source", parser))
        optimizer.evaluate_batch.assert_not_called()
        self.assertEqual(optimizer.baseline_alpha_id, "baseline-cached")
        self.assertEqual(len(optimizer.current_position["stage_branches"]), 1)

    def test_rate_limited_baseline_refresh_keeps_rate_limit_status(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.current_position = {}
        optimizer.template_retry_after = "2099-01-01T00:00:00+08:00"
        self.assertFalse(optimizer._set_refreshed_baseline({"status": "PENDING"}))
        self.assertEqual(optimizer.baseline_refresh_status, "PENDING_RATE_LIMIT")
        self.assertEqual(
            optimizer.current_position["baseline_refresh_status"],
            "PENDING_RATE_LIMIT",
        )

    def test_stage_one_deficit_improvement_threshold_is_point_zero_five(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 1
        baseline = {
            "sharpe": 1.0, "fitness": 0.6, "margin": 0.0004,
            "sharpe_2y": 1.1, "turnover": 0.2, "sc": 0.2,
        }
        optimizer.template_baseline_stats = dict(baseline)
        optimizer.template_baseline_gate = optimizer._assess_stats(baseline)["gate"]
        self.assertFalse(optimizer._gate_progress_improved(dict(baseline, sharpe=1.05)))
        self.assertTrue(optimizer._gate_progress_improved(dict(baseline, sharpe=1.07)))
        self.assertTrue(optimizer._gate_progress_improved(dict(baseline, sharpe=1.21)))

    def test_stage_one_can_expand_to_four_batches_after_valid_improvement(self):
        formal = self._template_candidates(24)
        local = [
            {**candidate, "template_id": f"probe.neighbor.{index}",
             "expression": f"rank(ts_mean(field_a, {index + 40}))",
             "expression_hash": f"local-{index}", "kind": "probe_neighbor"}
            for index, candidate in enumerate(self._template_candidates(8))
        ]
        results = {
            item["expression"]: {
                "status": "COMPLETE", "alpha_id": f"child-{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, item in enumerate([*local, *formal])
        }
        optimizer = self._template_optimizer(results)
        optimizer.stage_target_batches = 4
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])
        with (
            patch.object(hill, "select_template_candidates", return_value=(formal, [])),
            patch.object(optimizer, "_probe_neighborhood_candidates", return_value=local),
            patch.object(optimizer, "_gate_progress_improved", return_value=True),
            patch.object(optimizer, "_retains_previous_gates", return_value=True),
        ):
            self.assertTrue(optimizer.run_template_exploration("source_a", parser))
        self.assertEqual(optimizer.evaluate_batch.call_count, 4)
        self.assertEqual(optimizer.current_position["stage_post_batches_used"], 4)

    def test_missing_baseline_target_metric_cannot_promote_template(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.hill_stage = 2
        baseline = {
            "sharpe": 1.5, "fitness": 0.8, "margin": 0.0007,
            "sharpe_2y": 1.4, "turnover": 0.2, "sc": None,
        }
        optimizer.template_baseline_stats = dict(baseline)
        optimizer.template_baseline_gate = optimizer._assess_stats(baseline)["gate"]
        result = dict(baseline, sharpe=1.2, sharpe_2y=1.2, sc=0.2)
        candidate = {"target_metrics": ("sharpe_2y", "turnover", "sc")}
        self.assertFalse(optimizer._gate_progress_improved(result, candidate))

    def test_factory_prefilter_reuses_local_target_pnl_without_redownload(self):
        context = hill.OptimizerContext.__new__(hill.OptimizerContext)
        response = Mock(status_code=404, text="")
        context.core_client = Mock()
        context.core_client.get.return_value = response
        cached = pd.DataFrame({"alpha_a": [0.0, 1.0, 2.0]})
        with (
            patch.object(hill, "load_target_pnl_cache", return_value=cached),
            patch.object(hill.time, "sleep"),
        ):
            self.assertFalse(context.check_factory_shape("alpha_a"))
        requested = [call.args[0] for call in context.core_client.get.call_args_list]
        self.assertTrue(requested)
        self.assertFalse(any(url.endswith("/recordsets/pnl") for url in requested))

    def test_single_instance_lock_rejects_second_process_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "instance.lock"
            first = hill.SingleInstanceLock(path)
            second = hill.SingleInstanceLock(path)
            try:
                self.assertTrue(first.acquire())
                self.assertFalse(second.acquire())
            finally:
                second.release()
                first.release()

    def test_stale_submitted_batch_is_never_reposted(self):
        self.assertEqual(hill.MULTI_SUBMITTED_REPOST_AFTER_SECONDS, 20 * 60)
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.settings = {"region": "GBR", "universe": "TOP3000", "delay": 1}
        optimizer.stop_requested = False
        expressions = [f"rank(ts_delay(field_a, {index + 1}))" for index in range(8)]
        batch_key = hill._multi_batch_key(expressions, optimizer.settings)
        optimizer.client.history = {
            "__pending_multi__": {
                batch_key: {
                    "status": "SUBMITTED", "location": "expired-parent-url",
                    "expressions": expressions, "settings": optimizer.settings,
                    "created_at": "2020-01-01T00:00:00", "budget_reserved": True,
                }
            }
        }
        budget = Mock()
        budget.reserve.return_value = {
            "used": 8, "remaining": 2992, "limit": 3000,
            "reset_at": "2026-08-27T12:00:00+08:00",
        }
        optimizer._ensure_backtest_budget = Mock(return_value=budget)

        with (
            patch.object(
                hill, "batch_verify_expressions",
                return_value=[{"valid": True} for _ in expressions],
            ),
            patch.object(
                hill, "post_multi_simulation",
                return_value={"location": "new-parent-url", "status_code": 201},
            ) as post_mock,
            patch.object(
                hill, "poll_simulation_progress",
                return_value={"status": "RUNNING", "children": []},
            ) as poll_mock,
        ):
            results = optimizer.evaluate_batch(expressions)

        self.assertEqual({item["status"] for item in results.values()}, {"RESULTS_UNOBSERVED"})
        post_mock.assert_not_called()
        budget.reserve.assert_not_called()
        poll_mock.assert_not_called()
        pending = optimizer.client.history["__pending_multi__"][batch_key]
        self.assertEqual(pending["location"], "expired-parent-url")
        self.assertEqual(pending["status"], "RESULTS_UNOBSERVED")
        self.assertEqual(pending["retry_kind"], "STALE_LOCATION")

    def test_parent_error_records_child_status_and_does_not_repost_same_batch(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.client.history = {}
        optimizer.settings = {"region": "GBR", "universe": "TOP700", "delay": 1}
        optimizer.stop_requested = False
        budget = Mock()
        budget.reserve.return_value = {
            "used": 8, "remaining": 2992, "limit": 3000,
            "reset_at": "2026-08-26T12:00:00+08:00",
        }
        optimizer._ensure_backtest_budget = Mock(return_value=budget)
        expressions = [f"rank(ts_delay(field_a, {index + 1}))" for index in range(8)]
        parent = {"status": "ERROR", "children": [f"child{index}" for index in range(8)]}
        children = [{
            "status": "ERROR",
            "message": 'Incompatible unit for input of "densify"',
        }] + [{"status": "CANCELLED"} for _ in range(7)]

        with (
            patch.object(
                hill, "batch_verify_expressions",
                return_value=[{"valid": True} for _ in expressions] * 2,
            ),
            patch.object(
                hill, "post_multi_simulation",
                return_value={"location": "parent-url", "status_code": 201},
            ) as post_mock,
            patch.object(
                hill, "poll_simulation_progress", side_effect=[parent, *children],
            ) as poll_mock,
        ):
            first = optimizer.evaluate_batch(expressions)
            second = optimizer.evaluate_batch(expressions)

        self.assertEqual(first[expressions[0]]["status"], "FAILED")
        self.assertTrue(first[expressions[0]]["negative_cache"])
        self.assertIn("Incompatible unit", first[expressions[0]]["failure_reason"])
        self.assertEqual(
            [first[expr]["status"] for expr in expressions[1:]],
            ["CANCELLED"] * 7,
        )
        self.assertEqual(second[expressions[0]]["status"], "FAILED")
        self.assertEqual(
            {second[expr]["status"] for expr in expressions[1:]},
            {"DEFERRED_INCOMPLETE_BATCH"},
        )
        self.assertEqual(post_mock.call_count, 1)
        self.assertEqual(poll_mock.call_count, 9)
        self.assertEqual(optimizer.client.history["__pending_multi__"], {})

    def test_template_selection_skips_negative_cache_before_slicing_batches(self):
        candidates = self._template_candidates(9)
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates[1:])
        }
        optimizer = self._template_optimizer(results)
        optimizer.client.history = {
            hill._cache_key(candidates[0]["expression"], optimizer.settings): {
                "status": "FAILED", "negative_cache": True,
            },
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        submitted = optimizer.evaluate_batch.call_args.args[0]
        self.assertEqual(len(submitted), 8)
        self.assertNotIn(candidates[0]["expression"], submitted)

    def test_template_selection_replaces_complete_cache_before_new_batch(self):
        candidates = self._template_candidates(10)
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(candidates[2:])
        }
        optimizer = self._template_optimizer(results)
        optimizer.client.history = {
            hill._cache_key(candidate["expression"], optimizer.settings): {
                "status": "COMPLETE", "alpha_id": f"cached{index}",
                "score": 0, "stats": {"passed": False}, "url": "cached",
            }
            for index, candidate in enumerate(candidates[:2])
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        submitted = optimizer.evaluate_batch.call_args.args[0]
        self.assertEqual(len(submitted), 8)
        self.assertFalse(set(submitted) & {
            candidate["expression"] for candidate in candidates[:2]
        })

    def test_restart_after_cached_first_batch_runs_second_batch(self):
        candidates = self._template_candidates(16)
        second_batch = candidates[8:]
        results = {
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"alpha{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(second_batch)
        }
        optimizer = self._template_optimizer(results)
        optimizer.current_position["template_batch"] = 1
        optimizer.stage_target_batches = 2
        optimizer.client.history = {
            hill._cache_key(candidate["expression"], optimizer.settings): {
                "status": "COMPLETE", "alpha_id": f"cached{index}",
                "score": 0, "stats": {"passed": False}, "url": "cached",
            }
            for index, candidate in enumerate(candidates[:8])
        }
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(candidates, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        optimizer.evaluate_batch.assert_called_once()
        submitted = optimizer.evaluate_batch.call_args.args[0]
        self.assertEqual(len(submitted), 8)
        self.assertEqual(set(submitted), {
            candidate["expression"] for candidate in second_batch
        })
        self.assertEqual(optimizer.current_position["template_batch"], 2)

    def test_complete_cache_does_not_consume_artificial_eighth_post(self):
        bases = self._template_candidates(8)
        optimizer = self._template_optimizer({})
        optimizer.current_position["template_batch"] = 7
        optimizer.stage_target_batches = 8
        adaptive_ops = {
            "rank", "reverse", "ts_decay_linear", "group_rank", "zscore",
            "signed_power", "ts_mean", "ts_delta", "ts_delay",
        }
        optimizer.client.get_available_operators.return_value = adaptive_ops
        optimizer.client.history = {
            hill._cache_key(candidate["expression"], optimizer.settings): {
                "status": "COMPLETE", "alpha_id": f"cached{index}",
                "score": 100 - index, "stats": {"passed": False}, "url": "cached",
            }
            for index, candidate in enumerate(bases)
        }
        completed = {
            candidate["expression"]: optimizer.client.history[
                hill._cache_key(candidate["expression"], optimizer.settings)
            ]
            for candidate in bases
        }
        pool = optimizer._adaptive_template_candidates(
            completed, adaptive_ops,
            [{"id": "field_a", "type": "MATRIX", "dataset_id": "dataset_a"}],
        )
        self.assertGreaterEqual(len(pool), 9)
        optimizer.client.history[
            hill._cache_key(pool[0]["expression"], optimizer.settings)
        ] = {"status": "FAILED", "negative_cache": True}
        expected = pool[1:9]
        optimizer.evaluate_batch = Mock(return_value={
            candidate["expression"]: {
                "status": "COMPLETE", "alpha_id": f"adaptive{index}",
                "score": 0, "stats": {"passed": False}, "url": "",
            }
            for index, candidate in enumerate(expected)
        })
        parser = Mock(tokens=[{"type": "data_field", "text": "field_a"}])

        with patch.object(hill, "select_template_candidates", return_value=(bases, [])):
            complete = optimizer.run_template_exploration("source_a", parser)

        self.assertTrue(complete)
        optimizer.evaluate_batch.assert_not_called()
        self.assertEqual(optimizer.current_position.get("stage_post_batches_used", 0), 0)
        self.assertEqual(optimizer.current_position["template_batch"], 8)

    def test_pending_core_refresh_pauses_source_selection(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock(stop_requested=False)
        optimizer.stop_requested = False
        optimizer.backtest_budget = Mock()
        optimizer.backtest_budget.snapshot.return_value = {
            "used": 0, "remaining": 3000, "limit": 3000,
            "reset_at": "2026-08-25T12:00:00+08:00",
        }
        pending = {
            "status": "PENDING", "sc_status": "PENDING",
            "pyramid_status": "REFRESHED", "cached_os_count": 12,
            "observed_new_os_alpha_ids": [], "cached_new_os_alpha_ids": [],
            "failed_pnl_alpha_ids": [], "next_due_at": None,
            "retry_after": None, "reason": "OS列表不可观察",
        }
        with (
            patch.object(hill, "load_source_state", return_value=hill._default_source_state()),
            patch.object(hill, "save_source_state"),
            patch.object(hill, "import_legacy_processed", return_value=False),
            patch.object(hill, "load_processed_alphas", return_value={}),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "refresh_sc_pyramid_bundle", return_value=pending),
            patch.object(hill, "select_next_source_record") as select_mock,
            patch.object(optimizer, "_wait_source_idle", side_effect=RuntimeError("stop")) as wait_mock,
            self.assertRaisesRegex(RuntimeError, "stop"),
        ):
            optimizer.run_continuous()

        wait_mock.assert_called_once()
        select_mock.assert_not_called()

    def test_state_save_uses_sqlite_and_keeps_legacy_json_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_text('{"legacy": true}\n', encoding="utf-8")
            state = hill._default_source_state()
            state['candidates']['a'] = {
                'alpha_id': 'a', 'status': 'ELIGIBLE', 'sharpe': 1.3, 'fitness': 0.6,
                'admission_profile': hill.SOURCE_ADMISSION_PROFILE,
            }
            hill.save_source_state(state, state_path)

            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), {'legacy': True})
            restored = hill.load_source_state(Path(directory) / 'source_state_v6.sqlite3')
            self.assertEqual(restored['candidates']['a']['status'], 'ELIGIBLE')

    def test_state_save_updates_only_dirty_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = hill.load_source_state(state_path)
            state['candidates']['a'] = {
                'alpha_id': 'a', 'status': 'ELIGIBLE', 'sharpe': 1.3, 'fitness': 0.6,
                'admission_profile': hill.SOURCE_ADMISSION_PROFILE,
            }
            state['candidates']['b'] = {
                'alpha_id': 'b', 'status': 'ELIGIBLE', 'sharpe': 1.3, 'fitness': 0.6,
                'admission_profile': hill.SOURCE_ADMISSION_PROFILE,
            }
            hill.save_source_state(state, state_path)
            state['candidates']['a']['status'] = 'INTERRUPTED'
            hill.save_source_state(state, state_path)

            restored = hill.load_source_state(state_path)
            self.assertEqual(restored['candidates']['a']['status'], 'INTERRUPTED')
            self.assertEqual(restored['candidates']['b']['status'], 'ELIGIBLE')

    def test_old_stage_complete_is_reclassified_by_metrics_not_batch_count(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = hill._default_source_state()
            state["candidates"]["old"] = {
                "alpha_id": "old", "status": "STAGE2_COMPLETE", "hill_stage": 2,
                "pool_status": "ACTIVE", "sharpe": 1.3, "fitness": 0.6,
                "admission_profile": hill.SOURCE_ADMISSION_PROFILE,
                "objective_version": "old-batch-accounting",
                "score_version": hill.STAGE_SCORE_VERSION,
                "stage_batches_used": 99,
                "best_stats": {
                    "sharpe": 1.3, "fitness": 0.6, "sharpe_2y": 1.1,
                    "margin": 0.0004, "turnover": 0.2, "sc": 0.3,
                },
            }
            hill.save_source_state(state, state_path)
            restored = hill.load_source_state(state_path)["candidates"]["old"]
            self.assertEqual(restored["status"], "INTERRUPTED")
            self.assertEqual(restored["hill_stage"], 2)
            self.assertEqual(restored["stage_post_batches_used"], 0)

    def test_empty_pnl_body_has_specific_exception_after_three_attempts(self):
        client = Mock()
        client.get.return_value = EmptyResponse()

        with patch.object(sc_engine.time, "sleep") as sleep_mock:
            with self.assertRaises(sc_engine.PnlUnavailableError):
                sc_engine._get_alpha_pnl(client, "alpha-empty")

        self.assertEqual(client.get.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 3)

    def test_validator_exposes_pnl_unavailable_instead_of_generic_error(self):
        with (
            patch.object(validator, "_ensure_sc_cache"),
            patch.object(validator, "_sc_rets", pd.DataFrame({"peer": [0.1]})),
            patch.object(validator, "_sc_ids", {"EUR": ["peer"]}),
            patch.object(
                validator, "calc_self_corr",
                side_effect=sc_engine.PnlUnavailableError("empty"),
            ),
        ):
            result = validator.get_sc_check(Mock(), "alpha-empty")

        self.assertEqual(result, "pnl_unavailable")

    def test_actual_empty_pnl_is_skipped_and_three_failures_open_circuit(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.client = Mock()
        state = hill._default_source_state()
        coverage = {
            "status": "HAS_GAP", "scopes": [],
            "gap_scopes": [{"raw_scope": "EUR/D1/MODEL"}], "reason": "gap",
        }

        def alpha(alpha_id):
            return {
                "id": alpha_id, "regular": "rank(model_field)",
                "dateCreated": "2026-07-30T00:02:06-04:00",
                "settings": {"region": "EUR", "delay": 1},
                "is": {"sharpe": 1.5, "fitness": 0.8, "margin": 0.0008, "turnover": 0.2},
                "train": {"sharpe": 1.5},
            }

        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "get_alpha_pyramid_pass_info", return_value={"status": "PASS"}),
            patch.object(hill, "evaluate_pyramid_coverage", return_value=coverage),
            patch.object(hill, "current_sc_cache_token", return_value="cache-1"),
            patch.object(hill, "get_sc_check", return_value="pnl_unavailable") as sc_mock,
        ):
            first_three = [
                optimizer._screen_source_alpha(alpha(f"a{index}"), state, {}, "d", "f")
                for index in range(3)
            ]
            deferred = optimizer._screen_source_alpha(alpha("a4"), state, {}, "d", "f")

        self.assertEqual([item["status"] for item in first_three], [
            "SKIPPED_PNL_UNAVAILABLE", "SKIPPED_PNL_UNAVAILABLE",
            "SKIPPED_PNL_UNAVAILABLE",
        ])
        self.assertEqual(deferred["status"], "PENDING_SC")
        self.assertEqual(deferred["sc_status"], "deferred_platform_pnl")
        self.assertEqual(sc_mock.call_count, 3)


if __name__ == "__main__":
    unittest.main()
