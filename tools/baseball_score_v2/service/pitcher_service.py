import logging
from collections import defaultdict
from model.pitcher_record import PitcherRecord
from model.team_pitcher_record import TeamPitcherRecord
from repository.db_repository import DBRepository


class PitcherService:
    def __init__(self):
        self.logger = logging.getLogger("app.service")
        self._db_repo = None

    def _get_db_repo(self):
        if self._db_repo is None:
            self._db_repo = DBRepository()
        return self._db_repo

    def close(self):
        if self._db_repo is not None:
            self._db_repo.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def summarize(
        self,
        records: list[PitcherRecord],
        team_records: list[TeamPitcherRecord] | None = None,
    ) -> dict:
        """
        PitcherRecord リストを試合・投手単位に集計する。
        team_records が指定された場合はイニング数・自責点もマージする。
        戻り値: { (date, opponent, game_number) -> { pitcher_name -> stats_dict } }
        """
        summary = defaultdict(lambda: defaultdict(lambda: {
            "batters_faced": 0,
            "pitch_count": 0,
            "hits_allowed": 0,
            "homerun_allowed": 0,
            "walks_allowed": 0,
            "strikeouts": 0,
            "runs_allowed": 0,
            "right_9": 0,
            "right_center": 0,
            "center": 0,
            "left_center": 0,
            "left_7": 0,
            "innings_pitched": 0,
            "outs": 0,
            "earned_runs": 0,
        }))

        for r in records:
            key = (r.date, r.opponent, r.game_number)
            s = summary[key][r.pitcher_name]
            s["batters_faced"]   += 1
            s["pitch_count"]     += r.pitch_count
            s["hits_allowed"]    += r.hits_allowed
            s["homerun_allowed"] += r.homerun_allowed
            s["walks_allowed"]   += r.walks_allowed
            s["strikeouts"]      += r.strikeouts
            s["runs_allowed"]    += r.runs_allowed
            s["right_9"]         += r.right_9
            s["right_center"]    += r.right_center
            s["center"]          += r.center
            s["left_center"]     += r.left_center
            s["left_7"]          += r.left_7

        if team_records:
            for tr in team_records:
                key = (tr.date, tr.opponent, tr.game_number)
                s = summary[key][tr.pitcher_name]
                s["innings_pitched"] = tr.innings_pitched
                s["outs"]            = tr.outs
                s["earned_runs"]     = tr.earned_runs

        return summary

    def import_to_db(
        self,
        records: list[PitcherRecord],
        team_records: list[TeamPitcherRecord] | None = None,
    ):
        self.logger.info("投手成績DB登録処理開始")
        db_repo = self._get_db_repo()
        summary = self.summarize(records, team_records)

        with db_repo.conn.cursor() as cur:
            our_team_id = db_repo.get_or_create_team(cur)

            inserted = 0
            for (date, opponent, game_number), pitchers in summary.items():
                away_team_id = db_repo.get_or_create_team(cur, opponent)
                game_id = db_repo.get_or_create_game(cur, date, our_team_id, away_team_id, game_number)

                for pitcher_name, stats in pitchers.items():
                    pitcher_id = db_repo.get_or_create_player(cur, pitcher_name, our_team_id)
                    db_repo.insert_pitcher_stats(cur, pitcher_id, game_id, stats)
                    inserted += 1

            db_repo.conn.commit()
        self.logger.info("投手成績DB登録完了: %d 件", inserted)
