import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

import msgpack
from openpyxl import load_workbook


TOOL_DIR = (
    Path(__file__).resolve().parents[1]
    / "代码"
    / "优化代码"
    / "Core"
    / "tools"
    / "webdata_quality"
)
sys.path.insert(0, str(TOOL_DIR))

import webdata_quality as tool
from webdata_classifier import classify_field, dataset_grade, load_rules, map_category
from webdata_loader import resolve_source


def packed(value):
    return zlib.compress(msgpack.packb(value, use_bin_type=True))


def sample_snapshot():
    good = {
        "Coverage": [100] * 10,
        "CoverageRatio": [0.82] * 7 + [0.85, 0.86, 0.84],
        "IndicativePositiveRatio": [0.55] * 10,
        "IndicativeNegativeRatio": [0.45] * 10,
        "IntegerStatus": [0] * 10,
        "skenewss": [0.4] * 10,
        "kurtosis": [2.0] * 10,
        "frequency": ["daily"] * 10,
    }
    warning = {
        **good,
        "CoverageRatio": [0.9] * 7 + [1.2, 1.1, 1.0],
    }
    info = {
        "USA_1": {
            "sub_beg_time": "2025-01-01",
            "sub_end_time": "2026-01-01",
            "isos": {
                "mean": {"count": 100, "sharpe_ratio": 0.5, "fitness_ratio": 0.4},
                "total_count": 100,
                "category": {
                    "fundamental": {"count": 10, "sharpe_ratio": 0.2, "fitness_ratio": 0.2},
                    "model": {"count": 10, "sharpe_ratio": 0.6, "fitness_ratio": 0.5},
                    "other": {"count": 10, "sharpe_ratio": 0.1, "fitness_ratio": 0.1},
                },
                "dataset": {
                    "fundamental2": {"count": 10, "sharpe_ratio": -0.1, "fitness_ratio": 0.1},
                    "model1": {"count": 20, "sharpe_ratio": 0.6, "fitness_ratio": 0.5},
                    "search_interest": {"count": 5, "sharpe_ratio": 0.1, "fitness_ratio": 0.1},
                },
                "datafield": {
                    "good_field": {"count": 8, "sharpe_ratio": 0.2, "fitness_ratio": 0.1},
                    "warning_field": {"count": 7, "sharpe_ratio": 0.1, "fitness_ratio": 0.1},
                    "community_only": {"count": 3, "sharpe_ratio": 0.0, "fitness_ratio": 0.0},
                },
            },
            "neutralization": {
                "mean": {"COUNTRY": {"count": 50, "sharpe_ratio": 0.4, "fitness_ratio": 0.3}},
                "category": {},
                "dataset": {
                    "fundamental2": {"COUNTRY": {"count": 5, "sharpe_ratio": 0.1, "fitness_ratio": 0.1}}
                },
                "datafield": {
                    "good_field": {
                        "COUNTRY": {"count": 5, "sharpe_ratio": 0.5, "fitness_ratio": 0.4},
                        "INDUSTRY": {"count": 499, "sharpe_ratio": 0.6, "fitness_ratio": 0.5},
                        "MARKET": {"count": 500, "sharpe_ratio": 0.9, "fitness_ratio": 0.9},
                        "NONE": {"count": 5, "sharpe_ratio": 0.4, "fitness_ratio": 0.5},
                        "SECTOR": {"count": 5, "sharpe_ratio": 0.5, "fitness_ratio": 0.39},
                        "FAST": {"count": 4, "sharpe_ratio": 0.9, "fitness_ratio": 0.9},
                        "SLOW": {"count": 5, "sharpe_ratio": 0.9},
                    },
                    "warning_field": {
                        "COUNTRY": {"count": 6, "sharpe_ratio": 0.7, "fitness_ratio": 0.6}
                    },
                    "neutral_only": {"COUNTRY": {"count": 2, "sharpe_ratio": 0.1, "fitness_ratio": 0.1}},
                },
            },
        }
    }
    osis = {
        "USA_1": {
            "mean": {"count": 90, "sharpe_ratio": 0.45, "fitness_ratio": 0.35},
            "total_count": 90,
            "dataset": {"fundamental2": {"count": 9, "sharpe_ratio": -0.05, "fitness_ratio": 0.1}},
            "category": {"fundamental": {"count": 9, "sharpe_ratio": 0.1, "fitness_ratio": 0.1}},
        }
    }
    return info, osis, {"good_field": good, "warning_field": warning}


