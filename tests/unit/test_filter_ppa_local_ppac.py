import datetime
import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CORE_PARENT = ROOT / "legacy_core"
sys.path.insert(0, str(CORE_PARENT))

SCRIPT = CORE_PARENT / "pipelines" / "ppa_screening" / "filter_ppa_alphas.py"
SPEC = importlib.util.spec_from_file_location("filter_ppa_alphas_local", SCRIPT)
FILTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FILTER)

from Core.api.sim_api import set_alpha_properties
from Core.sim import sc_engine


class Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def __bool__(self):
        return True

    def json(self):
        return self._payload


class LocalPpaTests(unittest.TestCase):
    def setUp(self):
        # 测试指标/RA逻辑时不依赖用户当前区域与Universe配置。
        for name, value in (("TARGET_REGION", []), ("TARGET_UNIVERSE", [])):
            patcher = patch.object(FILTER, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_sparse_property_update(self):
        client = MagicMock()
        client.patch.return_value = Response(200)
        response = set_alpha_properties(client, "alpha1", name="PPC 0.4000", tags=["PPA"])
        self.assertEqual(response.status_code, 200)
        client.patch.assert_called_once_with(
            "/alphas/alpha1",
            json={"name": "PPC 0.4000", "tags": ["PPA"]},
        )

    def test_failed_pnl_does_not_enter_cache_ids(self):
        alphas = [
            {"id": "good", "settings": {"region": "GLB"}},
            {"id": "bad", "settings": {"region": "GLB"}},
        ]
        good_pnl = pd.DataFrame({"Date": ["2026-01-01", "2026-01-02"], "good": [1.0, 2.0]})
        with patch.object(sc_engine, "_get_alpha_pnl", side_effect=[good_pnl, RuntimeError("failed")]):
            ids, pnls = sc_engine.get_alpha_pnls(MagicMock(), alphas)
        self.assertEqual(ids["GLB"], ["good"])
        self.assertIn("good", pnls.columns)
        self.assertNotIn("bad", pnls.columns)

    def test_load_data_ignores_stale_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            pnls = pd.DataFrame(
                {"good": [1.0, 2.0]},
                index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
            )
            sc_engine._save_obj({"GLB": ["good", "missing"]}, cache_dir / "os_alpha_ids")
            sc_engine._save_obj(pnls, cache_dir / "os_alpha_pnls")
            sc_engine._save_obj(["good", "missing"], cache_dir / "ppac_alpha_ids")
            ids, rets = sc_engine.load_data(cache_dir, tag="PPAC")
        self.assertEqual(ids, {"GLB": ["good"]})
        self.assertEqual(list(rets.columns), ["good"])

    def test_refresh_ppac_data_refreshes_once(self):
        expected = ({"GLB": ["peer"]}, pd.DataFrame({"peer": [1.0]}))
        with patch.object(sc_engine, "download_data_with_report") as download, patch.object(
            sc_engine, "load_ppac_data", return_value=expected
        ) as load:
            actual = sc_engine.refresh_ppac_data(MagicMock(), flag_increment=True)
        self.assertIs(actual, expected)
        download.assert_called_once()
        load.assert_called_once()

    def test_refresh_ppac_data_can_return_added_count_report(self):
        expected = ({"GLB": ["peer"]}, pd.DataFrame({"peer": [1.0]}))
        report = {
            "status": "REFRESHED",
            "observed_new_os_alpha_ids": ["peer"],
            "cached_new_os_alpha_ids": ["peer"],
            "failed_pnl_alpha_ids": [],
            "cached_os_count": 63,
        }
        with patch.object(
            sc_engine, "download_data_with_report", return_value=report
        ), patch.object(sc_engine, "load_ppac_data", return_value=expected):
            actual = sc_engine.refresh_ppac_data(
                MagicMock(), flag_increment=True, return_report=True
            )
        self.assertEqual(actual[0:2], expected)
        self.assertIs(actual[2], report)

    def test_calc_ppac_returns_nan_without_valid_overlap(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
        target_pnl = pd.DataFrame({"target": [1.0, 2.0, 3.0]}, index=dates)
        peer_rets = pd.DataFrame({"peer": [math.nan, math.nan, math.nan]}, index=dates)
        value = sc_engine.calc_ppac(
            MagicMock(),
            "target",
            peer_rets,
            {"GLB": ["peer"]},
            alpha_result={"id": "target", "settings": {"region": "GLB"}},
            alpha_pnls=target_pnl,
        )
        self.assertTrue(math.isnan(value))

    def test_calc_ppac_returns_zero_without_region_peers(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
        target_pnl = pd.DataFrame({"target": [1.0, 2.0, 3.0]}, index=dates)
        client = MagicMock()
        value = sc_engine.calc_ppac(
            client,
            "target",
            pd.DataFrame(index=dates),
            {"GLB": []},
            alpha_result={"id": "target", "settings": {"region": "GLB"}},
            alpha_pnls=target_pnl,
        )
        self.assertEqual(value, 0.0)
        client.get.assert_not_called()

    def test_local_result_marking_boundaries_and_pending(self):
        alpha = {"id": "alpha1", "tags": ["MANUAL", "PPA"]}
        with patch.object(FILTER, "set_alpha_properties", return_value=Response(200)) as update:
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.4), "PPA_PASS")
            self.assertEqual(update.call_args.kwargs["tags"], ["MANUAL", "PPA"])
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.5), "PPC_HIGH")
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.6), "PPC_HIGH")
            self.assertEqual(update.call_args.kwargs["tags"], ["MANUAL", "PPC_IS_HIGHT"])
            update.reset_mock()
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, float("nan")), "PENDING")
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, "no_cache"), "PENDING")
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, "error"), "PENDING")
            update.assert_not_called()

    def test_low_ppac_adds_exact_field_categories_as_tags(self):
        alpha = {
            "id": "alpha1",
            "tags": ["MANUAL"],
            "regular": {"code": "rank(foo_field)"},
            "settings": {"region": "GLB", "universe": "TOPDIV3000", "delay": 1},
        }
        fields = pd.DataFrame([{
            "id": "foo_field",
            "category": {"id": "analyst", "name": "Analyst"},
        }])
        with patch.object(FILTER, "get_datafields", return_value=fields) as get_fields, patch.object(
            FILTER, "set_alpha_properties", return_value=Response(200)
        ) as update:
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.39), "PPA_PASS")
        get_fields.assert_called_once()
        self.assertEqual(update.call_args.kwargs["tags"], ["MANUAL", "PPA", "Analyst"])

    def test_ppac_boundary_does_not_query_categories(self):
        alpha = {"id": "alpha1", "tags": ["MANUAL"]}
        with patch.object(FILTER, "get_datafields") as get_fields, patch.object(
            FILTER, "set_alpha_properties", return_value=Response(200)
        ) as update:
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.4), "PPA_PASS")
        get_fields.assert_not_called()
        self.assertEqual(update.call_args.kwargs["tags"], ["MANUAL", "PPA"])

    def test_property_write_failure_is_not_pass(self):
        alpha = {"id": "alpha1", "tags": []}
        with patch.object(FILTER, "set_alpha_properties", return_value=Response(500)):
            self.assertEqual(FILTER.apply_ppac_result(MagicMock(), alpha, 0.4), "WRITE_FAILED")

    def test_beijing_window_is_half_open_thirty_days(self):
        now = datetime.datetime(2026, 8, 20, 17, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
        start, end = FILTER.beijing_date_window(now)
        self.assertEqual(start.isoformat(), "2026-07-22T00:00:00+08:00")
        self.assertEqual(end.isoformat(), "2026-08-21T00:00:00+08:00")
        self.assertEqual((end - start).days, 30)

    def test_candidate_fetch_never_uses_power_pool_endpoint(self):
        client = MagicMock()
        client.get.return_value = Response(200, {"results": [], "count": 0})
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            FILTER, "CACHE_DIR", Path(temp_dir)
        ):
            FILTER.fetch_recent_alphas(client)
        urls = [call.args[0] for call in client.get.call_args_list]
        self.assertTrue(urls)
        self.assertFalse(any("correlations/power-pool" in url for url in urls))

    def test_incomplete_pagination_does_not_return_partial_candidates(self):
        client = MagicMock()
        client.get.side_effect = [
            Response(200, {"results": [{"id": str(i)} for i in range(100)], "count": 101}),
            Response(500),
        ]
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            FILTER, "CACHE_DIR", Path(temp_dir)
        ), self.assertRaisesRegex(RuntimeError, "结果未完整观测"):
            FILTER.fetch_recent_alphas(client)

    def test_ra_and_warning_filter_compatibility(self):
        original_exclude_ra = FILTER.EXCLUDE_REGULAR_RA
        original_patterns = FILTER.PPC_EXCLUDED_WARNING_PATTERNS
        try:
            regular_ra = {
                "id": "ra1",
                "settings": {},
                "is": {
                    "checks": [],
                    "sharpe": 1.4,
                    "fitness": 1.0,
                    "margin": 0.0009,
                },
                "tags": [],
            }
            FILTER.EXCLUDE_REGULAR_RA = False
            candidates, counters = FILTER.filter_candidates(MagicMock(), [regular_ra])
            self.assertEqual([item["id"] for item in candidates], ["ra1"])
            self.assertEqual(counters["ra_retained"], 1)

            FILTER.EXCLUDE_REGULAR_RA = True
            candidates, counters = FILTER.filter_candidates(MagicMock(), [regular_ra])
            self.assertEqual(candidates, [])
            self.assertEqual(counters["ra_dropped"], 1)

            FILTER.EXCLUDE_REGULAR_RA = False
            FILTER.PPC_EXCLUDED_WARNING_PATTERNS = ["High Turnover"]
            warned = {
                "id": "warn1",
                "settings": {},
                "tags": ["PPA", "MANUAL"],
                "is": {
                    "checks": [{"name": "HIGH_TURNOVER", "result": "WARNING"}],
                    "sharpe": 1.4,
                    "fitness": 1.0,
                    "margin": 0.0009,
                },
            }
            with patch.object(FILTER, "set_alpha_properties", return_value=Response(200)) as update:
                candidates, counters = FILTER.filter_candidates(MagicMock(), [warned])
            self.assertEqual(candidates, [])
            self.assertEqual(counters["warning"], 1)
            self.assertEqual(update.call_args.kwargs["tags"], ["MANUAL"])
        finally:
            FILTER.EXCLUDE_REGULAR_RA = original_exclude_ra
            FILTER.PPC_EXCLUDED_WARNING_PATTERNS = original_patterns

    def test_cached_candidates_apply_metric_filters_without_mutating_cache_data(self):
        original = (FILTER.FILTER_SHARPE, FILTER.FILTER_FITNESS, FILTER.FILTER_MARGIN)
        try:
            FILTER.FILTER_SHARPE = 1.4
            FILTER.FILTER_FITNESS = 1
            FILTER.FILTER_MARGIN = 8
            alphas = [
                {"id": "pass", "settings": {}, "is": {"sharpe": 1.4, "fitness": 1, "margin": 0.00081}, "tags": []},
                {"id": "low-sharpe", "settings": {}, "is": {"sharpe": 1.39, "fitness": 2, "margin": 0.01}, "tags": []},
                {"id": "low-fitness", "settings": {}, "is": {"sharpe": 2, "fitness": 0.99, "margin": 0.01}, "tags": []},
                {"id": "low-margin", "settings": {}, "is": {"sharpe": 2, "fitness": 2, "margin": 0.0008}, "tags": []},
            ]
            candidates, counters = FILTER.filter_candidates(MagicMock(), alphas)
            self.assertEqual([alpha["id"] for alpha in candidates], ["pass"])
            self.assertEqual(counters["sharpe"], 1)
            self.assertEqual(counters["fitness"], 1)
            self.assertEqual(counters["margin"], 1)
            self.assertEqual(alphas[1]["is"]["sharpe"], 1.39)
        finally:
            FILTER.FILTER_SHARPE, FILTER.FILTER_FITNESS, FILTER.FILTER_MARGIN = original


if __name__ == "__main__":
    unittest.main()
