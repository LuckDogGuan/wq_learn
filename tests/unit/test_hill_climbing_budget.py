import importlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path


HILL_ROOT = Path(__file__).resolve().parents[1] / "代码" / "优化代码" / "爬山代码"
OPTIMIZATION_ROOT = HILL_ROOT.parent
for path in (HILL_ROOT, OPTIMIZATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from hill_climbing.budget import (
    BEIJING_TZ,
    DailyBacktestBudget,
    DailyBacktestLimitReached,
)
from hill_climbing.config import DAILY_BACKTEST_LIMIT, DAILY_BACKTEST_RESET_HOUR

with redirect_stdout(io.StringIO()):
    hill = importlib.import_module("hill_climbing.optimizer")

_TEST_RUNTIME = tempfile.TemporaryDirectory()
hill.HILL_CLIMBING_SOURCE_DB_PATH = Path(_TEST_RUNTIME.name) / "source_state_v6.sqlite3"


class DailyBacktestBudgetTest(unittest.TestCase):
    def test_default_configuration(self):
        self.assertEqual(DAILY_BACKTEST_LIMIT, 3000)
        self.assertEqual(DAILY_BACKTEST_RESET_HOUR, 12)

    def test_reservation_persists_across_restart(self):
        now = datetime(2026, 8, 24, 11, 59, tzinfo=BEIJING_TZ)
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            first = DailyBacktestBudget(
                limit=10, reset_hour=12, state_path=state_path,
                now_func=lambda: now,
            )
            self.assertEqual(first.reserve(8)["remaining"], 2)

            restarted = DailyBacktestBudget(
                limit=10, reset_hour=12, state_path=state_path,
                now_func=lambda: now,
            )
            self.assertEqual(restarted.snapshot()["used"], 8)

    def test_limit_is_hard_and_failed_reservation_does_not_change_state(self):
        now = datetime(2026, 8, 24, 13, 0, tzinfo=BEIJING_TZ)
        with tempfile.TemporaryDirectory() as temp_dir:
            budget = DailyBacktestBudget(
                limit=10, reset_hour=12,
                state_path=Path(temp_dir) / "state.json",
                now_func=lambda: now,
            )
            budget.reserve(8)
            with self.assertRaises(DailyBacktestLimitReached) as caught:
                budget.reserve(3)
            self.assertEqual(caught.exception.snapshot["remaining"], 2)
            self.assertEqual(budget.snapshot()["used"], 8)

    def test_window_resets_at_beijing_noon(self):
        clock = [datetime(2026, 8, 24, 11, 59, tzinfo=BEIJING_TZ)]
        with tempfile.TemporaryDirectory() as temp_dir:
            budget = DailyBacktestBudget(
                limit=10, reset_hour=12,
                state_path=Path(temp_dir) / "state.json",
                now_func=lambda: clock[0],
            )
            budget.reserve(8)
            clock[0] = datetime(2026, 8, 24, 12, 0, tzinfo=BEIJING_TZ)
            snapshot = budget.snapshot()
            self.assertEqual(snapshot["used"], 0)
            self.assertEqual(snapshot["remaining"], 10)
            self.assertTrue(snapshot["window_started_at"].startswith("2026-08-24T12:00:00"))

    def test_account_post_cooldown_survives_restart_and_noon_reset(self):
        clock = [datetime(2026, 8, 24, 11, 59, tzinfo=BEIJING_TZ)]
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            budget = DailyBacktestBudget(
                limit=10, reset_hour=12, state_path=state_path,
                now_func=lambda: clock[0],
            )
            budget.record_post_rate_limit(300)
            clock[0] += timedelta(minutes=1)
            restarted = DailyBacktestBudget(
                limit=10, reset_hour=12, state_path=state_path,
                now_func=lambda: clock[0],
            )
            self.assertTrue(restarted.post_cooldown_snapshot()["active"])
            self.assertEqual(restarted.snapshot()["used"], 0)
            clock[0] += timedelta(minutes=5)
            self.assertFalse(restarted.post_cooldown_snapshot()["active"])

    def test_new_multi_simulation_reserves_expression_count_before_post(self):
        now = datetime(2026, 8, 24, 13, 0, tzinfo=BEIJING_TZ)
        with tempfile.TemporaryDirectory() as temp_dir:
            optimizer = hill.AsyncOptimizer.__new__(hill.AsyncOptimizer)
            optimizer.settings = {"region": "USA", "delay": 1}
            optimizer.backtest_budget = DailyBacktestBudget(
                limit=8, reset_hour=12,
                state_path=Path(temp_dir) / "state.json",
                now_func=lambda: now,
            )

            class Client:
                history = {}
                stop_requested = False

                @staticmethod
                def save_history():
                    return None

            optimizer.client = Client()
            expressions = [f"rank(field_{index})" for index in range(8)]
            valid = [{"valid": True} for _ in expressions]
            from unittest.mock import patch
            with (
                patch.object(hill, "batch_verify_expressions", return_value=valid),
                patch.object(hill, "post_multi_simulation", return_value=None) as post,
            ):
                optimizer.evaluate_batch(expressions)
                self.assertEqual(optimizer.backtest_budget.snapshot()["used"], 8)
                with self.assertRaises(DailyBacktestLimitReached):
                    optimizer.evaluate_batch([f"zscore(field_{index})" for index in range(8)])
                post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
