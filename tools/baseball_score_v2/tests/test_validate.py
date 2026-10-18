"""validate.py のチェック関数と終了コードのテスト"""
import os
import sys
import unittest
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import validate
from model.batting_record import BattingRecord
from model.pitcher_record import PitcherRecord
from model.team_pitcher_record import TeamPitcherRecord


def _batting(**kwargs) -> BattingRecord:
    base = dict(date="2026-04-18", opponent="相手A", player="選手1", game_number=1)
    base.update(kwargs)
    return BattingRecord(**base)


class TestCheckBattingStats(unittest.TestCase):

    def test_valid_record_has_no_issue(self):
        r = _batting(at_bat_count=4, hit_count=2, double=1, strike_out=1,
                     on_base_opportunity=5, on_base=3)
        self.assertEqual(validate.check_batting_stats([r]), [])

    def test_extra_bases_exceed_hits(self):
        r = _batting(at_bat_count=4, hit_count=1, double=1, triple=1)
        issues = validate.check_batting_stats([r])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "ERROR")
        self.assertIn("長打計(2) > 安打(1)", issues[0].message)

    def test_hits_exceed_at_bats(self):
        r = _batting(at_bat_count=2, hit_count=3)
        issues = validate.check_batting_stats([r])
        self.assertEqual([i.level for i in issues], ["ERROR"])
        self.assertIn("安打(3) > 打数(2)", issues[0].message)

    def test_strike_outs_exceed_at_bats(self):
        r = _batting(at_bat_count=2, strike_out=3)
        issues = validate.check_batting_stats([r])
        self.assertEqual(len(issues), 1)
        self.assertIn("三振(3) > 打数(2)", issues[0].message)

    def test_on_base_exceeds_opportunity(self):
        r = _batting(at_bat_count=4, on_base_opportunity=3, on_base=4)
        issues = validate.check_batting_stats([r])
        self.assertEqual(len(issues), 1)
        self.assertIn("出塁(4) > 出塁機会(3)", issues[0].message)

    def test_on_base_not_checked_when_opportunity_is_zero(self):
        r = _batting(at_bat_count=4, on_base_opportunity=0, on_base=2)
        self.assertEqual(validate.check_batting_stats([r]), [])

    def test_message_contains_record_key(self):
        r = _batting(player="選手A", opponent="相手B", game_number=2,
                     at_bat_count=1, hit_count=2)
        message = validate.check_batting_stats([r])[0].message
        self.assertIn("選手A", message)
        self.assertIn("相手B", message)
        self.assertIn("game=2", message)


class TestCheckDateFormat(unittest.TestCase):

    def test_accepts_known_formats(self):
        for date in ("2026-04-18", "2026/04/18", "04/18/2026", "04-18-2026"):
            with self.subTest(date=date):
                self.assertEqual(validate.check_date_format([_batting(date=date)]), [])

    def test_rejects_unparsable_date(self):
        issues = validate.check_date_format([_batting(date="4月18日")])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "WARNING")
        self.assertIn("4月18日", issues[0].message)

    def test_same_bad_date_is_reported_once(self):
        records = [_batting(date="abc", player="A"), _batting(date="abc", player="B")]
        self.assertEqual(len(validate.check_date_format(records)), 1)


class TestCheckOpponentNameVariants(unittest.TestCase):

    def test_detects_fullwidth_space_variant(self):
        records = [
            _batting(opponent="相手 A"),
            _batting(opponent="相手　A"),
        ]
        issues = validate.check_opponent_name_variants(records)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "WARNING")

    def test_detects_trailing_space_variant(self):
        records = [_batting(opponent="相手A"), _batting(opponent="相手A ")]
        self.assertEqual(len(validate.check_opponent_name_variants(records)), 1)

    def test_distinct_names_are_not_flagged(self):
        records = [_batting(opponent="相手A"), _batting(opponent="相手B")]
        self.assertEqual(validate.check_opponent_name_variants(records), [])


class TestCheckPitcherInTeamData(unittest.TestCase):

    def test_unknown_pitcher_is_warned_once(self):
        pitchers = [
            PitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手A"),
            PitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手A"),
            PitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手B"),
        ]
        team = [TeamPitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手B")]
        issues = validate.check_pitcher_in_team_data(pitchers, team)
        self.assertEqual(len(issues), 1)
        self.assertIn("投手A", issues[0].message)

    def test_all_known_pitchers_pass(self):
        pitchers = [PitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手B")]
        team = [TeamPitcherRecord(date="2026-04-18", opponent="相手A", pitcher_name="投手B")]
        self.assertEqual(validate.check_pitcher_in_team_data(pitchers, team), [])


class TestRunValidation(unittest.TestCase):
    """run_validation の終了コード（後続ステップを止めるゲートとして使われる）"""

    CONFIG = {"excel_file": "dummy.xlsx", "sheet_name": "打撃"}

    def _run(self, batting, pitchers=(), team=(), strict=False) -> int:
        with patch.object(validate, "setup_logging"), \
             patch.object(validate, "load_config", return_value=self.CONFIG), \
             patch.object(validate.BattingRepository, "load_records", return_value=list(batting)), \
             patch.object(validate.PitcherRepository, "load_records", return_value=list(pitchers)), \
             patch.object(validate.TeamPitcherRepository, "load_records", return_value=list(team)), \
             redirect_stdout(StringIO()):
            return validate.run_validation(strict=strict)

    def test_clean_data_returns_zero(self):
        self.assertEqual(self._run([_batting(at_bat_count=4, hit_count=1)]), 0)

    def test_error_returns_one(self):
        self.assertEqual(self._run([_batting(at_bat_count=1, hit_count=2)]), 1)

    def test_warning_only_returns_zero(self):
        self.assertEqual(self._run([_batting(date="不正な日付")]), 0)

    def test_strict_mode_promotes_warning_to_error(self):
        self.assertEqual(self._run([_batting(date="不正な日付")], strict=True), 1)


if __name__ == "__main__":
    unittest.main()
