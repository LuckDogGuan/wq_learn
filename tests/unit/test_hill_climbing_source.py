import importlib.util
import io
import json
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).parents[1] / "代码" / "优化代码" / "爬山代码" / "hill_climbing" / "optimizer.py"
SPEC = importlib.util.spec_from_file_location("hill_climbing_source", SCRIPT)
hill = importlib.util.module_from_spec(SPEC)
with redirect_stdout(io.StringIO()):
    SPEC.loader.exec_module(hill)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 8, 25, 12, 0, 0)
        return value if tz is None else value.replace(tzinfo=tz)


class SourceSelectionTest(unittest.TestCase):
    def setUp(self):
        self.runtime_dir = tempfile.TemporaryDirectory()
        runtime_path = Path(self.runtime_dir.name)
        self.runtime_patches = (
            patch.object(
                hill,
                "HILL_CLIMBING_SOURCE_STATE_PATH",
                runtime_path / "state.json",
            ),
            patch.object(
                hill,
                "HILL_CLIMBING_SOURCE_EVENTS_PATH",
                runtime_path / "events.jsonl",
            ),
            patch.object(
                hill,
                "HILL_CLIMBING_SOURCE_DB_PATH",
                runtime_path / "source_state_v6.sqlite3",
            ),
        )
        for runtime_patch in self.runtime_patches:
            runtime_patch.start()

    def tearDown(self):
        for runtime_patch in reversed(self.runtime_patches):
            runtime_patch.stop()
        self.runtime_dir.cleanup()

    def make_optimizer(self):
        optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        optimizer.stop_requested = False
        optimizer.client = Mock(stop_requested=False)
        return optimizer

    def test_ctrl_c_uses_immediate_process_exit(self):
        client = hill.OptimizerContext.__new__(hill.OptimizerContext)
        with patch.object(hill.os, "_exit", side_effect=SystemExit(130)) as exit_mock:
            with self.assertRaisesRegex(SystemExit, "130"):
                client._signal_handler(None, None)
        exit_mock.assert_called_once_with(130)

    def test_resume_mode_initializes_console_logging(self):
        fake_client = Mock()
        with (
            patch.object(hill, "RUN_MODE", 2),
            patch.object(hill, "OptimizerContext", return_value=fake_client),
            patch.object(hill, "setup_logging") as setup_mock,
            patch.object(hill.signal, "signal"),
            redirect_stdout(io.StringIO()),
        ):
            hill.AsyncOptimizer()

        setup_mock.assert_called_once_with(None)

    def test_sqlite_state_and_legacy_import_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = hill.load_source_state(path)
            changed = hill.import_legacy_processed(
                state, {"old": {"expr": "rank(close)", "timestamp": "2026-08-20"}}
            )
            hill.save_source_state(state, path)
            restored = hill.load_source_state(path)

            self.assertTrue(changed)
            self.assertEqual(restored["candidates"]["old"]["status"], "OPTIMIZED")
            self.assertFalse(hill.import_legacy_processed(restored, {}))
            self.assertTrue((path.parent / 'source_state_v6.sqlite3').exists())

    def test_stale_optimizing_record_is_recovered_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(
                '{"schema_version":1,"candidates":{"a":{"status":"OPTIMIZING"}}}',
                encoding="utf-8",
            )
            restored = hill.load_source_state(path)
            self.assertEqual(restored["candidates"]["a"]["status"], "INTERRUPTED")
            self.assertIn("recovered_at", restored["candidates"]["a"])

    def test_legacy_stage_score_is_not_ranked_as_stage_v2(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(
                '{"candidates":{"a":{"status":"STAGE1_COMPLETE",'
                '"hill_stage":1,"stage_score":999}}}', encoding="utf-8",
            )
            record = hill.load_source_state(path)["candidates"]["a"]
        self.assertEqual(record["status"], "INTERRUPTED")
        self.assertEqual(record["hill_stage"], 1)
        self.assertEqual(record["previous_stage_status"], "STAGE1_COMPLETE")
        self.assertIn(record["status"], hill.SOURCE_QUEUE_STATUSES)
        self.assertNotIn(record["status"], hill.SOURCE_RETRYABLE_STATUSES)

    def test_failed_and_bug_blocked_records_are_not_requeued(self):
        state = hill._default_source_state()
        for status in ("FAILED", "BUG_BLOCKED"):
            state["candidates"][status] = {
                "alpha_id": status, "expression": "rank(close)",
                "status": status, "pool_status": "ACTIVE",
            }
        self.assertIsNone(hill.select_next_source_record(state))

    def test_incomplete_batch_waits_for_candidate_pool_fingerprint_change(self):
        state = hill._default_source_state()
        record = {
            "alpha_id": "blocked", "expression": "rank(close)",
            "status": "BLOCKED_INCOMPLETE_BATCH", "pool_status": "ACTIVE",
            "candidate_pool_fingerprint": "same",
            "blocked_candidate_pool_fingerprint": "same",
        }
        state["candidates"]["blocked"] = record
        self.assertIsNone(hill.select_next_source_record(state))
        record["candidate_pool_fingerprint"] = "changed"
        self.assertEqual(hill.select_next_source_record(state)["alpha_id"], "blocked")

    def test_complete_legacy_metrics_are_invalidated_for_test_p2y_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps({"candidates": {"a": {
                "status": "STAGE1_COMPLETE", "hill_stage": 1, "stage_score": 999,
                "best_stats": {
                    "sharpe": 1.8, "fitness": 1.0, "margin": 0.001,
                    "sharpe_2y": 1.7, "turnover": 0.2, "sc": 0.2,
                },
            }}}), encoding="utf-8")
            record = hill.load_source_state(path)["candidates"]["a"]
        self.assertEqual(record["status"], "INTERRUPTED")
        self.assertEqual(record["score_version"], hill.STAGE_SCORE_VERSION)
        self.assertIsNone(record["stage_score"])
        self.assertIsNone(record["best_stats"]["sharpe_2y"])

    def test_original_forbidden_operators_do_not_reject_source_scope(self):
        record = {
            'field_ids': ['field_a'],
            'field_metadata': {'field_a': {'dataset_id': 'demo', 'type': 'MATRIX'}},
            'expression': 'trade_when(field_a > 0, add(rank(field_a), 1), -1)',
        }
        self.assertEqual(hill.source_scope_reason(record), '')

    def test_sqlite_claim_is_atomic_and_due_batch_has_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            state = hill.load_source_state(path)
            for alpha_id in ('ordinary', 'retry'):
                state['candidates'][alpha_id] = {
                    'alpha_id': alpha_id, 'status': 'ELIGIBLE',
                    'pool_status': 'ACTIVE', 'expression': f'rank({alpha_id})',
                    'sharpe': 1.3, 'fitness': 0.6,
                    'admission_profile': hill.SOURCE_ADMISSION_PROFILE,
                }
            hill.save_source_state(state, path)
            state._store.save_batch('batch-retry', {
                'source_alpha_id': 'retry', 'stage': 2,
                'status': 'PENDING_RATE_LIMIT',
                'retry_after': '2000-01-01T00:00:00+00:00',
            })
            stale_first = hill.load_source_state(path)
            stale_second = hill.load_source_state(path)
            first = hill.claim_next_source_record(stale_first)
            self.assertEqual(first['alpha_id'], 'retry')
            self.assertEqual(first['_due_batch']['status'], 'PENDING_RATE_LIMIT')
            self.assertEqual(first['_due_batch']['source_alpha_id'], 'retry')
            second = hill.claim_next_source_record(stale_second)
            self.assertEqual(second['alpha_id'], 'ordinary')
            self.assertIsNone(hill.claim_next_source_record(hill.load_source_state(path)))

    def test_source_metric_thresholds_are_strict_and_skip_remote_checks(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        alpha = {
            "id": "a1", "regular": "rank(close)", "dateCreated": "2026-08-23T01:00:00Z",
            "settings": {"region": "USA", "delay": 1},
            "is": {"sharpe": 1.0, "fitness": 0.5},
        }
        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "get_alpha_pyramid_pass_info") as pyramid_mock,
            patch.object(hill, "get_sc_check") as sc_mock,
        ):
            record = optimizer._screen_source_alpha(alpha, state, {"alphas": []}, "d", "f")

        self.assertEqual(record["status"], "METRIC_REJECTED")
        pyramid_mock.assert_not_called()
        sc_mock.assert_not_called()

    def test_all_pass_skips_sc_and_partial_gap_checks_sc(self):
        optimizer = self.make_optimizer()
        alpha = {
            "id": "a1", "regular": "rank(close)", "dateCreated": "2026-08-23T01:00:00Z",
            "settings": {"region": "GBR", "delay": 1},
            "is": {"sharpe": 1.6, "fitness": 0.9, "margin": 0.0008, "turnover": 0.2},
            "train": {"sharpe": 1.6},
        }
        diversity = {"alphas": []}
        with patch.object(hill, "append_source_event"):
            with (
                patch.object(hill, "get_alpha_pyramid_pass_info", return_value={"status": "PASS", "categories": ["GBR/D1/MODEL"]}),
                patch.object(hill, "evaluate_pyramid_coverage", return_value={"status": "ALL_PASS", "scopes": [], "gap_scopes": [], "reason": "pass"}),
                patch.object(hill, "get_sc_check") as sc_mock,
            ):
                record = optimizer._screen_source_alpha(alpha, hill._default_source_state(), diversity, "d", "f")
                self.assertEqual(record["status"], "SKIPPED_ALL_TOWERS_PASS")
                sc_mock.assert_not_called()

            with (
                patch.object(hill, "get_alpha_pyramid_pass_info", return_value={"status": "PASS", "categories": ["GBR/D1/ANALYST"]}),
                patch.object(hill, "evaluate_pyramid_coverage", return_value={"status": "HAS_GAP", "scopes": [], "gap_scopes": [{"category": "analyst"}], "reason": "gap"}),
                patch.object(hill, "get_sc_check", return_value=hill.SOURCE_SC_MAX - 0.01),
                patch.object(hill, "current_sc_cache_token", return_value="sc1"),
            ):
                record = optimizer._screen_source_alpha(alpha, hill._default_source_state(), diversity, "d", "f")
                self.assertEqual(record["status"], "ELIGIBLE")

    def test_all_pass_record_is_never_automatically_rescreened(self):
        optimizer = self.make_optimizer()
        record = {
            "alpha_id": "a1",
            "status": "SKIPPED_ALL_TOWERS_PASS",
            "filter_hash": "same-filter",
            "diversity_snapshot_hash": "old-tower-snapshot",
            "pyramid_scopes": [{"raw_scope": "EUR/D1/ANALYST", "check": "PASS"}],
            "gap_scopes": [],
        }

        with patch.object(hill, "ENABLE_PYRAMID_BACKFILL", True):
            self.assertFalse(optimizer._source_record_needs_screening(
                record, "new-tower-snapshot", "sc-token", "same-filter"
            ))

        with patch.object(hill, "ENABLE_PYRAMID_BACKFILL", False):
            self.assertFalse(optimizer._source_record_needs_screening(
                record, "disabled", "sc-token", "same-filter"
            ))

    def test_sc_rejected_is_terminal_even_when_filter_configuration_changes(self):
        optimizer = self.make_optimizer()
        record = {
            "alpha_id": "a1",
            "status": "SC_REJECTED",
            "filter_hash": "same-filter",
            "sc_cache_token": "old-sc-token",
            "sc_value": 0.51,
        }

        self.assertFalse(optimizer._source_record_needs_screening(
            record, "tower-snapshot", "new-sc-token", "same-filter"
        ))
        self.assertFalse(optimizer._source_record_needs_screening(
            record, "tower-snapshot", "new-sc-token", "changed-filter"
        ))

    def test_only_discovered_and_pending_records_are_rescreened(self):
        optimizer = self.make_optimizer()
        terminal_statuses = (
            "METRIC_REJECTED", "SKIPPED_ALL_TOWERS_PASS", "SC_REJECTED",
            "SKIPPED_PNL_UNAVAILABLE", "ELIGIBLE", "INTERRUPTED", "FAILED",
            "PRUNED_SOURCE", "OPTIMIZED",
        )

        for status in terminal_statuses:
            with self.subTest(status=status):
                self.assertFalse(optimizer._source_record_needs_screening(
                    {"status": status, "filter_hash": "old"},
                    "new-diversity", "new-sc-token", "new-filter",
                ))

        for status in ("DISCOVERED", "PENDING_DIVERSITY", "PENDING_PYRAMID"):
            with self.subTest(status=status):
                self.assertTrue(optimizer._source_record_needs_screening(
                    {"status": status}, "diversity", "sc-token", "filter",
                ))

        for status in ("PRE_SC_ELIGIBLE", "PENDING_SC", "PRUNED_PRE_SC"):
            with self.subTest(status=status):
                self.assertFalse(optimizer._source_record_needs_screening(
                    {"status": status}, "diversity", "sc-token", "filter",
                ))

    def test_deferred_sc_persists_tower_classification_without_calling_sc(self):
        optimizer = self.make_optimizer()
        alpha = {
            "id": "cached-tower", "regular": "rank(field_a)",
            "dateCreated": "2026-08-24T01:00:00Z",
            "settings": {"region": "GBR", "delay": 1},
            "is": {"sharpe": 1.8, "fitness": 1.1, "margin": 0.001, "turnover": 0.2},
            "train": {"sharpe": 1.8},
        }
        coverage = {
            "status": "HAS_GAP",
            "scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
            "gap_scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
            "reason": "gap",
        }
        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "get_alpha_pyramid_pass_info", return_value={
                "status": "PASS", "categories": ["GBR/D1/MODEL"],
            }),
            patch.object(hill, "evaluate_pyramid_coverage", return_value=coverage),
            patch.object(hill, "get_sc_check") as sc_mock,
        ):
            record = optimizer._screen_source_alpha(
                alpha, hill._default_source_state(), {}, "tower-hash", "filter-hash",
                defer_sc=True,
            )

        self.assertEqual(record["status"], "PRE_SC_ELIGIBLE")
        self.assertEqual(record["gap_scopes"][0]["raw_scope"], "GBR/D1/MODEL")
        self.assertEqual(record["diversity_snapshot_hash"], "tower-hash")
        sc_mock.assert_not_called()

        with tempfile.TemporaryDirectory() as directory:
            state = hill._default_source_state()
            state["candidates"]["cached-tower"] = record
            path = Path(directory) / "state.json"
            hill.save_source_state(state, path)
            restored = hill.load_source_state(path)["candidates"]["cached-tower"]
        self.assertEqual(restored["pyramid_categories"], ["GBR/D1/MODEL"])
        self.assertEqual(restored["gap_scopes"][0]["raw_scope"], "GBR/D1/MODEL")
        self.assertFalse(optimizer._source_record_needs_screening(
            restored, "new-tower-hash", "new-sc-token", "new-filter-hash",
        ))

    def test_pre_sc_pruning_calls_sc_only_for_kept_candidate_and_reuses_tower_cache(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        common = {
            "status": "PRE_SC_ELIGIBLE", "fitness": 1.0,
            "region": "GBR", "delay": 1, "settings": {"decay": 5},
            "pyramid_scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
            "gap_scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
        }
        state["candidates"] = {
            "best": dict(common, alpha_id="best", expression="rank(field_a)", sharpe=1.8),
            "weak": dict(common, alpha_id="weak", expression="zscore(field_a)", sharpe=1.2),
        }

        best = dict(state["candidates"]["best"], field_combination_key=("combo",))
        weak = dict(state["candidates"]["weak"], field_combination_key=("combo",))
        pool = {
            "active": [best], "reserve": [], "hold_pass": [],
            "superseded": [weak], "pending_metadata": [],
            "tower_summary": {"GBR/D1/MODEL": {"combination_count": 1, "active_count": 1}},
            "ranked": {("combo",): [best, weak]},
        }

        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
            patch.object(hill, "build_candidate_pool", return_value=pool),
            patch.object(hill, "get_alpha_pyramid_pass_info") as pyramid_mock,
            patch.object(hill, "get_sc_check", return_value=0.2) as sc_mock,
            patch.object(hill, "current_sc_cache_token", return_value="sc-token"),
        ):
            summary = optimizer._prune_and_screen_pre_sc(state)

        self.assertEqual(summary["before"], 2)
        self.assertEqual(summary["kept"], 1)
        self.assertEqual(state["candidates"]["best"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["weak"]["pool_status"], "SUPERSEDED")
        sc_mock.assert_not_called()
        self.assertEqual(state["candidates"]["best"]["source_sc_kind"], "MISSING_ALLOWED")
        pyramid_mock.assert_not_called()

    def test_saved_high_sc_is_rejected_before_prune_recalculation(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state["candidates"]["known-high"] = {
            "alpha_id": "known-high", "status": "PRE_SC_ELIGIBLE",
            "expression": "rank(field_a)", "sharpe": 1.8, "fitness": 1.0,
            "sc_value": 0.55, "region": "GBR", "delay": 1,
            "settings": {"decay": 5},
            "gap_scopes": [{"raw_scope": "GBR/D1/MODEL"}],
            "pyramid_scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
        }

        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
            patch.object(hill, "delete_target_pnl_cache") as delete_mock,
            patch.object(hill, "get_sc_check") as sc_mock,
        ):
            summary = optimizer._prune_and_screen_pre_sc(state)

        self.assertEqual(summary["before"], 0)
        self.assertEqual(state["candidates"]["known-high"]["status"], "SC_REJECTED")
        delete_mock.assert_called_once_with("known-high", hill.SC_PPA_CACHE_DIR)
        sc_mock.assert_not_called()

    def test_date_scan_classifies_all_towers_before_first_sc_call(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state["last_complete_scan_date"] = "2026-08-25"
        alphas = [
            {
                "id": alpha_id, "regular": expression,
                "dateCreated": f"2026-08-25T00:00:0{index}Z",
                "settings": {"region": "GBR", "delay": 1, "decay": 5},
                "is": {"sharpe": sharpe, "fitness": 1.0, "margin": 0.001, "turnover": 0.2},
                "train": {"sharpe": 1.7},
            }
            for index, (alpha_id, expression, sharpe) in enumerate((
                ("best", "rank(field_a)", 1.8),
                ("weak", "zscore(field_a)", 1.5),
            ), 1)
        ]
        call_order = []
        coverage = {
            "status": "HAS_GAP",
            "scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
            "gap_scopes": [{"raw_scope": "GBR/D1/MODEL", "check": "MISSING"}],
            "reason": "gap",
        }

        def pyramid_info(_client, alpha_id):
            call_order.append(f"tower:{alpha_id}")
            return {"status": "PASS", "categories": ["GBR/D1/MODEL"]}

        def sc_check(_client, alpha_id, **_kwargs):
            call_order.append(f"sc:{alpha_id}")
            return 0.2

        best = {
            "alpha_id": "best", "expression": "rank(field_a)", "sharpe": 1.8,
            "fitness": 1.0, "settings": {"region": "GBR", "delay": 1, "decay": 5},
            "region": "GBR", "delay": 1, "status": "PRE_SC_ELIGIBLE",
            "pyramid_scopes": coverage["scopes"], "gap_scopes": coverage["gap_scopes"],
            "primary_tower": "GBR/D1/MODEL", "covered_towers": ["GBR/D1/MODEL"],
            "field_combination_key": ("combo",),
        }
        weak = dict(best, alpha_id="weak", expression="zscore(field_a)", sharpe=1.2)
        pool = {
            "active": [best], "reserve": [], "hold_pass": [],
            "superseded": [weak], "pending_metadata": [],
            "tower_summary": {"GBR/D1/MODEL": {"combination_count": 1, "active_count": 1}},
            "ranked": {("combo",): [best, weak]},
        }

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", return_value={
                "results": alphas, "count": 2,
            }),
            patch.object(hill, "get_alpha_pyramid_pass_info", side_effect=pyramid_info),
            patch.object(hill, "evaluate_pyramid_coverage", return_value=coverage),
            patch.object(hill, "build_candidate_pool", return_value=pool),
            patch.object(hill, "get_sc_check", side_effect=sc_check),
            patch.object(hill, "current_sc_cache_token", return_value="sc-token"),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "tower-hash"))

        self.assertEqual(call_order, ["tower:best", "tower:weak"])
        self.assertEqual(state["candidates"]["best"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["best"]["source_sc_kind"], "MISSING_ALLOWED")
        self.assertEqual(state["candidates"]["weak"]["pool_status"], "SUPERSEDED")

    def test_tighter_sc_threshold_uses_saved_value_without_recalculation(self):
        state = hill._default_source_state()
        state["candidates"] = {
            "old-pass": {"alpha_id": "old-pass", "status": "ELIGIBLE", "sc_value": 0.45},
            "still-pass": {"alpha_id": "still-pass", "status": "ELIGIBLE", "sc_value": 0.39},
            "already-rejected": {"alpha_id": "already-rejected", "status": "SC_REJECTED", "sc_value": 0.6},
        }

        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "delete_target_pnl_cache") as delete_mock,
            patch.object(hill, "get_sc_check") as sc_mock,
        ):
            changed = hill.tighten_saved_sc_threshold(state, sc_max=0.4)

        self.assertEqual(changed, ["old-pass"])
        self.assertEqual(state["candidates"]["old-pass"]["status"], "SC_REJECTED")
        self.assertEqual(state["candidates"]["still-pass"]["status"], "ELIGIBLE")
        delete_mock.assert_called_once_with("old-pass", hill.SC_PPA_CACHE_DIR)
        sc_mock.assert_not_called()

    def test_sc_boundary_and_unobserved_values(self):
        optimizer = self.make_optimizer()
        alpha = {
            "id": "a1", "regular": "rank(close)", "settings": {"region": "USA", "delay": 1},
            "is": {"sharpe": 1.6, "fitness": 0.9, "margin": 0.0008, "turnover": 0.2},
            "train": {"sharpe": 1.6},
        }
        coverage = {"status": "HAS_GAP", "scopes": [], "gap_scopes": [{}], "reason": "gap"}
        with (
            patch.object(hill, "append_source_event"),
            patch.object(hill, "get_alpha_pyramid_pass_info", return_value={"status": "PASS", "categories": ["USA/D1/MODEL"]}),
            patch.object(hill, "evaluate_pyramid_coverage", return_value=coverage),
            patch.object(hill, "current_sc_cache_token", return_value="sc1"),
        ):
            for value, expected in ((0.5, "SC_REJECTED"), ("no_cache", "PENDING_SC"), ("error", "PENDING_SC"), (math.nan, "PENDING_SC")):
                with self.subTest(value=value), patch.object(hill, "get_sc_check", return_value=value):
                    record = optimizer._screen_source_alpha(alpha, hill._default_source_state(), {}, "d", "f")
                    self.assertEqual(record["status"], expected)

    def test_disabled_pyramid_switch_only_bypasses_tower_check(self):
        optimizer = self.make_optimizer()
        alpha = {
            "id": "a1", "regular": "rank(close)", "settings": {"region": "USA", "delay": 1},
            "is": {"sharpe": 1.6, "fitness": 0.9, "margin": 0.0008, "turnover": 0.2},
            "train": {"sharpe": 1.6},
        }
        with (
            patch.object(hill, "ENABLE_PYRAMID_BACKFILL", False),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "get_alpha_pyramid_pass_info") as pyramid_mock,
            patch.object(hill, "get_sc_check", return_value=hill.SOURCE_SC_MAX - 0.01) as sc_mock,
            patch.object(hill, "current_sc_cache_token", return_value="sc1"),
        ):
            record = optimizer._screen_source_alpha(alpha, hill._default_source_state(), {}, "disabled", "f")

        self.assertEqual(record["status"], "ELIGIBLE")
        pyramid_mock.assert_not_called()
        sc_mock.assert_called_once()

    def test_date_resume_is_inclusive_and_failure_does_not_advance(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state["last_complete_scan_date"] = "2026-08-23"
        calls = []

        def empty_page(_client, start, end, *_args, **_kwargs):
            calls.append((start, end))
            return {"results": [], "count": 0}

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=empty_page),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))

        self.assertEqual(calls, [("2026-08-23", "2026-08-23"), ("2026-08-24", "2026-08-24"), ("2026-08-25", "2026-08-25")])
        self.assertEqual(state["last_complete_scan_date"], "2026-08-25")

        failed_state = hill._default_source_state()
        failed_state["last_complete_scan_date"] = "2026-08-23"
        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", return_value=None),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertFalse(optimizer._scan_source_candidates(failed_state, {}, "disabled"))
        self.assertEqual(failed_state["last_complete_scan_date"], "2026-08-23")
        self.assertEqual(failed_state["scan_resume"]["date"], "2026-08-23")
        self.assertEqual(failed_state["scan_resume"]["offset"], 0)

    def test_failed_page_resumes_from_offset_after_cooldown(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state["last_complete_scan_date"] = "2026-08-25"
        rows = [
            {
                "id": f"a{index}", "regular": "rank(field_a)",
                "dateCreated": "2026-08-25T00:00:00Z",
            }
            for index in range(100)
        ]
        offsets = []

        def first_attempt(_client, _start, _end, *_args, **kwargs):
            offsets.append(kwargs["offset"])
            return {"results": rows, "count": 200} if kwargs["offset"] == 0 else None

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=first_attempt),
            patch.object(optimizer, "_screen_source_alpha"),
            patch.object(optimizer, "_prune_and_screen_pre_sc"),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertFalse(optimizer._scan_source_candidates(state, {}, "disabled"))
        self.assertEqual(offsets, [0, 100])
        self.assertEqual(state["scan_resume"]["offset"], 100)

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page") as page_mock,
            patch.object(optimizer, "_prune_and_screen_pre_sc"),
        ):
            self.assertFalse(optimizer._scan_source_candidates(state, {}, "disabled"))
        page_mock.assert_not_called()

        state["scan_resume"]["retry_after"] = "2026-08-25T11:59:00+08:00"
        resumed_offsets = []

        def resumed(_client, _start, _end, *_args, **kwargs):
            resumed_offsets.append(kwargs["offset"])
            return {"results": [], "count": 100}

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=resumed),
            patch.object(optimizer, "_prune_and_screen_pre_sc"),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))
        self.assertEqual(resumed_offsets, [100])
        self.assertIsNone(state["scan_resume"])

    def test_dense_day_switches_to_descending_before_platform_offset_limit(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state["last_complete_scan_date"] = "2026-08-25"
        calls = []

        def dense_page(_client, _start, _end, *_args, **kwargs):
            offset = kwargs["offset"]
            descending = kwargs["descending"]
            calls.append((descending, offset))
            if descending:
                start = 1100 - offset
            else:
                start = offset
            rows = [
                {
                    "id": f"a{index}", "regular": "rank(field_a)",
                    "dateCreated": "2026-08-25T00:00:00Z",
                }
                for index in range(start, start + 100)
            ]
            return {"results": rows, "count": 1200}

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=dense_page),
            patch.object(optimizer, "_screen_source_alpha"),
            patch.object(optimizer, "_prune_and_screen_pre_sc"),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))

        self.assertEqual(calls[:10], [(False, offset) for offset in range(0, 1000, 100)])
        self.assertEqual(calls[10:], [(True, 0), (True, 100)])
        self.assertNotIn((False, 1000), calls)
        self.assertIsNone(state["scan_resume"])

    def test_first_scan_covers_exactly_thirty_calendar_days(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        calls = []

        def empty_page(_client, start, end, *_args, **_kwargs):
            calls.append((start, end))
            return {"results": [], "count": 0}

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=empty_page),
            patch.object(hill, "append_source_event"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))

        self.assertEqual(len(calls), 30)
        self.assertEqual(calls[0], ("2026-07-27", "2026-07-27"))
        self.assertEqual(calls[-1], ("2026-08-25", "2026-08-25"))

    def test_completed_today_skips_remote_scan_until_incremental_due(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state.update({
            "last_complete_scan_date": "2026-08-25",
            "last_full_scan_at": "2026-08-25T11:45:00+08:00",
            "last_incremental_scan_at": "2026-08-25T11:58:00+08:00",
        })
        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page") as page_mock,
            patch.object(optimizer, "_prune_and_screen_pre_sc") as prune_mock,
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))
        page_mock.assert_not_called()
        prune_mock.assert_not_called()

    def test_completed_today_uses_one_descending_incremental_page(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state.update({
            "last_complete_scan_date": "2026-08-25",
            "last_full_scan_at": "2026-08-25T11:45:00+08:00",
            "last_incremental_scan_at": "2026-08-25T11:50:00+08:00",
        })
        state["candidates"]["known"] = {"alpha_id": "known", "status": "OPTIMIZED"}
        page = {
            "count": 2,
            "results": [
                {"id": "new", "regular": "rank(field_a)", "dateCreated": "2026-08-25T11:59:00Z"},
                {"id": "known", "regular": "rank(field_b)", "dateCreated": "2026-08-25T11:58:00Z"},
            ],
        }
        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", return_value=page) as page_mock,
            patch.object(optimizer, "_screen_source_alpha") as screen_mock,
            patch.object(optimizer, "_prune_and_screen_pre_sc") as prune_mock,
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))
        self.assertTrue(page_mock.call_args.kwargs["descending"])
        self.assertEqual(page_mock.call_args.kwargs["offset"], 0)
        screen_mock.assert_called_once()
        self.assertEqual(screen_mock.call_args.args[0]["id"], "new")
        prune_mock.assert_called_once_with(state)
        self.assertIn("new", state["candidates"])

    def test_incremental_scan_pages_until_it_reaches_known_alpha(self):
        optimizer = self.make_optimizer()
        state = hill._default_source_state()
        state.update({
            "last_complete_scan_date": "2026-08-25",
            "last_full_scan_at": "2026-08-25T11:45:00+08:00",
            "last_incremental_scan_at": "2026-08-25T11:50:00+08:00",
        })
        state["candidates"]["known"] = {"alpha_id": "known", "status": "OPTIMIZED"}
        offsets = []

        def page(_client, _start, _end, *_args, **kwargs):
            offset = kwargs["offset"]
            offsets.append(offset)
            if offset < 200:
                rows = [
                    {"id": f"new-{offset + index}", "regular": "rank(field_a)"}
                    for index in range(100)
                ]
            else:
                rows = [{"id": "known", "regular": "rank(field_a)"}]
            return {"count": 250, "results": rows}

        with (
            patch.object(hill, "datetime", FixedDateTime),
            patch.object(hill, "get_user_alphas_page", side_effect=page),
            patch.object(optimizer, "_screen_source_alpha"),
            patch.object(optimizer, "_prune_and_screen_pre_sc"),
            patch.object(hill, "save_source_state"),
        ):
            self.assertTrue(optimizer._scan_source_candidates(state, {}, "disabled"))

        self.assertEqual(offsets, [0, 100, 200])
        self.assertEqual(len(state["candidates"]), 201)

    def test_factory_shape_check_is_skipped_for_failed_platform_checks(self):
        optimizer = self.make_optimizer()
        optimizer.settings = {"region": "GBR", "universe": "TOP3000", "delay": 1}
        optimizer.client.history = {}
        optimizer.client.sc_status = {}
        optimizer.client.save_history = Mock()
        results = {}
        response = {
            "id": "failed-alpha",
            "is": {
                "sharpe": 0.4, "fitness": 0.2, "margin": 0.001,
                "turnover": 0.1, "checks": [{"result": "FAIL"}],
            },
        }
        optimizer._process_result(response, "rank(field_a)", "url", results)
        optimizer.client.check_factory_shape.assert_not_called()
        self.assertFalse(results["rank(field_a)"]["stats"]["passed"])

    def test_pending_platform_check_is_not_treated_as_pass(self):
        optimizer = self.make_optimizer()
        optimizer.settings = {"region": "GBR", "universe": "TOP3000", "delay": 1}
        optimizer.client.history = {}
        optimizer.client.sc_status = {}
        optimizer.client.save_history = Mock()
        results = {}
        response = {
            "id": "pending-alpha",
            "is": {
                "sharpe": 1.8, "fitness": 1.1, "margin": 0.001,
                "turnover": 0.1, "checks": [{"result": "PENDING"}],
            },
        }
        optimizer._process_result(response, "rank(field_a)", "url", results)
        optimizer.client.check_factory_shape.assert_not_called()
        optimizer.client.get_alpha_details.assert_not_called()
        self.assertIsNone(results["rank(field_a)"]["stats"]["passed"])

    def test_candidate_order_prefers_gap_then_age_sc_and_distance(self):
        state = hill._default_source_state()
        state["candidates"] = {
            "optimized": {"alpha_id": "optimized", "status": "OPTIMIZED", "expression": "rank(close)"},
            "one": {"alpha_id": "one", "status": "ELIGIBLE", "expression": "rank(open)", "gap_scopes": [{}], "date_created": "2026-08-20", "sc_value": 0.1},
            "two-new": {"alpha_id": "two-new", "status": "ELIGIBLE", "expression": "zscore(volume)", "gap_scopes": [{}, {}], "date_created": "2026-08-22", "sc_value": 0.1},
            "two-old": {"alpha_id": "two-old", "status": "ELIGIBLE", "expression": "ts_mean(volume,22)", "gap_scopes": [{}, {}], "date_created": "2026-08-21", "sc_value": 0.4},
        }

        selected = hill.select_next_source_record(state)

        self.assertEqual(selected["alpha_id"], "two-new")

    def test_core_prune_keeps_top_sharpe_per_field_combination(self):
        state = hill._default_source_state()
        state["candidates"] = {
            "best": {"alpha_id": "best", "status": "ELIGIBLE", "expression": "rank(field_a)", "sharpe": 1.8, "fitness": 1.2, "settings": {"decay": 5}},
            "second": {"alpha_id": "second", "status": "ELIGIBLE", "expression": "zscore(field_a)", "sharpe": 1.6, "fitness": 1.0, "settings": {"decay": 5}},
            "weak": {"alpha_id": "weak", "status": "ELIGIBLE", "expression": "reverse(field_a)", "sharpe": 1.2, "fitness": 0.7, "settings": {"decay": 5}},
            "other": {"alpha_id": "other", "status": "ELIGIBLE", "expression": "rank(field_b)", "sharpe": 1.1, "fitness": 0.7, "settings": {"decay": 5}},
        }

        with patch.object(hill, "append_source_event"):
            summary = hill.prune_source_queue(state, keep_num=2)

        self.assertEqual(summary["before"], 4)
        self.assertEqual(summary["kept"], 3)
        self.assertEqual(state["candidates"]["weak"]["status"], "PRUNED_SIMILAR")
        self.assertEqual(state["candidates"]["best"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["other"]["status"], "ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
