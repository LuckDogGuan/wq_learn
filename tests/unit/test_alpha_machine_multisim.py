import ast
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_PARENT = REPO_ROOT / "代码" / "优化代码"
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.sim import sim_engine


class TestPayloadSettings(unittest.TestCase):
    def test_two_item_payload_uses_default_maxtrade_off(self):
        payload = sim_engine.build_sim_payload(
            "rank(close)", 6, "GBR", "TOP700", "SUBINDUSTRY", "P2Y"
        )

        self.assertEqual(payload, {
            "type": "REGULAR",
            "settings": {
                "instrumentType": "EQUITY",
                "region": "GBR",
                "universe": "TOP700",
                "delay": 1,
                "decay": 6,
                "neutralization": "SUBINDUSTRY",
                "truncation": 0.08,
                "pasteurization": "ON",
                "testPeriod": "P2Y",
                "unitHandling": "VERIFY",
                "nanHandling": "ON",
                "maxTrade": "OFF",
                "language": "FASTEXPR",
                "visualization": False,
            },
            "regular": "rank(close)",
        })

    def test_each_expression_can_override_research_settings(self):
        payloads = sim_engine.generate_sim_data([
            ("rank(close)", 4, {
                "neutralization": "INDUSTRY",
                "truncation": 0.05,
                "nanHandling": "OFF",
                "testPeriod": "P1Y",
                "maxTrade": "ON",
            }),
            ("rank(open)", 9, {"pasteurization": "OFF", "visualization": True}),
        ], "GBR", "TOP700", "SUBINDUSTRY")

        self.assertEqual(payloads[0]["settings"]["decay"], 4)
        self.assertEqual(payloads[0]["settings"]["neutralization"], "INDUSTRY")
        self.assertEqual(payloads[0]["settings"]["truncation"], 0.05)
        self.assertEqual(payloads[0]["settings"]["nanHandling"], "OFF")
        self.assertEqual(payloads[0]["settings"]["testPeriod"], "P1Y")
        self.assertEqual(payloads[0]["settings"]["maxTrade"], "ON")
        self.assertEqual(payloads[1]["settings"]["decay"], 9)
        self.assertEqual(payloads[1]["settings"]["pasteurization"], "OFF")
        self.assertTrue(payloads[1]["settings"]["visualization"])
        self.assertEqual(payloads[1]["settings"]["maxTrade"], "OFF")

    def test_unknown_or_protected_settings_fail_before_submission(self):
        with self.assertRaisesRegex(ValueError, "region"):
            sim_engine.build_sim_payload(
                "rank(close)", 6, "GBR", "TOP700", "SUBINDUSTRY",
                settings_overrides={"region": "USA"},
            )
        with self.assertRaisesRegex(TypeError, "dict"):
            sim_engine.build_sim_payload(
                "rank(close)", 6, "GBR", "TOP700", "SUBINDUSTRY",
                settings_overrides=[],
            )


class TestMultiSimulationRetries(unittest.TestCase):
    def setUp(self):
        self.items = [
            ("alpha_0", 1),
            ("alpha_1", 2, {"truncation": 0.04}),
            ("alpha_2", 3),
            ("alpha_3", 4, {"nanHandling": "OFF"}),
        ]

    def _run(self, post_results, poll_results):
        with (
            patch.object(sim_engine, "login", return_value=MagicMock()),
            patch.object(sim_engine, "post_multi_simulation", side_effect=post_results) as post_mock,
            patch.object(sim_engine, "poll_simulation_progress", side_effect=poll_results) as poll_mock,
        ):
            sim_engine.multi_simulate(
                [[self.items]], "SUBINDUSTRY", "GBR", "TOP700", 0
            )
        return post_mock, poll_mock

    def test_two_filtered_retries_keep_survivors_and_settings(self):
        post_mock, poll_mock = self._run(
            ["url-1", "url-2", "url-3"],
            [
                {"status": "ERROR", "message": "Got invalid input at index 1, must be an event data"},
                {"status": "ERROR", "errors": [{"index": 0, "message": "Invalid data field"}]},
                {"status": "COMPLETE"},
            ],
        )

        submitted = [[payload["regular"] for payload in call.args[1]] for call in post_mock.call_args_list]
        self.assertEqual(submitted, [
            ["alpha_0", "alpha_1", "alpha_2", "alpha_3"],
            ["alpha_0", "alpha_2", "alpha_3"],
            ["alpha_2", "alpha_3"],
        ])
        self.assertEqual(post_mock.call_args_list[1].args[1][2]["settings"]["nanHandling"], "OFF")
        self.assertEqual(post_mock.call_count, 3)
        self.assertEqual(poll_mock.call_count, 3)

    def test_third_error_does_not_create_fourth_submission(self):
        post_mock, poll_mock = self._run(
            ["url-1", "url-2", "url-3"],
            [
                {"status": "ERROR", "message": "invalid input at index 0"},
                {"status": "ERROR", "message": "invalid input at index 0"},
                {"status": "ERROR", "message": "invalid input at index 0"},
            ],
        )

        self.assertEqual(post_mock.call_count, 3)
        self.assertEqual(poll_mock.call_count, 3)

    def test_error_without_valid_index_is_not_retried(self):
        for result in (
            {"status": "ERROR", "message": "Invalid data field"},
            {"status": "ERROR", "index": 99},
        ):
            with self.subTest(result=result):
                post_mock, poll_mock = self._run(["url-1"], [result])
                self.assertEqual(post_mock.call_count, 1)
                self.assertEqual(poll_mock.call_count, 1)

    def test_unobserved_submission_or_poll_is_not_retried(self):
        with (
            patch.object(sim_engine, "login", return_value=MagicMock()),
            patch.object(sim_engine, "post_multi_simulation", return_value=None) as post_mock,
            patch.object(sim_engine, "poll_simulation_progress") as poll_mock,
        ):
            sim_engine.multi_simulate([[self.items]], "SUBINDUSTRY", "GBR", "TOP700", 0)
        self.assertEqual(post_mock.call_count, 1)
        poll_mock.assert_not_called()

        post_mock, poll_mock = self._run(["url-1"], [{}])
        self.assertEqual(post_mock.call_count, 1)
        self.assertEqual(poll_mock.call_count, 1)


class TestNotebookSyntaxFilter(unittest.TestCase):
    def test_notebook_filter_preserves_valid_items_and_settings(self):
        notebook_path = (
            CORE_PARENT / "Core" / "notebooks" / "Alpha_Machine.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        source = next(
            "".join(cell["source"]) for cell in notebook["cells"]
            if cell["cell_type"] == "code"
            and "def filter_valid_alpha_items" in "".join(cell["source"])
        )
        tree = ast.parse(source)
        helper = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "filter_valid_alpha_items"
        )
        namespace = {
            "batch_verify_expressions": lambda expressions: [
                {"valid": True, "errors": []},
                {"valid": False, "errors": ["bad syntax"]},
                {"valid": True, "errors": []},
            ]
        }
        exec(compile(ast.Module(body=[helper], type_ignores=[]), str(notebook_path), "exec"), namespace)

        items = [
            ("alpha_0", 1),
            ("alpha_bad", 2),
            ("alpha_2", 3, {"truncation": 0.03}),
        ]
        filtered = namespace["filter_valid_alpha_items"](items, "测试")

        self.assertEqual(filtered, [items[0], items[2]])


if __name__ == "__main__":
    unittest.main()
