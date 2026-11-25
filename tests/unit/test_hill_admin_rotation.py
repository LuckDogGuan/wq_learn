"""Offline hill integration checks; no platform calls or production ledger writes."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "代码" / "优化代码" / "爬山代码"))
from hill_climbing import optimizer as hill
from Core.factor import template_usage as usage


class SelectionObserved(Exception):
    pass


class HillAdminRotationTests(unittest.TestCase):
    def test_route_cannot_override_catalog_order(self):
        from hill_climbing.routes import prioritize_route
        candidates = [
            {"template_id": "post.decay", "family": "decay"},
            {"template_id": "admin.catalog.z", "catalog_status": "LOCAL_PASS_UNVALIDATED"},
            {"template_id": "admin.catalog.a", "catalog_status": "LOCAL_PASS_UNVALIDATED"},
        ]
        result = prioritize_route(candidates, "smooth", prefer_catalog=True)
        self.assertEqual([item["template_id"] for item in result], ["admin.catalog.z", "admin.catalog.a", "post.decay"])

    def optimizer(self, stage=1):
        instance = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
        instance.settings = {"region": "USA", "universe": "TOP3000", "delay": 1}
        instance.hill_stage = stage
        instance.stop_requested = False
        instance.current_position = {}
        instance.best_expr = "rank(field_a)"
        instance.best_stats = {}
        instance.initial_score = 0
        instance.source_record = {"primary_tower": "USA/FUNDAMENTAL"}
        instance.client = Mock()
        instance.client.get_available_operators.return_value = {"rank", "ts_rank"}
        instance.client.get_field_metadata.return_value = {
            "id": "field_a", "dataset_id": "fundamental_a", "category": "FUNDAMENTAL",
            "type": "MATRIX",
        }
        instance._assess_stats = Mock(return_value={"gate": {}})
        instance._metric_once = Mock()
        instance._metric = Mock()
        return instance

    def test_source_and_margin_contexts_opt_into_same_scope_rotation(self):
        for stage in (1, 2):
            with self.subTest(stage=stage):
                instance = self.optimizer(stage)
                contexts = []

                def capture(context, *args, **kwargs):
                    contexts.append(dict(context))
                    if len(contexts) == 2:
                        raise SelectionObserved
                    return [], []

                with patch.object(hill, "select_template_candidates", side_effect=capture), \
                     patch.object(hill, "post_multi_simulation") as post:
                    with self.assertRaises(SelectionObserved):
                        instance.run_template_exploration(
                            "source_alpha", Mock(tokens=[{"type": "data_field", "text": "field_a"}])
                        )
                    post.assert_not_called()
                self.assertTrue(all(context["prefer_admin_templates"] for context in contexts))
                self.assertEqual(contexts[0]["dataset_id"], "fundamental_a")
                self.assertEqual(contexts[0]["category"], "FUNDAMENTAL")
                self.assertEqual(contexts[0]["stage"], stage)
                self.assertEqual(contexts[1]["template_role"], "MARGIN_REPAIR")
                self.assertEqual(hill.TEMPLATE_BATCH_SIZE, 8)

    def test_completed_event_preserves_provenance_and_attempt_count(self):
        instance = self.optimizer()
        candidate = {
            "candidate_origin": "FORMAL_TEMPLATE", "template_id": "admin.profit_to_size",
            "source_kind": "ADMIN_DISTRIBUTED", "source_post_id": "32134389476503",
            "source_url": "https://support.worldquantbrain.com/hc/zh-cn/community/posts/32134389476503",
            "template_attempt_count": 7, "role": "SIGNAL_BUILD",
            "expression": "rank(field_a)", "expression_hash": "expr_hash",
            "field_metadata": [instance.client.get_field_metadata.return_value],
            "eligible": True, "candidate_key": "run|expr_hash", "formal_batch_id": "run:0",
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"

            def write(event, **kwargs):
                return usage.record_template_usage(event, path=path, **kwargs)

            with patch.object(hill, "record_template_usage", side_effect=write):
                instance._record_template_candidate("run", "source_alpha", candidate, "COMPLETE")
                instance._record_template_candidate("run", "source_alpha", candidate, "COMPLETE")
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(events), 1)
        for key in ("source_kind", "source_post_id", "source_url", "template_attempt_count"):
            self.assertEqual(events[0][key], candidate[key])
        self.assertEqual(events[0]["formal_batch_id"], "run:0")
        self.assertEqual(events[0]["candidate_key"], "run|expr_hash")

    def test_rotation_does_not_bypass_cross_dataset_source_guard(self):
        instance = self.optimizer()
        instance.client.get_field_metadata.side_effect = [
            {"id": "field_a", "dataset_id": "dataset_a", "category": "FUNDAMENTAL"},
            {"id": "field_b", "dataset_id": "dataset_b", "category": "FUNDAMENTAL"},
        ]
        parser = Mock(tokens=[{"type": "data_field", "text": name}
                              for name in ("field_a", "field_b")])
        with patch.object(hill, "select_template_candidates") as select, \
             patch.object(hill, "post_multi_simulation") as post:
            self.assertFalse(instance.run_template_exploration("source_alpha", parser))
            select.assert_not_called()
            post.assert_not_called()
        self.assertEqual(instance.template_blocked_status, "DISABLED_SCOPE")

    def test_stage3_unobserved_sc_remains_pending_without_type_comparison(self):
        for sc_result in ("no_cache", "pnl_unavailable", "error"):
            with self.subTest(sc_result=sc_result):
                instance = self.optimizer(3)
                instance.best_alpha_id = "source_alpha"
                instance.best_stats = {"pc": 0.3}
                with patch.object(hill, "evaluate_margin_repair_readiness", return_value={
                    "non_margin_passed": True, "margin_passed": True,
                }), patch.object(hill, "_core_client"), \
                     patch.object(hill, "get_sc_check", return_value=sc_result), \
                     patch.object(hill, "PREFER_CATALOG_TEMPLATES", False), \
                     patch.object(hill, "select_template_candidates") as select, \
                     patch.object(hill, "post_multi_simulation") as post:
                    self.assertFalse(instance.run_template_exploration(
                        "source_alpha", Mock(tokens=[{"type": "data_field", "text": "field_a"}])
                    ))
                    select.assert_not_called()
                    post.assert_not_called()
                self.assertEqual(instance.template_pending_status, "PENDING_SC")
                self.assertIsNone(instance.best_stats["sc"])


if __name__ == "__main__":
    unittest.main()
