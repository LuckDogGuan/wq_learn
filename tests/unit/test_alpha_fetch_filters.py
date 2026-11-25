import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_PARENT = REPO_ROOT / "代码" / "优化代码"
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.api import sim_api
from Core.sim import alpha_manager


def response(results, count=None):
    mock = MagicMock(status_code=200)
    payload = {"results": results}
    if count is not None:
        payload["count"] = count
    mock.json.return_value = payload
    return mock


def alpha_item(index, sharpe=1.5, eligible=False):
    return {
        "id": f"alpha-{index}",
        "is": {
            "sharpe": sharpe,
            "fitness": 1.1,
            "turnover": 0.2,
            "margin": 0.001,
            "longCount": 101 if eligible else 0,
            "shortCount": 0,
        },
        "settings": {"decay": 4},
        "regular": {"code": f"rank(field_{index})"},
        "dateCreated": "2026-08-21T00:00:00-04:00",
    }


class TestAlphaPageQuery(unittest.TestCase):
    def test_legacy_query_is_unchanged_without_tag(self):
        client = MagicMock()
        client.get.return_value = response([])

        self.assertEqual(
            sim_api.get_user_alphas(
                client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR", 100
            ),
            [],
        )

        client.get.assert_called_once_with(
            "/users/self/alphas?limit=100&offset=100"
            "&status=UNSUBMITTED%1FIS_FAIL"
            "&dateCreated%3E=2026-07-01T00:00:00-04:00"
            "&dateCreated%3C=2026-08-21T23:59:59-04:00"
            "&is.fitness%3E=1.0&is.sharpe%3E=1.25"
            "&settings.region=GBR&order=-is.sharpe&hidden=false&type!=SUPER",
            timeout=30,
        )

    def test_tag_is_trimmed_and_url_encoded(self):
        client = MagicMock()
        client.get.return_value = response([])

        sim_api.get_user_alphas(
            client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR",
            tag="  研究 Useful/A&B  ",
        )

        url = client.get.call_args.args[0]
        self.assertIn("&tag=%E7%A0%94%E7%A9%B6%20Useful%2FA%26B", url)

    def test_empty_tag_is_omitted_and_negative_query_uses_same_filter(self):
        client = MagicMock()
        client.get.return_value = response([])

        sim_api.get_user_alphas(
            client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR", tag="   "
        )
        self.assertNotIn("&tag=", client.get.call_args.args[0])

        sim_api._get_user_alphas_page(
            client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR",
            tag="Useful", negative=True,
        )
        url = client.get.call_args.args[0]
        self.assertIn("&is.fitness%3C=-1.0&is.sharpe%3C=-1.25", url)
        self.assertIn("&tag=Useful", url)

    def test_failures_are_distinct_from_a_successful_empty_page(self):
        client = MagicMock()
        bad_shape = response([])
        bad_shape.json.return_value = {"results": {}}

        for failed_response in (
            None,
            MagicMock(status_code=401),
            MagicMock(status_code=429),
            bad_shape,
        ):
            with self.subTest(failed_response=failed_response):
                client.get.return_value = failed_response
                page = sim_api._get_user_alphas_page(
                    client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR"
                )
                self.assertIsNone(page)

        client.get.return_value = response([], count=0)
        page = sim_api._get_user_alphas_page(
            client, "2026-07-01", "2026-08-21", 1.25, 1.0, "GBR"
        )
        self.assertEqual(page, {"results": [], "count": 0})


