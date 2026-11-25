import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


OPTIMIZATION_ROOT = Path(__file__).resolve().parents[1] / "代码" / "优化代码"
if str(OPTIMIZATION_ROOT) not in sys.path:
    sys.path.insert(0, str(OPTIMIZATION_ROOT))

from Core.api.sim_api import get_alpha_check, get_prod_correlation
from Core.sim.validator import get_pc_check


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return self.responses.pop(0)


class TestProductionCorrelation(unittest.TestCase):
    def test_dedicated_endpoint_returns_max(self):
        client = FakeClient([FakeResponse(payload={"max": 0.42, "min": -0.1})])

        self.assertEqual(get_prod_correlation(client, "alpha1"), 0.42)
        self.assertEqual(client.urls, ["/alphas/alpha1/correlations/prod"])

    def test_check_is_not_called_when_dedicated_endpoint_succeeds(self):
        client = FakeClient([])
        with patch("Core.sim.validator.get_prod_correlation", return_value=0.33), \
             patch("Core.sim.validator.get_alpha_check") as fallback:
            self.assertEqual(get_pc_check(client, "alpha2"), 0.33)
            fallback.assert_not_called()

    def test_check_fallback_can_be_limited_to_one_request(self):
        payload = {"is": {"checks": []}}
        client = FakeClient([
            FakeResponse(payload=payload, headers={"retry-after": "60"}),
        ])

        self.assertEqual(
            get_alpha_check(client, "alpha2", wait_for_result=False), payload
        )
        self.assertEqual(client.urls, ["/alphas/alpha2/check"])

    def test_check_is_called_once_after_dedicated_attempts_fail(self):
        check = {"is": {"checks": [{"name": "PROD_CORRELATION", "value": 0.61}]}}
        client = FakeClient([])
        with patch("Core.sim.validator.get_prod_correlation", return_value=None) as primary, \
             patch("Core.sim.validator.get_alpha_check", return_value=check) as fallback:
            self.assertEqual(
                get_pc_check(client, "alpha3", max_attempts=3, wait_seconds=0),
                0.61,
            )
            self.assertEqual(primary.call_count, 3)
            fallback.assert_called_once_with(client, "alpha3", wait_for_result=False)

    def test_missing_pc_stays_pending_nan(self):
        check = {"is": {"checks": [{"name": "SELF_CORRELATION", "value": 0.2}]}}
        with patch("Core.sim.validator.get_prod_correlation", return_value=None), \
             patch("Core.sim.validator.get_alpha_check", return_value=check):
            self.assertTrue(math.isnan(get_pc_check(FakeClient([]), "alpha4")))

    def test_stop_skips_all_remote_calls(self):
        with patch("Core.sim.validator.get_prod_correlation") as primary, \
             patch("Core.sim.validator.get_alpha_check") as fallback:
            result = get_pc_check(FakeClient([]), "alpha5", should_stop=lambda: True)
            self.assertEqual(result, "interrupted")
            primary.assert_not_called()
            fallback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
