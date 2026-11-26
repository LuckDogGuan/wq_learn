"""离线回归：所有 HTTP 均为模拟，不读取凭据、不连接平台。"""

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "legacy_core"))
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
from Core.api.sim_api import (
    check_alpha_submission_status,
    get_alpha_details,
    is_alpha_submitted,
)
from Core.api.submission import (
    classify_submission_check,
    poll_submission_result,
    run_submission_group,
    submit_all_checked,
    submit_alpha_verified,
    wait_submission_check,
)


def response(data=None, code=200, headers=None, text=""):
    resp = Mock(
        status_code=code,
        headers=dict(headers or {}),
        text=text,
        json=Mock(return_value=data),
    )
    return resp


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
        run.assert_called_once_with(
            ["A", "B"], confirmed_ids={"A", "B"}, poll_max_wait_seconds=180.0
        )

    def test_manual_entry_supports_check_only_and_poll_timeout(self):
        from 提交因子 import submit_alphas as entry
        with patch.object(sys, "argv", ["submit_alphas.py", "--check-only", "--poll-timeout", "90", "A"]), \
             patch.object(entry, "run_submission_group", return_value=True) as run:
            self.assertEqual(entry.main(), 0)
        run.assert_called_once_with(["A"], check_only=True, poll_max_wait_seconds=90.0)

    def test_check_polls_empty_retry_after_then_reads_result(self):
        pending = response(headers={"Retry-After": "1.0"})
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
        pending = response(headers={"Retry-After": "1"})
        client = Mock()
        client.get.return_value = pending
        with patch("Core.api.submission.asyncio.sleep", new_callable=AsyncMock):
            state, _ = asyncio.run(wait_submission_check(client, "A", report=Mock(), max_attempts=2))
        self.assertEqual(state, "PENDING")
        self.assertEqual(client.get.call_count, 2)
        client.post.assert_not_called()

    def test_async_post_201_polls_get_submit_then_confirms_os(self):
        post_resp = response(code=201, headers={"Retry-After": "1.0"})
        post_resp.json.side_effect = ValueError("html body")
        poll_pending = response(code=200, headers={"Retry-After": "1.0"})
        poll_pending.json.side_effect = ValueError("html body")
        poll_done = response({"is": {"checks": [{"name": "SHARPE", "result": "PASS"}]}}, code=200)

        client = Mock()
        client.post.return_value = post_resp
        client.get.side_effect = [
            response(UNSUBMITTED),  # pre-check /alphas/A
            poll_pending,           # /alphas/A/submit #1
            poll_pending,           # /alphas/A/submit #2
            poll_done,              # /alphas/A/submit #3 done
            response(SUBMITTED),    # final /alphas/A confirmation
        ]
        logs = []
        with patch("Core.api.submission.time.sleep") as sleep:
            ok = submit_alpha_verified(client, "A", report=logs.append, confirmed_alpha_id="A")
        self.assertTrue(ok)
        client.post.assert_called_once_with("/alphas/A/submit")
        self.assertEqual(client.get.call_count, 5)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1.0, 1.0, 1.0])
        self.assertTrue(any("已确认提交成功" in line for line in logs))

    def test_async_post_201_retries_detail_once_after_done(self):
        client = Mock()
        client.post.return_value = response(code=201, headers={"Retry-After": "1.0"})
        client.get.side_effect = [
            response(UNSUBMITTED),
            response({"is": {"checks": [{"name": "SHARPE", "result": "PASS"}]}}, code=200),
            response(UNSUBMITTED),  # first detail check right after done
            response(SUBMITTED),    # reconciled 2s later
        ]
        with patch("Core.api.submission.time.sleep") as sleep:
            ok = submit_alpha_verified(client, "A", report=Mock(), confirmed_alpha_id="A")
        self.assertTrue(ok)
        client.post.assert_called_once()
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1.0, 2.0])

    def test_async_get_submit_403_prints_failed_checks(self):
        client = Mock()
        client.post.return_value = response(code=201, headers={"Retry-After": "1.0"})
        client.get.side_effect = [
            response(UNSUBMITTED),
            response(
                {
                    "is": {
                        "checks": [
                            {"name": "LOW_2Y_SHARPE", "result": "FAIL", "value": 1.2, "limit": 1.58},
                            {"name": "PROD_CORRELATION", "result": "FAIL", "value": 0.78, "limit": 0.7},
                        ]
                    }
                },
                code=403,
            ),
        ]
        logs = []
        with patch("Core.api.submission.time.sleep"):
            ok = submit_alpha_verified(client, "A", report=logs.append, confirmed_alpha_id="A")
        self.assertFalse(ok)
        client.post.assert_called_once()
        joined = "\n".join(logs)
        self.assertIn("HTTP 403", joined)
        self.assertIn("LOW_2Y_SHARPE=FAIL(value=1.2, limit=1.58)", joined)
        self.assertIn("PROD_CORRELATION=FAIL(value=0.78, limit=0.7)", joined)

    def test_async_get_submit_403_already_submitted_returns_true(self):
        client = Mock()
        client.post.return_value = response(code=201, headers={"Retry-After": "1.0"})
        client.get.side_effect = [
            response(UNSUBMITTED),
            response({"is": {"checks": [{"name": "ALREADY_SUBMITTED", "result": "FAIL"}]}}, code=403),
        ]
        with patch("Core.api.submission.time.sleep"):
            ok = submit_alpha_verified(client, "A", report=Mock(), confirmed_alpha_id="A")
        self.assertTrue(ok)
        client.post.assert_called_once()

    def test_async_get_submit_404_checks_detail_before_failing(self):
        client = Mock()
        client.post.return_value = response(code=201, headers={"Retry-After": "1.0"})
        client.get.side_effect = [
            response(UNSUBMITTED),
            response({}, code=404),
            response(UNSUBMITTED),
        ]
        logs = []
        with patch("Core.api.submission.time.sleep"):
            ok = submit_alpha_verified(client, "A", report=logs.append, confirmed_alpha_id="A")
        self.assertFalse(ok)
        self.assertTrue(any("HTTP 404" in line for line in logs))

    def test_async_poll_bounded_reports_pending_without_repost(self):
        client = Mock()
        client.post.return_value = response(code=201, headers={"Retry-After": "1.0"})
        client.get.side_effect = [
            response(UNSUBMITTED),
            response(code=200, headers={"Retry-After": "1.0"}),
            response(code=200, headers={"Retry-After": "1.0"}),
        ]
        logs = []
        with patch("Core.api.submission.time.sleep"):
            ok = submit_alpha_verified(
                client, "A", report=logs.append, confirmed_alpha_id="A", poll_max_attempts=2
            )
        self.assertFalse(ok)
        client.post.assert_called_once()
        joined = "\n".join(logs)
        self.assertIn("PENDING", joined)
        self.assertIn("--check-only", joined)

    def test_post_429_is_explicitly_reported_without_blind_repost(self):
        client = Mock()
        client.get.side_effect = [response(UNSUBMITTED)]
        client.post.return_value = response({}, code=429, headers={"Retry-After": "5"})
        logs = []
        with patch("Core.api.submission.time.sleep") as sleep:
            ok = submit_alpha_verified(client, "A", report=logs.append, confirmed_alpha_id="A")
        self.assertFalse(ok)
        client.post.assert_called_once()
        self.assertEqual(client.get.call_count, 1)
        sleep.assert_not_called()
        joined = "\n".join(logs)
        self.assertIn("RATE_LIMITED", joined)
        self.assertIn("HTTP 429", joined)
        self.assertIn("Retry-After=5s", joined)

    def test_post_400_already_reconciles_readonly(self):
        client = Mock()
        client.post.return_value = response({"detail": "Alpha is already submitted"}, code=400)
        client.get.side_effect = [response(UNSUBMITTED), response(SUBMITTED)]
        ok = submit_alpha_verified(client, "A", report=Mock(), confirmed_alpha_id="A")
        self.assertTrue(ok)
        client.post.assert_called_once()

    def test_sync_post_and_transient_reconcile_scenarios(self):
        scenarios = [
            ("200 sync but unsubmitted", [UNSUBMITTED, UNSUBMITTED], [response()], False, 1, 1),
            ("already submitted", [SUBMITTED], [], True, 0, 0),
            ("200 sync confirmed", [UNSUBMITTED, SUBMITTED], [response()], True, 1, 1),
            ("200 error", [UNSUBMITTED], [response({"error": "rejected"})], False, 1, 0),
            ("http 403 rejection", [UNSUBMITTED], [response({}, 403)], False, 1, 0),
            ("no response but committed", [UNSUBMITTED, SUBMITTED], [None], True, 1, 1),
            ("unknown after submit", [UNSUBMITTED, {}], [response()], False, 1, 1),
            ("initial unknown", [{}], [], False, 0, 0),
            ("detail error", [{"error": "invalid alpha"}], [], False, 0, 0),
            ("post detail error", [UNSUBMITTED, {"error": "invalid alpha"}], [response()], False, 1, 1),
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
                self.assertTrue(all(call.args == (2,) or call.args == (2.0,) for call in sleep.call_args_list))

    def test_poll_submission_result_handles_invalid_retry_after(self):
        client = Mock()
        client.get.return_value = response(code=200, headers={"Retry-After": "nan"})
        with patch("Core.api.submission.time.sleep") as sleep:
            state, _ = poll_submission_result(client, "A", report=Mock())
        self.assertEqual(state, "PENDING")
        sleep.assert_not_called()

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
        detail_response = response(SUBMITTED, headers={"retry-after": "10"})
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
        current = {"is_submitted": False, "stage": "IS", "status": "UNSUBMITTED"}
        with patch("Core.api.submission.wait_submission_check", new_callable=AsyncMock,
                   side_effect=[("PASS", "ok"), ("ERROR", "fail"), RuntimeError("temporary")]) as check, \
                patch("Core.api.submission.BrainClient"), \
                patch("Core.api.submission.check_alpha_submission_status",
                      return_value=current), \
                patch("Core.api.submission.submit_alpha_verified",
                      return_value=False) as submit, \
                patch("Core.api.submission.asyncio.sleep", new_callable=AsyncMock) as sleep:
            self.assertFalse(asyncio.run(submit_all_checked(
                session, ["A", "B", "C"], confirmed_ids={"A", "B", "C"}
            )))
            self.assertEqual([call.args[1] for call in submit.call_args_list], ["A"])
            self.assertEqual(check.await_count, 3)
            # 1s post-check cooldown + 2s between-alphas cooldown after A
            self.assertEqual([call.args[0] for call in sleep.await_args_list], [1.0, 2.0])

    def test_check_only_mode_never_submits_and_requires_no_confirmation(self):
        session = Mock()
        current = {"is_submitted": False, "stage": "IS", "status": "UNSUBMITTED"}
        with patch("Core.api.submission.create_submit_session", return_value=session), \
             patch("Core.api.submission.BrainClient"), \
             patch("Core.api.submission.check_alpha_submission_status", return_value=current), \
             patch("Core.api.submission.wait_submission_check", new_callable=AsyncMock,
                   return_value=("PASS", "check 成功")), \
             patch("Core.api.submission.submit_alpha_verified") as submit:
            self.assertTrue(run_submission_group(["A"], report=Mock(), check_only=True))
            submit.assert_not_called()
            session.close.assert_called_once()

    def test_already_submitted_skips_check_and_post(self):
        session = Mock()
        with patch("Core.api.submission.BrainClient"), \
                patch("Core.api.submission.check_alpha_submission_status",
                      return_value={"is_submitted": True, "status": "ACTIVE", "date_submitted": "2026-09-06"}), \
                patch("Core.api.submission.submit_alpha_verified") as submit:
            self.assertTrue(asyncio.run(submit_all_checked(
                session, ["A"], confirmed_ids={"A"}
            )))
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
