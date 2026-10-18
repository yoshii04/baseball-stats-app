"""デモ用の合成データ生成（demo/generate_demo_data.py）のテスト"""
import os
import sys
import unittest
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from demo import generate_demo_data as demo


class TestDemoData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.games, cls.sql, cls.history = demo.generate()

    def test_deterministic(self):
        _, sql, history = demo.generate()
        self.assertEqual(sql, self.sql)
        self.assertEqual(history, self.history)

    def test_committed_seed_matches_generator(self):
        with open(os.path.join(ROOT, "demo", "seed.sql"), encoding="utf-8") as f:
            self.assertEqual(f.read(), self.sql, "python demo/generate_demo_data.py を実行して seed.sql を更新する")
        with open(os.path.join(ROOT, "demo", "logs", "run_history.jsonl"), encoding="utf-8") as f:
            self.assertEqual(f.read(), self.history)

    def test_batting_lines_are_consistent(self):
        for game in self.games:
            for _, b in game.batting:
                self.assertLessEqual(b["hit_count"], b["at_bat_count"])
                self.assertLessEqual(b["double_hit"] + b["triple"] + b["homerun"], b["hit_count"])
                self.assertLessEqual(b["strike_out"], b["at_bat_count"])
                self.assertEqual(b["on_base"], b["hit_count"] + b["walk_count"])
                self.assertLessEqual(b["on_base"], b["on_base_opportunity"])
                self.assertEqual(b["at_bat_count"] + b["walk_count"], b["on_base_opportunity"])

    def test_one_batting_line_per_player_per_game(self):
        for game in self.games:
            players = [idx for idx, _ in game.batting]
            self.assertEqual(len(players), len(set(players)))
            pitchers = [idx for idx, _ in game.pitching]
            self.assertEqual(len(pitchers), len(set(pitchers)))

    def test_game_score_matches_pitching(self):
        for game in self.games:
            self.assertEqual(game.runs_against, sum(p["runs_allowed"] for _, p in game.pitching))
            outs = sum(p["innings_pitched"] * 3 + p["outs"] for _, p in game.pitching)
            self.assertEqual(outs, 27)
            for _, p in game.pitching:
                self.assertLessEqual(p["earned_runs"], p["runs_allowed"])

    def test_result_matches_score(self):
        for game in self.games:
            expected = "〇" if game.runs_for > game.runs_against else \
                "×" if game.runs_for < game.runs_against else "△"
            self.assertEqual(game.result, expected)

    def test_schedule_is_unique_and_in_one_season(self):
        keys = Counter((g.date, g.game_number) for g in self.games)
        self.assertEqual(max(keys.values()), 1)
        for game in self.games:
            self.assertGreaterEqual(game.date, demo.SEASON_START)
            self.assertLessEqual(game.date, demo.SEASON_END)
            self.assertIn(game.opponent, demo.OPPONENTS)

    def test_team_name_matches_demo_compose(self):
        compose = os.path.join(ROOT, "demo", "docker-compose.yml")
        with open(compose, encoding="utf-8") as f:
            self.assertIn(f"TEAM_NAME: {demo.TEAM_NAME}", f.read())


if __name__ == "__main__":
    unittest.main()
