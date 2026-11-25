import unittest
import pickle
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, Mock, patch

import pandas as pd
import requests

import filter_ra_alphas_core as core
import filter_ra_alphas_v5 as v5


class V5AliasTests(unittest.TestCase):
    def test_login_retries_transient_tls_error(self):
        session = Mock()
        session.post.side_effect = [
            requests.exceptions.SSLError("temporary TLS EOF"),
            Mock(status_code=201),
        ]
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text("username: user\npassword: pass\n", encoding="utf-8")
            with (
                patch.object(core, "resolve_config_path", return_value=config),
                patch.object(core.requests, "Session", return_value=session),
                patch.object(core.time, "sleep") as sleep,
            ):
                result = core.get_session()

        self.assertIs(result, session)
        self.assertEqual(session.post.call_count, 2)
        sleep.assert_called_once_with(core.CONFIG_AUTH_RETRY_BASE_SECONDS)

    def test_server_useful_audit_repairs_high_name_and_removes_basic_failure(self):
        alphas = [
            {
                "id": "pc-high", "name": "SC 0.531 PC 0.905",
                "tags": [core.USEFUL_TAG, "Model"],
                "dateCreated": pd.Timestamp.now(tz="UTC").isoformat(),
                "is": {"sharpe": 1.85, "fitness": 1.51, "margin": 0.0015, "checks": []},
            },
            {
                "id": "weak", "name": "SC 0.000",
                "tags": [core.USEFUL_TAG],
                "dateCreated": pd.Timestamp.now(tz="UTC").isoformat(),
                "is": {"sharpe": 1.23, "fitness": 1.3, "margin": 0.0035, "checks": []},
            },
        ]
        with (
            patch.object(v5, "_server_useful_alphas", side_effect=[alphas, []]),
            patch.object(core, "set_alpha_properties", return_value=True) as update,
        ):
            result = v5.audit_server_useful(Mock())

        self.assertEqual(result, [])
        self.assertEqual(update.call_count, 2)
        update.assert_any_call(
            ANY, "pc-high", name="SC 0.531 PC 0.905",
            tags=["Model", core.PC_HIGH_TAG],
        )
        update.assert_any_call(ANY, "weak", tags=[])

    def test_server_useful_audit_keeps_low_name_without_complete_remote_pc(self):
        alpha = {
            "id": "pending", "name": "SC 0.200 PC 0.600",
            "tags": [core.USEFUL_TAG],
            "dateCreated": pd.Timestamp.now(tz="UTC").isoformat(),
            "is": {"sharpe": 1.8, "fitness": 1.2, "margin": 0.001, "checks": []},
        }
        with (
            patch.object(v5, "_server_useful_alphas", side_effect=[[alpha], [alpha]]),
            patch.object(core, "set_alpha_properties") as update,
        ):
            result = v5.audit_server_useful(Mock())

        self.assertEqual(result, [alpha])
        update.assert_not_called()

    def test_server_useful_audit_removes_useful_when_terminal_tag_already_exists(self):
        alpha = {
            "id": "mixed", "name": "SC 0.200",
            "tags": [core.USEFUL_TAG, core.PC_HIGH_TAG, "Model"],
            "dateCreated": pd.Timestamp.now(tz="UTC").isoformat(),
            "is": {"sharpe": 1.8, "fitness": 1.2, "margin": 0.001, "checks": []},
        }
        with (
            patch.object(v5, "_server_useful_alphas", side_effect=[[alpha], []]),
            patch.object(core, "set_alpha_properties", return_value=True) as update,
        ):
            v5.audit_server_useful(Mock())

        update.assert_called_once_with(
            ANY, "mixed", name="SC 0.200", tags=["Model", core.PC_HIGH_TAG]
        )

    def test_stale_cached_useful_is_not_used_for_excluded_patch(self):
        cached = {"id": "stale", "tags": [core.USEFUL_TAG, "OldTag"]}
        with patch.object(core, "remove_useful_tag_if_present") as remove:
            v5.remove_excluded_usefuls(
                Mock(), [(cached, "FAIL_COUNT=1")], live_useful_by_id={}
            )
        remove.assert_not_called()

    def test_cached_high_pc_retries_terminal_tag_and_complete_alias(self):
        frame = pd.DataFrame([{
            "alpha_id": "abc123", "_tags": ["Useful"],
            "self_correlation": 0.1234, "prod_correlation_max": 0.8768,
            "prod_correlation_min": None,
            "Platform_Name": "SC 0.123", "Platform_Tags": "Useful",
            "Platform_Update_Status": "PENDING_PLATFORM_RATE_LIMIT",
            "PC_Status": "PENDING_PC", "Processing_Status": "READY_FOR_PC",
        }])

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertFalse(v5._apply_pc_state(Mock(), frame, 0, {"abc123": {}}))

        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.123 PC 0.877")
        self.assertEqual(frame.at[0, "Platform_Tags"], "PC_IS_HIGHT")
        self.assertEqual(frame.at[0, "PC_Status"], "PC_IS_HIGHT")
        self.assertEqual(frame.at[0, "Processing_Status"], "PC_IS_HIGHT")
        update.assert_called_once_with(
            ANY, "abc123", name="SC 0.123 PC 0.877", tags=["PC_IS_HIGHT"]
        )

    def test_absolute_value_drives_sc_and_pc_high_state(self):
        self.assertTrue(core.is_high_correlation(-0.701))
        self.assertFalse(core.is_high_correlation(-0.700))
        self.assertTrue(core.is_correlation_pass(0.700))
        self.assertTrue(core.is_complete_low_pc(0.700, -0.700))
        self.assertTrue(core.is_high_pc(0.21, -0.745))
        self.assertFalse(core.is_complete_low_pc(0.21, -0.701))

    def test_partial_pc_with_high_min_is_terminal(self):
        frame = pd.DataFrame([{
            "alpha_id": "pc-min-high", "_tags": ["Useful"],
            "self_correlation": 0.1234, "prod_correlation_max": None,
            "prod_correlation_min": -0.812,
            "Platform_Name": "SC 0.123", "Platform_Tags": "Useful",
        }])

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertFalse(v5._apply_pc_state(Mock(), frame, 0, {"pc-min-high": {}}))

        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.123 PC 0.812")
        self.assertEqual(frame.at[0, "PC_Status"], "PC_IS_HIGHT")
        update.assert_called_once_with(
            ANY, "pc-min-high", name="SC 0.123 PC 0.812", tags=["PC_IS_HIGHT"]
        )

    def test_pc_alias_uses_one_absolute_value_from_two_raw_values(self):
        self.assertEqual(core.pc_alias_value(0.61, -0.745), 0.745)
        self.assertEqual(core.normal_alias(0.123, -0.745), "SC 0.123 PC 0.745")
        self.assertEqual(
            core.partial_alias("SC 0.123 PC -0.700", "SC", 0.234),
            "SC 0.234 PC 0.700",
        )

    def test_warning_exclusion_rules_are_extensible(self):
        alpha = {
            "id": "j26nxAxj",
            "is": {"checks": [{
                "name": "CONCENTRATED_WEIGHT",
                "result": "WARNING",
            }]},
        }
        matches = core.find_warning_exclusions(alpha)
        self.assertEqual([match["code"] for match in matches], ["CONCENTRATED_WEIGHT"])
        self.assertEqual(core.find_warning_exclusions({"is": {"checks": []}}), [])

        sharpe_warning = {
            "id": "VkGkPEWM",
            "is": {"checks": [{
                "result": "WARNING",
                "name": "LOW_2Y_SHARPE",
                "message": "[2 year Sharpe](https://support.worldquantbrain.com/hc/en-us/articles/20251383456663) of 1.22 is below cutoff of 1.58.",
            }]},
        }
        self.assertEqual(
            [match["code"] for match in core.find_warning_exclusions(sharpe_warning)],
            ["SHARPE_BELOW_CUTOFF"],
        )

        ladder_sharpe_warning = {
            "id": "P0ObaGdp",
            "is": {"checks": [{
                "result": "WARNING",
                "name": "IS_LADDER_SHARPE",
                "message": (
                    "IS ladder Sharpe of 1.38 is below cutoff of 1.58 "
                    "for ladder year 2: 1/1/2024…1/2/2022."
                ),
            }]},
        }
        self.assertEqual(
            [match["code"] for match in core.find_warning_exclusions(ladder_sharpe_warning)],
            ["IS_LADDER_SHARPE"],
        )

    def test_excluded_alpha_removes_useful_tag_but_keeps_other_tags(self):
        alpha = {"id": "excluded1", "tags": ["Useful", "Submit", "Model"]}
        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertTrue(core.remove_useful_tag_if_present(Mock(), alpha, "FAIL_COUNT=1"))
        update.assert_called_once_with(ANY, "excluded1", tags=["Model"])

    def test_excluded_alpha_without_useful_tag_skips_platform_update(self):
        alpha = {"id": "excluded2", "tags": ["Model"]}
        with patch.object(core, "set_alpha_properties") as update:
            self.assertTrue(core.remove_useful_tag_if_present(Mock(), alpha, "WARNING=TEST"))
        update.assert_not_called()

    def test_warning_excluded_rows_are_removed_from_output(self):
        frame = pd.DataFrame([
            {"alpha_id": "=HYPERLINK(\"https://platform.worldquantbrain.com/alpha/j26nxAxj\",\"j26nxAxj\")",
             "alpha_id_raw": "j26nxAxj", "Processing_Status": "EXCLUDED_WARNING"},
            {"alpha_id": "keep1", "alpha_id_raw": "keep1", "Processing_Status": "COMPLETE"},
        ])
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            frame.to_excel(output, index=False)
            removed = v5.remove_excluded_rows_from_output(output, {"j26nxAxj"})
            result = pd.read_excel(output)
        self.assertEqual(removed, 1)
        self.assertEqual(result["alpha_id_raw"].tolist(), ["keep1"])

    def test_platform_429_enters_run_level_circuit_breaker(self):
        core.reset_platform_update_state()
        session = Mock()
        session.patch.return_value = Mock(status_code=429)
        with patch.object(core.time, "sleep"):
            self.assertFalse(core.set_alpha_properties(session, "rate1", name="SC 0.100"))
            self.assertEqual(core.platform_update_status(), "RATE_LIMITED")
            self.assertFalse(core.set_alpha_properties(session, "rate2", name="SC 0.200"))
            self.assertEqual(core.platform_update_status(), "SKIPPED_RATE_LIMIT")
        self.assertEqual(session.patch.call_count, core.CONFIG_PLATFORM_UPDATE_MAX_RETRIES)
        core.reset_platform_update_state()

    def test_platform_update_retries_three_times(self):
        session = Mock()
        response = Mock(status_code=200)
        session.patch.side_effect = [requests.ConnectionError("temporary"), response]
        with patch.object(core.time, "sleep") as sleep:
            self.assertTrue(core.set_alpha_properties(session, "abc123", name="SC 0.100"))
        self.assertEqual(session.patch.call_count, 2)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(sleep.call_args_list[0].args, (core.CONFIG_PLATFORM_UPDATE_DELAY_SECONDS,))

    def test_pc_empty_response_has_finite_retries(self):
        session = Mock()
        response = Mock(status_code=200, content=b"")
        session.get.return_value = response
        with patch.object(core, "CONFIG_PC_MAX_RETRIES", 3), patch.object(core.time, "sleep") as sleep:
            result = core.get_prod_correlation_stats_resilient(session, "pc_pending")
        self.assertEqual(result[:2], (None, None))
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [20, 40])

    def test_pc_response_with_only_high_min_is_terminal_result(self):
        session = Mock()
        response = Mock(status_code=200, content=b'{"min": -0.812}')
        response.json.return_value = {"min": -0.812}
        session.get.return_value = response

        result = core.get_prod_correlation_stats_resilient(session, "pc-min-high")

        self.assertEqual(result[:2], (None, -0.812))

    def test_partial_alias_preserves_the_other_correlation(self):
        self.assertEqual(
            core.partial_alias("SC 0.123 PC 0.456", "SC", 0.234),
            "SC 0.234 PC 0.456",
        )
        self.assertEqual(
            core.partial_alias("SC 0.234 PC 0.456", "PC", 0.567),
            "SC 0.234 PC 0.567",
        )
        self.assertEqual(core.partial_alias("", "SC", 0.234), "SC 0.234")

    def test_build_dataframe_restores_sc_pc_from_platform_alias(self):
        frame = core.build_dataframe([{
            "id": "alias-high",
            "name": "SC 0.812 PC 0.901",
            "tags": ["Useful"],
            "regular": {"code": "rank(field_a)"},
            "settings": {"region": "EUR", "universe": "TOP2500", "delay": 1},
        }], {})

        self.assertEqual(frame.at[0, "self_correlation"], 0.812)
        self.assertEqual(frame.at[0, "prod_correlation_max"], 0.901)
        self.assertTrue(frame.at[0, "_sc_cached"])
        self.assertTrue(frame.at[0, "_pc_cached"])
        self.assertTrue(frame.at[0, "_sc_from_alias"])
        self.assertTrue(frame.at[0, "_pc_from_alias"])

    def test_prefilter_checks_tags_then_name_and_excludes_them_from_sc(self):
        frame = core.build_dataframe([
            {"id": "tag-high", "name": "", "tags": [core.SC_HIGH_TAG]},
            {"id": "name-high", "name": "SC 0.234 PC 0.812", "tags": ["Useful"]},
            {"id": "needs-sc", "name": "SC 0.234", "tags": ["Useful"]},
        ], {})

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            remaining = v5._prefilter_terminal_states(Mock(), frame)

        self.assertEqual(remaining, [2])
        self.assertEqual(frame.at[1, "Platform_Tags"], core.PC_HIGH_TAG)
        self.assertEqual(frame.at[1, "PC_Status"], core.PC_HIGH_TAG)
        update.assert_called_once_with(
            ANY,
            "name-high",
            name="SC 0.234 PC 0.812",
            tags=[core.PC_HIGH_TAG],
        )

    def test_sc_base_change_preserves_cached_high_pc(self):
        frame = core.build_dataframe([{
            "id": "alias-high",
            "name": "SC 0.612 PC 0.901",
            "tags": ["Useful", core.PC_HIGH_TAG, core.SC_HIGH_TAG],
        }], {})

        v5._invalidate_sc_cache_after_base_change(frame, frame.index)

        self.assertFalse(frame.at[0, "_sc_cached"])
        self.assertTrue(frame.at[0, "_pc_cached"])
        self.assertEqual(frame.at[0, "prod_correlation_max"], 0.901)
        self.assertEqual(frame.at[0, "Platform_Tags"], "PC_IS_HIGHT")

    def test_high_alias_state_syncs_both_terminal_tags_and_removes_useful(self):
        frame = core.build_dataframe([{
            "id": "alias-high",
            "name": "SC 0.812 PC 0.901",
            "tags": ["Useful"],
        }], {})
        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            v5._sync_high_correlation_state(Mock(), frame, 0)

        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.812 PC 0.901")
        self.assertEqual(frame.at[0, "Platform_Tags"], "SC_IS_HIGHT, PC_IS_HIGHT")
        update.assert_called_once_with(
            ANY,
            "alias-high",
            name="SC 0.812 PC 0.901",
            tags=["SC_IS_HIGHT", "PC_IS_HIGHT"],
        )

    def test_stage1_checkpoint_resumes_only_missing_page(self):
        now = pd.Timestamp.now(tz="UTC").isoformat()
        page_one = [{"id": f"a{i}", "dateCreated": now} for i in range(100)]
        first_page = Mock(status_code=200)
        first_page.json.return_value = {"results": page_one, "count": 101}
        failed_page = Mock(status_code=500)
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "alpha_fetch_state.json"
            session = Mock()
            session.cookies = []
            session.request.side_effect = [first_page, failed_page]
            with patch("Core.api.client.GET_RETRY_DELAYS", ()), patch.object(core, "CONFIG_DAYS_AGO", 1):
                fetched, failures = core.fetch_recent_alphas(session, checkpoint)
            self.assertEqual(len(fetched), 100)
            self.assertEqual(failures, ["slice=1/1 offset=100"])

            final_page = Mock(status_code=200)
            final_page.json.return_value = {"results": [{"id": "a100", "dateCreated": now}], "count": 101}
            resumed = Mock()
            resumed.cookies = []
            resumed.request.return_value = final_page
            with patch("Core.api.client.GET_RETRY_DELAYS", ()), patch.object(core, "CONFIG_DAYS_AGO", 1):
                fetched, failures = core.fetch_recent_alphas(resumed, checkpoint)
            self.assertEqual(len(fetched), 101)
            self.assertEqual(failures, [])
            self.assertEqual(resumed.request.call_count, 1)

    def test_stage1_uses_time_slices_before_offset_reaches_platform_limit(self):
        now = pd.Timestamp.now(tz="UTC").isoformat()
        responses = []
        for slice_number in range(2):
            full_page = Mock(status_code=200)
            full_page.json.return_value = {
                "results": [{"id": f"s{slice_number}-{i}", "dateCreated": now} for i in range(100)], "count": 101
            }
            short_page = Mock(status_code=200)
            short_page.json.return_value = {
                "results": [{"id": f"s{slice_number}-last", "dateCreated": now}], "count": 101
            }
            responses.extend([full_page, short_page])

        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "alpha_fetch_state.json"
            session = Mock()
            session.cookies = []
            session.request.side_effect = responses
            with patch.object(core, "CONFIG_DAYS_AGO", 2), patch.object(core, "CONFIG_FETCH_SLICE_HOURS", 24):
                fetched, failures = core.fetch_recent_alphas(session, checkpoint)

        self.assertEqual(len(fetched), 202)
        self.assertEqual(failures, [])
        requested_urls = [call.args[1] for call in session.request.call_args_list]
        self.assertTrue(all("offset=1100" not in url for url in requested_urls))

    def test_sc_result_cache_skips_second_local_calculation(self):
        class FakeSkill:
            def __init__(self):
                self.calculate_calls = 0
                self.pnl_calls = 0

            def download_data(self, session, data_path, flag_increment=True):
                ids = {"EUR": ["os1"]}
                with (Path(data_path) / "os_alpha_ids.pickle").open("wb") as cache_file:
                    pickle.dump(ids, cache_file)
                return ids, pd.DataFrame()

            def load_data(self, data_path, tag="SelfCorr"):
                return ["EUR"], pd.DataFrame({"os": [1.0]})

            def get_alpha_pnls(self, session, records, alpha_pnls, alpha_ids):
                self.pnl_calls += 1
                return None, pd.DataFrame({"a1": [1.0]})

            def calc_self_corr(self, **kwargs):
                self.calculate_calls += 1
                return 0.25

        skill = FakeSkill()
        alpha_df = pd.DataFrame([{"alpha_id": "a1", "Region": "EUR"}])
        with TemporaryDirectory() as directory, patch.object(core, "sc_skill", skill):
            first = core.calculate_self_correlation_for_alphas_optimized(
                Mock(), Path(directory), alpha_df, max_workers=1
            )
            second = core.calculate_self_correlation_for_alphas_optimized(
                Mock(), Path(directory), alpha_df, max_workers=1
            )
        self.assertEqual(first.loc[0, "self_correlation"], 0.25)
        self.assertEqual(second.loc[0, "self_correlation"], 0.25)
        self.assertEqual(skill.calculate_calls, 1)
        self.assertEqual(skill.pnl_calls, 1)

    def test_known_sc_results_skip_local_calculation_when_base_data_is_unchanged(self):
        class FakeSkill:
            def __init__(self):
                self.calculate_calls = 0

            def download_data(self, session, data_path, flag_increment=True):
                ids = {"EUR": ["os1"]}
                with (Path(data_path) / "os_alpha_ids.pickle").open("wb") as cache_file:
                    pickle.dump(ids, cache_file)
                return ids, pd.DataFrame()

            def calc_self_corr(self, **kwargs):
                self.calculate_calls += 1
                return 0.1

        skill = FakeSkill()
        alpha_df = pd.DataFrame([{"alpha_id": "a1", "Region": "EUR"}])
        with TemporaryDirectory() as directory, patch.object(core, "sc_skill", skill):
            with (Path(directory) / "os_alpha_ids.pickle").open("wb") as cache_file:
                pickle.dump({"EUR": ["os1"]}, cache_file)
            result = core.calculate_self_correlation_for_alphas_optimized(
                Mock(),
                Path(directory),
                alpha_df,
                max_workers=1,
                known_sc_results={"a1": 0.812},
            )

        self.assertEqual(result.loc[0, "self_correlation"], 0.812)
        self.assertEqual(skill.calculate_calls, 0)

    def test_new_sc_base_alpha_invalidates_cached_sc_result(self):
        class FakeSkill:
            def __init__(self):
                self.calculate_calls = 0
                self.download_calls = 0

            def download_data(self, session, data_path, flag_increment=True):
                self.download_calls += 1
                ids = {"EUR": ["os1", "os2"] if self.download_calls > 1 else ["os1"]}
                with (Path(data_path) / "os_alpha_ids.pickle").open("wb") as cache_file:
                    pickle.dump(ids, cache_file)
                return ids, pd.DataFrame()

            def load_data(self, data_path, tag="SelfCorr"):
                return ["EUR"], pd.DataFrame({"os": [1.0]})

            def get_alpha_pnls(self, session, records, alpha_pnls, alpha_ids):
                return None, pd.DataFrame({"a1": [1.0]})

            def calc_self_corr(self, **kwargs):
                self.calculate_calls += 1
                return 0.25

        skill = FakeSkill()
        alpha_df = pd.DataFrame([{"alpha_id": "a1", "Region": "EUR"}])
        with TemporaryDirectory() as directory, patch.object(core, "sc_skill", skill):
            first = core.calculate_self_correlation_for_alphas_optimized(
                Mock(), Path(directory), alpha_df, max_workers=1
            )
            second = core.calculate_self_correlation_for_alphas_optimized(
                Mock(), Path(directory), alpha_df, max_workers=1
            )
        self.assertTrue(first.attrs["base_data_changed"])
        self.assertTrue(second.attrs["base_data_changed"])
        self.assertEqual(skill.calculate_calls, 2)

    def test_existing_output_only_restores_useful_for_sc_pc_pass_rows(self):
        frame = pd.DataFrame([
            {"alpha_id": "pass1", "Expression": "rank(field_a)", "Region": "EUR", "Universe": "TOP2500", "Delay": 1,
             "self_correlation": 0.1, "prod_correlation_max": 0.2, "prod_correlation_min": -0.2, "SC_Status": "PASS", "PC_Status": "PASS",
             "Platform_Name": "SC 0.100 PC 0.200", "Platform_Tags": "Useful", "Processing_Status": "COMPLETE"},
            {"alpha_id": "pending1", "Expression": "rank(field_a)", "Region": "EUR", "Universe": "TOP2500", "Delay": 1,
             "self_correlation": 0.1, "prod_correlation_max": 0.2, "SC_Status": "PASS", "PC_Status": "PENDING_PC",
             "Platform_Name": "SC 0.100", "Platform_Tags": "Useful", "Processing_Status": "READY_FOR_PC"},
        ])
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            frame.to_excel(output, index=False)
            with patch.object(core, "set_alpha_properties", return_value=True) as update:
                self.assertEqual(v5.restore_existing_output_usefuls(Mock(), output), 1)
            result = pd.read_excel(output)
            self.assertTrue(pd.isna(result.loc[0, "Matched_Categories"]))
            self.assertTrue(pd.isna(result.loc[1, "Matched_Categories"]))
            self.assertEqual(update.call_count, 1)

    def test_category_enrichment_handles_float_typed_empty_alpha_id_column(self):
        frame = pd.DataFrame([{
            "alpha_id": None, "alpha_id_raw": "abc123",
            "Expression": "rank(field_a)", "Region": "EUR", "Universe": "TOP2500", "Delay": 1,
            "self_correlation": 0.1, "prod_correlation_max": 0.2, "prod_correlation_min": -0.2,
            "SC_Status": "PASS", "PC_Status": "PASS",
            "Platform_Name": None, "Platform_Tags": None,
            "Processing_Status": None,
        }])
        with TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.xlsx"
            frame.to_excel(output, index=False)
            with patch.object(core, "apply_low_correlation_categories", return_value=True):
                self.assertEqual(v5.restore_existing_output_usefuls(Mock(), output), 1)
            result = pd.read_excel(output)
        self.assertEqual(result.loc[0, "alpha_id_raw"], "abc123")

    def test_pyramid_categories_are_read_directly_from_alpha_details(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"is": {"checks": [{
            "name": "MATCHES_PYRAMID", "result": "PASS", "effective": 2,
            "pyramids": [{"name": "GLB/D1/PV"}, {"name": "GLB/D1/OTHER"}],
        }]}}
        session.get.return_value = response

        result = core.get_alpha_pyramid_pass_info(session, "abc123")

        self.assertEqual(result["categories"], ["GLB/D1/PV", "GLB/D1/OTHER"])
        requested_url = session.get.call_args.args[0]
        self.assertTrue(requested_url.endswith("/alphas/abc123"))
        self.assertNotIn("data-fields", requested_url)

    def test_useful_write_defers_category_to_final_pyramid_audit(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"results": []}
        session.get.return_value = response
        frame = pd.DataFrame([{
            "alpha_id": "abc123",
            "_tags": [],
            "self_correlation": 0.1234,
            "prod_correlation_max": 0.4567,
            "prod_correlation_min": -0.3456,
            "Platform_Name": "SC 0.123",
            "Platform_Tags": "",
        }])
        alpha = {
            "regular": {"code": "rank(unknown_field)"},
            "settings": {"region": "EUR", "universe": "TOP2500", "delay": 1},
        }

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertTrue(core.apply_low_correlation_categories(session, frame, 0, alpha))

        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.123 PC 0.457")
        self.assertEqual(frame.at[0, "Platform_Tags"], core.USEFUL_TAG)
        self.assertEqual(frame.at[0, "Processing_Status"], "COMPLETE")
        self.assertEqual(frame.at[0, "Category_Status"], "PENDING_PYRAMID_AUDIT")
        update.assert_called_once_with(
            session, "abc123", name="SC 0.123 PC 0.457", tags=[core.USEFUL_TAG]
        )

    def test_final_useful_replaces_stale_high_tags_but_keeps_other_tags(self):
        frame = pd.DataFrame([{
            "alpha_id": "abc123", "_tags": [core.SC_HIGH_TAG, "Model"],
            "self_correlation": 0.7,
            "prod_correlation_max": 0.7,
            "prod_correlation_min": -0.7,
            "Platform_Name": "SC 0.700 PC 0.700",
            "Platform_Tags": f"{core.SC_HIGH_TAG}, Model",
        }])
        alpha = {"regular": {"code": "rank(unknown_field)"}, "settings": {}}

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertTrue(core.apply_low_correlation_categories(Mock(), frame, 0, alpha))

        self.assertEqual(frame.at[0, "Platform_Tags"], f"{core.USEFUL_TAG}, Model")
        update.assert_called_once_with(
            ANY, "abc123", name="SC 0.700 PC 0.700", tags=[core.USEFUL_TAG, "Model"]
        )

    def test_useful_write_does_not_add_field_metadata_category_tag(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"results": [{"id": "field_a"}]}
        session.get.return_value = response
        frame = pd.DataFrame([{
            "alpha_id": "abc123", "_tags": ["Useful"],
            "self_correlation": 0.1, "prod_correlation_max": 0.2,
            "prod_correlation_min": -0.1,
            "Platform_Name": "SC 0.100", "Platform_Tags": "Useful",
        }])
        alpha = {"regular": {"code": "rank(field_a)"}, "settings": {}}

        with patch.object(core, "set_alpha_properties", return_value=True) as update:
            self.assertTrue(core.apply_low_correlation_categories(session, frame, 0, alpha))

        self.assertEqual(frame.at[0, "Platform_Name"], "SC 0.100 PC 0.200")
        self.assertEqual(frame.at[0, "Platform_Tags"], "Useful")
        session.get.assert_not_called()
        update.assert_called_once_with(session, "abc123", name="SC 0.100 PC 0.200", tags=["Useful"])

    def test_default_window_is_thirty_beijing_days_and_configurable(self):
        now = datetime(2026, 8, 28, 2, 30, tzinfo=timezone.utc)
        start, end = core.beijing_date_window_utc(now)
        short_start, short_end = core.beijing_date_window_utc(now, days=7)

        self.assertEqual(core.CONFIG_DAYS_AGO, 30)
        self.assertEqual(start.isoformat(), "2026-07-29T16:00:00+00:00")
        self.assertEqual(end.isoformat(), "2026-08-28T16:00:00+00:00")
        self.assertEqual(short_start.isoformat(), "2026-08-21T16:00:00+00:00")
        self.assertEqual(short_end, end)

    def test_pyramid_coverage_keeps_limit_and_exact_scope(self):
        diversity = {"alphas": [{
            "region": "GLB", "delay": 1, "alphaCount": 4,
            "dataCategory": {"id": "pv", "name": "Price Volume"},
            "dataDiversity": {"check": "PASS", "limit": 0.3},
        }]}
        result = core.evaluate_pyramid_coverage(
            diversity, {"status": "PASS", "categories": ["GLB/D1/PRICE VOLUME", "EUR/D1/PV"]}
        )

        self.assertEqual(result["status"], "HAS_GAP")
        self.assertEqual(result["scopes"][0]["limit"], 0.3)
        self.assertEqual(result["gap_scopes"][0]["raw_scope"], "EUR/D1/PV")

    def test_pyramid_audit_adds_removes_and_preserves_submit(self):
        alphas = [
            {"id": "gap", "tags": ["Useful", "Model"]},
            {"id": "lit", "tags": ["Useful", "Submit", "Model"]},
            {"id": "pending", "tags": ["Useful", "Submit"]},
            {"id": "already-gap", "tags": ["Submit", "Useful"]},
        ]
        infos = {
            "gap": {"status": "PASS", "categories": ["GLB/D1/PV"]},
            "lit": {"status": "PASS", "categories": ["GLB/D1/MODEL"]},
            "pending": {"status": "PENDING", "categories": []},
            "already-gap": {"status": "PASS", "categories": ["GLB/D1/PV"]},
        }
        diversity = {"alphas": [
            {"region": "GLB", "delay": 1, "dataCategory": {"id": "model"},
             "dataDiversity": {"check": "PASS", "limit": 0.3}},
        ]}
        with TemporaryDirectory() as directory:
            with (
                patch.object(v5, "_server_useful_alphas", return_value=alphas),
                patch.object(core, "get_user_diversity", return_value=diversity),
                patch.object(core, "get_alpha_pyramid_pass_info", side_effect=lambda _s, aid: infos[aid]),
                patch.object(core, "set_alpha_properties", return_value=True) as update,
            ):
                records = v5.audit_server_useful_pyramids(
                    Mock(), Path(directory) / "audit.xlsx"
                )

        self.assertEqual(update.call_args_list[0].kwargs["tags"], ["Useful", "Model", "Submit"])
        self.assertEqual(update.call_args_list[1].kwargs["tags"], ["Useful", "Model"])
        self.assertEqual(len(update.call_args_list), 2)
        self.assertEqual(records[2]["Platform_Update_Status"], "PENDING_PYRAMID")
        self.assertEqual(records[3]["Platform_Update_Status"], "UNCHANGED")

    def test_incomplete_pc_never_writes_useful(self):
        frame = pd.DataFrame([{
            "alpha_id": "pending-pc", "_tags": [],
            "self_correlation": 0.1,
            "prod_correlation_max": 0.2,
            "prod_correlation_min": None,
            "Platform_Name": "SC 0.100 PC 0.200",
            "Platform_Tags": "",
        }])

        with patch.object(core, "set_alpha_properties") as update:
            self.assertFalse(core.apply_low_correlation_categories(Mock(), frame, 0, {}))

        update.assert_not_called()

    def test_sc_runs_before_remote_pc_and_pending_pc_does_not_add_useful(self):
        alpha = {
            "id": "flow1", "name": "", "tags": [core.USEFUL_TAG],
            "regular": {"code": "rank(field_a)"},
            "settings": {"region": "EUR", "universe": "TOP2500", "delay": 1},
            "is": {"checks": []}, "dateCreated": "2026-08-20T00:00:00Z",
        }
        events = []

        def calculate(*args, **kwargs):
            events.append("SC")
            result = pd.DataFrame([{"alpha_id": "flow1", "self_correlation": 0.2}])
            result.attrs["base_data_changed"] = False
            return result

        def get_pc(session, alpha_id):
            events.append("PC")
            return None, None, session

        session = Mock()
        with (
            patch.object(core, "configure_run_logging"),
            patch.object(core, "get_session", return_value=session),
            patch.object(v5, "audit_server_useful", return_value=[]),
            patch.object(v5, "audit_server_useful_pyramids"),
            patch.object(core, "fetch_recent_alphas", return_value=([alpha], [])),
            patch.object(v5, "remove_excluded_rows_from_output"),
            patch.object(v5, "restore_existing_output_usefuls") as enrich,
            patch.object(core, "load_excel_history", return_value={}),
            patch.object(core, "save_snapshot"),
            patch.object(core, "sc_skill", object()),
            patch.object(core, "calculate_self_correlation_for_alphas_optimized", side_effect=calculate),
            patch.object(core, "get_prod_correlation_stats_resilient", side_effect=get_pc),
            patch.object(core, "set_alpha_properties", return_value=True) as update,
            patch.object(core, "CONFIG_PC_SUCCESS_DELAY_SECONDS", 0),
        ):
            v5.run_job()

        self.assertEqual(events, ["SC", "PC"])
        enrich.assert_not_called()
        update.assert_called_once_with(session, "flow1", name="SC 0.200")
        self.assertNotIn("tags", update.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
