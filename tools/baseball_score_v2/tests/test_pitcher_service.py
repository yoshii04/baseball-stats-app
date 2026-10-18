"""PitcherService の集計・DB 登録処理のテスト"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.pitcher_record import PitcherRecord
from model.team_pitcher_record import TeamPitcherRecord
from service.pitcher_service import PitcherService

DATE = "2026-04-18"
OPP = "相手A"


def _pitch(name="投手A", game_number=1, **kwargs) -> PitcherRecord:
    return PitcherRecord(date=DATE, opponent=OPP, pitcher_name=name,
                         game_number=game_number, **kwargs)


class TestSummarize(unittest.TestCase):

    def setUp(self):
        self.service = PitcherService()

    def tearDown(self):
        self.service.close()

    def test_empty_records(self):
        self.assertEqual(len(self.service.summarize([])), 0)

    def test_sums_stats_per_pitcher(self):
        records = [
            _pitch(pitch_count=5, hits_allowed=1, strikeouts=0, right_9=1),
            _pitch(pitch_count=3, walks_allowed=1, strikeouts=0, runs_allowed=1),
            _pitch(pitch_count=4, strikeouts=1, homerun_allowed=0),
        ]
        stats = self.service.summarize(records)[(DATE, OPP, 1)]["投手A"]
        self.assertEqual(stats["batters_faced"], 3)
        self.assertEqual(stats["pitch_count"], 12)
        self.assertEqual(stats["hits_allowed"], 1)
        self.assertEqual(stats["walks_allowed"], 1)
        self.assertEqual(stats["strikeouts"], 1)
        self.assertEqual(stats["runs_allowed"], 1)
        self.assertEqual(stats["right_9"], 1)

    def test_separates_pitchers_and_games(self):
        records = [
            _pitch("投手A", game_number=1),
            _pitch("投手B", game_number=1),
            _pitch("投手A", game_number=2),
        ]
        summary = self.service.summarize(records)
        self.assertEqual(set(summary.keys()), {(DATE, OPP, 1), (DATE, OPP, 2)})
        self.assertEqual(set(summary[(DATE, OPP, 1)].keys()), {"投手A", "投手B"})
        self.assertEqual(set(summary[(DATE, OPP, 2)].keys()), {"投手A"})

    def test_merges_team_records(self):
        records = [_pitch("投手A", pitch_count=10)]
        team = [TeamPitcherRecord(date=DATE, opponent=OPP, pitcher_name="投手A",
                                  innings_pitched=6, outs=1, earned_runs=2)]
        stats = self.service.summarize(records, team)[(DATE, OPP, 1)]["投手A"]
        self.assertEqual(stats["innings_pitched"], 6)
        self.assertEqual(stats["outs"], 1)
        self.assertEqual(stats["earned_runs"], 2)
        self.assertEqual(stats["pitch_count"], 10)

    def test_without_team_records_innings_stay_zero(self):
        stats = self.service.summarize([_pitch("投手A")])[(DATE, OPP, 1)]["投手A"]
        self.assertEqual(stats["innings_pitched"], 0)
        self.assertEqual(stats["earned_runs"], 0)


class TestImportToDb(unittest.TestCase):

    def _service_with_fake_repo(self):
        service = PitcherService()
        repo = MagicMock()
        repo.get_or_create_team.side_effect = lambda cur, name=None: 1 if name is None else 2
        repo.get_or_create_game.return_value = 100
        repo.get_or_create_player.side_effect = lambda cur, name, team_id: {"投手A": 10, "投手B": 11}[name]
        service._db_repo = repo
        return service, repo

    def test_inserts_one_row_per_pitcher_and_commits(self):
        service, repo = self._service_with_fake_repo()
        records = [_pitch("投手A", pitch_count=5), _pitch("投手B", pitch_count=3)]
        service.import_to_db(records)

        self.assertEqual(repo.insert_pitcher_stats.call_count, 2)
        inserted_ids = sorted(c.args[1] for c in repo.insert_pitcher_stats.call_args_list)
        self.assertEqual(inserted_ids, [10, 11])
        repo.conn.commit.assert_called_once()

    def test_game_is_created_with_our_team_first(self):
        service, repo = self._service_with_fake_repo()
        service.import_to_db([_pitch("投手A", game_number=2)])
        args = repo.get_or_create_game.call_args.args
        # (cur, date, home_team_id=自チーム, away_team_id=相手, game_number)
        self.assertEqual(args[1:], (DATE, 1, 2, 2))

    def test_empty_records_commit_without_insert(self):
        service, repo = self._service_with_fake_repo()
        service.import_to_db([])
        repo.insert_pitcher_stats.assert_not_called()
        repo.conn.commit.assert_called_once()

    def test_close_closes_repository(self):
        service, repo = self._service_with_fake_repo()
        with service:
            pass
        repo.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
