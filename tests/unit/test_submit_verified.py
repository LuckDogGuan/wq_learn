"""离线回归：所有 HTTP 均为模拟，不读取凭据、不连接平台。"""

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "代码/优化代码"))
from Core.api.sim_api import (
    check_alpha_submission_status,
    get_alpha_details,
    is_alpha_submitted,
)
from Core.api.submission import (
    classify_submission_check,
    submit_all_checked,
    submit_alpha_verified,
    wait_submission_check,
)


def response(data=None, code=200):
    return Mock(status_code=code, headers={}, json=Mock(return_value=data))


UNSUBMITTED = {"id": "A", "stage": "IS", "status": "UNSUBMITTED"}
SUBMITTED = {
    "id": "A", "stage": "OS", "status": "ACTIVE",
    "dateSubmitted": "2026-09-06",
}


class SubmissionTests(unittest.TestCase):
    def test_manual_entry_uses_configured_ids_without_second_confirmation(self):
        from 提交因子 import submit_alphas as entry
        with patch.object(entry, "ALPHA_IDS", ["A", "B", "A"]), \
             patch.object(sys, "argv", ["submit_alphas.py"]), \
             patch("builtins.input", side_effect=AssertionError("no second confirmation")), \
             patch.object(entry, "run_submission_group", return_value=True) as run:
            self.assertEqual(entry.main(), 0)
        run.assert_called_once_with(["A", "B"], confirmed_ids={"A", "B"})

    def test_check_polls_empty_retry_after_then_reads_result(self):
        pending = response()
        pending.headers = {"Retry-After": "1.0"}
        pending.json.side_effect = ValueError("empty body")
        client = Mock()
        client.get.side_effect = [pending, response({"is": {"checks": [{"result": "PASS"}]}})]
        with patch("Core.api.submission.asyncio.sleep", new_callable=AsyncMock) as sleep:
            state, _ = asyncio.run(wait_submission_check(client, "A", report=Mock()))
        self.assertEqual(state, "PASS")
        self.assertEqual(client.get.call_count, 2)
        sleep.assert_awaited_once_with(1.0)
        client.post.assert_not_called()

    def test_check_wait_is_bounded(self):
        pending = response()
        pending.headers = {"Retry-After": "1"}
        client = Mock()
        client.get.return_value = pending
        with patch("Core.api.submission.asyncio.sleep", new_callable=AsyncMock):
            state, _ = asyncio.run(wait_submission_check(client, "A", report=Mock(), max_attempts=2))
        self.assertEqual(state, "PENDING")
        self.assertEqual(client.get.call_count, 2)
        client.post.assert_not_called()

    def test_one_post_and_one_final_status_query(self):
        scenarios = [
            ("200 but unsubmitted", [UNSUBMITTED, UNSUBMITTED], [response()], False, 1, 1),
            ("already submitted", [SUBMITTED], [], True, 0, 0),
            ("confirmed", [UNSUBMITTED, SUBMITTED], [response()], True, 1, 1),
            ("200 error", [UNSUBMITTED], [response({"error": "rejected"})], False, 1, 0),
            ("http rejection", [UNSUBMITTED], [response({}, 403)], False, 1, 0),
            ("no response but committed", [UNSUBMITTED, SUBMITTED], [None], True, 1, 1),
            ("unknown after submit", [UNSUBMITTED, {}], [response()], False, 1, 1),
            ("initial unknown", [{}], [], False, 0, 0),
            ("detail error", [{"error": "invalid alpha"}], [], False, 0, 0),
            ("post detail error", [UNSUBMITTED, {"error": "invalid alpha"}], [response()], False, 1, 1),
            ("429 then unsubmitted", [UNSUBMITTED, UNSUBMITTED], [response({}, 429)], False, 1, 1),
            ("503 then unsubmitted", [UNSUBMITTED, UNSUBMITTED], [response({}, 503)], False, 1, 1),
        ]
        for name, details, posts, expected, post_count, sleeps in scenarios:
            with self.subTest(name=name), patch("Core.api.submission.time.sleep") as sleep:
                client = Mock()
                client.get.side_effect = [response(data) for data in details]
                client.post.side_effect = posts
                self.assertIs(submit_alpha_verified(
                    client, "A", report=Mock(), confirmed_alpha_id="A"
                ), expected)
                self.assertEqual(client.post.call_count, post_count)
                self.assertEqual(client.get.call_count, len(details))
                self.assertEqual(sleep.call_count, sleeps)
                self.assertTrue(all(call.args == (2,) for call in sleep.call_args_list))

    def test_malformed_details_are_pending(self):
        for data in (None, [], {}, {"id": "A"}, {"stage": "IS"},
                     {**SUBMITTED, "id": "B"}, {"id": "A", "is": [1]}):
            with self.subTest(data=data):
                client = Mock()
                client.get.return_value = response(data)
                self.assertIsNone(check_alpha_submission_status(client, "A")["is_submitted"])

    def test_submit_requires_exact_current_confirmation(self):
        client = Mock()
        self.assertFalse(submit_alpha_verified(client, "A", report=Mock()))
        self.assertFalse(submit_alpha_verified(
            client, "A", report=Mock(), confirmed_alpha_id="B"
        ))
        client.get.assert_not_called()
        client.post.assert_not_called()

    def test_detail_queries_once_even_with_retry_after_header(self):
        client = Mock()
        detail_response = response(SUBMITTED)
        detail_response.headers = {"retry-after": "10"}
        client.get.return_value = detail_response
        self.assertEqual(get_alpha_details(client, "A"), SUBMITTED)
        client.get.assert_called_once()

    def test_submitted_requires_date_and_os_confirmation(self):
        self.assertTrue(is_alpha_submitted(SUBMITTED))
        self.assertFalse(is_alpha_submitted({**SUBMITTED, "dateSubmitted": None}))
        self.assertFalse(is_alpha_submitted({
            "id": "A", "stage": "IS", "status": "UNSUBMITTED",
            "dateSubmitted": "2026-09-06",
        }))

    def test_core_entry_checks_each_alpha_once(self):
        session = Mock()
        session.check = AsyncMock(side_effect=[
            response({"is": {"checks": [{"result": "PASS"}]}}),
            response({"is": {"checks": [{"result": "FAIL"}]}}),
            RuntimeError("temporary"),
        ])
        current = {"is_submitted": False}
        with patch("Core.api.submission.wait_submission_check", new_callable=AsyncMock,
                   side_effect=[("PASS", "ok"), ("ERROR", "fail"), RuntimeError("temporary")]) as check, \
                patch("Core.api.submission.BrainClient"), \
                patch("Core.api.submission.check_alpha_submission_status",
                      return_value=current), \
                patch("Core.api.submission.submit_alpha_verified",
                      return_value=False) as submit:
            self.assertFalse(asyncio.run(submit_all_checked(
                session, ["A", "B", "C"], confirmed_ids={"A", "B", "C"}
            )))
            self.assertEqual([call.args[1] for call in submit.call_args_list], ["A"])
            self.assertEqual(check.await_count, 3)

    def test_already_submitted_skips_check_and_post(self):
        session = Mock()
        with patch("Core.api.submission.BrainClient"), \
                patch("Core.api.submission.check_alpha_submission_status",
                      return_value={"is_submitted": True}), \
                patch("Core.api.submission.submit_alpha_verified") as submit:
            self.assertTrue(asyncio.run(submit_all_checked(
                session, ["A"], confirmed_ids={"A"}
            )))
            session.check.assert_not_called()
            submit.assert_not_called()

    def test_initial_pending_or_error_skips_check_and_post(self):
        for current in (
            {"is_submitted": None},
            {"is_submitted": None, "error": "HTTP 404"},
        ):
            with self.subTest(current=current):
                session = Mock()
                with patch("Core.api.submission.BrainClient"), \
                        patch("Core.api.submission.check_alpha_submission_status",
                              return_value=current), \
                        patch("Core.api.submission.submit_alpha_verified") as submit:
                    self.assertFalse(asyncio.run(submit_all_checked(
                        session, ["A"], confirmed_ids={"A"}
                    )))
                    session.check.assert_not_called()
                    submit.assert_not_called()

    def test_submission_check_classification(self):
        cases = [
            (None, "PENDING"),
            (response({"error": "unauthorized"}, 401), "PENDING"),
            (response({"error": "rate limited"}, 429), "PENDING"),
            (response({"error": "unavailable"}, 503), "PENDING"),
            (response({}, 429), "PENDING"),
            (response({}, 503), "PENDING"),
            (response({}, 403), "ERROR"),
            (response({"error": "rejected"}), "ERROR"),
            (response({"is": {"checks": []}}), "PENDING"),
            (response({"is": {"checks": [{"result": "PENDING"}]}}), "PENDING"),
            (response({"is": {"checks": [{"result": "FAIL"}]}}), "ERROR"),
            (response({"is": {"checks": [
                {"result": "PASS"}, {"result": "WARNING"},
            ]}}), "PASS"),
        ]
        for check_response, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_submission_check(check_response)[0], expected)


if __name__ == "__main__":
    unittest.main()
