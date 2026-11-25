import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import requests

import filter_ra_alphas_v3 as v3


class V3CorrelationStateTests(unittest.TestCase):
    def test_alpha_page_retries_proxy_error_then_succeeds(self):
        response = Mock(status_code=200)
        session = Mock()
        session.get.side_effect = [requests.exceptions.ProxyError("proxy disconnected"), response]
        with patch.object(v3.time, "sleep") as sleeper:
            result = v3.get_alpha_page_with_retry(session, "https://example.test", "day=1", max_retries=2)
        self.assertIs(result, response)
        sleeper.assert_called_once_with(v3.CONFIG_FETCH_RETRY_BASE_SECONDS)

    def test_alpha_page_returns_none_after_proxy_retries_exhausted(self):
        session = Mock()
        session.get.side_effect = requests.exceptions.ProxyError("proxy disconnected")
        with patch.object(v3.time, "sleep"):
            result = v3.get_alpha_page_with_retry(session, "https://example.test", "day=1", max_retries=2)
        self.assertIsNone(result)

    def test_threshold_is_strictly_greater_than_point_seven(self):
        self.assertFalse(v3.is_high_correlation(0.6999))
        self.assertFalse(v3.is_high_correlation(0.7))
        self.assertTrue(v3.is_high_correlation(0.7001))

    def test_terminal_tags_support_string_and_object_shapes(self):
        self.assertEqual(v3.terminal_high_tag(["Useful", "SC_IS_HIGHT"]), v3.SC_HIGH_TAG)
        self.assertEqual(v3.terminal_high_tag([{"name": "PC_IS_HIGHT"}]), v3.PC_HIGH_TAG)
        self.assertIsNone(v3.terminal_high_tag(["Useful"]))

    def test_alias_format_and_legacy_parse(self):
        self.assertEqual(v3.high_alias("SC", 0.81234), "SC 0.812")
        self.assertEqual(v3.high_alias("PC", 0.74567), "PC 0.746")
        self.assertEqual(v3.normal_alias(0.61234, 0.45678), "SC 0.612 PC 0.457")
        self.assertEqual(v3.parse_alias_value("SC=0.65 PC=0.72", "PC"), 0.72)
        self.assertEqual(v3.parse_alias_value("SC 0.812", "SC"), 0.812)

    def test_mark_platform_preserves_existing_tags(self):
        frame = pd.DataFrame([{
            "alpha_id": "alpha-1",
            "_tags": ["Existing", "Useful"],
            "Platform_Tags": "Existing, Useful",
            "Platform_Name": "old",
        }])
        with patch.object(v3, "set_alpha_properties", return_value=True) as setter:
            self.assertTrue(v3.mark_platform(None, frame, 0, v3.SC_HIGH_TAG, "SC 0.801"))
        setter.assert_called_once_with(
            None,
            "alpha-1",
            name="SC 0.801",
            tags=["Existing", "SC_IS_HIGHT"],
        )
        self.assertEqual(frame.at[0, "Platform_Tags"], "Existing, SC_IS_HIGHT")

    def test_both_high_tags_remove_useful(self):
        for high_tag in (v3.SC_HIGH_TAG, v3.PC_HIGH_TAG):
            with self.subTest(high_tag=high_tag):
                frame = pd.DataFrame([{
                    "alpha_id": "alpha-1",
                    "_tags": ["Useful", "KeepMe"],
                    "Platform_Tags": "Useful, KeepMe",
                    "Platform_Name": "old",
                }])
                with patch.object(v3, "set_alpha_properties", return_value=True):
                    v3.mark_platform(None, frame, 0, high_tag)
                self.assertEqual(frame.at[0, "Platform_Tags"], f"KeepMe, {high_tag}")

    def test_pc_network_error_reauthenticates_and_keeps_retrying(self):
        original_session = Mock()
        original_session.get.side_effect = requests.exceptions.ConnectionError("disconnected")
        valid_response = Mock(status_code=200, content=b"{}")
        valid_response.json.return_value = {"max": 0.68, "min": -0.12}
        refreshed_session = Mock()
        refreshed_session.get.return_value = valid_response

        with patch.object(v3, "get_session", return_value=refreshed_session) as login, patch.object(v3.time, "sleep") as sleeper:
            max_pc, min_pc, returned_session = v3.get_prod_correlation_stats_resilient(original_session, "alpha-1")

        self.assertEqual((max_pc, min_pc), (0.68, -0.12))
        self.assertIs(returned_session, refreshed_session)
        login.assert_called_once()
        sleeper.assert_called_once_with(2)

    def test_pc_empty_response_has_no_retry_limit(self):
        empty_response = Mock(status_code=200, content=b"")
        valid_response = Mock(status_code=200, content=b"{}")
        valid_response.json.return_value = {"max": 0.75, "min": -0.20}
        session = Mock()
        session.get.side_effect = [empty_response, empty_response, valid_response]

        with patch.object(v3.time, "sleep") as sleeper:
            max_pc, min_pc, returned_session = v3.get_prod_correlation_stats_resilient(session, "alpha-2")

        self.assertEqual((max_pc, min_pc), (0.75, -0.20))
        self.assertIs(returned_session, session)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [20, 30])

    def test_pc_retry_delay_is_capped_at_three_minutes(self):
        self.assertEqual(v3.pc_retry_wait(1), 2)
        self.assertEqual(v3.pc_retry_wait(20), 180)

    def test_pc_low_target_has_priority_over_max_count(self):
        with patch.object(v3, "CONFIG_PC_LOW_TARGET_COUNT", 2), patch.object(v3, "CONFIG_PC_MAX_COUNT", 150):
            self.assertIn("PC <", v3.get_pc_stop_reason(10, 2))
            self.assertIsNone(v3.get_pc_stop_reason(10, 1))
        with patch.object(v3, "CONFIG_PC_LOW_TARGET_COUNT", 5), patch.object(v3, "CONFIG_PC_MAX_COUNT", 3):
            self.assertIn("PC 上限", v3.get_pc_stop_reason(3, 1))

    def test_complete_excel_keeps_high_rows_and_restores_values(self):
        frame = pd.DataFrame([
            {
                "alpha_id": "sc-high",
                "self_correlation": 0.8123,
                "prod_correlation_max": None,
                "prod_correlation_min": None,
                "Platform_Name": "SC 0.812",
                "Processing_Status": "SC_IS_HIGHT",
            },
            {
                "alpha_id": "pc-high",
                "self_correlation": 0.6123,
                "prod_correlation_max": 0.7456,
                "prod_correlation_min": -0.123,
                "Platform_Name": "PC 0.746",
                "Processing_Status": "PC_IS_HIGHT",
            },
        ])
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            output_path = output_dir / "filtered_RAs_20260809.xlsx"
            v3.save_snapshot(frame, output_path)
            written = pd.read_excel(output_path, engine="openpyxl")
            self.assertEqual(len(written), 2)
            self.assertEqual(set(written["alpha_id_raw"]), {"sc-high", "pc-high"})
            self.assertEqual(set(written["Platform_Name"]), {"SC 0.812", "PC 0.746"})

            history = v3.load_excel_history(output_path)
            self.assertAlmostEqual(history["sc-high"]["self_correlation"], 0.8123)
            self.assertAlmostEqual(history["pc-high"]["prod_correlation_max"], 0.7456)
            self.assertAlmostEqual(history["pc-high"]["prod_correlation_min"], -0.123)

    def test_build_dataframe_marks_same_day_sc_and_pc_cache(self):
        alpha = {"id": "cached", "regular": {"code": "x"}, "settings": {}, "is": {}}
        history = {
            "cached": {
                "self_correlation": 0.41,
                "prod_correlation_max": 0.22,
                "prod_correlation_min": -0.11,
                "Platform_Name": "SC 0.410 PC 0.220",
                "Processing_Status": "COMPLETE",
                "PC_Status": "PASS",
            }
        }
        frame = v3.build_dataframe([alpha], history)
        self.assertTrue(frame.at[0, "_sc_cached"])
        self.assertTrue(frame.at[0, "_pc_cached"])
        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.410 PC 0.220")
        self.assertEqual(frame.at[0, "_history_processing_status"], "COMPLETE")

    def test_load_excel_history_ignores_previous_day_file(self):
        frame = pd.DataFrame([{
            "alpha_id": "old-day",
            "self_correlation": 0.51,
            "prod_correlation_max": 0.21,
            "prod_correlation_min": -0.10,
            "Platform_Name": "SC 0.510 PC 0.210",
        }])
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            old_path = output_dir / "filtered_RAs_20260808.xlsx"
            today_path = output_dir / "filtered_RAs_20260809.xlsx"
            v3.save_snapshot(frame, old_path)
            self.assertEqual(v3.load_excel_history(today_path), {})


if __name__ == "__main__":
    unittest.main()
