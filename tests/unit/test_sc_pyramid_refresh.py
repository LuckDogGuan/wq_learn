"""SC参考池与Pyramid统一刷新测试；全部Mock，不访问平台。"""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from Core.sim import sc_engine
from Core.sim import sc_pyramid_refresh as refresh


NOW = datetime(2026, 8, 24, 8, 0, tzinfo=timezone(timedelta(hours=8)))


def sc_report(status="NO_CHANGE", observed=None, cached=None, failed=None,
              cache_changed=False):
    return {
        "status": status,
        "reason": "" if status != "PENDING" else "OS Alpha列表不可观察",
        "observed_new_os_alpha_ids": observed or [],
        "cached_new_os_alpha_ids": cached or [],
        "failed_pnl_alpha_ids": failed or [],
        "cached_os_count": 12,
        "cache_changed": cache_changed,
    }


def diversity(check="PASS", count=12):
    return {"alphas": [{
        "region": "GBR", "delay": 1, "alphaCount": count,
        "dataCategory": {"id": "model", "name": "Model"},
        "dataDiversity": {"check": check, "limit": 0.3},
    }]}


class ScPyramidRefreshTest(unittest.TestCase):
    def run_refresh(self, state_path, **kwargs):
        return refresh.refresh_sc_pyramid_bundle(
            Mock(), state_path=state_path,
            cache_dir=state_path.parent / "cache", **kwargs,
        )

    def test_first_run_refreshes_pyramid_even_without_new_os_alpha(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with (
                patch.object(refresh, "_now", return_value=NOW),
                patch.object(refresh, "download_data_with_report", return_value=sc_report()) as sc_mock,
                patch.object(refresh, "get_user_diversity", return_value=diversity()) as tower_mock,
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["status"], "REFRESHED")
        self.assertEqual(result["pyramid_status"], "REFRESHED")
        sc_mock.assert_called_once()
        tower_mock.assert_called_once()

    def test_not_due_uses_saved_snapshot_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with (
                patch.object(refresh, "_now", return_value=NOW),
                patch.object(refresh, "download_data_with_report", return_value=sc_report()),
                patch.object(refresh, "get_user_diversity", return_value=diversity()),
            ):
                self.run_refresh(state_path)
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=1)),
                patch.object(refresh, "download_data_with_report") as sc_mock,
                patch.object(refresh, "get_user_diversity") as tower_mock,
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["status"], "NOT_DUE")
        self.assertEqual(result["diversity_payload"]["alphas"][0]["region"], "GBR")
        sc_mock.assert_not_called()
        tower_mock.assert_not_called()

    def test_due_without_new_os_alpha_does_not_refresh_pyramid(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=6)),
                patch.object(refresh, "download_data_with_report", return_value=sc_report()),
                patch.object(refresh, "get_user_diversity") as tower_mock,
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["status"], "REFRESHED")
        tower_mock.assert_not_called()

    def test_new_os_alpha_refreshes_tower_and_invalidates_memory_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            report = sc_report(
                status="REFRESHED", observed=["new1"], cached=["new1"],
                cache_changed=True,
            )
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=6)),
                patch.object(refresh, "download_data_with_report", return_value=report),
                patch.object(refresh, "get_user_diversity", return_value=diversity("PASS", 13)) as tower_mock,
                patch.object(refresh, "invalidate_cache") as invalidate_mock,
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["cached_new_os_alpha_ids"], ["new1"])
        tower_mock.assert_called_once()
        invalidate_mock.assert_called_once()

    def test_force_refreshes_sc_and_tower_before_six_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=1)),
                patch.object(refresh, "download_data_with_report", return_value=sc_report()) as sc_mock,
                patch.object(refresh, "get_user_diversity", return_value=diversity()) as tower_mock,
            ):
                self.run_refresh(state_path, force=True)

        sc_mock.assert_called_once()
        tower_mock.assert_called_once()

    def test_partial_pnl_still_refreshes_tower(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            report = sc_report(
                status="PARTIAL", observed=["good", "bad"], cached=["good"],
                failed=["bad"], cache_changed=True,
            )
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=6)),
                patch.object(refresh, "download_data_with_report", return_value=report),
                patch.object(refresh, "get_user_diversity", return_value=diversity()),
                patch.object(refresh, "invalidate_cache"),
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["failed_pnl_alpha_ids"], ["bad"])
        self.assertEqual(
            result["failed_pnl_retry_at"],
            (NOW + timedelta(hours=6, minutes=5)).isoformat(timespec="seconds"),
        )

    def test_partial_pnl_is_retried_without_postponing_six_hour_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            partial_at = NOW + timedelta(hours=6)
            partial_report = sc_report(
                status="PARTIAL", observed=["good", "bad"], cached=["good"],
                failed=["bad"], cache_changed=True,
            )
            recovered_report = sc_report(
                status="REFRESHED", observed=["bad"], cached=["bad"],
                cache_changed=True,
            )
            with (
                patch.object(refresh, "_now", return_value=partial_at),
                patch.object(refresh, "download_data_with_report", return_value=partial_report),
                patch.object(refresh, "get_user_diversity", return_value=diversity()),
                patch.object(refresh, "invalidate_cache"),
            ):
                self.run_refresh(state_path)

            with (
                patch.object(refresh, "_now", return_value=partial_at + timedelta(minutes=4)),
                patch.object(refresh, "download_data_with_report") as early_mock,
            ):
                early = self.run_refresh(state_path)

            with (
                patch.object(refresh, "_now", return_value=partial_at + timedelta(minutes=5)),
                patch.object(refresh, "download_data_with_report", return_value=recovered_report) as retry_mock,
                patch.object(refresh, "get_user_diversity") as tower_mock,
                patch.object(refresh, "invalidate_cache"),
            ):
                recovered = self.run_refresh(state_path)

        self.assertEqual(early["status"], "NOT_DUE")
        early_mock.assert_not_called()
        retry_mock.assert_called_once_with(
            unittest.mock.ANY, cache_dir=state_path.parent / "cache",
            flag_increment=True, retry_alpha_ids=["bad"],
        )
        tower_mock.assert_not_called()
        self.assertEqual(recovered["failed_pnl_alpha_ids"], [])
        self.assertIsNone(recovered["failed_pnl_retry_at"])
        self.assertEqual(
            recovered["next_due_at"],
            (partial_at + timedelta(hours=6)).isoformat(timespec="seconds"),
        )

    def test_legacy_partial_state_gets_quick_retry_without_waiting_six_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            state = refresh.load_sc_pyramid_refresh_state(state_path)
            state.update({
                "sc_status": "PARTIAL",
                "failed_pnl_alpha_ids": ["legacy-bad"],
                "failed_pnl_retry_at": None,
                "last_attempt_at": NOW.isoformat(timespec="seconds"),
            })
            refresh._save_state(state, state_path)
            report = sc_report(
                status="REFRESHED", observed=["legacy-bad"],
                cached=["legacy-bad"], cache_changed=True,
            )
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(minutes=5)),
                patch.object(refresh, "download_data_with_report", return_value=report) as retry_mock,
                patch.object(refresh, "get_user_diversity") as tower_mock,
                patch.object(refresh, "invalidate_cache"),
            ):
                result = self.run_refresh(state_path)

        retry_mock.assert_called_once()
        tower_mock.assert_not_called()
        self.assertEqual(result["failed_pnl_alpha_ids"], [])

    def test_pending_keeps_old_snapshot_and_waits_five_minutes(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            with (
                patch.object(refresh, "_now", return_value=NOW + timedelta(hours=6)),
                patch.object(refresh, "download_data_with_report", return_value=sc_report("PENDING")),
                patch.object(refresh, "get_user_diversity") as tower_mock,
            ):
                result = self.run_refresh(state_path)

        self.assertEqual(result["status"], "PENDING")
        self.assertTrue(result["diversity_payload"]["alphas"])
        self.assertEqual(
            result["retry_after"],
            (NOW + timedelta(hours=6, minutes=5)).isoformat(timespec="seconds"),
        )
        tower_mock.assert_not_called()

    def test_pyramid_failure_keeps_snapshot_and_retry_only_refreshes_pyramid(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self._bootstrap(state_path)
            report = sc_report(status="REFRESHED", observed=["new1"],
                               cached=["new1"], cache_changed=True)
            failed_at = NOW + timedelta(hours=6)
            with (
                patch.object(refresh, "_now", return_value=failed_at),
                patch.object(refresh, "download_data_with_report", return_value=report),
                patch.object(refresh, "get_user_diversity", return_value={}),
                patch.object(refresh, "invalidate_cache"),
            ):
                pending = self.run_refresh(state_path)

            with (
                patch.object(refresh, "_now", return_value=failed_at + timedelta(minutes=5)),
                patch.object(refresh, "download_data_with_report") as sc_mock,
                patch.object(refresh, "get_user_diversity", return_value=diversity("PASS", 13)) as tower_mock,
            ):
                recovered = self.run_refresh(state_path)

        self.assertEqual(pending["status"], "PENDING")
        self.assertEqual(pending["diversity_payload"]["alphas"][0]["alphaCount"], 12)
        self.assertEqual(recovered["status"], "REFRESHED")
        self.assertEqual(recovered["diversity_payload"]["alphas"][0]["alphaCount"], 13)
        sc_mock.assert_not_called()
        tower_mock.assert_called_once()

    def test_coverage_hash_ignores_alpha_count_but_tracks_pass_state(self):
        self.assertEqual(refresh._coverage_hash(diversity("PASS", 1)),
                         refresh._coverage_hash(diversity("PASS", 99)))
        self.assertNotEqual(refresh._coverage_hash(diversity("PASS", 1)),
                            refresh._coverage_hash(diversity("FAIL", 1)))

    def test_sc_refresh_report_does_not_rewrite_unchanged_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            ids = {"GBR": ["old"]}
            pnls = pd.DataFrame({"old": [1.0]}, index=["2026-01-01"])
            sc_engine._save_obj(ids, cache_dir / "os_alpha_ids")
            sc_engine._save_obj(pnls, cache_dir / "os_alpha_pnls")
            sc_engine._save_obj([], cache_dir / "ppac_alpha_ids")
            before = (cache_dir / "os_alpha_pnls.pickle").stat().st_mtime_ns

            with (
                patch.object(sc_engine, "_get_os_alphas_result", return_value=([], True)),
                patch.object(sc_engine, "_save_obj") as save_mock,
            ):
                report = sc_engine.download_data_with_report(Mock(), cache_dir)
            after = (cache_dir / "os_alpha_pnls.pickle").stat().st_mtime_ns

        self.assertEqual(report["status"], "NO_CHANGE")
        self.assertFalse(report["cache_changed"])
        self.assertEqual(before, after)
        save_mock.assert_not_called()

    def test_sc_refresh_report_distinguishes_observed_cached_and_failed_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            sc_engine._save_obj({"GBR": ["old"]}, cache_dir / "os_alpha_ids")
            old_pnls = pd.DataFrame({"old": [1.0]}, index=["2026-01-01"])
            sc_engine._save_obj(old_pnls, cache_dir / "os_alpha_pnls")
            sc_engine._save_obj([], cache_dir / "ppac_alpha_ids")
            observed = [
                {"id": "good", "settings": {"region": "GBR"}},
                {"id": "bad", "settings": {"region": "GBR"}},
            ]
            merged = pd.DataFrame(
                {"old": [1.0], "good": [2.0]}, index=["2026-01-01"]
            )
            with (
                patch.object(sc_engine, "_get_os_alphas_result", return_value=(observed, True)),
                patch.object(sc_engine, "get_alpha_pnls", return_value=({"GBR": ["old", "good"]}, merged)),
            ):
                report = sc_engine.download_data_with_report(Mock(), cache_dir)

        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["observed_new_os_alpha_ids"], ["good", "bad"])
        self.assertEqual(report["cached_new_os_alpha_ids"], ["good"])
        self.assertEqual(report["failed_pnl_alpha_ids"], ["bad"])

    def test_sc_refresh_list_failure_preserves_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            sc_engine._save_obj({"GBR": ["old"]}, cache_dir / "os_alpha_ids")
            sc_engine._save_obj(
                pd.DataFrame({"old": [1.0]}, index=["2026-01-01"]),
                cache_dir / "os_alpha_pnls",
            )
            sc_engine._save_obj([], cache_dir / "ppac_alpha_ids")
            with (
                patch.object(sc_engine, "_get_os_alphas_result", return_value=([], False)),
                patch.object(sc_engine, "_save_obj") as save_mock,
            ):
                report = sc_engine.download_data_with_report(Mock(), cache_dir)

        self.assertEqual(report["status"], "PENDING")
        self.assertEqual(report["cached_os_count"], 1)
        save_mock.assert_not_called()

    def test_incremental_os_list_pages_until_first_cached_alpha(self):
        first_page = [
            {"id": f"new-{index}", "settings": {"region": "GBR"}}
            for index in range(100)
        ]
        second_page = [
            {"id": "new-100", "settings": {"region": "GBR"}},
            {"id": "old", "settings": {"region": "GBR"}},
            {"id": "older", "settings": {"region": "GBR"}},
        ]
        responses = []
        extra_cached = {f"cached-{i}" for i in range(97)}
        second_page.extend({"id": alpha_id} for alpha_id in sorted(extra_cached))
        for results in (first_page, second_page):
            response = Mock(status_code=200)
            response.json.return_value = {"count": 203, "results": results}
            responses.append(response)
        client = Mock()
        client.get.side_effect = responses

        alphas, observed = sc_engine._get_os_alphas_result(
            client, limit=100, stop_at_ids={"old"} | extra_cached
        )

        self.assertTrue(observed)
        self.assertEqual(len(alphas), 102)
        self.assertEqual(alphas[-1]["id"], "older")
        self.assertEqual(client.get.call_count, 2)

    def test_incremental_os_list_recovers_missing_alpha_after_cached_one_on_same_page(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "count": 3,
            "results": [
                {"id": "new", "settings": {"region": "GBR"}},
                {"id": "old", "settings": {"region": "GBR"}},
                {"id": "previously-missed", "settings": {"region": "GBR"}},
            ],
        }
        client = Mock()
        client.get.return_value = response

        alphas, observed = sc_engine._get_os_alphas_result(
            client, limit=100, stop_at_ids={"old"}
        )

        self.assertTrue(observed)
        self.assertEqual([alpha["id"] for alpha in alphas], ["new", "previously-missed"])
        client.get.assert_called_once()

    def test_sc_passed_target_pnl_is_reused_without_remote_download(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            pnl = pd.DataFrame(
                {"Date": ["2026-01-01", "2026-01-02"], "pass1": [0.0, 1.0]}
            )
            details = {"settings": {"region": "GBR"}}
            with patch.object(sc_engine, "_get_alpha_pnl", return_value=pnl) as pnl_mock:
                value = sc_engine.calc_self_corr(
                    Mock(), "pass1", pd.DataFrame(), {}, alpha_result=details,
                    cache_pnl_below=0.5, cache_dir=cache_dir,
                )
            self.assertEqual(value, 0.0)
            pnl_mock.assert_called_once()

            with patch.object(
                sc_engine, "_get_alpha_pnl", side_effect=AssertionError("不应访问远端PnL")
            ) as pnl_mock:
                value = sc_engine.calc_self_corr(
                    Mock(), "pass1", pd.DataFrame(), {}, alpha_result=details,
                    cache_pnl_below=0.5, cache_dir=cache_dir,
                )

        self.assertEqual(value, 0.0)
        pnl_mock.assert_not_called()

    def test_sc_rejected_target_deletes_local_pnl(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            index = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
            target_pnl = pd.DataFrame({"reject1": [0.0, 1.0, 3.0, 6.0]}, index=index)
            sc_engine.save_target_pnl_cache("reject1", target_pnl, cache_dir)
            peer_rets = pd.DataFrame(
                {"peer": [float("nan"), 1.0, 2.0, 3.0]}, index=index
            )

            value = sc_engine.calc_self_corr(
                Mock(), "reject1", peer_rets, {"GBR": ["peer"]},
                alpha_result={"settings": {"region": "GBR"}},
                cache_pnl_below=0.5, cache_dir=cache_dir,
            )

            self.assertGreaterEqual(value, 0.5)
            self.assertTrue(
                sc_engine.load_target_pnl_cache("reject1", cache_dir).empty
            )

    def _bootstrap(self, state_path):
        with (
            patch.object(refresh, "_now", return_value=NOW),
            patch.object(refresh, "download_data_with_report", return_value=sc_report()),
            patch.object(refresh, "get_user_diversity", return_value=diversity()),
        ):
            self.run_refresh(state_path)


if __name__ == "__main__":
    unittest.main()
