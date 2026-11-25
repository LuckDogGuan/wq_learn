import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "代码" / "优化代码"))
from Core.factor.templates import forum_verified as catalog
from Core.tools.forum_template_audit import _local_checks, strict_unary
from Core.factor import template_usage as usage


class AdminCatalogTest(unittest.TestCase):
    def test_explicit_catalog_priority_runs_in_first_stage_before_old_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            _, allowed, _ = _local_checks()
            context = {"prefer_admin_templates": True, "prefer_catalog_templates": True,
                       "template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                       "region": "EUR", "category": "MODEL", "stage": 1,
                       "template_role": "SIGNAL_BUILD",
                       "fields": [{"id": "mdl110_value", "type": "MATRIX", "dataset_id": "model110"}],
                       "expression": "rank(mdl110_value)", "allowed_operators": allowed,
                       "usage_path": Path(directory) / "events.jsonl"}
            selected = usage.select_template_candidates(context, limit=64)
            self.assertGreaterEqual(len(selected), 8)
            self.assertTrue(all(item.get("catalog_status") == "LOCAL_PASS_UNVALIDATED" for item in selected[:8]))

    def test_classified_templates_cover_all_224_once(self):
        root = Path(catalog.__file__).parent / "forum_catalog" / "分类模板" / "待验证"
        files = list(root.glob("*/templates.json"))
        entries = [entry for file in files for entry in json.loads(file.read_text(encoding="utf-8"))["templates"]]
        self.assertEqual(len(files), 8)
        self.assertEqual(len(entries), 224)
        self.assertEqual(len({entry["template_id"] for entry in entries}), 224)
        loaded = {entry["template_id"]: entry for entry in catalog.load_verified_catalog()}
        self.assertEqual({entry["template_id"] for entry in entries}, set(loaded))
        for entry in entries:
            self.assertEqual(entry["formula"], loaded[entry["template_id"]]["formula"])
            self.assertEqual(entry["family"], loaded[entry["template_id"]]["family"])

    def test_explicit_overfit_failures_are_excluded_but_pending_is_not_failure(self):
        for record in ({"overfit_status": "FAIL"}, {"robust_status": "FAILED"},
                       {"checks": [{"name": "STRICT_OVERFIT", "result": "FAIL"}]}):
            self.assertTrue(usage._explicit_overfit_failure(record))
        for record in ({}, {"overfit_status": "PENDING"},
                       {"checks": [{"name": "ROBUST", "result": "PENDING"}]}):
            self.assertFalse(usage._explicit_overfit_failure(record))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            event = {"template_learning_version": usage.TEMPLATE_LEARNING_VERSION, "region": "EUR", "category": "MODEL",
                     "stage": 2, "template_id": "bad.overfit", "candidate_key": "alpha1", "status": "COMPLETE",
                     "candidate_origin": "FORMAL_TEMPLATE", "baseline_metrics_complete": True,
                     "result_metrics_complete": True, "gate_improved": True, "retained_previous_gates": True,
                     "checks": [{"name": "STRICT_OVERFIT", "result": "FAIL"}]}
            path.write_text(json.dumps(event), encoding="utf-8")
            row = usage.summarize_template_usage(path=path, summary_path=None)[0]
            self.assertEqual(row["template_state"], "DISABLED_SCOPE")
            self.assertEqual(row["disabled_reason"], "OVERFIT_OR_ROBUST_FAIL")

    def test_bad_templates_cannot_reenter_admin_rotation_even_if_recheck_due(self):
        with tempfile.TemporaryDirectory() as directory:
            context = {"prefer_admin_templates": True, "template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                       "region": "EUR", "category": "MODEL", "stage": 2,
                       "fields": [{"id": "mdl110_value", "type": "MATRIX", "dataset_id": "model110"}],
                       "expression": "rank(mdl110_value)", "allowed_operators": {"group_zscore"},
                       "usage_path": Path(directory) / "events.jsonl"}
            entry = next(item for item in usage.TEMPLATE_CANDIDATES if item["template_id"] == "fundamental.group_zscore")
            candidate = usage._make_candidate(usage._entry_for_stage(entry, 2), context, usage._usable_fields(context))
            for state in ("LOW_PRIORITY", "DISABLED_SCOPE", "MANUAL_DISABLED"):
                row = {"template_id": candidate["template_id"], "template_version": candidate["template_version"],
                       "variant_id": candidate["variant_id"], "template_state": state}
                with patch.object(usage, "TEMPLATE_CANDIDATES", (entry,)), \
                     patch.object(usage, "_variant_params", return_value=[entry["params"]]), \
                     patch.object(usage, "summarize_template_usage", return_value=[row]), \
                     patch.object(usage, "_low_recheck_context", return_value=(1, set())):
                    selected = usage.select_template_candidates(context, limit=256)
                self.assertFalse(any(item["template_id"] == candidate["template_id"] for item in selected), state)

    def test_entire_registered_catalog_passes_strict_local_validator(self):
        checked = catalog.load_verified_catalog()
        self.assertEqual(len(checked), 224)
        self.assertEqual(len({entry["template_id"] for entry in checked}), 224)
        verify, allowed, _ = _local_checks()
        for entry in checked:
            passed, reason = strict_unary({"raw_expression": entry["formula"]}, verify, allowed)
            self.assertIsNotNone(passed, (entry["template_id"], reason))
            self.assertLess(entry["total_operator_count"], 6)
            self.assertEqual(entry["status"], "LOCAL_PASS_UNVALIDATED")
        self.assertEqual(len(usage._VERIFIED_FORUM_ENTRIES), len(checked))

    def test_rotation_moves_used_templates_behind_unused_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            _, allowed, _ = _local_checks()
            context = {"prefer_admin_templates": True, "template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                       "region": "EUR", "category": "MODEL", "stage": 2,
                       "fields": [{"id": "mdl110_value", "type": "MATRIX", "dataset_id": "model110"}],
                       "expression": "rank(mdl110_value)", "allowed_operators": allowed,
                       "usage_path": Path(directory) / "events.jsonl"}
            with patch.object(usage, "TEMPLATE_CANDIDATES", usage._VERIFIED_FORUM_ENTRIES), \
                 patch.object(usage, "_shape_candidates", return_value=[]):
                before = usage.select_template_candidates(context, limit=5000)
                first = before[0]
                context["usage_path"].write_text(json.dumps({**first, "template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                    "region": "EUR", "category": "MODEL", "stage": 2, "candidate_key": "attempt1",
                    "status": "PENDING"}, default=str), encoding="utf-8")
                after = usage.select_template_candidates(context, limit=5000)
            self.assertNotEqual(after[0]["template_id"], first["template_id"])
            previous = next(item for item in after if item["template_id"] == first["template_id"])
            self.assertEqual(previous["template_attempt_count"], 1)
            self.assertNotEqual(previous["template_state"], "LOW_PRIORITY")

    def test_bad_domains_hidden_fields_and_unknown_operators_are_rejected(self):
        verify, allowed, _ = _local_checks()
        for expression in ("ts_mean({field},0)", "ts_mean({field},-5)", "ts_mean({field},1.5)",
                           "group_rank({field},3)", "ts_rank({field},industry)", "rank({field}+close)",
                           "made_up_op({field})", "trade_when(1,{field},-1)"):
            result, _ = strict_unary({"raw_expression": expression}, verify, allowed)
            self.assertIsNone(result, expression)

    def test_catalog_cannot_hide_existing_champion_with_identical_expression(self):
        with tempfile.TemporaryDirectory() as directory:
            context = {"prefer_admin_templates": True, "template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                       "region": "EUR", "category": "MODEL", "stage": 2,
                       "fields": [{"id": "mdl110_value", "type": "MATRIX", "dataset_id": "model110", "description": "model value score"}],
                       "expression": "rank(mdl110_value)", "allowed_operators": {"group_zscore"},
                       "usage_path": Path(directory) / "events.jsonl"}
            # 先定位旧注册项的函数版本，避免把未知结果当性能证据。
            entry = next(entry for entry in usage.TEMPLATE_CANDIDATES if entry["template_id"] == "fundamental.group_zscore")
            candidate = usage._make_candidate(usage._entry_for_stage(entry, 2), context, usage._usable_fields(context))
            events = [{**candidate, "template_learning_version": usage.TEMPLATE_LEARNING_VERSION, "region": "EUR", "category": "MODEL", "stage": 2,
                       "candidate_key": f"event{i}", "source_alpha_id": f"source{i % 4}", "status": "COMPLETE",
                       "baseline_metrics_complete": True, "result_metrics_complete": True,
                       "gate_improved": True, "retained_previous_gates": True, "target_improvement_value": 1.0} for i in range(8)]
            context["usage_path"].write_text("\n".join(json.dumps(event, default=str) for event in events), encoding="utf-8")
            selected = usage.select_template_candidates(context, limit=256)
            original = [item for item in selected if item["template_id"] == "fundamental.group_zscore"]
            self.assertTrue(original)
            self.assertEqual(original[0]["template_state"], "CHAMPION")
