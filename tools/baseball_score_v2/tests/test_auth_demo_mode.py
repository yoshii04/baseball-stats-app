"""Web API の認証（デモモード）のテスト"""
import importlib
import os
import sys
import unittest
from unittest.mock import patch

BACKEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp", "backend"
)
sys.path.insert(0, BACKEND_DIR)


def _load_auth(env: dict):
    """環境変数を差し替えて auth モジュールを読み込み直す"""
    with patch.dict(os.environ, env, clear=True):
        sys.modules.pop("auth", None)
        return importlib.import_module("auth")


class TestAuthDemoMode(unittest.TestCase):

    def tearDown(self):
        sys.modules.pop("auth", None)

    def test_demo_mode_skips_verification(self):
        auth = _load_auth({"DEMO_MODE": "true", "ENV": "development"})
        self.assertTrue(auth.DEMO_MODE)
        self.assertEqual(auth.verify_token(None), {"email": "demo@example.com"})

    def test_demo_mode_is_refused_in_production(self):
        with self.assertRaises(RuntimeError):
            _load_auth({"DEMO_MODE": "true", "ENV": "production"})

    def test_demo_mode_is_off_by_default(self):
        auth = _load_auth({})
        self.assertFalse(auth.DEMO_MODE)
        # 認証ヘッダーなしは HTTPBearer が拒否する（デモモードでは None を許容する）
        self.assertTrue(auth.security.auto_error)

    def test_other_values_do_not_enable_demo_mode(self):
        auth = _load_auth({"DEMO_MODE": "1"})
        self.assertFalse(auth.DEMO_MODE)


if __name__ == "__main__":
    unittest.main()
