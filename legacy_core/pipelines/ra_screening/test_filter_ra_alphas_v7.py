import unittest
from unittest.mock import call, patch

import filter_ra_alphas_v7 as v7


class V7WorkflowTests(unittest.TestCase):
    @patch.object(v7.core, "run_stage_file")
    def test_v7_runs_v5_then_v6_through_core_only(self, run_stage):
        v7.run_job(run_v5=True, run_v6=True)
        self.assertEqual(run_stage.call_args_list, [
            call("filter_ra_alphas_v5.py"),
            call("filter_ra_alphas_v6.py"),
        ])

    @patch.object(v7.core, "run_stage_file")
    def test_v7_can_use_latest_v5_output(self, run_stage):
        v7.run_job(run_v5=False, run_v6=True)
        run_stage.assert_called_once_with("filter_ra_alphas_v6.py")

    @patch.object(v7.core.runpy, "run_path")
    def test_core_stage_runner_uses_file_settings_entry(self, run_path):
        configured = unittest.mock.Mock()
        plain = unittest.mock.Mock()
        run_path.return_value = {
            "run_job": plain,
            "run_from_file_settings": configured,
        }
        v7.core.run_stage_file("filter_ra_alphas_v6.py")
        configured.assert_called_once_with()
        plain.assert_not_called()


if __name__ == "__main__":
    unittest.main()
