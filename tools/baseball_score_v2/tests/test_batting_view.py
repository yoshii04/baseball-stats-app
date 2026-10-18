import unittest
import sys
import os
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from view.batting_view import BattingView


class TestBattingViewDisplayBattingStats(unittest.TestCase):
    """Test cases for BattingView.display_batting_stats()"""

    def setUp(self):
        """Create a BattingView instance for testing"""
        self.view = BattingView()

    def test_display_batting_stats_shows_header(self):
        """Test that header is displayed"""
        stats = [
            {"player_name": "Player 1", "double_hit": 2, "triple": 0, "homerun": 1,
             "hit_count": 5, "stolen_base": 2, "walk_count": 3, "strike_out": 4,
             "batting_avg": 0.333, "on_base_pct": 0.400, "ops": 0.733},
        ]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("=== 打撃成績リスト ===", output)
        self.assertIn("名前", output)
        self.assertIn("安打", output)
        self.assertIn("盗塁", output)
        self.assertIn("四死球", output)
        self.assertIn("三振", output)
        self.assertIn("打率", output)
        self.assertIn("OPS", output)

    def test_display_batting_stats_empty_shows_no_data_message(self):
        """Test that empty data message is shown"""
        stats = []
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("(データなし)", output)

    def test_display_batting_stats_shows_player_rows(self):
        """Test that player rows are displayed"""
        stats = [
            {"player_name": "Player 1", "double_hit": 2, "triple": 0, "homerun": 1,
             "hit_count": 5, "stolen_base": 2, "walk_count": 3, "strike_out": 4,
             "batting_avg": 0.333, "on_base_pct": 0.400, "ops": 0.733},
            {"player_name": "Player 2", "double_hit": 0, "triple": 1, "homerun": 2,
             "hit_count": 3, "stolen_base": 0, "walk_count": 1, "strike_out": 2,
             "batting_avg": 0.250, "on_base_pct": 0.300, "ops": 0.550},
        ]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Player 1", output)
        self.assertIn("Player 2", output)
        # Check for hit counts and other new stats
        self.assertIn("5", output)  # Player 1 hit_count
        self.assertIn("3", output)  # Player 2 hit_count

    def test_display_batting_stats_column_header_present(self):
        """Test that column headers are formatted correctly"""
        stats = [
            {"player_name": "Player 1", "double_hit": 2, "triple": 0, "homerun": 1,
             "hit_count": 5, "stolen_base": 2, "walk_count": 3, "strike_out": 4,
             "batting_avg": 0.333, "on_base_pct": 0.400, "ops": 0.733},
        ]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        lines = output.split('\n')
        # Header should be in first or second line
        header_found = any("名前" in line and "安打" in line and "盗塁" in line for line in lines[:3])
        self.assertTrue(header_found)

    def test_display_batting_stats_shows_batting_avg(self):
        """Test that batting average is displayed"""
        stats = [
            {"player_name": "田中 太郎", "double_hit": 0, "triple": 0, "homerun": 0,
             "hit_count": 5, "stolen_base": 0, "walk_count": 0, "strike_out": 0,
             "batting_avg": 0.333, "on_base_pct": 0.400, "ops": 0.733},
        ]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn(".333", output)
        self.assertIn("0.733", output)

    def test_display_batting_stats_shows_none_for_missing_avg(self):
        """Test that '----' is displayed when batting average is None"""
        stats = [
            {"player_name": "山田 花子", "double_hit": 0, "triple": 0, "homerun": 0,
             "hit_count": 0, "stolen_base": 0, "walk_count": 0, "strike_out": 0,
             "batting_avg": None, "on_base_pct": None, "ops": None},
        ]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.view.display_batting_stats(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("----", output)


if __name__ == "__main__":
    unittest.main()
