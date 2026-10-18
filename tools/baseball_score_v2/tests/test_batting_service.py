import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.batting_record import BattingRecord
from service.batting_service import BattingService


class TestBattingService(unittest.TestCase):
    """Test cases for BattingService"""

    def setUp(self):
        """Create a BattingService instance for testing"""
        self.service = BattingService()

    def tearDown(self):
        """Clean up after tests"""
        self.service.close()

    def test_summarize_hits_empty_records(self):
        """Test summarize_hits with empty records"""
        records = []
        summary = self.service.summarize_hits(records)
        self.assertEqual(len(summary), 0)

    def test_summarize_hits_single_double(self):
        """Test summarizing a single double hit"""
        records = [
            BattingRecord(
                date="2026-03-12",
                opponent="Team A",
                player="Player 1",
                game_number=1,
                double=1,
                triple=0,
                homerun=0
            )
        ]
        summary = self.service.summarize_hits(records)

        self.assertIn("2026-03-12", summary)
        self.assertIn("Team A", summary["2026-03-12"])
        self.assertIn(1, summary["2026-03-12"]["Team A"])
        self.assertIn("2塁打", summary["2026-03-12"]["Team A"][1])
        self.assertEqual(summary["2026-03-12"]["Team A"][1]["2塁打"]["Player 1"], 1)

    def test_summarize_hits_multiple_hits_same_player(self):
        """Test summarizing multiple hits for same player in different games"""
        records = [
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=1, double=1, triple=0, homerun=0),
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=2, double=1, triple=0, homerun=0),
        ]
        summary = self.service.summarize_hits(records)

        # Check game 1
        self.assertEqual(summary["2026-03-12"]["Team A"][1]["2塁打"]["Player 1"], 1)
        # Check game 2
        self.assertEqual(summary["2026-03-12"]["Team A"][2]["2塁打"]["Player 1"], 1)

    def test_summarize_hits_accumulates_hits(self):
        """Test that multiple hits of same type are accumulated"""
        records = [
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=1, double=2, triple=0, homerun=0),
        ]
        summary = self.service.summarize_hits(records)

        self.assertEqual(summary["2026-03-12"]["Team A"][1]["2塁打"]["Player 1"], 2)

    def test_summarize_hits_multiple_hit_types(self):
        """Test summarizing multiple types of hits"""
        records = [
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=1, double=1, triple=1, homerun=1),
        ]
        summary = self.service.summarize_hits(records)

        game_data = summary["2026-03-12"]["Team A"][1]
        self.assertEqual(game_data["2塁打"]["Player 1"], 1)
        self.assertEqual(game_data["3塁打"]["Player 1"], 1)
        self.assertEqual(game_data["本塁打"]["Player 1"], 1)

    def test_summarize_hits_ignores_zero_counts(self):
        """Test that hits with zero count are not added to summary"""
        records = [
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=1, double=0, triple=0, homerun=0),
        ]
        summary = self.service.summarize_hits(records)

        # The game exists in the summary, but should be empty since all hits are 0
        if 1 in summary.get("2026-03-12", {}).get("Team A", {}):
            game_data = summary["2026-03-12"]["Team A"][1]
            self.assertEqual(len(game_data), 0)

    def test_summarize_hits_multiple_players(self):
        """Test summarizing hits from multiple players"""
        records = [
            BattingRecord("2026-03-12", "Team A", "Player 1", game_number=1, double=1, triple=0, homerun=0),
            BattingRecord("2026-03-12", "Team A", "Player 2", game_number=1, double=1, triple=0, homerun=0),
        ]
        summary = self.service.summarize_hits(records)

        game_data = summary["2026-03-12"]["Team A"][1]["2塁打"]
        self.assertEqual(game_data["Player 1"], 1)
        self.assertEqual(game_data["Player 2"], 1)


class TestBattingServiceGetBattingStatsList(unittest.TestCase):
    """Test cases for BattingService.get_batting_stats_list()"""

    def setUp(self):
        """Create a BattingService instance for testing"""
        self.service = BattingService()

    def tearDown(self):
        """Clean up after tests"""
        self.service.close()

    @patch('service.batting_service.DBRepository')
    def test_get_batting_stats_list_returns_data_from_db(self, mock_db_repo_class):
        """Test that get_batting_stats_list returns data from DB"""
        mock_db_repo = MagicMock()
        mock_db_repo.fetch_batting_stats.return_value = [
            {"player_name": "Player 1", "double_hit": 2, "triple": 0, "homerun": 1,
             "hit_count": 5, "stolen_base": 2, "walk_count": 3, "strike_out": 4,
             "batting_avg": 0.333, "on_base_pct": 0.400},
            {"player_name": "Player 2", "double_hit": 0, "triple": 1, "homerun": 2,
             "hit_count": 3, "stolen_base": 0, "walk_count": 1, "strike_out": 2,
             "batting_avg": 0.250, "on_base_pct": 0.300},
        ]
        mock_db_repo_class.return_value = mock_db_repo

        self.service._db_repo = None  # Reset to force new instance
        stats = self.service.get_batting_stats_list()

        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]["player_name"], "Player 1")
        self.assertEqual(stats[0]["double_hit"], 2)
        self.assertEqual(stats[0]["hit_count"], 5)
        self.assertEqual(stats[1]["player_name"], "Player 2")

    @patch('service.batting_service.DBRepository')
    def test_get_batting_stats_list_returns_empty_list(self, mock_db_repo_class):
        """Test that get_batting_stats_list returns empty list when no data"""
        mock_db_repo = MagicMock()
        mock_db_repo.fetch_batting_stats.return_value = []
        mock_db_repo_class.return_value = mock_db_repo

        self.service._db_repo = None  # Reset to force new instance
        stats = self.service.get_batting_stats_list()

        self.assertEqual(len(stats), 0)

    @patch('service.batting_service.DBRepository')
    def test_get_batting_stats_list_reuses_existing_db_repo(self, mock_db_repo_class):
        """Test that get_batting_stats_list reuses existing _db_repo"""
        mock_db_repo = MagicMock()
        mock_db_repo.fetch_batting_stats.return_value = [
            {"player_name": "Player 1", "double_hit": 1, "triple": 0, "homerun": 0},
        ]
        self.service._db_repo = mock_db_repo

        stats = self.service.get_batting_stats_list()

        # Verify that the mock DB repo's method was called
        mock_db_repo.fetch_batting_stats.assert_called_once()


if __name__ == "__main__":
    unittest.main()