def write_snapshot(root, as_zip):
    info, osis, archive = sample_snapshot()
    files = {
        "data/oth/info_data.bin": packed(info),
        "data/oth/osis_data.bin": packed(osis),
        "data/fundamental2_USA_TOP3000_Delay1.bin": packed(archive),
        "data/dataSetList.json": b'["fundamental2_USA_TOP3000_Delay1"]',
    }
    if as_zip:
        path = root / "sample.zip"
        with zipfile.ZipFile(path, "w") as handle:
            for name, data in files.items():
                handle.writestr(name, data)
        return path
    path = root / "extracted"
    for name, data in files.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return path


def all_filters(**overrides):
    filters = {
        "regions": None,
        "delays": None,
        "universes": None,
        "categories": None,
        "dataset_grades": None,
        "field_tiers": None,
        "neutralizations": None,
        "count_min": 5,
        "count_max": 500,
        "sharpe_min": "auto",
        "fitness_min": "auto",
        "dataset": None,
    }
    filters.update(overrides)
    return filters


class WebDataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(TOOL_DIR / "tier_rules.json")

    def test_dataset_and_category_rules(self):
        self.assertEqual(dataset_grade(-0.01, 0.5), "RED")
        self.assertEqual(dataset_grade(0.1, 0.5), "YELLOW")
        self.assertEqual(dataset_grade(0.6, 0.5), "GREEN")
        self.assertEqual(dataset_grade(None, 0.5), "GRAY")
        self.assertEqual(map_category("fundamental2", {"fundamental"}, self.rules), ("fundamental", "CATEGORY_PREFIX"))
        self.assertEqual(map_category("search_interest", {"other"}, self.rules), ("other", "CATEGORY_ALIAS"))
        self.assertEqual(map_category("earningscall_sentiment", {"earnings", "other"}, self.rules), ("other", "CATEGORY_ALIAS"))

    def test_tier_boundaries_and_out_of_range_is_preserved(self):
        _, _, archive = sample_snapshot()
        good = classify_field(archive["good_field"], "fundamental", self.rules)
        warning = classify_field(archive["warning_field"], "fundamental", self.rules)
        self.assertEqual(good["field_tier"], "T2")
        self.assertIn(warning["field_tier"], {"T1", "T2"})
        self.assertIn("COVERAGE_OUT_OF_RANGE", warning["risk_flags"])

    def test_zip_and_extracted_directory_have_same_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledgers = []
            for as_zip in (True, False):
                path = write_snapshot(root, as_zip)
                with resolve_source(path, TOOL_DIR) as source:
                    ledgers.append(tool.build_ledger(source, self.rules, all_filters()))
            for key in ("coordinates", "datasets", "fields", "neutralizations", "annual", "audit"):
                self.assertEqual(ledgers[0][key], ledgers[1][key])

    def test_red_dataset_good_field_is_exported_and_unmapped_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_path = write_snapshot(root, True)
            with resolve_source(source_path, TOOL_DIR) as source:
                ledger = tool.build_ledger(source, self.rules, all_filters())
            self.assertEqual(ledger["audit"]["exact_field_records"], 2)
            self.assertEqual(ledger["audit"]["exported_exact_field_records"], 2)
            self.assertEqual(ledger["audit"]["neutralization_only_fields"], 1)
            self.assertIn("UNMAPPED", ledger["categories"])
            self.assertTrue(any(row["field"] == "neutral_only" for row in ledger["categories"]["UNMAPPED"]["fields"]))

            result = tool.export_ledger(ledger, root / "output")
            workbook = load_workbook(
                root / "output" / "USA" / "fundamental.xlsx",
                data_only=False,
            )
            self.assertEqual(workbook.sheetnames, ["数据"])
            ws = workbook["数据"]
            headers = [cell.value for cell in ws[1]]
            rows = [dict(zip(headers, values)) for values in ws.iter_rows(min_row=2, values_only=True)]
            workbook.close()
            match = next(row for row in rows if row["field"] == "good_field")
            self.assertEqual(match["dataset_grade"], "RED")
            self.assertEqual(match["field_tier"], "T2")
            self.assertEqual(len(rows), 3)
            self.assertEqual([row["sharpe"] for row in rows], [0.7, 0.6, 0.5])
            self.assertTrue(Path(result["readme"]).is_file())
            self.assertFalse((root / "output" / "webdata_quality_full.json").exists())
            self.assertFalse(list((root / "output").rglob("*.json")))

    def test_default_delay_is_d1(self):
        args = tool.build_parser().parse_args([])
        self.assertEqual(args.delay, "1")
        self.assertEqual((args.count_min, args.count_max), ("5", "500"))
        self.assertEqual((args.sharpe_min, args.fitness_min), ("auto", "auto"))

    def test_export_filters_field_tier_neutralization_and_empty_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_snapshot(root, True)
            filters = all_filters(field_tiers={"T2"}, neutralizations={"COUNTRY"})
            with resolve_source(path, TOOL_DIR) as source:
                ledger = tool.build_ledger(source, self.rules, filters)
            tool.export_ledger(ledger, root / "selected")
            workbook = load_workbook(root / "selected" / "USA" / "fundamental.xlsx")
            ws = workbook["数据"]
            headers = [cell.value for cell in ws[1]]
            rows = [dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)]
            workbook.close()
            self.assertEqual([(row["field"], row["neutralization"]) for row in rows], [("good_field", "COUNTRY")])

            ledger["filters"]["count_min"] = 1000
            tool.export_ledger(ledger, root / "empty")
            workbook = load_workbook(root / "empty" / "USA" / "fundamental.xlsx")
            self.assertEqual(workbook["数据"].max_row, 1)
            workbook.close()

    def test_category_filter_does_not_export_unmapped_or_other_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_snapshot(root, True)
            with resolve_source(path, TOOL_DIR) as source:
                ledger = tool.build_ledger(
                    source,
                    self.rules,
                    all_filters(categories={"fundamental"}),
                )
            self.assertEqual(set(ledger["categories"]), {"fundamental"})
            self.assertEqual(ledger["audit"]["unmapped_field_records"], 0)
            self.assertGreater(ledger["audit"]["unmapped_input_records"], 0)

    def test_malformed_archive_is_preserved_only_in_unfiltered_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_snapshot(root, True)
            with zipfile.ZipFile(path, "a") as handle:
                handle.writestr(
                    "data/other395_CHN_TOP3000_Delay1_wrong.bin",
                    packed({"orphan_field": sample_snapshot()[2]["good_field"]}),
                )
            with resolve_source(path, TOOL_DIR) as source:
                ledger = tool.build_ledger(source, self.rules, all_filters())
            orphan = next(row for row in ledger["exact_fields"] if row["field"] == "orphan_field")
            self.assertEqual(orphan["category"], "UNMAPPED")
            self.assertIsNone(orphan["field_tier"])
            self.assertEqual(orphan["field_profile_status"], "ARCHIVE_NAME_UNPARSED")
            self.assertEqual(ledger["audit"]["exact_field_records"], 3)
            self.assertEqual(ledger["audit"]["exported_exact_field_records"], 3)

    def test_invalid_path_prints_help_and_legacy_zip_writes_json(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = tool.main(["--source", "Z:/definitely_missing_snapshot.zip"])
        self.assertEqual(code, 2)
        self.assertIn("Expand-Archive", stderr.getvalue())
        self.assertIn("usage:", stderr.getvalue())

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_snapshot(root, True)
            target = root / "legacy.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = tool.main([
                    "--zip", str(path), "--region", "USA", "--delay", "1",
                    "--universe", "TOP3000", "--dataset", "fundamental2",
                    "--fields", "--json-out", str(target),
                ])
            self.assertEqual(code, 0)
            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["coordinates"], ["USA_1"])


if __name__ == "__main__":
    unittest.main()
