import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

RA = Path(__file__).parents[1] / "代码" / "优化代码" / "区分RA并标记"
sys.path.insert(0, str(RA))
import ra_daily_runtime as daily
import filter_ra_alphas_core as core


class DailyRuntimeTest(unittest.TestCase):
    def chunk(self, identity="batch1", status="COMPLETE"):
        return {"id": identity, "status": status, "completed_at": "2026-10-12T10:00:00+08:00",
                "results": [{"alpha_id": f"alpha{i}", "sharpe": 0.1, "fitness": 0.1, "margin": 0.0001, "turnover": 0.1} for i in range(8)]}

    def test_counts_observed_batches_only_and_deduplicates_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            good, pending, broken = self.chunk(), self.chunk("pending", "PENDING"), self.chunk("broken")
            broken["results"][0]["fitness"] = None
            for index in range(2):
                Path(directory, f"filter_ra_alphas_v6_state_{index}.json").write_text(json.dumps({"chunk_batches": [good, pending, broken]}), encoding="utf-8")
            now = datetime(2026, 10, 12, 12, tzinfo=ZoneInfo("Asia/Shanghai"))
            self.assertEqual(daily.completed_batches_today(directory, now), 1)
            self.assertEqual(daily.completed_batches_today(directory, now.replace(day=13)), 0)

    def test_eight_unique_alpha_ids_and_real_date_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            chunk = self.chunk()
            chunk["results"][1]["alpha_id"] = "alpha0"
            Path(directory, "filter_ra_alphas_v6_state_20261012.json").write_text(json.dumps({"chunk_batches": [chunk]}), encoding="utf-8")
            self.assertEqual(daily.completed_batches_today(directory, datetime(2026, 10, 12, 12, tzinfo=ZoneInfo("Asia/Shanghai"))), 0)

    def test_exception_leaves_pending_health_and_keeps_controlled_retry(self):
        module = Mock()
        run = Mock(side_effect=RuntimeError("no source"))
        with tempfile.TemporaryDirectory() as directory, patch.object(daily.time, "sleep", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            daily.keep_running(run, module, directory)
        run.assert_called_once_with(run_v5=True, run_v6=True)
        self.assertEqual(module._atomic_write_json.call_args.args[1]["status"], "PENDING_DAILY_TARGET")

    def test_core_read_only_recovery_rejects_duplicate_and_invalid_children(self):
        client = Mock()
        with patch.object(core, "get_core_client", return_value=client):
            for children in (["same"] * 8, [{}] * 8):
                client.get.return_value = Mock(status_code=200, json=Mock(return_value={"children": children}))
                self.assertEqual(core.recover_multi_simulation_core("/simulations/existing")["error"], "PENDING_CHILDREN")
        client.post.assert_not_called()
