"""app_util の設定取得ヘルパーのテスト"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_util import (
    DEFAULT_TEAM_DATA_SHEET_NAME,
    get_our_team_name,
    get_team_data_sheet_name,
)


class TestGetTeamDataSheetName(unittest.TestCase):

    def test_default(self):
        self.assertEqual(get_team_data_sheet_name({}), DEFAULT_TEAM_DATA_SHEET_NAME)

    def test_config_overrides_default(self):
        config = {"team_data_sheet_name": "チーム単位のデータ（A）"}
        self.assertEqual(get_team_data_sheet_name(config), "チーム単位のデータ（A）")


class TestGetOurTeamName(unittest.TestCase):

    def test_config_takes_priority_over_env(self):
        with patch.dict(os.environ, {"TEAM_NAME": "環境変数チーム"}):
            self.assertEqual(get_our_team_name({"our_team_name": "設定チーム"}), "設定チーム")

    def test_falls_back_to_env(self):
        with patch.dict(os.environ, {"TEAM_NAME": "環境変数チーム"}):
            self.assertEqual(get_our_team_name({}), "環境変数チーム")

    def test_raises_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                get_our_team_name({})


if __name__ == "__main__":
    unittest.main()
