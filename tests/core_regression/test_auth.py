import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))

# 现在从统一 API 层导入 login
from Core.api.auth import login
from Core.api.client import BrainClient

class TestAuth(unittest.TestCase):
    @patch("Core.api.auth.requests.Session")
    @patch("Core.api.auth.load_config", return_value={
        "username": "name@example.com", "password": "secret",
    })
    def test_login_returns_authenticated_brain_client(self, _config, session_cls):
        response = MagicMock(status_code=201)
        session_cls.return_value.request.return_value = response
        with patch.object(BrainClient, "mark_authenticated") as mark:
            client = login()
        self.assertIsInstance(client, BrainClient)
        mark.assert_called_once_with()

    @patch("Core.api.auth.requests.Session")
    @patch("Core.api.auth.load_config", return_value={
        "username": "name@example.com", "password": "secret",
    })
    def test_login_failure_does_not_return_unauthed_client(self, _config, session_cls):
        session_cls.return_value.request.return_value = MagicMock(status_code=403)
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            login()

if __name__ == '__main__':
    unittest.main()
