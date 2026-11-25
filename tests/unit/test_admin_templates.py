import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "代码" / "优化代码"))

from Core.factor import template_usage as usage
from Core.factor.templates import admin_distributed as admin
from Core.tools.forum_template_audit import classify_block


class AdminTemplatesTest(unittest.TestCase):
    def field(self, name, description="", dataset="analyst14"):
        return {"id": name, "description": description, "type": "MATRIX", "dataset_id": dataset}

    def test_pair_orientation_and_frequency(self):
        near, far = self.field("anl14_mean_eps_fy1"), self.field("anl14_mean_eps_fy2")
        self.assertEqual(admin.semantic_pair([far, near], "admin_term_pair"), (near, far))
        self.assertIsNone(admin.semantic_pair([near, self.field("anl14_mean_eps_fp2")], "admin_term_pair"))
        self.assertIsNone(admin.semantic_pair([near, self.field("anl14_mean_eps_fy2", dataset="analyst15")], "admin_term_pair"))
        self.assertIsNone(admin.semantic_pair([near, self.field("anl14_mean_revenue_fy2")], "admin_term_pair"))
        self.assertIsNone(admin.semantic_pair([self.field("random_a"), self.field("random_b")], "admin_dupont_pair"))

    def test_admin_priority_then_rotation_and_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            context = {"template_learning_version": usage.TEMPLATE_LEARNING_VERSION,
                       "prefer_admin_templates": True,
                       "region": "USA", "category": "ANALYST", "stage": 1,
                       "fields": [self.field("anl14_mean_eps_fy2", "analyst earnings estimate"),
                                  self.field("anl14_mean_eps_fy1", "analyst earnings estimate")],
                       "allowed_operators": {"group_zscore", "subtract", "winsorize", "ts_backfill", "group_mean", "ts_regression", "ts_rank", "rank", "ts_delta", "ts_mean", "ts_zscore"},
                       "usage_path": path}
            candidates = usage.select_template_candidates(context)
            self.assertEqual(candidates[0]["source_kind"], "ADMIN_DISTRIBUTED")
            term = next(c for c in candidates if c["template_id"] == "admin.term_structure")
            self.assertTrue(term["expression"].find("fy1") < term["expression"].find("fy2"))
            self.assertEqual(term["source_post_id"], "32092606398999")
            path.write_text(json.dumps({**context, "usage_path": None, "allowed_operators": [],
                                       "status": "PENDING", "template_id": term["template_id"],
                                       "candidate_key": "attempt1", "run_id": "run1"}, default=str) + "\n", encoding="utf-8")
            rotated = usage.select_template_candidates(context)
            self.assertNotEqual(rotated[0]["template_id"], term["template_id"])
            self.assertTrue(all(c.get("template_state") != "DISABLED_SCOPE" for c in rotated))
            context["allowed_operators"] = set()
            self.assertFalse(any(c["template_id"].startswith("admin.") for c in usage.select_template_candidates(context)))

    def test_implementations_are_low_complexity_and_no_forbidden_calls(self):
        examples = [admin.profit_to_size("profit", "assets"), admin.net_sentiment("positive", "negative"),
                    admin.term_structure("near", "far"), admin.dupont_difference("roe", "margin"),
                    admin.group_residual("score"), admin.group_beta("a", "b")]
        for expression in examples:
            self.assertLess(len(usage._CALL_PATTERN.findall(expression)), 6)
            self.assertLess(admin.operator_count(expression), 6)
            self.assertFalse(set(usage._operators(expression)) & {"trade_when", "add", "multiply"})
            self.assertTrue(usage.verify_alpha_expression(expression)["valid"], expression)
        self.assertGreaterEqual(admin.operator_count(admin.peg_relative_value("pe", "growth")), 6)
        self.assertFalse(next(e for e in usage.TEMPLATE_CANDIDATES if e["template_id"] == "admin.peg_relative_value")["enabled"])

    def test_static_exclusion_does_not_claim_bad_performance(self):
        self.assertEqual(classify_block("rank(x)")["status"], "UNVALIDATED")
        self.assertEqual(classify_block("trade_when(a,b,c)")["status"], "EXCLUDED_STATIC")
        self.assertTrue(any("跨数据集" in reason for reason in classify_block("mdl26_x / fnd6_y")["reasons"]))
        self.assertTrue(any("语法" in reason for reason in classify_block("ts_rank(x")["reasons"]))
