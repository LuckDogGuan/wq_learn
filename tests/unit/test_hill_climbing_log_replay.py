import tempfile
import unittest
from pathlib import Path

from testFile.hill_climbing_log_replay import replay


class HillClimbingLogReplayTest(unittest.TestCase):
    def test_replay_collapses_repeated_incomplete_source_and_computes_objective(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source_a_hill_climbing_v4.7.log").write_text(
                "首次提交 Multi-Simulation\n"
                "回测额度已预扣 8\n"
                "DEFERRED_INCOMPLETE_BATCH: 7/8\n"
                "DEFERRED_INCOMPLETE_BATCH: 7/8\n"
                "阶段=1 门槛=PENDING\n"
                "阶段=1 门槛=PASS\n"
                "阶段=1 门槛=FAIL\n"
                "[阶段门槛未通过] missing=['sc'] failed=['margin_bp<=3']\n"
                "TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'\n"
                "阶段=3 门槛=PASS\n",
                encoding="utf-8",
            )
            result = replay(root)
        self.assertEqual(result["parent_batches"], 1)
        self.assertEqual(result["incomplete_7_of_8_sources"], 1)
        self.assertEqual(result["projected_eliminated_7_of_8_reschedules"], 1)
        self.assertEqual(result["stage3_full_pass_per_1000_backtests"], 125.0)
        self.assertAlmostEqual(result["stage1_all_result_pass_rate"], 1 / 3)
        self.assertEqual(result["stage1_observable_pass_rate"], 0.5)
        self.assertEqual(result["stage1_margin_ready_records"], 1)
        self.assertEqual(result["python_none_exceptions"], 1)


if __name__ == "__main__":
    unittest.main()
