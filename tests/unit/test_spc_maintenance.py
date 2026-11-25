import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spc"))
from maintain_spc import Client, replacement, swap, validate_sample


SAMPLE = [{"company_name": "Microsoft Corp", "ticker": "MSFT", "isin": "US5949181045",
           "mic": "XNAS", "confidence_score": 0.35, "investment_horizon": 30,
           "return_prediction": 0.0}]


class SPCMaintenanceTests(unittest.TestCase):
    def test_sample_accepts_valid_instrument(self):
        self.assertEqual(validate_sample(json.dumps(SAMPLE)), SAMPLE)

    def test_rejects_bad_checksum_duplicate_and_nonfinite(self):
        for sample in [SAMPLE * 2, [{**SAMPLE[0], "isin": "US5949181044"}],
                       [{**SAMPLE[0], "confidence_score": float("nan")}],
                       [{**SAMPLE[0], "investment_horizon": True}]]:
            with self.assertRaises(ValueError):
                validate_sample(json.dumps(sample))

    def test_replacement_count_agrees_and_source_is_preserved(self):
        source = {"name": "Example", "prompt": "Rank exactly 10 distinct stocks.",
                  "sampleOutput": json.dumps(SAMPLE)}
        before = copy.deepcopy(source)
        result = replacement(source, "deepseek", "DeepSeek-V4.1-Flash")
        self.assertIn("Rank exactly 1 distinct", result["prompt"])
        self.assertIn("exactly 1 objects", result["prompt"])
        self.assertEqual(result["weight"], "0.00")
        self.assertEqual(source, before)

    def test_unstable_cannot_be_activated(self):
        client = Client.__new__(Client)
        client.folder = Path(__file__).resolve().parent / "unused_spc_test_log"
        client.listing = lambda: [{"id": "abc", "sampleOutput": json.dumps(SAMPLE),
                                   "status": "Unstable Output", "weight": "0.00"}]
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
        rows = [{"id": "old", "name": "old", "weight": "1.00", "status": "Failed"},
                {"id": "new", "name": "new", "weight": "0.00", "status": "Active",
                 "model": "deepseek", "modelVersion": "DeepSeek-V4.1-Flash",
                 "sampleOutput": json.dumps(SAMPLE), "prompt": "Rank exactly 1 distinct stocks."}]
        client = Client.__new__(Client)
        client.listing = lambda: rows
        operations = []

        def set_weight(identifier, weight):
            operations.append((identifier, weight))
            if identifier == "new":
                raise RuntimeError("activation failed")
            return rows[0]

        client.set_weight = set_weight
        with self.assertRaisesRegex(RuntimeError, "activation failed"):
            swap(client, {"new_name": "new", "model": "deepseek", "modelVersion": "DeepSeek-V4.1-Flash",
                          "source_id": "old", "old_active_ids": ["old"]})
        self.assertEqual(operations, [("old", "0.00"), ("new", "1.00")])

    def test_stable_source_cannot_be_replaced(self):
        client = Client.__new__(Client)
        client.listing = lambda: [{"id": "old", "status": "Active"}]
        client.set_weight = lambda *a: self.fail("must not change a stable source")
        with self.assertRaisesRegex(RuntimeError, "stable source must be preserved"):
            swap(client, {"source_id": "old"})


if __name__ == "__main__":
    unittest.main()
