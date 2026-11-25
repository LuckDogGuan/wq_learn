import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd

import filter_ra_alphas_core as core
import filter_ra_alphas_v6 as v6


class V6SelectionTests(unittest.TestCase):
    def test_source_tag_filter_uses_shared_useful_constant(self):
        with patch.object(core, "USEFUL_TAG", "Candidate"):
            self.assertTrue(v6._is_useful("Model, Candidate"))
            self.assertFalse(v6._is_useful("Model, Useful"))

    def test_latest_v5_output_excludes_v6_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "filtered_RAs_20260811.xlsx"
            latest = root / "filtered_RAs_20260812.xlsx"
            v6_file = root / "filtered_RAs_v6_dry_run_20260813.xlsx"
            for path in (old, latest, v6_file):
                path.write_text("x", encoding="utf-8")
            old.touch()
            latest.touch()
            v6_file.touch()
            self.assertEqual(v6.find_latest_v5_output(root), latest)

    def test_correlation_rules_use_absolute_values_and_one_pc_alias(self):
        self.assertTrue(core.is_high_correlation(-0.701))
        self.assertTrue(core.is_high_pc(None, -0.8))
        self.assertFalse(core.is_complete_low_pc(0.2, -0.8))
        self.assertEqual(core.pc_alias_value(0.2, -0.6), 0.6)
        self.assertEqual(core.normal_alias(0.1234, -0.6), "SC 0.123 PC 0.600")

    def test_correlation_payload_parser_keeps_raw_pc_pair(self):
        payload = {"schema": {"max": 0.21, "min": -0.34}}
        self.assertEqual(core.production_correlation_values(payload), (0.21, -0.34))

    def test_429_detection_does_not_discard_success_with_child_429_detail(self):
        response = {"success": True, "alpha_results": [{"error": "Failed to get alpha details: 429"}]}
        self.assertFalse(v6._is_429(response))
        self.assertTrue(v6._is_429({"error": "Failed to create multisimulation. Status: 429"}))

    def test_selects_twenty_useful_rows_with_low_sc_pc_first(self):
        rows = []
        for index in range(25):
            rows.append({
                "alpha_id": f"a{index:02d}",
                "Platform_Tags": "Useful" if index < 22 else "Model",
                "Region": "GLB", "Margin": 0.002,
                "self_correlation": 0.2 + index / 1000,
                "prod_correlation_max": 0.3 + index / 1000,
                "prod_correlation_min": -0.1,
            })
        selected = v6.select_top_useful(pd.DataFrame(rows), 20)
        self.assertEqual(len(selected), 20)
        self.assertEqual(selected.iloc[0]["alpha_id"], "a00")
        self.assertEqual(selected.iloc[-1]["alpha_id"], "a19")

    def test_region_options_are_read_from_platform_shape(self):
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": ["TOP2500", "TOP1200"],
            "Neutralization": ["INDUSTRY", "COUNTRY"],
        }]}
        result = v6.region_setting_options(options, "EUR", 1)
        self.assertEqual(result["universes"], ("TOP2500", "TOP1200"))
        self.assertEqual(result["neutralizations"], ("INDUSTRY", "COUNTRY"))

    def test_region_options_exclude_none_but_keep_region_specific_values(self):
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "MEA", "Delay": 1,
            "Universe": ["TOP400", "TOP300"],
            "Neutralization": ["NONE", "MARKET", "SECTOR", "COUNTRY"],
        }]}
        result = v6.region_setting_options(options, "MEA", 1)
        self.assertEqual(result["neutralizations"], ("MARKET", "SECTOR", "COUNTRY"))

    def test_margin_filter_uses_8bp_for_eur_and_13bp_elsewhere(self):
        frame = pd.DataFrame([
            {"alpha_id_raw": "eur-pass", "Platform_Tags": "Useful", "Region": "EUR", "Margin": 0.000801,
             "self_correlation": 0.1, "prod_correlation_max": 0.1, "prod_correlation_min": -0.1},
            {"alpha_id_raw": "eur-fail", "Platform_Tags": "Useful", "Region": "EUR", "Margin": 0.0008,
             "self_correlation": 0.1, "prod_correlation_max": 0.1, "prod_correlation_min": -0.1},
            {"alpha_id_raw": "glb-pass", "Platform_Tags": "Useful", "Region": "GLB", "Margin": 0.001301,
             "self_correlation": 0.1, "prod_correlation_max": 0.1, "prod_correlation_min": -0.1},
            {"alpha_id_raw": "glb-fail", "Platform_Tags": "Useful", "Region": "GLB", "Margin": 0.0013,
             "self_correlation": 0.1, "prod_correlation_max": 0.1, "prod_correlation_min": -0.1},
        ])
        result = v6.select_top_useful(frame, 5)
        self.assertEqual(set(result["alpha_id_raw"]), {"eur-pass", "glb-pass"})

    def test_variants_keep_expression_and_expand_all_combinations(self):
        source = pd.DataFrame([{
            "alpha_id": "source1", "Expression": "rank(field_a)",
            "Region": "EUR", "Delay": 1, "Platform_Tags": "Useful",
        }])
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": ["TOP2500", "TOP1200"],
            "Neutralization": ["INDUSTRY", "COUNTRY"],
        }]}
        variants = v6.build_variants(source, options, decays=(0, 5, 20))
        self.assertEqual(len(variants), 12)
        self.assertTrue(all(item["expression"] == "rank(field_a)" for item in variants))
        self.assertEqual({item["decay"] for item in variants}, {0, 5, 20})

    def test_variant_identity_changes_with_source_or_expression(self):
        base = {
            "region": "EUR", "universe": "TOP2500", "delay": 1,
            "neutralization": "INDUSTRY", "decay": 0,
        }
        first = {**base, "source_alpha_id": "source1", "expression": "rank(a)"}
        other_source = {**base, "source_alpha_id": "source2", "expression": "rank(a)"}
        other_expression = {**base, "source_alpha_id": "source1", "expression": "rank(b)"}
        self.assertNotEqual(v6._variant_identity(first), v6._variant_identity(other_source))
        self.assertNotEqual(v6._variant_identity(first), v6._variant_identity(other_expression))

    def test_source_signature_detects_same_day_source_change(self):
        useful = pd.DataFrame([{"alpha_id_raw": "new", "Expression": "rank(new_field)"}])
        old_variants = [{
            "source_rank": 1, "source_alpha_id": "old", "expression": "rank(old_field)"
        }]
        self.assertNotEqual(
            v6._source_signature(useful_frame=useful),
            v6._source_signature(variants=old_variants),
        )

    def test_large_setting_lists_are_balanced_across_five_sources(self):
        source = pd.DataFrame([{
            "alpha_id_raw": f"source{index}", "Expression": f"rank(field_{index})",
            "Region": "EUR", "Delay": 1,
        } for index in range(5)])
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": [f"U{index}" for index in range(6)],
            "Neutralization": [f"N{index}" for index in range(8)],
        }]}
        variants = v6.build_variants(source, options, decays=(0,))
        self.assertEqual(len(variants), 5 * 4 * 5)
        self.assertEqual(len({item["universe"] for item in variants}), 4)
        self.assertEqual(len({item["neutralization"] for item in variants}), 5)

    def test_exactly_six_neutralizations_are_all_kept(self):
        source = pd.DataFrame([{
            "alpha_id_raw": "source", "Expression": "rank(field)",
            "Region": "EUR", "Delay": 1,
        }])
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": ["TOP2500"],
            "Neutralization": [f"N{index}" for index in range(6)],
        }]}
        variants = v6.build_variants(source, options, decays=(0,))
        self.assertEqual(len({item["neutralization"] for item in variants}), 6)

    def test_sources_share_settings_so_each_multi_simulation_batch_has_five_expressions(self):
        source = pd.DataFrame([{
            "alpha_id_raw": f"source{index}", "Expression": f"rank(field_{index})",
            "Region": "EUR", "Delay": 1,
        } for index in range(5)])
        options = {"instrument_options": [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": [f"U{index}" for index in range(6)],
            "Neutralization": [f"N{index}" for index in range(8)],
        }]}
        variants = v6.build_variants(source, options, decays=(0,), setting_seed="same-file")
        grouped = v6.group_variants(variants)
        self.assertEqual(set(map(len, grouped.values())), {5})


