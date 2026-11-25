"""V6 chunk safety and daily counting evidence, with no live API calls."""
import asyncio
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from unittest.mock import AsyncMock
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "代码" / "优化代码" / "区分RA并标记"))
import filter_ra_alphas_core as core
import filter_ra_alphas_v6 as v6


class V6RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "state.json"
        self.variants = [{"variant_key": f"v{index}", "expression": f"rank(field_{index})",
                          "region": "GLB", "universe": "TOPDIV3000", "delay": 1,
                          "neutralization": "SUBINDUSTRY", "decay": 0,
                          "status": "PENDING_SIMULATION"} for index in range(8)]
        self.progress = patch.object(v6, "_progress")
        self.progress.start()
        self.addCleanup(self.progress.stop)
        self.create_patch = patch.object(core, "create_multi_simulation_core")
        self.create = self.create_patch.start()
        self.addCleanup(self.create_patch.stop)
        self.policy_patch = patch.object(core, "check_single_dataset_batch", create=True,
            return_value={"status": "PASS", "dataset_id": "dataset_a", "field_ids": ["field_a"]})
        self.policy = self.policy_patch.start()
        self.addCleanup(self.policy_patch.stop)

    def run_v6(self, variants=None):
        return asyncio.run(v6.simulate_variants(copy.deepcopy(variants or self.variants), self.path))

    def read_state(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def complete_response(self, offset=0):
        return {"location": "/simulations/parent", "alpha_results": [
            {"alpha_id": f"alpha_{index + offset}", "details": {"regular": {"code": self.variants[index]["expression"]}, "is": {
                "sharpe": 2.0, "fitness": 1.2, "margin": 0.002, "turnover": 0.1}}}
            for index in range(8)]}

    def same_source_variants(self):
        return [{**item, "source_alpha_id": "source_a", "expression": "rank(field_a)",
                 "universe": "TOPDIV3000" if index < 4 else "TOP1000", "decay": index}
                for index, item in enumerate(self.variants)]

    def response_for_variants(self, variants):
        return {"multisimulation_location": "/simulations/source_a", "alpha_results": [
            {"alpha_id": f"alpha_{index}", "details": {"regular": {"code": item["expression"]},
                "settings": {name: item[name] for name in ("region", "universe", "delay", "neutralization", "decay")},
                "is": {"sharpe": 2.0, "fitness": 1.2, "margin": 0.002, "turnover": 0.1}}}
            for index, item in enumerate(variants)]}

    def test_same_source_eight_different_settings_use_one_multisim_unchanged_expression(self):
        variants = self.same_source_variants()
        self.create.return_value = self.response_for_variants(variants)
        self.run_v6(variants)
        self.create.assert_called_once()
        kwargs = self.create.call_args.kwargs
        self.assertTrue(kwargs["defer_polling"])
        self.assertEqual(kwargs["alpha_expressions"], ["rank(field_a)"] * 8)
        self.assertEqual([setting["decay"] for setting in kwargs["individual_settings"]], list(range(8)))
        self.assertEqual(self.policy.call_count, 2)
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "COMPLETE")

    def test_repeated_expression_shuffled_settings_preserve_correct_attribution(self):
        variants = self.same_source_variants()
        result = self.response_for_variants(variants)
        result["alpha_results"].reverse()
        self.create.return_value = result
        observed = self.run_v6(variants)
        self.assertEqual([item["alpha_id"] for item in observed], [f"alpha_{index}" for index in range(8)])
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "COMPLETE")

    def test_two_same_expression_chunks_with_different_settings_are_distinct(self):
        first = self.same_source_variants()
        second = [{**item, "decay": item["decay"] + 20} for item in first]
        self.create.side_effect = [self.response_for_variants(first), self.response_for_variants(second)]
        self.run_v6(first + second)
        self.assertEqual(self.create.call_count, 2)
        chunks = self.read_state()["chunk_batches"]
        self.assertEqual(len(chunks), 2)
        self.assertNotEqual(chunks[0]["id"], chunks[1]["id"])
        self.assertTrue(all(chunk["status"] == "COMPLETE" for chunk in chunks))

    def test_incomplete_read_only_recovery_allows_next_distinct_chunk_without_repost(self):
        first = self.same_source_variants()
        second = [{**item, "decay": item["decay"] + 20} for item in first]
        self.create.side_effect = [{"error": "PENDING", "multisimulation_location": "/simulations/old"},
                                   self.response_for_variants(second)]
        with patch("time.time", return_value=1000):
            self.run_v6(first + second)
        with patch.object(core, "recover_multi_simulation_core", return_value={
                "error": "PENDING_CHILDREN", "multisimulation_location": "/simulations/old"}) as recover:
            with patch("time.time", return_value=1299):
                self.run_v6(first + second)
            self.assertEqual(self.create.call_count, 1)
            recover.assert_not_called()
            with patch("time.time", return_value=1301):
                self.run_v6(first + second)
            recover.assert_called_once()
            with patch("time.time", return_value=1302):
                self.run_v6(first + second)
                self.run_v6(first + second)
            recover.assert_called_once()
        self.assertEqual(self.create.call_count, 2)
        chunks = self.read_state()["chunk_batches"]
        self.assertEqual(chunks[0]["status"], "PENDING")
        self.assertTrue(chunks[0]["reconciled"])
        self.assertNotIn("completed_at", chunks[0])
        self.assertEqual(chunks[1]["status"], "COMPLETE")

    def test_no_location_after_cooldown_skips_unknown_and_runs_next_chunk(self):
        first = self.same_source_variants()
        second = [{**item, "decay": item["decay"] + 20} for item in first]
        self.create.side_effect = [TimeoutError("mock"), self.response_for_variants(second)]
        with patch("time.time", return_value=1000):
            self.run_v6(first + second)
        with patch.object(core, "recover_multi_simulation_core") as recover:
            with patch("time.time", return_value=1299):
                self.run_v6(first + second)
            self.assertEqual(self.create.call_count, 1)
            with patch("time.time", return_value=1301):
                self.run_v6(first + second)
                self.run_v6(first + second)
            recover.assert_not_called()
        self.assertEqual(self.create.call_count, 2)
        chunks = self.read_state()["chunk_batches"]
        self.assertEqual(chunks[0]["status"], "RESULTS_UNOBSERVED")
        self.assertTrue(chunks[0]["readonly_unavailable"])
        self.assertNotIn("completed_at", chunks[0])
        self.assertEqual(chunks[1]["status"], "COMPLETE")

    def test_repeated_expression_without_returned_settings_is_pending(self):
        variants = self.same_source_variants()
        result = self.response_for_variants(variants)
        result["alpha_results"][0]["details"].pop("settings")
        self.create.return_value = result
        self.run_v6(variants)
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "PENDING")
        self.assertNotIn("completed_at", self.read_state()["chunk_batches"][0])

    def test_different_source_ids_never_fill_each_others_incomplete_batch(self):
        variants = [{**item, "source_alpha_id": "source_a" if index < 4 else "source_b"}
                    for index, item in enumerate(self.variants)]
        self.assertEqual(len(v6.group_variants(variants)), 1)
        self.assertEqual(len(v6.group_variants(variants, by_source=True)), 2)
        self.run_v6(variants)
        self.create.assert_not_called()
        self.policy.assert_not_called()

    def test_scope_metadata_disagreement_rejects_entire_source_batch(self):
        for fields, second_dataset in ((["field_a"], "dataset_b"), (["field_b", "field_c"], "dataset_a")):
            with self.subTest(fields=fields), tempfile.TemporaryDirectory() as temporary:
                self.policy.side_effect = [{"status": "PASS", "dataset_id": "dataset_a", "field_ids": ["field_a"]},
                                           {"status": "PASS", "dataset_id": second_dataset, "field_ids": fields}]
                path = Path(temporary) / "state.json"
                asyncio.run(v6.simulate_variants(self.same_source_variants(), path))
                chunk = json.loads(path.read_text(encoding="utf-8"))["chunk_batches"][0]
                self.assertEqual(chunk["status"], "LOCAL_REJECTED")
                self.assertFalse(chunk["post_attempted"])
        self.create.assert_not_called()

    def test_post_sees_atomic_eight_item_chunk_already_persisted(self):
        def inspect(**kwargs):
            state = self.read_state()
            self.assertEqual(len(kwargs["alpha_expressions"]), 8)
            chunk = state["chunk_batches"][0]
            self.assertEqual(chunk["status"], "SUBMITTING")
            self.assertEqual(chunk["expressions"], kwargs["alpha_expressions"])
            return self.complete_response()
        self.create.side_effect = inspect
        self.run_v6()
        self.create.assert_called_once()
        chunk = self.read_state()["chunk_batches"][0]
        self.assertEqual(chunk["status"], "COMPLETE")
        self.assertEqual(len(set(chunk["valid_alpha_ids"])), 8)
        self.assertTrue(chunk["completed_at"].endswith("+08:00"))

    def test_429_is_not_retried_or_reposted_on_resume(self):
        self.create.return_value = {"error": "HTTP 429", "status_code": 429}
        self.run_v6()
        self.run_v6()
        self.create.assert_called_once()
        chunk = self.read_state()["chunk_batches"][0]
        self.assertEqual(chunk["http_status"], 429)
        self.assertNotEqual(chunk["status"], "COMPLETE")
        self.assertNotIn("completed_at", chunk)

    def test_hidden_cross_dataset_expression_is_locally_rejected_before_post(self):
        variants = copy.deepcopy(self.variants)
        variants[0]["expression"] = "rank(subtract(dataset_a_field, dataset_b_field))"
        self.policy.return_value = {"status": "LOCAL_REJECTED", "dataset_id": None,
                                    "field_ids": ["dataset_a_field", "dataset_b_field"],
                                    "reason": "MULTIPLE_DATASETS"}
        self.run_v6(variants)
        self.run_v6(variants)
        self.create.assert_not_called()
        chunk = self.read_state()["chunk_batches"][0]
        self.assertEqual(chunk["status"], "LOCAL_REJECTED")
        self.assertFalse(chunk["post_attempted"])
        self.assertNotIn("completed_at", chunk)
        self.assertEqual(self.policy.call_args.args[0][0], variants[0]["expression"])

    def test_policy_pending_can_retry_validation_but_not_post_until_pass(self):
        self.policy.return_value = {"status": "PENDING", "reason": "HTTP429"}
        with patch("time.time", return_value=1000):
            self.run_v6()
        with patch("time.time", return_value=1200):
            self.run_v6()
        self.assertEqual(self.policy.call_count, 1)
        self.create.assert_not_called()
        self.assertFalse(self.read_state()["chunk_batches"][0]["post_attempted"])
        self.policy.return_value = {"status": "PASS", "dataset_id": "dataset_a", "field_ids": ["field_a"]}
        self.create.return_value = self.complete_response()
        with patch("time.time", return_value=1301):
            self.run_v6()
        self.assertEqual(self.policy.call_count, 2)
        self.create.assert_called_once()
        self.assertEqual(len(self.read_state()["chunk_batches"]), 1)
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "COMPLETE")

    def test_local_rejection_does_not_block_other_valid_chunks(self):
        variants = self.variants + [{**item, "neutralization": "INDUSTRY"} for item in self.variants]
        self.policy.side_effect = [{"status": "LOCAL_REJECTED", "reason": "MULTIPLE_DATASETS"},
                                   {"status": "PASS", "dataset_id": "dataset_a", "field_ids": ["field_a"]}]
        self.create.return_value = self.complete_response()
        self.run_v6(variants)
        self.create.assert_called_once()
        self.assertEqual(self.create.call_args.kwargs["individual_settings"][0]["neutralization"], "INDUSTRY")
        self.assertEqual([chunk["status"] for chunk in self.read_state()["chunk_batches"]],
                         ["LOCAL_REJECTED", "COMPLETE"])

    def test_shuffled_results_are_matched_by_expression_not_position(self):
        result = self.complete_response()
        result["alpha_results"].reverse()
        result["alpha_results"][0]["details"]["regular"]["code"] = " rank ( field_7 ) "
        self.create.return_value = result
        variants = self.run_v6()
        self.assertEqual([item["alpha_id"] for item in variants], [f"alpha_{index}" for index in range(8)])
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "COMPLETE")

    def test_missing_wrong_and_duplicate_expression_cannot_count_complete(self):
        for kind in ("missing", "wrong", "duplicate"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                result = self.complete_response()
                if kind == "missing":
                    result["alpha_results"][0]["details"].pop("regular")
                else:
                    result["alpha_results"][0]["details"]["regular"]["code"] = "rank(wrong)" if kind == "wrong" else self.variants[1]["expression"]
                self.create.return_value = result
                path = Path(temporary) / "state.json"
                variants = asyncio.run(v6.simulate_variants(copy.deepcopy(self.variants), path))
                chunk = json.loads(path.read_text(encoding="utf-8"))["chunk_batches"][0]
                self.assertEqual(chunk["status"], "PENDING")
                self.assertNotIn("completed_at", chunk)
                self.assertNotIn("alpha_id", variants[0])

    def test_timeout_never_reposts_and_keeps_attempt_fingerprint(self):
        self.create.side_effect = TimeoutError("mock timeout")
        self.run_v6()
        first = self.read_state()["chunk_batches"][0]
        self.run_v6()
        self.assertEqual(self.read_state()["chunk_batches"][0]["id"], first["id"])
        self.create.assert_called_once()
        self.assertEqual(first["status"], "RESULTS_UNOBSERVED")

    def test_pending_with_location_preserves_read_only_recovery_entry(self):
        self.create.return_value = {"error": "children unobserved", "location": "/simulations/parent"}
        self.run_v6()
        self.run_v6()
        self.create.assert_called_once()
        chunk = self.read_state()["chunk_batches"][0]
        self.assertEqual(chunk["location"], "/simulations/parent")
        self.assertEqual(chunk["status"], "PENDING")
        self.assertNotIn("completed_at", chunk)

    def test_location_recovers_read_only_once_after_five_minutes(self):
        self.create.return_value = {"error": "children unobserved", "multisimulation_location": "/simulations/parent"}
        with patch("time.time", return_value=1000):
            self.run_v6()
        with patch.object(core, "recover_multi_simulation_core", create=True, return_value=self.complete_response()) as recover:
            with patch("time.time", return_value=1200):
                self.run_v6()
            recover.assert_not_called()
            with patch("time.time", return_value=1301):
                self.run_v6()
                self.run_v6()
            recover.assert_called_once_with("/simulations/parent")
        self.create.assert_called_once()
        chunk = self.read_state()["chunk_batches"][0]
        self.assertTrue(chunk["reconciled"])
        self.assertEqual(chunk["status"], "COMPLETE")

    def test_failed_read_only_recovery_is_not_repeated(self):
        self.create.return_value = {"error": "children unobserved", "location": "/simulations/parent"}
        with patch("time.time", return_value=1000):
            self.run_v6()
        with patch.object(core, "recover_multi_simulation_core", create=True, side_effect=TimeoutError("mock")) as recover:
            with patch("time.time", return_value=1301):
                self.run_v6()
            with patch("time.time", return_value=2000):
                self.run_v6()
            recover.assert_called_once()
        self.create.assert_called_once()
        self.assertNotIn("completed_at", self.read_state()["chunk_batches"][0])

    def test_first_failed_group_stops_all_later_posts(self):
        variants = self.variants + [{**item, "neutralization": "INDUSTRY"} for item in self.variants]
        self.create.return_value = {"error": "HTTP 429", "status_code": 429}
        with patch("time.time", return_value=1000):
            self.run_v6(variants)
        self.create.assert_called_once()
        self.assertEqual(len(self.read_state()["chunk_batches"]), 1)
        self.assertEqual(self.read_state()["chunk_batches"][0]["retry_after"], 1300)

    def test_one_through_seven_items_never_post(self):
        for size in range(1, 8):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "state.json"
                asyncio.run(v6.simulate_variants(copy.deepcopy(self.variants[:size]), path))
        self.create.assert_not_called()

    def test_old_alpha_ids_block_post_even_properties_pending_clear(self):
        variants = copy.deepcopy(self.variants)
        for index, item in enumerate(variants):
            item.update(alpha_id=f"old_{index}", status="PENDING_CLEAR")
        self.run_v6(variants)
        chunk = self.read_state()["chunk_batches"][0]
        self.assertEqual(chunk["status"], "LEGACY_OBSERVED")
        self.assertNotIn("completed_at", chunk)
        self.create.assert_not_called()

    def test_partial_old_ids_block_whole_chunk_post(self):
        variants = copy.deepcopy(self.variants)
        variants[0]["alpha_id"] = "old_alpha"
        self.run_v6(variants)
        self.assertEqual(self.read_state()["chunk_batches"][0]["status"], "RESULTS_UNOBSERVED")
        self.create.assert_not_called()

    def test_legacy_failed_group_without_chunk_ledger_does_not_post(self):
        state = {"version": 6, "variant_plan_version": v6.V6_VARIANT_PLAN_VERSION,
                 "variants": self.variants, "last_pending_settings": ["GLB", "TOPDIV3000", 1, "SUBINDUSTRY", 0]}
        self.path.write_text(json.dumps(state), encoding="utf-8")
        self.run_v6()
        self.create.assert_not_called()

    def test_successful_first_chunk_is_not_replayed_when_second_failed(self):
        variants = self.variants + [{**item, "variant_key": "second_" + item["variant_key"],
                                     "expression": "ts_rank(" + item["expression"] + ", 5)"}
                                    for item in self.variants]
        self.create.side_effect = [self.complete_response(), {"error": "timeout"}]
        self.run_v6(variants)
        self.run_v6(variants)
        self.assertEqual(self.create.call_count, 2)
        statuses = [chunk["status"] for chunk in self.read_state()["chunk_batches"]]
        self.assertEqual(statuses, ["COMPLETE", "RESULTS_UNOBSERVED"])

    def test_missing_metrics_duplicate_ids_and_missing_results_do_not_count(self):
        cases = []
        incomplete = self.complete_response()
        incomplete["alpha_results"][0]["details"]["is"].pop("fitness")
        cases.append(incomplete)
        duplicate = self.complete_response()
        duplicate["alpha_results"][1]["alpha_id"] = "alpha_0"
        cases.append(duplicate)
        short = self.complete_response()
        short["alpha_results"].pop()
        cases.append(short)
        for value in (float("nan"), float("inf"), True):
            invalid = self.complete_response()
            invalid["alpha_results"][0]["details"]["is"]["sharpe"] = value
            cases.append(invalid)
        cases.append({"location": "/simulations/parent", "alpha_results": []})
        for result in cases:
            with self.subTest(result=result), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "state.json"
                self.create.return_value = result
                asyncio.run(v6.simulate_variants(copy.deepcopy(self.variants), path))
                chunk = json.loads(path.read_text(encoding="utf-8"))["chunk_batches"][0]
                self.assertNotEqual(chunk["status"], "COMPLETE")
                self.assertNotIn("completed_at", chunk)

    def test_corrupt_existing_state_is_preserved_without_post(self):
        self.path.write_text("{broken", encoding="utf-8")
        self.run_v6()
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")
        self.create.assert_not_called()

    def run_job_checkpoint(self, previous):
        root = self.path.parent
        output = root / "output"
        output.mkdir(exist_ok=True)
        filename = "filtered_RAs_20261012.xlsx"
        frame = pd.DataFrame([{"Expression": item["expression"], "alpha_id_raw": f"source_{index}",
                               "Region": "GLB", "Margin": 0.002, "Platform_Tags": "Useful"}
                              for index, item in enumerate(self.variants)])
        frame.to_excel(output / filename, index=False)
        state_path = output / "filter_ra_alphas_v6_state_20261012.json"
        state_path.write_text(json.dumps(previous), encoding="utf-8")
        original = state_path.read_bytes()
        with patch.object(v6, "__file__", str(root / "filter_ra_alphas_v6.py")), patch.object(core, "configure_run_logging"), \
             patch.object(v6, "fetch_platform_options", AsyncMock(return_value={})), \
             patch.object(v6, "build_variants", return_value=copy.deepcopy(self.variants)), \
             patch.object(v6, "simulate_variants", AsyncMock(return_value=[])) as simulate, \
             patch.object(v6, "label_variants", AsyncMock(return_value=pd.DataFrame())), \
             patch.object(core, "save_snapshot"):
            v6.run_job()
        return state_path, original, simulate

    def test_run_job_checkpoint_preserves_existing_chunk_ledger(self):
        previous = {"version": 6, "variant_plan_version": v6.V6_VARIANT_PLAN_VERSION,
                    "source_file": "filtered_RAs_20261012.xlsx", "variants": self.variants,
                    "chunk_batches": [{"id": "known", "status": "PENDING", "location": "/simulations/known"}],
                    "completed_batches": [], "results": [], "last_pending_settings": ["GLB", "TOPDIV3000", 1, "SUBINDUSTRY", 0]}
        path, _, simulate = self.run_job_checkpoint(previous)
        state = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(state["chunk_batches"], previous["chunk_batches"])
        self.assertEqual(state["last_pending_settings"], previous["last_pending_settings"])
        simulate.assert_awaited_once()

    def test_run_job_incompatible_plan_preserves_state_without_simulation(self):
        previous = {"version": 6, "variant_plan_version": -1,
                    "source_file": "filtered_RAs_20261012.xlsx", "variants": self.variants,
                    "chunk_batches": [{"id": "known", "status": "SUBMITTING"}]}
        path, original, simulate = self.run_job_checkpoint(previous)
        self.assertEqual(path.read_bytes(), original)
        simulate.assert_not_awaited()


class CoreScopeAndRecoveryTests(unittest.TestCase):
    def test_actual_create_builds_individual_settings_and_defers_all_get_polling(self):
        client = Mock()
        individual = [{"region": "GLB", "universe": "TOPDIV3000" if index < 4 else "TOP1000",
                       "delay": 1, "neutralization": "SUBINDUSTRY", "decay": index} for index in range(8)]
        with patch.object(core, "get_core_client", return_value=client), patch(
                "Core.api.sim_api.post_multi_simulation", return_value={"location": "/simulations/parent", "status_code": 201}) as post:
            result = core.create_multi_simulation_core(["rank(field_a)"] * 8, individual_settings=individual,
                                                       defer_polling=True, max_trade="OFF")
        payload = post.call_args.args[1]
        self.assertEqual(len(payload), 8)
        for expected, item in zip(individual, payload):
            self.assertEqual(item["regular"], "rank(field_a)")
            for key, value in expected.items():
                self.assertEqual(item["settings"][key], value)
        self.assertEqual(result["multisimulation_location"], "/simulations/parent")
        client.get.assert_not_called()

    def test_actual_scope_guard_checks_nested_fields_and_rejects_different_datasets(self):
        client = Mock()
        expression = "rank(subtract(field_a, field_b))"
        metadata = {"status": "OK", "metadata": {"field_a": {"dataset": {"id": "dataset_a"}},
                                                  "field_b": {"dataset": {"id": "dataset_b"}}}}
        with patch.object(core, "get_core_client", return_value=client), patch(
                "Core.api.data_api.get_datafield_metadata", return_value=metadata) as lookup:
            checked = core.check_single_dataset_batch([expression] * 8, "GLB", "TOPDIV3000", 1)
        self.assertEqual(checked["status"], "LOCAL_REJECTED")
        self.assertEqual(set(checked["field_ids"]), {"field_a", "field_b"})
        self.assertTrue(lookup.call_args.kwargs["read_only"])
        client.post.assert_not_called()

    def test_actual_scope_guard_excludes_local_variable_names_from_metadata(self):
        metadata = {"status": "OK", "metadata": {"field_a": {"dataset": {"id": "test_dataset"}},
                                                  "field_b": {"dataset": {"id": "test_dataset"}}}}
        with patch.object(core, "get_core_client", return_value=Mock()), patch(
                "Core.api.data_api.get_datafield_metadata", return_value=metadata) as lookup:
            checked = core.check_single_dataset_batch(["local_score=subtract(field_a,field_b);rank(local_score)"] * 8,
                                                     "GLB", "TOPDIV3000", 1)
        self.assertEqual(checked["status"], "PASS")
        self.assertEqual(set(lookup.call_args.args[1]), {"field_a", "field_b"})

    def test_actual_scope_guard_missing_metadata_is_pending(self):
        with patch.object(core, "get_core_client", return_value=Mock()), patch(
                "Core.api.data_api.get_datafield_metadata", return_value={"status": "OK", "metadata": {}}):
            checked = core.check_single_dataset_batch(["rank(field_a)"] * 8, "GLB", "TOPDIV3000", 1)
        self.assertEqual(checked["status"], "PENDING")

    def test_actual_recovery_reads_one_parent_and_eight_children_without_post(self):
        client = Mock()
        def response(body):
            return Mock(status_code=200, json=Mock(return_value=body))
        client.get.side_effect = [response({"children": [f"child_{index}" for index in range(8)]})] + [
            response({"alpha": f"alpha_{index}", "status": "COMPLETE"}) for index in range(8)]
        with patch.object(core, "get_core_client", return_value=client), patch.object(
                core, "get_alpha_details_core", return_value={"is": {"sharpe": 2.0}}) as details:
            result = core.recover_multi_simulation_core("/simulations/known")
        self.assertEqual(client.get.call_count, 9)
        self.assertEqual(details.call_count, 8)
        self.assertEqual(len(result["alpha_results"]), 8)
        self.assertEqual(result["multisimulation_location"], "/simulations/known")
        client.post.assert_not_called()

    def test_actual_recovery_rejects_dict_children_without_unhashable_crash(self):
        client = Mock()
        client.get.return_value = Mock(status_code=200, json=Mock(return_value={"children": [{}] * 8}))
        with patch.object(core, "get_core_client", return_value=client):
            result = core.recover_multi_simulation_core("/simulations/known")
        self.assertEqual(result["error"], "PENDING_CHILDREN")
        client.get.assert_called_once()
        client.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
