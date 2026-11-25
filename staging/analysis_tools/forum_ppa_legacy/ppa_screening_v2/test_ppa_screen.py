import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from ppa_screen import (_api_query_spec, classify, date_window, intersect_scope_window,
                        load_scope, screen_pipeline, subtract_months, write_reports)


STANDARD = {
    "entry_requirements": {
        "sharpe_min": 1.0, "operators_max": 8,
        "unique_data_fields_max_excluding_support_fields": 3,
        "turnover": {"min": 0.01, "max": 0.70},
    }
}
SCOPE = {"core_requirements": {
    "region": "GLB", "delay": 1, "universe": "TOPDIV3000",
    "neutralization": ["RAM"], "forbidden_datasets": ["PV1", "MODEL110"],
}}


def alpha(**overrides):
    value = {
        "id": "a1", "status": "UNSUBMITTED",
        "settings": {"region": "GLB", "delay": 1, "universe": "TOPDIV3000", "neutralization": "RAM"},
        "datasets": ["fundamental"], "fields": ["book_value"],
        "sharpe": 1.2, "turnover": 0.2, "operator_count": 2,
        "check_payload": {"is": {"checks": [
            {"name": "LOW_TURNOVER", "result": "PASS"},
            {"name": "MATCHES_THEMES", "result": "PASS"},
            {"name": "PURE_POWER_POOL_THEME", "result": "PASS"},
            {"name": "POWER_POOL_CORRELATION", "result": "PASS", "value": 0.1},
            {"name": "POWER_POOL_DESCRIPTION_LENGTH", "result": "PASS"},
            {"name": "POWER_POOL_DESCRIPTION_FORMAT", "result": "PASS"},
        ]}},
    }
    value.update(overrides)
    return value