class TestGetAlphasPagination(unittest.TestCase):
    def _run(self, page_side_effect, **kwargs):
        with (
            patch.object(alpha_manager, "login", return_value=MagicMock()) as login_mock,
            patch.object(
                alpha_manager, "_get_user_alphas_page", side_effect=page_side_effect
            ) as page_mock,
            redirect_stdout(io.StringIO()) as stdout,
        ):
            result = alpha_manager.get_alphas(**kwargs)
        return result, page_mock, login_mock, stdout.getvalue()

    def test_dates_must_be_both_set_before_login(self):
        with patch.object(alpha_manager, "login") as login_mock:
            with self.assertRaisesRegex(ValueError, "同时填写"):
                alpha_manager.get_alphas(start_date="2026-07-01")
        login_mock.assert_not_called()

    def test_invalid_limit_or_tag_fails_before_login(self):
        with patch.object(alpha_manager, "login") as login_mock:
            for kwargs in ({"alpha_num": 0}, {"alpha_num": "200"}, {"tag": ["Useful"]}):
                with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                    alpha_manager.get_alphas(**kwargs)
        login_mock.assert_not_called()

    def test_finite_mode_keeps_existing_page_budget(self):
        result, page_mock, _, output = self._run(
            lambda *args, **kwargs: {"results": [], "count": 0},
            start_date="2026-07-01", end_date="2026-08-21",
            region="GBR", alpha_num=200, usage="submit",
        )

        self.assertEqual(result, [])
        self.assertEqual([call.args[6] for call in page_mock.call_args_list], [0, 100])
        self.assertIn("检索完成", output)

    def test_unlimited_mode_stops_on_third_short_page(self):
        pages = [
            {"results": [alpha_item(i) for i in range(100)], "count": 203},
            {"results": [alpha_item(i) for i in range(100, 200)], "count": 203},
            {"results": [alpha_item(i) for i in range(200, 203)], "count": 203},
        ]
        _, page_mock, _, output = self._run(
            pages,
            start_date="2026-07-01", end_date="2026-08-21",
            region="GBR", alpha_num=None, usage="submit", tag="Useful",
        )

        self.assertEqual([call.args[6] for call in page_mock.call_args_list], [0, 100, 200])
        self.assertTrue(all(call.kwargs["tag"] == "Useful" for call in page_mock.call_args_list))
        self.assertIn("返回=3，总量=203", output)

    def test_track_mode_finishes_positive_and_negative_independently(self):
        def pages(*args, **kwargs):
            offset = args[6]
            negative = kwargs.get("negative", False)
            if not negative:
                self.assertEqual(offset, 0)
                return {"results": [alpha_item(i) for i in range(20)], "count": 20}
            if offset == 0:
                return {"results": [alpha_item(i, sharpe=-1.5) for i in range(100)], "count": 110}
            return {"results": [alpha_item(i, sharpe=-1.5) for i in range(100, 110)], "count": 110}

        _, page_mock, _, _ = self._run(
            pages,
            start_date="2026-07-01", end_date="2026-08-21",
            region="GBR", alpha_num=None, usage="track",
        )

        calls = [(call.args[6], call.kwargs.get("negative", False)) for call in page_mock.call_args_list]
        self.assertEqual(calls, [(0, False), (0, True), (100, True)])

    def test_failure_stops_and_returns_observed_records_as_partial(self):
        pages = [
            {"results": [alpha_item(i, eligible=True) for i in range(100)], "count": 200},
            None,
        ]
        result, page_mock, _, output = self._run(
            pages,
            start_date="2026-07-01", end_date="2026-08-21",
            region="GBR", alpha_num=None, usage="submit",
        )

        self.assertEqual(len(result), 100)
        self.assertEqual(page_mock.call_count, 2)
        self.assertIn("PARTIAL/PENDING", output)
        self.assertIn("部分完成", output)


class TestSubmitNotebookConfig(unittest.TestCase):
    def test_section_11_exposes_optional_range_limit_and_tag(self):
        path = CORE_PARENT / "Core" / "notebooks" / "Alpha_Machine.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        source = next(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if "th_tracker = get_alphas" in "".join(cell.get("source", []))
        )

        compile(source, str(path), "exec")
        self.assertIn("SUBMIT_ALPHA_START_DATE = None", source)
        self.assertIn("SUBMIT_ALPHA_END_DATE = None", source)
        self.assertIn("SUBMIT_ALPHA_NUM = 200", source)
        self.assertIn("SUBMIT_ALPHA_TAG = None", source)
        self.assertIn("tag=SUBMIT_ALPHA_TAG", source)


if __name__ == "__main__":
    unittest.main()
