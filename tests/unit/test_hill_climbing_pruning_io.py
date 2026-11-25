"""源 Alpha 剪枝的独立输入/输出契约测试；不登录、不创建回测。"""

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "代码" / "优化代码" / "爬山代码" / "hill_climbing" / "optimizer.py"
SPEC = importlib.util.spec_from_file_location("hill_climbing_pruning_io", SCRIPT)
hill = importlib.util.module_from_spec(SPEC)
with redirect_stdout(io.StringIO()):
    SPEC.loader.exec_module(hill)


def candidate(alpha_id, expression, sharpe, status="ELIGIBLE", decay=5):
    """构造与平台筛选完成后相同形状的最小候选记录。"""
    return {
        "alpha_id": alpha_id,
        "status": status,
        "expression": expression,
        "sharpe": sharpe,
        "fitness": 1.0,
        "date_created": "2026-08-24T12:00:00+08:00",
        "settings": {"decay": decay},
    }


class PruningInputOutputTest(unittest.TestCase):
    def run_prune(self, records, keep_num=1):
        state = hill._default_source_state()
        state["candidates"] = {record["alpha_id"]: record for record in records}
        with patch.object(hill, "append_source_event"):
            summary = hill.prune_source_queue(state, keep_num=keep_num)
        return state, summary

    def test_wrapper_sends_core_get_alphas_shape_and_restores_alpha_ids(self):
        records = [candidate("A", "rank(field_a)", 1.8, decay=10)]
        captured = []

        def fake_core_prune(core_records, **kwargs):
            captured.extend(core_records)
            self.assertEqual(kwargs, {"keep_num": 1, "field_ids": ["field_a"]})
            return [["rank(field_a)", 10]]

        state = hill._default_source_state()
        state["candidates"] = {"A": records[0]}
        with (
            patch.object(hill, "core_prune", side_effect=fake_core_prune),
            patch.object(hill, "append_source_event"),
        ):
            summary = hill.prune_source_queue(state, keep_num=1)

        self.assertEqual(captured[0][0:3], ["A", "rank(field_a)", 1.8])
        self.assertEqual(captured[0][-1], 10)
        self.assertEqual(summary, {"before": 1, "kept": 1, "pruned": 0, "field_ids": ["field_a"]})
        self.assertEqual(state["candidates"]["A"]["status"], "ELIGIBLE")

    def test_same_field_keeps_strongest_but_different_field_is_independent(self):
        state, summary = self.run_prune([
            candidate("best-a", "rank(field_a)", 1.8),
            candidate("weak-a", "zscore(field_a)", 1.2),
            candidate("only-b", "rank(field_b)", 1.1),
        ])

        self.assertEqual(summary["kept"], 2)
        self.assertEqual(state["candidates"]["best-a"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["weak-a"]["status"], "PRUNED_SIMILAR")
        self.assertEqual(state["candidates"]["only-b"]["status"], "ELIGIBLE")

    def test_identical_expression_keeps_one_best_candidate_per_sharpe_direction(self):
        state, summary = self.run_prune([
            candidate("positive-best", "rank(field_a)", 2.0),
            candidate("positive-weak", "rank(field_a)", 1.5),
            candidate("negative-best", "rank(field_a)", -3.0),
            candidate("negative-weak", "rank(field_a)", -1.0),
        ])

        self.assertEqual(summary["kept"], 2)
        self.assertEqual(state["candidates"]["positive-best"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["negative-best"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["positive-weak"]["status"], "PRUNED_SIMILAR")
        self.assertEqual(state["candidates"]["negative-weak"]["status"], "PRUNED_SIMILAR")

    def test_pruned_candidate_can_be_reconsidered_after_previous_best_leaves_queue(self):
        state, _ = self.run_prune([
            candidate("old-best", "rank(field_a)", 1.8),
            candidate("old-second", "zscore(field_a)", 1.4),
        ])
        state["candidates"]["old-best"]["status"] = "OPTIMIZED"

        with patch.object(hill, "append_source_event"):
            summary = hill.prune_source_queue(state, keep_num=1)

        self.assertEqual(summary["before"], 1)
        self.assertEqual(state["candidates"]["old-second"]["status"], "ELIGIBLE")

    def test_incomplete_records_do_not_enter_core_prune(self):
        state, summary = self.run_prune([
            candidate("valid", "rank(field_a)", 1.2),
            candidate("no-expression", "", 2.0),
            candidate("string-sharpe", "zscore(field_a)", "1.9"),
        ])

        self.assertEqual(summary["before"], 1)
        self.assertEqual(state["candidates"]["no-expression"]["status"], "ELIGIBLE")
        self.assertEqual(state["candidates"]["string-sharpe"]["status"], "ELIGIBLE")

    def test_pre_sc_prune_separates_candidates_by_cached_tower_scope(self):
        state = hill._default_source_state()
        first = candidate("model", "rank(field_a)", 1.8, status="PRE_SC_ELIGIBLE")
        second = candidate("analyst", "zscore(field_a)", 1.2, status="PRE_SC_ELIGIBLE")
        first["gap_scopes"] = [{"raw_scope": "GBR/D1/MODEL"}]
        second["gap_scopes"] = [{"raw_scope": "GBR/D1/ANALYST"}]
        state["candidates"] = {"model": first, "analyst": second}

        with patch.object(hill, "append_source_event"):
            summary = hill.prune_source_candidates_before_sc(state, keep_num=1)

        self.assertEqual(summary["groups"], 2)
        self.assertEqual(summary["kept"], 2)
        self.assertEqual(state["candidates"]["model"]["status"], "PRE_SC_ELIGIBLE")
        self.assertEqual(state["candidates"]["analyst"]["status"], "PRE_SC_ELIGIBLE")

    def test_run_output_directory_contains_date_time_and_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            result = hill.create_run_output_dir(
                directory, datetime(2026, 8, 24, 12, 34, 56), process_id=321,
            )

            self.assertEqual(
                Path(result).relative_to(directory).parts,
                ("2026-08-24", "12-34-56_321"),
            )
            self.assertTrue(Path(result).is_dir())


if __name__ == "__main__":
    unittest.main()
