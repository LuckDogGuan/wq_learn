import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "代码" / "优化代码"))

from Core.factor.template_usage import (
    TEMPLATE_LEARNING_VERSION,
    TEMPLATE_CANDIDATES,
    compose_stage1_template_batch,
    compose_template_batch,
    load_template_usage,
    record_template_usage,
    record_template_usage_batch,
    resolve_template_category,
    select_template_candidates,
    summarize_template_usage,
)


ALL_TEST_OPS = {
    "abs", "densify", "group_neutralize", "group_rank", "group_zscore",
    "inverse", "log", "normalize", "pasteurize", "rank", "regression_neut",
    "reverse", "sign", "signed_power", "sqrt", "ts_arg_max", "ts_av_diff",
    "ts_arg_min", "ts_backfill", "ts_corr", "ts_count_nans", "ts_decay_linear", "ts_delay",
    "ts_delta", "ts_ir", "ts_kurtosis", "ts_max_diff", "ts_mean", "ts_product",
    "ts_quantile", "ts_rank", "ts_regression", "ts_returns", "ts_std_dev",
    "ts_step", "ts_sum", "ts_zscore", "vec_avg", "vector_neut", "zscore",
}


def scope():
    return {
        "region": "USA", "universe": "TOP3000", "delay": 1,
        "dataset_id": "demo", "field_type": "MATRIX",
        "candidate_origin": "FORMAL_TEMPLATE",
    }


