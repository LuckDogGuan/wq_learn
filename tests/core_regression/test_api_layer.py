"""
tests/test_api_layer.py
测试 Core.api 层的核心功能（使用 Mock，不发真实 HTTP 请求）。
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))


class TestBrainClient(unittest.TestCase):
    """测试 BrainClient 的重试和限频退避逻辑（全 Mock）。"""

    def test_client_wraps_session(self):
        """BrainClient 应正确接受外部 session 并包装它。"""
        import requests
        from Core.api.client import BrainClient
        mock_session = requests.Session()
        client = BrainClient(session=mock_session)
        self.assertIs(client.session, mock_session)

    def test_client_creates_default_session(self):
        """BrainClient 不传 session 时应自动创建 Session。"""
        from Core.api.client import BrainClient
        import requests
        client = BrainClient()
        self.assertIsInstance(client.session, requests.Session)

    @patch('requests.Session.request')
    def test_get_returns_response(self, mock_request):
        """client.get 在 200 响应时应直接返回 response。"""
        from Core.api.client import BrainClient
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_request.return_value = mock_resp
        client = BrainClient()
        resp = client.get("https://api.worldquantbrain.com/test")
        self.assertEqual(resp.status_code, 200)

    @patch('requests.Session.request')
    def test_client_retries_on_429(self, mock_request):
        """client 遇到 429 时应等待然后重试，最终返回成功结果。"""
        import time
        from Core.api.client import BrainClient

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "0.01"}  # 极短等待方便测试

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.headers = {}

        # 第一次返回429，第二次返回200
        mock_request.side_effect = [mock_429, mock_200]

        client = BrainClient()
        resp = client.get("https://api.worldquantbrain.com/test")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)

    def test_client_returns_last_429_after_configured_cooldowns(self):
        """调用方应能区分明确429与无响应，并控制较长退避。"""
        from Core.api.client import BrainClient

        session = MagicMock()
        limited = MagicMock(status_code=429, headers={})
        session.request.return_value = limited
        client = BrainClient(session=session)

        with patch('Core.api.client.time.sleep') as sleep_mock:
            response = client.post('/simulations', rate_limit_waits=(60, 300))

        self.assertIs(response, limited)
        self.assertEqual(session.request.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep_mock.call_args_list], [60.0, 300.0]
        )

    def test_get_retries_5xx_with_shared_policy(self):
        from Core.api.client import BrainClient

        session = MagicMock()
        failed = MagicMock(status_code=503, headers={})
        succeeded = MagicMock(status_code=200, headers={})
        session.request.side_effect = [failed, succeeded]
        client = BrainClient(session=session)

        with patch("Core.api.client.time.sleep"):
            response = client.get("/users/self/alphas")

        self.assertIs(response, succeeded)
        self.assertEqual(session.request.call_count, 2)

    def test_configured_cooldown_is_not_shortened_by_retry_after_header(self):
        from Core.api.client import BrainClient

        session = MagicMock()
        limited = MagicMock(status_code=429, headers={"Retry-After": "5"})
        success = MagicMock(status_code=201, headers={"Location": "/simulations/ok"})
        session.request.side_effect = [limited, success]
        client = BrainClient(session=session)

        with patch('Core.api.client.time.sleep') as sleep_mock:
            response = client.post('/simulations', rate_limit_waits=(60,))

        self.assertIs(response, success)
        sleep_mock.assert_called_once_with(60.0)

    def test_client_normalizes_relative_urls(self):
        """相对路径无论是否带斜杠，都不能被拼进域名。"""
        from Core.api.client import BrainClient

        session = MagicMock()
        session.request.return_value = MagicMock(status_code=200)
        client = BrainClient(session=session)

        cases = (
            ("/alphas/test", "https://api.worldquantbrain.com/alphas/test"),
            ("alphas/test", "https://api.worldquantbrain.com/alphas/test"),
            ("https://example.test/progress", "https://example.test/progress"),
        )
        for supplied, expected in cases:
            with self.subTest(supplied=supplied):
                client.get(supplied)
                self.assertEqual(session.request.call_args.args[1], expected)

    def test_client_refreshes_after_180_minutes(self):
        """已认证会话达到 180 分钟时，应先刷新再发送原请求。"""
        import time
        from Core.api.client import AUTH_REFRESH_SECONDS, BrainClient

        session = MagicMock()
        session.auth = ("name@example.com", "secret")
        auth_response = MagicMock(status_code=201)
        response = MagicMock(status_code=200)
        session.request.side_effect = [auth_response, response]

        client = BrainClient(session=session)
        client._authenticated_at = time.monotonic() - AUTH_REFRESH_SECONDS

        self.assertIs(client.get("/test"), response)
        self.assertEqual(session.request.call_count, 2)
        self.assertEqual(session.request.call_args_list[0].args[:2], ("POST", "https://api.worldquantbrain.com/authentication"))

    def test_client_reauthenticates_once_on_401(self):
        """普通请求遇到 401 时，应刷新并只重试原请求一次。"""
        from Core.api.client import BrainClient

        session = MagicMock()
        session.auth = ("name@example.com", "secret")
        unauthorized = MagicMock(status_code=401)
        auth_response = MagicMock(status_code=201)
        response = MagicMock(status_code=200)
        session.request.side_effect = [unauthorized, auth_response, response]

        client = BrainClient(session=session)

        self.assertIs(client.get("/test"), response)
        self.assertEqual(session.request.call_count, 3)

    def test_client_does_not_loop_on_repeated_401(self):
        """续签后仍返回 401 时，应返回响应而不是无限重新登录。"""
        from Core.api.client import BrainClient

        session = MagicMock()
        session.auth = ("name@example.com", "secret")
        first_401 = MagicMock(status_code=401)
        auth_response = MagicMock(status_code=201)
        second_401 = MagicMock(status_code=401)
        session.request.side_effect = [first_401, auth_response, second_401]

        client = BrainClient(session=session)

        self.assertIs(client.get("/test"), second_401)
        self.assertEqual(session.request.call_count, 3)


class TestPlatformAPI(unittest.TestCase):
    """测试 Core.api.platform 的数据解析逻辑（全 Mock）。"""

    def test_get_day1_universe_map_parses_response(self):
        """get_day1_universe_map 应正确解析平台的 OPTIONS 响应。"""
        from Core.api.platform import get_day1_universe_map
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "actions": {
                "POST": {
                    "settings": {
                        "children": {
                            "universe": {
                                "type": "choice",
                                "label": "Universe",
                                "choices": {
                                    "instrumentType": {
                                        "EQUITY": {
                                            "region": {
                                                "USA": [{"value": "TOP3000"}, {"value": "TOP2000"}],
                                                "CHN": [{"value": "CHNALL"}]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_client.options.return_value = mock_resp

        result = get_day1_universe_map(mock_client)
        self.assertIn("USA", result)
        self.assertIn("TOP3000", result["USA"])
        self.assertIn("CHN", result)
        self.assertEqual(result["CHN"], ["CHNALL"])

    def test_get_day1_universe_map_empty_on_failure(self):
        """get_day1_universe_map 在请求失败时应返回空字典。"""
        from Core.api.platform import get_day1_universe_map
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_client.options.return_value = mock_resp

        result = get_day1_universe_map(mock_client)
        self.assertEqual(result, {})

    def test_get_all_valid_scopes_returns_list(self):
        """get_all_valid_scopes 应返回 (region, universe) 元组列表。"""
        from Core.api.platform import get_all_valid_scopes
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "actions": {
                "POST": {
                    "settings": {
                        "children": {
                            "universe": {
                                "type": "choice",
                                "label": "Universe",
                                "choices": {
                                    "instrumentType": {
                                        "EQUITY": {
                                            "region": {
                                                "USA": [{"value": "TOP3000"}]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_client.options.return_value = mock_resp

        scopes = get_all_valid_scopes(mock_client)
        self.assertIsInstance(scopes, list)
        self.assertIn(("USA", "TOP3000"), scopes)


class TestActivityAPI(unittest.TestCase):
    """测试用户活动接口解析（全 Mock）。"""

    def test_get_user_diversity_returns_platform_payload(self):
        from Core.api.activity_api import USER_DIVERSITY_PATH, get_user_diversity
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock(status_code=200)
        payload = {
            "USA": {"Fundamental": 2},
            "EUR": {"Fundamental": 11},
            "limit": 30,
        }
        mock_resp.json.return_value = payload
        mock_client.get.return_value = mock_resp

        result = get_user_diversity(mock_client)

        mock_client.get.assert_called_once_with(USER_DIVERSITY_PATH)
        self.assertEqual(result, payload)

    def test_get_user_diversity_returns_empty_on_failure_or_invalid_json(self):
        from Core.api.activity_api import get_user_diversity
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        failed = MagicMock(status_code=500)
        mock_client.get.return_value = failed
        self.assertEqual(get_user_diversity(mock_client), {})

        invalid = MagicMock(status_code=200)
        invalid.json.side_effect = ValueError("invalid json")
        mock_client.get.return_value = invalid
        self.assertEqual(get_user_diversity(mock_client), {})

        non_object = MagicMock(status_code=200)
        non_object.json.return_value = []
        mock_client.get.return_value = non_object
        self.assertEqual(get_user_diversity(mock_client), {})

    def test_get_alpha_pyramid_pass_info_extracts_one_or_more_scopes(self):
        from Core.api.activity_api import get_alpha_pyramid_pass_info
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "is": {"checks": [{
                "name": "MATCHES_PYRAMID",
                "result": "PASS",
                "effective": 2,
                "multiplier": 1.0,
                "pyramids": [
                    {"name": "GLB/D1/PV", "multiplier": 1.0},
                    {"name": "GLB/D1/OTHER", "multiplier": 1.3},
                ],
            }]}
        }
        mock_client.get.return_value = mock_resp

        result = get_alpha_pyramid_pass_info(mock_client, "alpha123")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["categories"], ["GLB/D1/PV", "GLB/D1/OTHER"])
        self.assertEqual(result["effective"], 2)
        self.assertEqual(result["multiplier"], 1.0)
        mock_client.get.assert_called_once_with("/alphas/alpha123")

    def test_get_alpha_pyramid_pass_info_keeps_unobserved_as_pending(self):
        from Core.api.activity_api import get_alpha_pyramid_pass_info
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_client.get.return_value = MagicMock(status_code=200)
        mock_client.get.return_value.json.return_value = {"is": {"checks": []}}

        result = get_alpha_pyramid_pass_info(mock_client, "alpha123")

        self.assertEqual(result["status"], "PENDING")
        self.assertEqual(result["categories"], [])

    def test_evaluate_pyramid_coverage_all_pass_and_partial_gap(self):
        from Core.api.activity_api import evaluate_pyramid_coverage

        diversity = {"alphas": [
            {
                "region": "GBR", "delay": 1, "alphaCount": 12,
                "dataCategory": {"id": "model", "name": "Model"},
                "dataDiversity": {"check": "PASS", "limit": 0.3},
            },
            {
                "region": "GBR", "delay": 1, "alphaCount": 2,
                "dataCategory": {"id": "fundamental", "name": "Fundamental"},
                "dataDiversity": {"check": "PASS", "limit": 0.3},
            },
            {"region": "GBR", "delay": 1,
             "dataCategory": {"id": None, "name": None}, "alphaCount": 12},
        ]}

        all_pass = evaluate_pyramid_coverage(
            diversity, {"status": "PASS", "categories": ["GBR/D1/MODEL"]}
        )
        partial = evaluate_pyramid_coverage(
            diversity,
            {"status": "PASS", "categories": ["GBR/D1/FUNDAMENTAL", "GBR/D1/ANALYST"]},
        )

        self.assertEqual(all_pass["status"], "ALL_PASS")
        self.assertEqual(partial["status"], "HAS_GAP")
        self.assertEqual(partial["gap_scopes"][0]["category"], "analyst")
        self.assertEqual(partial["gap_scopes"][0]["check"], "MISSING")

    def test_evaluate_pyramid_coverage_is_exact_by_region_delay_and_alias(self):
        from Core.api.activity_api import evaluate_pyramid_coverage

        diversity = {"alphas": [{
            "region": "GBR", "delay": 1,
            "dataCategory": {"id": "pv", "name": "Price Volume"},
            "dataDiversity": {"check": "PASS", "limit": 0.3},
        }]}

        alias_pass = evaluate_pyramid_coverage(
            diversity, {"status": "PASS", "categories": ["GBR/D1/PRICE VOLUME"]}
        )
        wrong_region = evaluate_pyramid_coverage(
            diversity, {"status": "PASS", "categories": ["USA/D1/PV"]}
        )

        self.assertEqual(alias_pass["status"], "ALL_PASS")
        self.assertEqual(wrong_region["status"], "HAS_GAP")

    def test_evaluate_pyramid_coverage_keeps_invalid_input_pending(self):
        from Core.api.activity_api import evaluate_pyramid_coverage

        self.assertEqual(
            evaluate_pyramid_coverage({}, {"status": "PASS", "categories": ["USA/D1/MODEL"]})["status"],
            "PENDING",
        )
        self.assertEqual(
            evaluate_pyramid_coverage({"alphas": []}, {"status": "PENDING", "categories": []})["status"],
            "PENDING",
        )
        self.assertEqual(
            evaluate_pyramid_coverage({"alphas": []}, {"status": "PASS", "categories": ["bad"]})["status"],
            "PENDING",
        )


class TestDataAPI(unittest.TestCase):
    """测试 Core.api.data_api 的 HTTP 调用逻辑（全 Mock）。"""

    def test_get_datasets_returns_dataframe(self):
        """get_datasets 应将响应正确转换为 DataFrame。"""
        from Core.api.data_api import get_datasets
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [{"id": "ds1", "name": "Dataset One"}, {"id": "ds2", "name": "Dataset Two"}]
        }
        mock_client.get.return_value = mock_resp

        df = get_datasets(mock_client, region="USA", universe="TOP3000")
        self.assertEqual(len(df), 2)
        self.assertIn("id", df.columns)

    def test_get_datasets_returns_empty_on_failure(self):
        """get_datasets 在请求失败时应返回空 DataFrame。"""
        from Core.api.data_api import get_datasets
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_client.get.return_value = None

        df = get_datasets(mock_client)
        self.assertTrue(df.empty)

    def test_get_vec_fields(self):
        """get_vec_fields 应为每个字段生成正确数量的向量算子表达式。"""
        from Core.api.data_api import get_vec_fields
        fields = ["field_a", "field_b"]
        result = get_vec_fields(fields)
        # 2 fields × 2 ops = 4 expressions
        self.assertEqual(len(result), 4)
        self.assertIn("vec_avg(field_a)", result)
        self.assertIn("vec_sum(field_b)", result)

    def test_process_datafields(self):
        """process_datafields 应正确提取 MATRIX 和 VECTOR 字段并应用预处理包装。"""
        import pandas as pd
        from Core.api.data_api import process_datafields

        df = pd.DataFrame({
            "id": ["f1", "f2", "f3"],
            "type": ["MATRIX", "VECTOR", "STRING"]
        })
        result = process_datafields(df)
        # f1 -> 1 wrapped matrix, f2 -> 2 vec expressions (vec_avg + vec_sum)
        self.assertEqual(len(result), 3)
        self.assertTrue(all("winsorize(ts_backfill(" in r for r in result))


class TestSimAPI(unittest.TestCase):
    """测试 Core.api.sim_api 的模拟提交与检查逻辑（全 Mock）。"""

    def test_post_simulation_returns_location(self):
        """post_simulation 应从响应头中提取 Location URL。"""
        from Core.api.sim_api import post_simulation
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {"Location": "https://api.worldquantbrain.com/simulations/abc123"}
        mock_client.post.return_value = mock_resp

        url = post_simulation(mock_client, {"type": "REGULAR", "regular": "rank(close)"})
        self.assertEqual(url, "https://api.worldquantbrain.com/simulations/abc123")

    def test_post_multi_simulation_can_return_observed_429_metadata(self):
        from Core.api.client import BrainClient
        from Core.api.sim_api import post_multi_simulation

        mock_client = MagicMock(spec=BrainClient)
        limited = MagicMock(status_code=429, headers={"Retry-After": "300"})
        mock_client.post.return_value = limited

        result = post_multi_simulation(
            mock_client, [{"type": "REGULAR"}] * 8,
            return_metadata=True, rate_limit_waits=(60, 300),
        )

        self.assertEqual(result["status_code"], 429)
        self.assertEqual(result["retry_after"], "300")
        self.assertIsNone(result["location"])
        self.assertTrue(result["response_observed"])
        mock_client.post.assert_called_once_with(
            "/simulations", json=[{"type": "REGULAR"}] * 8,
            rate_limit_waits=(60, 300),
        )

    def test_post_multi_simulation_rejects_single_or_oversized_batch(self):
        from Core.api.sim_api import post_multi_simulation

        mock_client = MagicMock()
        for size in (0, 1, 9):
            with self.subTest(size=size), self.assertRaises(ValueError):
                post_multi_simulation(
                    mock_client, [{"type": "REGULAR"}] * size
                )
        mock_client.post.assert_not_called()

    def test_get_user_alphas_page_distinguishes_empty_from_failure(self):
        from Core.api.client import BrainClient
        from Core.api.sim_api import get_user_alphas_page

        mock_client = MagicMock(spec=BrainClient)
        success = MagicMock(status_code=200)
        success.json.return_value = {"results": [], "count": 0}
        mock_client.get.return_value = success

        result = get_user_alphas_page(
            mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5,
            statuses=("UNSUBMITTED", "IS_FAIL"), offset=100, limit=50,
        )

        self.assertEqual(result, {"results": [], "count": 0})
        requested_url = mock_client.get.call_args.args[0]
        self.assertIn("status=UNSUBMITTED%1FIS_FAIL", requested_url)
        self.assertIn("type=REGULAR", requested_url)
        self.assertIn(
            "dateCreated%3E%3D2026-08-23T00%3A00%3A00%2B08%3A00",
            requested_url,
        )
        self.assertIn(
            "dateCreated%3C2026-08-24T00%3A00%3A00%2B08%3A00",
            requested_url,
        )
        self.assertIn("limit=50&offset=100", requested_url)
        self.assertIn("order=dateCreated", requested_url)

        mock_client.get.return_value = success
        get_user_alphas_page(
            mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5,
            descending=True,
        )
        self.assertIn("order=-dateCreated", mock_client.get.call_args.args[0])

        mock_client.get.return_value = MagicMock(status_code=500)
        self.assertIsNone(
            get_user_alphas_page(mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5)
        )

    def test_get_user_alphas_page_validates_pagination_and_statuses(self):
        from Core.api.client import BrainClient
        from Core.api.sim_api import get_user_alphas_page

        mock_client = MagicMock(spec=BrainClient)
        with self.assertRaises(ValueError):
            get_user_alphas_page(mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5, statuses=())
        with self.assertRaises(ValueError):
            get_user_alphas_page(mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5, limit=101)
        with self.assertRaises(ValueError):
            get_user_alphas_page(
                mock_client, "2026-08-23", "2026-08-23", 1.0, 0.5,
                descending="yes",
            )

    def test_post_simulation_returns_none_on_failure(self):
        """post_simulation 在失败时应返回 None。"""
        from Core.api.sim_api import post_simulation
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_client.post.return_value = None

        url = post_simulation(mock_client, {})
        self.assertIsNone(url)

    def test_poll_simulation_progress_returns_on_complete(self):
        """poll_simulation_progress 在收到 COMPLETE 状态时应立即返回结果。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.headers = {"Retry-After": "0"}
        mock_resp.json.return_value = {"status": "COMPLETE", "id": "alpha123"}
        mock_client.get.return_value = mock_resp

        result = poll_simulation_progress(mock_client, "https://url/progress")
        self.assertEqual(result.get("status"), "COMPLETE")

    def test_poll_simulation_progress_accepts_bare_child_id(self):
        """Multi-Simulation children 的裸 ID 应转换为 simulation 路径。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.headers = {"Retry-After": "0"}
        mock_resp.json.return_value = {"status": "COMPLETE", "alpha": "alpha123"}
        mock_client.get.return_value = mock_resp

        result = poll_simulation_progress(mock_client, "child123")

        mock_client.get.assert_called_once_with("/simulations/child123")
        self.assertEqual(result.get("alpha"), "alpha123")

    def test_poll_simulation_progress_returns_on_cancelled(self):
        """CANCELLED 是可观察终态，不应继续轮询到超时。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.headers = {"Retry-After": "0"}
        mock_resp.json.return_value = {"status": "CANCELLED"}
        mock_client.get.return_value = mock_resp

        result = poll_simulation_progress(mock_client, "child123")

        self.assertEqual(result.get("status"), "CANCELLED")
        mock_client.get.assert_called_once_with("/simulations/child123")

    def test_poll_simulation_progress_can_be_interrupted(self):
        """停止信号应在下一次网络请求前终止轮询。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        result = poll_simulation_progress(
            mock_client, "/simulations/child123", should_stop=lambda: True
        )

        self.assertEqual(result, {"status": "INTERRUPTED"})
        mock_client.get.assert_not_called()

    def test_poll_retry_after_wait_can_be_interrupted(self):
        """长 Retry-After 等待也应及时响应停止信号。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.headers = {"Retry-After": "60"}
        mock_client.get.return_value = mock_resp
        should_stop = MagicMock(side_effect=[False, True])

        result = poll_simulation_progress(
            mock_client, "/simulations/child123", should_stop=should_stop
        )

    def test_poll_simulation_progress_can_be_interrupted(self):
        """停止信号应在下一次网络请求前终止轮询。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        result = poll_simulation_progress(
            mock_client, "/simulations/child123", should_stop=lambda: True
        )

        self.assertEqual(result, {"status": "INTERRUPTED"})
        mock_client.get.assert_not_called()

    def test_poll_retry_after_wait_can_be_interrupted(self):
        """长 Retry-After 等待也应及时响应停止信号。"""
        from Core.api.sim_api import poll_simulation_progress
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)
        mock_resp = MagicMock()
        mock_resp.headers = {"Retry-After": "60"}
        mock_client.get.return_value = mock_resp
        should_stop = MagicMock(side_effect=[False, True])

        result = poll_simulation_progress(
            mock_client, "/simulations/child123", should_stop=should_stop
        )

        self.assertEqual(result, {"status": "INTERRUPTED"})
        mock_client.get.assert_called_once_with("/simulations/child123")


    def test_get_alpha_details_and_submission_status(self):
        from Core.api.sim_api import (
            get_alpha_details, is_alpha_submitted, check_alpha_submission_status
        )
        from Core.api.client import BrainClient

        mock_client = MagicMock(spec=BrainClient)

        # 1. 模拟已提交 Alpha (如 LL9x9aA2)
        mock_submitted_payload = {
            "id": "LL9x9aA2",
            "dateCreated": "2026-09-04T05:36:07-04:00",
            "dateSubmitted": "2026-09-04T12:07:41-04:00",
            "stage": "OS",
            "status": "ACTIVE",
            "settings": {"region": "GBR", "universe": "TOP700"},
            "regular": {"code": "alpha_expression_1"},
            "is": {"sharpe": 1.86, "fitness": 1.74, "turnover": 0.0775, "margin": 0.0028},
            "os": {"startDate": "2024-01-01"},
        }
        mock_resp_submitted = MagicMock(status_code=200)
        mock_resp_submitted.headers = {}
        mock_resp_submitted.json.return_value = mock_submitted_payload
        mock_client.get.return_value = mock_resp_submitted

        details = get_alpha_details(mock_client, "LL9x9aA2")
        self.assertEqual(details["id"], "LL9x9aA2")
        self.assertTrue(is_alpha_submitted(details))

        status_res = check_alpha_submission_status(mock_client, "LL9x9aA2")
        self.assertTrue(status_res["is_submitted"])
        self.assertEqual(status_res["stage"], "OS")
        self.assertEqual(status_res["status"], "ACTIVE")
        self.assertEqual(status_res["date_submitted"], "2026-09-04T12:07:41-04:00")
        self.assertEqual(status_res["sharpe"], 1.86)
        self.assertTrue(status_res["exists"])

        # 2. 模拟未提交 Alpha (如 ZY0Zbxqx)
        mock_unsubmitted_payload = {
            "id": "ZY0Zbxqx",
            "dateCreated": "2026-09-04T12:09:48-04:00",
            "dateSubmitted": None,
            "stage": "IS",
            "status": "UNSUBMITTED",
            "settings": {"region": "EUR", "universe": "TOP2500"},
            "regular": {"code": "alpha_expression_2"},
            "is": {"sharpe": 1.5, "fitness": 1.55, "turnover": 0.0552, "margin": 0.0048},
            "os": None,
        }
        mock_resp_unsub = MagicMock(status_code=200)
        mock_resp_unsub.headers = {}
        mock_resp_unsub.json.return_value = mock_unsubmitted_payload
        mock_client.get.return_value = mock_resp_unsub

        details_unsub = get_alpha_details(mock_client, "ZY0Zbxqx")
        self.assertFalse(is_alpha_submitted(details_unsub))

        status_unsub = check_alpha_submission_status(mock_client, "ZY0Zbxqx")
        self.assertFalse(status_unsub["is_submitted"])
        self.assertEqual(status_unsub["stage"], "IS")
        self.assertEqual(status_unsub["status"], "UNSUBMITTED")
        self.assertIsNone(status_unsub["date_submitted"])
        self.assertTrue(status_unsub["exists"])

        # 3. 模拟异常与不存在 (404 / None)
        mock_client.get.return_value = None
        self.assertIsNone(get_alpha_details(mock_client, "NON_EXISTENT"))
        status_none = check_alpha_submission_status(mock_client, "NON_EXISTENT")
        self.assertIsNone(status_none["is_submitted"])
        self.assertFalse(status_none["exists"])
        self.assertEqual(status_none["status"], "QUERY_FAILED")


if __name__ == '__main__':
    unittest.main()