class V6ExpandedCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_expanded_alpha_name_and_tags_are_cleared(self):
        with patch.object(
            v6.core,
            "set_alpha_properties_core",
            return_value={"id": "child1"},
        ) as update:
            self.assertTrue(await v6.clear_expanded_alpha_properties("child1"))
        update.assert_called_once_with("child1", "", [])

    async def test_sc_pc_waits_when_expanded_alpha_cannot_be_cleared(self):
        frame = pd.DataFrame([{"alpha_id": "child1"}])
        with (
            patch.object(
                v6, "clear_expanded_alpha_properties", new=AsyncMock(return_value=False)
            ),
            patch.object(v6.core, "get_correlation_payload_core") as check,
        ):
            result = await v6.label_variants(frame)
        check.assert_not_called()
        self.assertEqual(result.at[0, "Processing_Status"], "PENDING_CLEAR")

    async def test_failed_basic_metrics_never_enter_sc_pc_or_get_useful(self):
        variants = [{
            "variant_key": "child-key", "alpha_id": "child1", "source_alpha_id": "source1",
            "source_rank": 1,
            "expression": "rank(a)", "region": "EUR", "universe": "TOP2500", "delay": 1,
            "neutralization": "INDUSTRY", "decay": 0,
            "sharpe": 0.9, "fitness": 0.4, "margin": 0.002,
        }]
        frame = v6._variant_frame(variants)
        with (
            patch.object(v6, "clear_expanded_alpha_properties", new=AsyncMock(return_value=True)),
            patch.object(v6.core, "get_correlation_payload_core") as check,
            patch.object(v6, "set_expanded_alpha_properties", new=AsyncMock()) as update,
        ):
            result = await v6.label_variants(frame, variants)
        check.assert_not_called()
        update.assert_not_awaited()
        self.assertEqual(result.at[0, "Processing_Status"], "EXCLUDED_BASIC_METRICS")
        self.assertTrue(variants[0]["label_complete"])

    async def test_completed_label_is_not_cleared_again(self):
        variants = [{
            "variant_key": "child-key", "alpha_id": "child1", "source_alpha_id": "source1",
            "source_rank": 1,
            "expression": "rank(a)", "region": "EUR", "universe": "TOP2500", "delay": 1,
            "neutralization": "INDUSTRY", "decay": 0, "label_complete": True,
            "platform_name": "SC 0.100 PC 0.200", "platform_tags": "Useful",
        }]
        frame = v6._variant_frame(variants)
        with (
            patch.object(v6, "clear_expanded_alpha_properties", new=AsyncMock()) as clear,
        ):
            await v6.label_variants(frame, variants)
        clear.assert_not_awaited()

    async def test_final_property_update_retries_429(self):
        with (
            patch.object(
                v6.core, "set_alpha_properties_core",
                side_effect=[{"error": "Status: 429"}, {"id": "child1"}],
            ) as update,
            patch.object(v6.asyncio, "sleep", new=AsyncMock()) as sleep,
        ):
            self.assertTrue(await v6.set_expanded_alpha_properties(
                "child1", "SC 0.100 PC 0.200", ["Useful"], "分配最终标签"
            ))
        self.assertEqual(update.call_count, 2)
        sleep.assert_awaited_once_with(v6.V6_429_COOLDOWN_SECONDS)