class TemplateUsageTest(unittest.TestCase):
    def test_hu_ge_series2_is_the_only_registered_hu_ge_margin_family(self):
        registered = {
            item['template_id'] for item in TEMPLATE_CANDIDATES
            if item['template_id'].startswith('hu_ge.')
        }
        self.assertEqual(registered, {
            'hu_ge.series2_residual_stddev', 'hu_ge.series2_beta_lagged',
        })

    def test_hu_ge_margin_candidates_require_same_dataset_semantic_matrix_pair(self):
        context = {
            'template_learning_version': TEMPLATE_LEARNING_VERSION,
            'region': 'USA', 'category': 'MODEL', 'stage': 2,
            'template_role': 'MARGIN_REPAIR',
            'fields': [
                {'id': 'model_value_score', 'description': 'model value signal',
                 'type': 'MATRIX', 'dataset_id': 'model1'},
                {'id': 'model_growth_score', 'description': 'model growth signal',
                 'type': 'MATRIX', 'dataset_id': 'model1'},
            ],
            'expression': 'rank(model_value_score)',
            'allowed_operators': ALL_TEST_OPS,
        }
        selected = select_template_candidates(context, 64)
        hu = [item for item in selected if item['template_id'].startswith('hu_ge.')]
        self.assertEqual({item['template_id'] for item in hu}, {
            'hu_ge.series2_residual_stddev', 'hu_ge.series2_beta_lagged',
        })
        self.assertEqual({item['resolved_params']['d'] for item in hu}, {120, 252})
        context['fields'][1] = {**context['fields'][1], 'dataset_id': 'model2'}
        self.assertFalse([
            item for item in select_template_candidates(context, 64)
            if item['template_id'].startswith('hu_ge.')
        ])

    def test_margin_v4_summary_uses_effective_joint_improvement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / 'events_v4.jsonl'
            base = {
                'template_learning_version': TEMPLATE_LEARNING_VERSION,
                'region': 'GBR', 'category': 'ANALYST', 'stage': 2,
                'template_role': 'MARGIN_REPAIR', 'repair_goal': 'MARGIN',
                'template_id': 'margin.demo', 'template_version': 'v1',
                'variant_id': 'd22', 'candidate_origin': 'FORMAL_TEMPLATE',
                'status': 'COMPLETE', 'baseline_metrics_complete': True,
                'result_metrics_complete': True, 'margin_bp_delta': 2.0,
                'non_margin_gates_retained': True, 'turnover_retained': True,
                'margin_effective_improvement': True,
            }
            for index in range(2):
                record_template_usage({
                    **base, 'candidate_key': f'margin-{index}',
                    'source_alpha_id': f'source-{index}',
                }, events, None)
            rows = summarize_template_usage({
                'template_learning_version': TEMPLATE_LEARNING_VERSION,
                'region': 'GBR', 'category': 'ANALYST', 'stage': 2,
            }, events, None)
            self.assertEqual(rows[0]['template_state'], 'PROMISING')
            self.assertEqual(rows[0]['median_margin_bp_delta'], 2.0)
    def test_category_prefers_primary_tower_and_conflict_is_pending(self):
        resolved = resolve_template_category("USA/TOP3000/D1/MODEL", ["MODEL"])
        self.assertEqual(resolved["category"], "MODEL")
        self.assertEqual(resolved["category_source"], "PRIMARY_TOWER")
        fallback = resolve_template_category(None, [{"id": "ANALYST"}])
        self.assertEqual(fallback["category"], "ANALYST")
        conflict = resolve_template_category("USA/TOP3000/D1/PV", ["MODEL"])
        self.assertEqual(conflict["status"], "PENDING_CATEGORY_CONFLICT")

    def test_v2_summary_separates_category_version_and_variant(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events_v2.jsonl"
            base = {
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 1,
                "template_id": "demo.template", "template_version": "v1",
                "variant_id": "window-22", "template_role": "SIGNAL_BUILD",
                "status": "COMPLETE", "retained_previous_gates": True,
                "candidate_origin": "FORMAL_TEMPLATE",
                "baseline_metrics_complete": True, "result_metrics_complete": True,
            }
            for index in range(2):
                record_template_usage({
                    **base, "candidate_key": f"model-{index}",
                    "source_alpha_id": f"source-{index}", "gate_improved": True,
                    "gate_deficit_delta": 0.1,
                }, events, None)
            record_template_usage({
                **base, "category": "ANALYST", "candidate_key": "analyst",
                "source_alpha_id": "other", "gate_improved": False,
                "gate_deficit_delta": 0,
            }, events, None)
            record_template_usage({
                **base, "template_version": "v2", "candidate_key": "new-version",
                "source_alpha_id": "other", "gate_improved": False,
                "gate_deficit_delta": 0,
            }, events, None)
            rows = summarize_template_usage({
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 1,
            }, events, None)
            states = {
                (row["template_version"], row["variant_id"]): row["template_state"]
                for row in rows
            }
            self.assertEqual(states[("v1", "window-22")], "PROMISING")
            self.assertEqual(states[("v2", "window-22")], "PROBATION")
            self.assertEqual(sum(row["complete_count"] for row in rows), 3)

    def test_v2_stage_roles_variants_and_fixed_batch_mix(self):
        context = {
            "template_learning_version": TEMPLATE_LEARNING_VERSION,
            "region": "USA", "category": "MODEL", "stage": 2,
            "template_role": "STABILITY_CONTROL",
            "fields": [{"id": "demo_return", "type": "MATRIX", "dataset_id": "demo"}],
            "expression": "rank(demo_return)", "allowed_operators": ALL_TEST_OPS,
        }
        selected = select_template_candidates(context, 64)
        self.assertTrue(selected)
        self.assertTrue(all(item["stage"] == 2 for item in selected))
        self.assertTrue(all(item["role"] == "STABILITY_CONTROL" for item in selected))
        decay_variants = {
            item["variant_id"] for item in selected
            if item["template_id"] == "post.decay"
        }
        self.assertGreaterEqual(len(decay_variants), 2)

        candidates = []
        states = ["PROBATION"] * 4 + ["CHAMPION"] * 2 + ["PROBATION"] * 2 + ["LOW_PRIORITY"] * 2
        for index, state in enumerate(states):
            candidates.append({
                "expression_hash": f"h{index}", "eligible": True,
                "template_state": state,
                "template_class": "ECONOMIC_SIGNAL",
                "economic_match": True,
                "economic_thesis_id": f"thesis-{index}",
                "selection_bucket": "CHALLENGER" if index in {6, 7} else "PROBATION",
            })
        batch = compose_template_batch(candidates)
        self.assertEqual(len(batch), 8)
        self.assertFalse(any(item["template_state"] == "LOW_PRIORITY" for item in batch))

    def test_legacy_disabled_state_does_not_contaminate_v2_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "legacy.jsonl"
            for index in range(8):
                record_template_usage({
                    **scope(), "template_id": "economic.information_change",
                    "candidate_key": f"legacy-{index}", "status": "COMPLETE",
                    "score_delta": -1,
                }, events, None)
            context = {
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 1,
                "template_role": "SIGNAL_BUILD", "usage_path": events,
                "fields": [{
                    "id": "demo_return", "type": "MATRIX", "dataset_id": "demo",
                }],
                "expression": "rank(demo_return)",
                "allowed_operators": ALL_TEST_OPS,
            }
            selected = select_template_candidates(context, 64)
            candidate = next(
                item for item in selected
                if item["template_id"] == "economic.information_change"
            )
            self.assertEqual(candidate["template_state"], "PROBATION")

    def test_gate_damage_is_not_counted_as_v2_improvement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events_v2.jsonl"
            record_template_usage({
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 3,
                "template_id": "post.rank", "template_version": "v1",
                "variant_id": "default", "source_alpha_id": "source",
                "candidate_key": "damaged", "status": "COMPLETE",
                "gate_improved": True, "retained_previous_gates": False,
                "gate_deficit_delta": 0.2,
                "candidate_origin": "FORMAL_TEMPLATE",
                "baseline_metrics_complete": True, "result_metrics_complete": True,
            }, events, None)
            row = summarize_template_usage({
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 3,
            }, events, None)[0]
            self.assertEqual(row["improved_count"], 0)
            self.assertEqual(row["template_state"], "PROBATION")

    def test_pending_record_is_not_written_or_summarized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            summary = Path(temp_dir) / "summary.csv"
            with patch("Core.factor.template_usage.summarize_template_usage") as refresh:
                event = record_template_usage(
                    {**scope(), "template_id": "demo.template"}, events, summary,
                )
            self.assertIsNone(event)
            refresh.assert_not_called()
            self.assertFalse(events.exists())

    def test_batch_appends_all_records_and_refreshes_summary_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            summary = Path(temp_dir) / "summary.csv"
            records = [
                {**scope(), "template_id": "demo.template", "candidate_key": f"c{index}",
                 "status": "COMPLETE"}
                for index in range(8)
            ]
            with patch("Core.factor.template_usage.summarize_template_usage") as refresh:
                written = record_template_usage_batch(records, events, summary)
            self.assertEqual(len(written), 8)
            self.assertEqual(len(load_template_usage(events)), 8)
            refresh.assert_called_once_with(path=events, summary_path=summary)

    def test_append_only_mode_skips_rebuilding_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            with patch("Core.factor.template_usage.summarize_template_usage") as refresh:
                record_template_usage(
                    {**scope(), "template_id": "demo.template", "status": "COMPLETE"},
                    events, None, refresh_summary=False,
                )
            self.assertEqual(len(load_template_usage(events)), 1)
            refresh.assert_not_called()

    def test_recovery_does_not_append_same_complete_event_twice(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            record = {
                **scope(), "template_id": "demo.template",
                "candidate_key": "same-result", "status": "COMPLETE",
            }
            first = record_template_usage(record, events, None, refresh_summary=False)
            second = record_template_usage(record, events, None, refresh_summary=False)
            self.assertIsNotNone(first)
            self.assertIsNone(second)
            self.assertEqual(len(load_template_usage(events)), 1)

    def test_registry_is_broad_and_selection_is_bounded(self):
        self.assertGreaterEqual(len(TEMPLATE_CANDIDATES), 50)
        context = {
            **scope(),
            "fields": [
                {"id": "demo_return", "type": "MATRIX", "dataset_id": "demo"},
                {"id": "demo_value", "type": "MATRIX", "dataset_id": "demo"},
            ],
            "expression": "rank(demo_return)",
            "allowed_operators": ALL_TEST_OPS,
        }
        selected = select_template_candidates(context, 64)
        self.assertGreaterEqual(len(selected), 56)
        self.assertLessEqual(len(selected), 64)
        self.assertGreaterEqual(len([item for item in selected if item.get("kind") == "shape"]), 15)
        for candidate in selected:
            self.assertTrue(candidate["local_validation"]["valid"])
            self.assertLess(len(candidate["operators"]), 6)
            self.assertFalse({"add", "multiply", "trade_when"} & set(candidate["operators"]))

    def test_pending_does_not_demote_and_complete_results_do(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            summary = Path(temp_dir) / "summary.csv"
            base = {**scope(), "template_id": "demo.template"}
            for index in range(10):
                record_template_usage(
                    {**base, "candidate_key": f"p{index}", "status": "PENDING"},
                    events, summary,
                )
            self.assertEqual(summarize_template_usage(scope(), events, None), [])

            for index in range(3):
                record_template_usage(
                    {**base, "candidate_key": f"c{index}", "status": "COMPLETE", "score_delta": -0.1},
                    events, summary,
                )
            row = summarize_template_usage(scope(), events, None)[0]
            self.assertEqual(row["template_state"], "LOW_PRIORITY")

            for index in range(3, 8):
                record_template_usage(
                    {**base, "candidate_key": f"c{index}", "status": "COMPLETE", "score_delta": -0.1},
                    events, summary,
                )
            row = summarize_template_usage(scope(), events, None)[0]
            self.assertEqual(row["template_state"], "DISABLED_SCOPE")

    def test_incomplete_batch_is_not_written_to_performance_ledger(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            summary = Path(temp_dir) / "summary.csv"
            record_template_usage(
                {
                    **scope(), "template_id": "demo.template",
                    "candidate_key": "deferred",
                    "status": "DEFERRED_INCOMPLETE_BATCH",
                },
                events, summary,
            )
            self.assertEqual(summarize_template_usage(scope(), events, None), [])

    def test_vector_field_is_converted_and_cross_dataset_binary_is_skipped(self):
        context = {
            **scope(),
            "fields": [
                {"id": "vector_a", "type": "VECTOR", "dataset_id": "a"},
                {"id": "matrix_b", "type": "MATRIX", "dataset_id": "b"},
            ],
            "expression": "rank(vec_avg(vector_a))",
            "allowed_operators": ALL_TEST_OPS,
        }
        selected = select_template_candidates(context, 64)
        vector_templates = [item for item in selected if item.get("kind") == "field"]
        self.assertTrue(vector_templates)
        self.assertTrue(all("vec_avg(vector_a)" in item["expression"] for item in vector_templates))
        self.assertFalse(any(item["template_id"].startswith("tiger.binary") for item in selected))

    def test_densify_rejects_matrix_and_uses_explicit_group_metadata(self):
        matrix_context = {
            **scope(),
            "fields": [{"id": "price_field", "type": "MATRIX", "dataset_id": "demo"}],
            "expression": "rank(price_field)",
            "allowed_operators": ALL_TEST_OPS,
        }
        matrix_selected = select_template_candidates(matrix_context, 64)
        self.assertFalse(any(
            item["template_id"] == "cross.densify" for item in matrix_selected
        ))

        mixed_context = {
            **scope(),
            "fields": [
                {"id": "price_field", "type": "MATRIX", "dataset_id": "demo"},
                {"id": "event_group", "type": "GROUP", "dataset_id": "demo"},
            ],
            "expression": "rank(price_field)",
            "allowed_operators": ALL_TEST_OPS,
        }
        mixed_selected = select_template_candidates(mixed_context, 64)
        densify = next(item for item in mixed_selected if item["template_id"] == "cross.densify")
        self.assertEqual(densify["expression"], "densify(event_group)")
        self.assertEqual(densify["fields"], ["event_group"])
        self.assertEqual(densify["field_type"], "GROUP")

    def test_densify_does_not_guess_unknown_field_type(self):
        context = {
            **scope(),
            "fields": [{"id": "looks_like_group", "dataset_id": "demo"}],
            "expression": "rank(looks_like_group)",
            "allowed_operators": ALL_TEST_OPS,
        }
        selected = select_template_candidates(context, 64)
        self.assertFalse(any(item["template_id"] == "cross.densify" for item in selected))

    def test_cancelled_template_event_is_not_written(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            record_template_usage(
                {**scope(), "template_id": "demo.template", "status": "CANCELLED"},
                events, None,
            )
            self.assertEqual(summarize_template_usage(scope(), events, None), [])

    def test_complete_event_with_unknown_score_delta_does_not_break_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            record_template_usage(
                {
                    **scope(), "template_id": "demo.template",
                    "candidate_key": "unknown-score", "status": "COMPLETE",
                    "score_delta": None, "became_best": False,
                },
                events, None,
            )
            row = summarize_template_usage(scope(), events, None)[0]
            self.assertEqual(row["complete_count"], 1)
            self.assertEqual(row["improved_count"], 0)
            self.assertEqual(row["median_score_delta"], 0.0)

    def test_template_promotion_uses_gate_improvement_not_score_delta(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            base = {**scope(), "template_id": "demo.template", "status": "COMPLETE"}
            record_template_usage(
                {**base, "candidate_key": "score-only", "score_delta": 50.0,
                 "gate_improved": False}, events, None,
            )
            row = summarize_template_usage(scope(), events, None)[0]
            self.assertEqual(row["template_state"], "ACTIVE")
            self.assertEqual(row["improved_count"], 0)
            record_template_usage(
                {**base, "candidate_key": "gate", "score_delta": -5.0,
                 "gate_improved": True, "gate_deficit_delta": 0.2}, events, None,
            )
            row = summarize_template_usage(scope(), events, None)[0]
            self.assertEqual(row["template_state"], "PROMISING")
            self.assertEqual(row["improved_count"], 1)

    def test_corrupt_jsonl_tail_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events.jsonl"
            events.write_text(json.dumps({"status": "PENDING"}) + "\n{broken", encoding="utf-8")
            self.assertEqual(len(load_template_usage(events)), 1)

    def test_stage_one_requires_category_and_field_semantics(self):
        base = {
            "template_learning_version": TEMPLATE_LEARNING_VERSION,
            "region": "USA", "category": "ANALYST", "stage": 1,
            "template_role": "SIGNAL_BUILD",
            "expression": "rank(analyst_estimate_revision)",
            "allowed_operators": ALL_TEST_OPS,
        }
        selected = select_template_candidates({
            **base,
            "fields": [{
                "id": "analyst_estimate_revision", "description": "analyst estimate revision",
                "type": "MATRIX", "dataset_id": "analyst_demo",
            }],
        }, 64)
        self.assertGreaterEqual(len(selected), 8)
        self.assertTrue(all(item["template_class"] == "ECONOMIC_SIGNAL" for item in selected))
        self.assertTrue(all(item["economic_hypothesis"] for item in selected))
        self.assertFalse(any(item["template_id"].startswith("shape.") for item in selected))

        unknown = select_template_candidates({
            **base,
            "fields": [{"id": "opaque_x1", "type": "MATRIX", "dataset_id": "opaque"}],
        }, 64)
        self.assertEqual(unknown, [])

    def test_stage0_registry_excludes_forbidden_first_version_templates(self):
        ids = {item["template_id"] for item in TEMPLATE_CANDIDATES}
        self.assertIn("stage0.cross_sectional_rank", ids)
        self.assertIn("stage0.options_put_call", ids)
        self.assertNotIn("stage0.sentiment_polarity", ids)
        self.assertNotIn("stage0.analyst_surprise", ids)

    def test_stage1_formal_batch_uses_four_stage0_two_economic_and_two_learning_slots(self):
        candidates = []
        for index in range(4):
            candidates.append({
                "template_id": f"stage0.t{index}", "expression_hash": f"s{index}",
                "eligible": True, "template_state": "PROBATION",
                "template_class": "ECONOMIC_SIGNAL", "economic_thesis_id": f"s{index}",
            })
        for index in range(2):
            candidates.append({
                "template_id": f"economic.t{index}", "expression_hash": f"e{index}",
                "eligible": True, "template_state": "PROBATION",
                "template_class": "ECONOMIC_SIGNAL", "economic_thesis_id": f"e{index}",
            })
        candidates.extend([
            {
                "template_id": "winner", "expression_hash": "winner",
                "eligible": True, "template_state": "CHAMPION",
                "template_class": "ECONOMIC_SIGNAL",
            },
            {
                "template_id": "challenger", "expression_hash": "challenger",
                "eligible": True, "template_state": "PROBATION",
                "selection_bucket": "CHALLENGER", "template_class": "ECONOMIC_SIGNAL",
            },
        ])
        batch = compose_stage1_template_batch(candidates)
        self.assertEqual(len(batch), 8)
        self.assertEqual(sum(item["template_id"].startswith("stage0.") for item in batch), 4)
        self.assertIn("winner", {item["template_id"] for item in batch})
        self.assertIn("challenger", {item["template_id"] for item in batch})

    def test_low_priority_only_uses_due_challenger_slot(self):
        candidates = []
        for index in range(9):
            low = index == 8
            candidates.append({
                "expression_hash": f"e{index}", "eligible": True,
                "template_state": "LOW_PRIORITY" if low else "PROBATION",
                "selection_bucket": "PROBATION",
                "template_class": "ECONOMIC_SIGNAL", "economic_match": True,
                "economic_thesis_id": f"t{index}",
                "low_recheck_due": low,
            })
        batch = compose_template_batch(candidates)
        self.assertEqual(len(batch), 8)
        self.assertLessEqual(sum(item["template_state"] == "LOW_PRIORITY" for item in batch), 1)

    def test_v3_learning_ignores_local_probe_and_incomplete_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events = Path(temp_dir) / "events_v3.jsonl"
            base = {
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 1,
                "template_id": "economic.information_change",
                "template_version": "v1", "variant_id": "d22",
                "status": "COMPLETE", "gate_improved": True,
                "retained_previous_gates": True, "gate_deficit_delta": 0.1,
            }
            record_template_usage({
                **base, "candidate_key": "probe", "candidate_origin": "LOCAL_PROBE",
                "baseline_metrics_complete": True, "result_metrics_complete": True,
            }, events, None)
            record_template_usage({
                **base, "candidate_key": "missing-base",
                "candidate_origin": "FORMAL_TEMPLATE",
                "baseline_metrics_complete": False, "result_metrics_complete": True,
            }, events, None)
            row = summarize_template_usage({
                "template_learning_version": TEMPLATE_LEARNING_VERSION,
                "region": "USA", "category": "MODEL", "stage": 1,
            }, events, None)[0]
            self.assertEqual(row["complete_count"], 0)
            self.assertEqual(row["improved_count"], 0)


if __name__ == "__main__":
    unittest.main()