class ScreeningTests(unittest.TestCase):
    def test_pass(self):
        result = classify(alpha(), STANDARD, SCOPE, alpha()["check_payload"])
        self.assertEqual(result["classification"], "PPA_PASS")
        self.assertEqual(result["base_scope"]["region"], "GLB")
        self.assertEqual(result["base_scope"]["universe"], "TOPDIV3000")

    def test_theme_mismatch_is_excluded(self):
        value = alpha(settings={"region": "GLB", "delay": 1, "universe": "TOP3000", "neutralization": "RAM"})
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "EXCLUDED")

    def test_theme_label_matches_platform_enum(self):
        value = alpha(settings={"region": "GLB", "delay": 1, "universe": "TOPDIV3000",
                                "neutralization": "REVERSION_AND_MOMENTUM"})
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PPA_PASS")

    def test_short_platform_neutralization_enum(self):
        value = alpha(settings={"region": "GLB", "delay": 1, "universe": "TOPDIV3000",
                                "neutralization": "SLOW"})
        scope = {"core_requirements": {**SCOPE["core_requirements"],
                                       "neutralization": ["Slow Factors"]}}
        self.assertEqual(classify(value, STANDARD, scope, value["check_payload"])["classification"], "PPA_PASS")

    def test_platform_neutralization_aliases(self):
        for platform_value, theme_value in (("SLOW_AND_FAST", "Slow + Fast Factors"),
                                             ("SLOW_AND_FAST_FACTORS", "Slow + Fast Factors"),
                                             ("REVERSION_AND_MOMENTUM", "RAM")):
            value = alpha(settings={"region": "GLB", "delay": 1, "universe": "TOPDIV3000",
                                    "neutralization": platform_value})
            scope = {"core_requirements": {**SCOPE["core_requirements"],
                                           "neutralization": [theme_value]}}
            self.assertEqual(classify(value, STANDARD, scope, value["check_payload"])["classification"], "PPA_PASS")

    def test_forbidden_dataset_fails(self):
        value = alpha(datasets=["PV1"])
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "FAIL")

    def test_forbidden_dataset_support_field_exception(self):
        value = alpha(datasets=["PV1"], fields=["country"])
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PPA_PASS")

    def test_dynamic_forbidden_field_rules(self):
        scope = {**SCOPE, "forbidden_field_rules": {
            "PV1": {"forbidden_fields": ["close"]},
            "MODEL110": {"forbidden_prefixes": ["mdl110_"]},
        }}
        value = alpha(datasets=["fundamental"], fields=["mdl110_fake"])
        result = classify(value, STANDARD, scope, value["check_payload"])
        self.assertEqual(result["classification"], "FAIL")
        self.assertIn("mdl110_fake", result["reasons"][0])
        value = alpha(datasets=["fundamental"], fields=["close"])
        self.assertEqual(classify(value, STANDARD, scope, value["check_payload"])["classification"], "FAIL")

    def test_scope_loads_external_forbidden_field_json(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            scope_path = folder / "theme.json"
            config_path = folder / "ppa_forbidden_fields.json"
            scope_path.write_text(json.dumps({
                "forbidden_field_rules_file": config_path.name,
                "core_requirements": {},
            }), encoding="utf-8")
            config_path.write_text(json.dumps({
                "forbidden_field_rules": {"MODEL110": {"forbidden_prefixes": ["mdl110_"]}}
            }), encoding="utf-8")
            loaded = load_scope(scope_path)
            self.assertEqual(loaded["forbidden_field_rules"]["MODEL110"]["forbidden_prefixes"], ["mdl110_"])

    def test_inclusive_thresholds_pass(self):
        value = alpha(sharpe=1.0, turnover=0.01, operator_count=8, fields=["a", "b", "c"])
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PPA_PASS")
        value["turnover"] = 0.70
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PPA_PASS")

    def test_low_sharpe_check_value_fails_even_if_result_is_pending(self):
        value = alpha(check_payload={"is": {"checks": [
            {"name": "LOW_SHARPE", "result": "PENDING", "value": 0.9},
            {"name": "POWER_POOL_CORRELATION", "result": "PASS"},
        ]}})
        result = classify(value, STANDARD, SCOPE, value["check_payload"])
        self.assertEqual(result["classification"], "FAIL")
        self.assertEqual(result["failed_ppa_items"][0]["name"], "LOW_SHARPE")

    def test_ppa_pending_check_is_not_failure(self):
        value = alpha(check_payload={"is": {"checks": [
            {"name": "LOW_TURNOVER", "result": "PENDING"},
            {"name": "POWER_POOL_CORRELATION", "result": "PASS"},
        ]}})
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PENDING")

    def test_self_correlation_requires_exception_evidence(self):
        checks = alpha()["check_payload"]["is"]["checks"]
        checks = [dict(item) for item in checks]
        checks[3]["value"] = 0.51
        value = alpha(check_payload={"is": {"checks": checks}})
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "FAIL")
        value["self_correlation_exception_pass"] = True
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PPA_PASS")

    def test_missing_correlation_is_pending(self):
        value = alpha(check_payload={"is": {"checks": [{"name": "LOW_TURNOVER", "result": "PASS"}]}})
        self.assertEqual(classify(value, STANDARD, SCOPE, value["check_payload"])["classification"], "PENDING")

    def test_conflict_is_not_guessed(self):
        scope = {"core_requirements": {**SCOPE["core_requirements"], "sharpe_min": 1.1}}
        self.assertEqual(classify(alpha(), STANDARD, scope, alpha()["check_payload"])["classification"], "RULE_CONFLICT")

    def test_month_window(self):
        self.assertEqual(subtract_months(date(2026, 3, 31)), date(2026, 2, 28))
        window = date_window("2026-07-01", "2026-07-31")
        self.assertEqual(window.start.date().isoformat(), "2026-07-01")
        self.assertEqual(window.end.date().isoformat(), "2026-08-01")

    def test_api_query_uses_platform_timezone_and_explicit_filters(self):
        spec = _api_query_spec(SCOPE, STANDARD, date_window("2026-07-01", "2026-07-31"))
        self.assertEqual(spec["timezone"], "America/New_York")
        self.assertEqual(spec["filters"]["date_created"],
                         "[2026-07-01T00:00:00-04:00, 2026-08-01T00:00:00-04:00)")
        self.assertEqual(spec["filters"]["sharpe"], "(1, inf)")
        self.assertEqual(spec["filters"]["status"], "UNSUBMITTED")
        self.assertEqual(spec["filters"]["instrument_type"], "EQUITY")

    def test_scope_window_intersection(self):
        window = intersect_scope_window(date_window("2026-06-30", "2026-08-01"), {
            "duration": {"start_date": "2026-07-27", "end_date": "2026-08-09"}
        })
        self.assertEqual(window.start.date().isoformat(), "2026-07-27")
        self.assertEqual(window.end.date().isoformat(), "2026-08-02")

    def test_report_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rows = [classify(alpha(), STANDARD, SCOPE, alpha()["check_payload"])]
            write_reports(rows, output)
            self.assertTrue((output / "pass" / "a1.json").exists())
            self.assertEqual(json.loads((output / "summary.json").read_text())["count"], 1)

    def test_linear_pipeline_reports_each_stage(self):
        value = alpha()
        value["regular"] = {"code": "rank(book_value)", "operatorCount": 1}
        reports, final_rows, steps = screen_pipeline([value], {"a1": value["check_payload"]}, STANDARD, SCOPE)
        self.assertEqual([step["stage"] for step in steps], [
            "load_scope_json",
            "query_scope_region_delay_universe_sharpe", "neutralization_and_turnover",
            "error_check", "forbidden_datasets", "power_pool_self_correlation",
            "unique_fields_and_operators",
        ])
        self.assertEqual(steps[-1]["remaining"], 1)
        self.assertEqual(reports[-1]["classification"], "PPA_PASS")
        self.assertEqual(len(final_rows), 1)

    def test_pipeline_excludes_platform_error(self):
        value = alpha(check_payload={"is": {"checks": [
            {"name": "DATA_ERROR", "result": "ERROR"},
        ]}})
        reports, _, steps = screen_pipeline([value], {"a1": value["check_payload"]}, STANDARD, SCOPE)
        self.assertEqual(reports[0]["classification"], "EXCLUDED")
        self.assertEqual(steps[3]["remaining"], 0)


if __name__ == "__main__":
    unittest.main()
