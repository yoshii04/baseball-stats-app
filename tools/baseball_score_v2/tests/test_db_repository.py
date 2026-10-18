import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.number_util import marunum_to_int
from repository.db_repository import DBRepository


class TestMarunumToInt(unittest.TestCase):
    """Test cases for number utility functions"""

    def test_marunum_to_int_circled_digits(self):
        """Test parsing of Unicode circled numbers ①-⑨"""
        # Test circled numbers
        self.assertEqual(marunum_to_int("①"), 1)
        self.assertEqual(marunum_to_int("②"), 2)
        self.assertEqual(marunum_to_int("③"), 3)
        self.assertEqual(marunum_to_int("④"), 4)
        self.assertEqual(marunum_to_int("⑤"), 5)
        self.assertEqual(marunum_to_int("⑥"), 6)
        self.assertEqual(marunum_to_int("⑦"), 7)
        self.assertEqual(marunum_to_int("⑧"), 8)
        self.assertEqual(marunum_to_int("⑨"), 9)

    def test_marunum_to_int_with_kanji(self):
        """Test parsing with Japanese 回 (inning) character"""
        self.assertEqual(marunum_to_int("①回"), 1)
        self.assertEqual(marunum_to_int("⑤回"), 5)
        self.assertEqual(marunum_to_int("⑨回"), 9)

    def test_marunum_to_int_arabic_numerals(self):
        """Test parsing of regular Arabic numerals"""
        self.assertEqual(marunum_to_int("1"), 1)
        self.assertEqual(marunum_to_int("10"), 10)
        self.assertEqual(marunum_to_int("15"), 15)

    def test_marunum_to_int_arabic_with_kanji(self):
        """Test parsing of Arabic numerals with 回"""
        self.assertEqual(marunum_to_int("1回"), 1)
        self.assertEqual(marunum_to_int("10回"), 10)

    def test_marunum_to_int_with_whitespace(self):
        """Test parsing handles whitespace correctly"""
        self.assertEqual(marunum_to_int("  ①  "), 1)
        self.assertEqual(marunum_to_int("  5  "), 5)


class TestDBRepositoryHelpers(unittest.TestCase):
    """Test SELECT-first helper methods for get_or_create_* functions"""

    def setUp(self):
        """Initialize DBRepository with mocked connection"""
        with patch('repository.db_repository.psycopg2.connect'):
            self.repo = DBRepository()
        self.mock_cur = Mock()

    def test_get_or_create_team_existing(self):
        """Test retrieving existing team - SELECT only"""
        # Mock SELECT to return existing team
        self.mock_cur.fetchone.return_value = (1,)
        result = self.repo.get_or_create_team(self.mock_cur, "TeamA")
        self.assertEqual(result, 1)
        # Verify only one execute call (SELECT, not INSERT)
        self.assertEqual(self.mock_cur.execute.call_count, 1)
        call_args = self.mock_cur.execute.call_args[0][0]
        self.assertIn("SELECT", call_args)

    def test_get_or_create_team_new(self):
        """Test creating new team - SELECT then INSERT"""
        # Mock: first call (SELECT) returns None, second call (INSERT) returns new ID
        self.mock_cur.fetchone.side_effect = [None, (2,)]
        result = self.repo.get_or_create_team(self.mock_cur, "TeamB")
        self.assertEqual(result, 2)
        # Verify two execute calls (SELECT + INSERT)
        self.assertEqual(self.mock_cur.execute.call_count, 2)

    def test_get_or_create_team_uses_self_team_name_when_not_provided(self):
        """Test that team_name defaults to self.team_name"""
        self.mock_cur.fetchone.return_value = (3,)
        result = self.repo.get_or_create_team(self.mock_cur)
        self.assertEqual(result, 3)
        # Verify SELECT was called
        self.assertEqual(self.mock_cur.execute.call_count, 1)

    def test_get_or_create_game_existing(self):
        """Test retrieving existing game - SELECT only"""
        self.mock_cur.fetchone.return_value = (10,)
        result = self.repo.get_or_create_game(self.mock_cur, "2026-03-14", 1, 2)
        self.assertEqual(result, 10)
        self.assertEqual(self.mock_cur.execute.call_count, 1)

    def test_get_or_create_game_new(self):
        """Test creating new game - SELECT then INSERT"""
        self.mock_cur.fetchone.side_effect = [None, (11,)]
        result = self.repo.get_or_create_game(self.mock_cur, "2026-03-14", 1, 2)
        self.assertEqual(result, 11)
        self.assertEqual(self.mock_cur.execute.call_count, 2)

    def test_get_or_create_player_existing(self):
        """Test retrieving existing player - SELECT only"""
        self.mock_cur.fetchone.return_value = (50,)
        result = self.repo.get_or_create_player(self.mock_cur, "Player1", 1)
        self.assertEqual(result, 50)
        self.assertEqual(self.mock_cur.execute.call_count, 1)

    def test_get_or_create_player_new(self):
        """Test creating new player - SELECT then INSERT"""
        self.mock_cur.fetchone.side_effect = [None, (51,)]
        result = self.repo.get_or_create_player(self.mock_cur, "Player2", 1)
        self.assertEqual(result, 51)
        self.assertEqual(self.mock_cur.execute.call_count, 2)


if __name__ == "__main__":
    unittest.main()
