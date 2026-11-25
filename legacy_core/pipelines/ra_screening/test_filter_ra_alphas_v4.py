import unittest
from unittest.mock import Mock, patch

import filter_ra_alphas_v4 as v4


class V4CategoryTests(unittest.TestCase):
    def test_extract_expression_fields_excludes_helpers_and_operators(self):
        expression = (
            "group_zscore(ts_zscore(cashflow_op / split, 512) "
            "- ts_zscore(fnd23_annfvalld1_letq / current_ratio, 256), market)"
        )
        self.assertEqual(
            v4.extract_expression_fields(expression),
            ["cashflow_op", "fnd23_annfvalld1_letq", "current_ratio"],
        )

    def test_category_tags_are_plain_names(self):
        self.assertEqual(
            v4.category_tags(["Useful", "Model"], ["Fundamental", "Model"]),
            ["Useful", "Model", "Fundamental"],
        )

    def test_strict_low_excludes_equal_threshold_and_missing(self):
        self.assertTrue(v4.is_strictly_low(0.6999))
        self.assertFalse(v4.is_strictly_low(0.7))
        self.assertFalse(v4.is_strictly_low(None))

    def test_recent_alpha_has_lower_sort_key(self):
        import pandas as pd

        frame = pd.DataFrame([
            {"alpha_id": "old", "Date Created": "2026-08-08T00:00:00Z"},
            {"alpha_id": "new", "Date Created": "2026-08-09T00:00:00Z"},
        ])
        self.assertLess(v4.pc_priority_key(frame, 1), v4.pc_priority_key(frame, 0))

    def test_classification_uses_datafield_category(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {
            "results": [{
                "id": "avg_pct_change_estimate_quarter_revenue_7d",
                "dataset": {"id": "model26"},
                "category": {"id": "model", "name": "Model"},
            }]
        }
        session.get.return_value = response
        alpha = {
            "regular": {
                "code": "rank(avg_pct_change_estimate_quarter_revenue_7d)"
            },
            "settings": {
                "instrumentType": "EQUITY",
                "region": "EUR",
                "universe": "TOP2500",
                "delay": 1,
            },
        }
        categories, evidence, status = v4.classify_expression_categories(session, alpha)
        self.assertEqual(categories, ["Model"])
        self.assertEqual(evidence[0]["dataset"], "model26")
        self.assertEqual(status, "CATEGORY_MATCHED")


if __name__ == "__main__":
    unittest.main()
