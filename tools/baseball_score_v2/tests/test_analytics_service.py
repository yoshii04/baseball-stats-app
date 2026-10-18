"""AnalyticsService の累積成績・打球方向割合のテスト"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.analytics_service import AnalyticsService


def _game(player="選手1", ab=0, hit=0, double=0, triple=0, hr=0, ob=0, ob_opp=0, date="2026-04-18"):
    return {
        "player_name": player, "game_date": date,
        "at_bat_count": ab, "hit_count": hit,
        "double_hit": double, "triple": triple, "homerun": hr,
        "on_base": ob, "on_base_opportunity": ob_opp,
    }


class TestCumulativeStats(unittest.TestCase):

    def setUp(self):
        self.service = AnalyticsService()

    def test_empty_log(self):
        self.assertEqual(self.service.calculate_cumulative_stats([]), [])

    def test_cumulative_average_and_ops(self):
        log = [
            _game(ab=4, hit=2, double=1, ob=3, ob_opp=5, date="2026-04-18"),
            _game(ab=4, hit=1, hr=1, ob=1, ob_opp=4, date="2026-04-25"),
        ]
        result = self.service.calculate_cumulative_stats(log)

        # 1試合目: 打率 2/4、出塁率 3/5、長打率 (2+1)/4 → OPS 0.6 + 0.75
        self.assertEqual(result[0]["cum_avg"], 0.5)
        self.assertEqual(result[0]["cum_ops"], 1.35)
        # 2試合目: 打数 8、安打 3、出塁 4/9、塁打 (3 + 1 + 3)/8
        self.assertEqual(result[1]["cum_avg"], 0.375)
        self.assertEqual(result[1]["cum_ops"], round(round(4 / 9, 3) + round(7 / 8, 3), 3))

    def test_total_bases_weight_each_hit_type(self):
        # 単打1・二塁打1・三塁打1・本塁打1（4打数4安打）→ 塁打 1+2+3+4 = 10 → 長打率 2.5
        # 出塁率 4/4 = 1.0 → OPS 3.5
        game = _game(ab=4, hit=4, double=1, triple=1, hr=1, ob=4, ob_opp=4)
        result = self.service.calculate_cumulative_stats([game])[0]
        self.assertEqual(result["cum_avg"], 1.0)
        self.assertEqual(result["cum_ops"], 3.5)

    def test_zero_at_bats_gives_none(self):
        result = self.service.calculate_cumulative_stats([_game(ab=0, ob_opp=0)])
        self.assertIsNone(result[0]["cum_avg"])
        self.assertIsNone(result[0]["cum_ops"])

    def test_players_are_accumulated_separately(self):
        log = [
            _game("選手A", ab=4, hit=4),
            _game("選手B", ab=4, hit=0),
            _game("選手A", ab=4, hit=0),
        ]
        result = self.service.calculate_cumulative_stats(log)
        by_player = {}
        for row in result:
            by_player.setdefault(row["player_name"], []).append(row["cum_avg"])
        self.assertEqual(by_player["選手A"], [1.0, 0.5])
        self.assertEqual(by_player["選手B"], [0.0])

    def test_original_fields_are_kept(self):
        row = self.service.calculate_cumulative_stats([_game(ab=1, hit=1)])[0]
        self.assertEqual(row["player_name"], "選手1")
        self.assertEqual(row["game_date"], "2026-04-18")


class TestDirectionPct(unittest.TestCase):

    def setUp(self):
        self.service = AnalyticsService()

    def test_percentages(self):
        rows = [{"right_9": 1, "right_center": 1, "center_field": 2, "left_center": 0, "left_7": 0}]
        result = self.service.calculate_direction_pct(rows)[0]
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["pct_right_9"], 25.0)
        self.assertEqual(result["pct_center"], 50.0)
        self.assertEqual(result["pct_left_7"], 0.0)

    def test_zero_total_gives_zero_percent(self):
        rows = [{"right_9": 0, "right_center": 0, "center_field": 0, "left_center": 0, "left_7": 0}]
        result = self.service.calculate_direction_pct(rows)[0]
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["pct_center"], 0.0)

    def test_rounds_to_one_decimal(self):
        rows = [{"right_9": 1, "right_center": 1, "center_field": 1, "left_center": 0, "left_7": 0}]
        self.assertEqual(self.service.calculate_direction_pct(rows)[0]["pct_right_9"], 33.3)


if __name__ == "__main__":
    unittest.main()