class V6CoreBridgeTests(unittest.TestCase):
    def test_platform_options_are_normalized_without_cnhkmcp(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "actions": {"POST": {"settings": {"children": {
                "instrumentType": {"type": "choice", "label": "Instrument type", "choices": [{"value": "EQUITY"}]},
                "region": {"type": "choice", "label": "Region", "choices": {"instrumentType": {"EQUITY": [{"value": "EUR"}]}}},
                "delay": {"type": "choice", "label": "Delay", "choices": {"instrumentType": {"EQUITY": {"region": {"EUR": [{"value": 1}]}}}}},
                "universe": {"type": "choice", "label": "Universe", "choices": {"instrumentType": {"EQUITY": {"region": {"EUR": [{"value": "TOP2500"}]}}}}},
                "neutralization": {"type": "choice", "label": "Neutralization", "choices": {"instrumentType": {"EQUITY": {"region": {"EUR": [{"value": "INDUSTRY"}]}}}}},
            }}}}
        }
        client = Mock()
        client.options.return_value = response
        with patch.object(core, "get_core_client", return_value=client):
            result = core.get_platform_setting_options_core()
        self.assertEqual(result["instrument_options"], [{
            "InstrumentType": "EQUITY", "Region": "EUR", "Delay": 1,
            "Universe": ["TOP2500"], "Neutralization": ["INDUSTRY"],
        }])


if __name__ == "__main__":
    unittest.main()
