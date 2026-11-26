import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "legacy_core" / "pipelines" / "spc"))
from maintain_spc import (
    Client,
    base_strategy_name,
    parse_model_catalog,
    replacement,
    summarize,
    swap,
    validate_sample,
)


SAMPLE = [
    {
        "company_name": "Microsoft Corp",
        "ticker": "MSFT",
        "isin": "US5949181045",
        "mic": "XNAS",
        "confidence_score": 0.35,
        "investment_horizon": 30,
        "return_prediction": 0.0,
    }
]


class SPCMaintenanceTests(unittest.TestCase):
    def test_sample_accepts_valid_instrument(self):
        self.assertEqual(validate_sample(json.dumps(SAMPLE)), SAMPLE)

    def test_rejects_bad_checksum_duplicate_and_nonfinite(self):
        for sample in [
            SAMPLE * 2,
            [{**SAMPLE[0], "isin": "US5949181044"}],
            [{**SAMPLE[0], "confidence_score": float("nan")}],
            [{**SAMPLE[0], "investment_horizon": True}],
        ]:
            with self.assertRaises(ValueError):
                validate_sample(json.dumps(sample))

    def test_replacement_uses_model_family_and_is_idempotent(self):
        source = {
            "name": "AM101 Demo | R20261012 GPT-6 Astra",
            "prompt": "Rank exactly 10 distinct stocks.",
            "sampleOutput": json.dumps(SAMPLE),
        }
        before = copy.deepcopy(source)
        first = replacement(source, "us.anthropic.claude-fable-5", "Claude Fable 5", tag="R20261126")
        self.assertEqual(first["name"], "AM101 Demo | R20261126 Claude Fable 5")
        self.assertEqual(first["modelFamily"], "us.anthropic.claude-fable-5")
        self.assertNotIn("model", first)
        self.assertNotIn("modelVersion", first)
        self.assertIn("Rank exactly 1 distinct", first["prompt"])
        self.assertEqual(first["prompt"].count("Output contract:"), 1)
        self.assertEqual(first["weight"], "0.00")
        self.assertEqual(source, before)

        second = replacement(first, "gemini-3.8-flash", "Gemini 3.8 Flash", tag="R20261126")
        self.assertEqual(second["name"], "AM101 Demo | R20261126 Gemini 3.8 Flash")
        self.assertEqual(second["prompt"].count("Output contract:"), 1)

    def test_parse_model_catalog(self):
        options_body = {
            "actions": {
                "POST": {
                    "modelFamily": {
                        "choices": [
                            {
                                "value": "claude",
                                "label": "Claude",
                                "items": [
                                    {"value": "us.anthropic.claude-fable-5", "label": "Claude Fable 5"},
                                    {"value": "us.anthropic.claude-opus-4-8", "label": "Claude Opus 4.8"},
                                ],
                            },
                            {
                                "value": "gemini",
                                "label": "Gemini",
                                "items": [{"value": "gemini-3.8-flash", "label": "Gemini 3.8 Flash"}],
                            },
                        ]
                    }
                }
            }
        }
        catalog = parse_model_catalog(options_body)
        self.assertEqual(set(catalog), {"us.anthropic.claude-fable-5", "us.anthropic.claude-opus-4-8", "gemini-3.8-flash"})
        self.assertEqual(catalog["us.anthropic.claude-fable-5"]["label"], "Claude Fable 5")

    def test_unstable_cannot_be_activated(self):
        client = Client.__new__(Client)
        client.folder = Path(__file__).resolve().parent / "unused_spc_test_log"
        client.listing = lambda: [
            {
                "id": "abc",
                "sampleOutput": json.dumps(SAMPLE),
                "status": "Unstable Output",
                "weight": "0.00",
            }
        ]
        client.request = lambda *a: self.fail("must not PATCH")
        with self.assertRaisesRegex(RuntimeError, "unverified"):
            client.set_weight("abc", "1.00")

    def test_non_spc_endpoint_is_blocked(self):
        client = Client.__new__(Client)
        with self.assertRaisesRegex(ValueError, "SPC endpoint"):
            client.request("POST", "/alphas/abc/submit", {})

    def test_already_zero_is_read_only(self):
        row = {"id": "abc", "weight": "0.00"}
        client = Client.__new__(Client)
        client.folder = Path(__file__).resolve().parent / "unused_spc_test_log"
        client.listing = lambda: [row]
        client.request = lambda *a: self.fail("must not PATCH")
        self.assertEqual(client.set_weight("abc", "0.00"), row)

    def test_failed_activation_never_reactivates_failed_source(self):
        rows = [
            {"id": "old", "name": "old", "weight": "1.00", "status": "Failed"},
            {
                "id": "new",
                "name": "new",
                "weight": "0.00",
                "status": "Active",
                "modelFamily": "deepseek.v3.2",
                "sampleOutput": json.dumps(SAMPLE),
                "prompt": "Rank exactly 1 distinct stocks.",
            },
        ]
        client = Client.__new__(Client)
        client.listing = lambda: rows
        operations = []

        def set_weight(identifier, weight, *, allow_protected=False):
            operations.append((identifier, weight))
            if identifier == "new":
                raise RuntimeError("activation failed")
            return rows[0]

        client.set_weight = set_weight
        with self.assertRaisesRegex(RuntimeError, "activation failed"):
            swap(
                client,
                {
                    "new_name": "new",
                    "modelFamily": "deepseek.v3.2",
                    "source_id": "old",
                    "old_active_ids": ["old"],
                },
            )
        self.assertEqual(operations, [("old", "0.00"), ("new", "1.00")])

    def test_stable_source_blocked_by_default_and_rolled_back_on_upgrade_failure(self):
        client = Client.__new__(Client)
        client.listing = lambda: [{"id": "old", "status": "Active"}]
        client.set_weight = lambda *a, **kw: self.fail("must not change a stable source")
        with self.assertRaisesRegex(RuntimeError, "stable source must be preserved"):
            swap(client, {"source_id": "old"})

        rows = [
            {"id": "old", "name": "old", "weight": "1.00", "status": "Active", "modelFamily": "gpt-4o"},
            {
                "id": "new",
                "name": "new",
                "weight": "0.00",
                "status": "Active",
                "modelFamily": "us.anthropic.claude-fable-5",
                "sampleOutput": json.dumps(SAMPLE),
                "prompt": "Rank exactly 1 distinct stocks.",
            },
        ]
        client.listing = lambda: rows
        ops = []

        def set_weight(identifier, weight, *, allow_protected=False):
            ops.append((identifier, weight, allow_protected))
            if identifier == "new":
                raise RuntimeError("boom")
            return rows[0]

        client.set_weight = set_weight
        with self.assertRaisesRegex(RuntimeError, "boom"):
            swap(
                client,
                {
                    "source_id": "old",
                    "old_active_ids": ["old"],
                    "new_id": "new",
                    "modelFamily": "us.anthropic.claude-fable-5",
                    "allow_stable_upgrade": True,
                },
            )
        self.assertEqual(ops, [("old", "0.00", True), ("new", "1.00", False), ("old", "1.00", True)])

    def test_summarize_counts_unique_strategies(self):
        rows = [
            {"id": "1", "name": "AM101 | R20261126 A", "status": "Active", "weight": "1.00", "modelFamily": "deepseek.v3.2", "updateFrequency": "daily"},
            {"id": "2", "name": "AM101", "status": "Failed", "weight": "0.00", "modelFamily": "gpt-4o", "updateFrequency": "daily"},
        ]
        summary = summarize(rows)
        self.assertEqual(summary["weighted_count"], 1)
        self.assertEqual(summary["unique_weighted_strategies"], 1)
        self.assertEqual(base_strategy_name(rows[0]["name"]), "AM101")


if __name__ == "__main__":
    unittest.main()
