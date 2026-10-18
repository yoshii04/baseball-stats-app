import logging
from collections import defaultdict
from model.batting_record import BattingRecord
from repository.db_repository import DBRepository
class BattingService:
    def __init__(self):
        self.logger = logging.getLogger("app.service")
        self._db_repo = None

    def _get_db_repo(self):
        """Lazily initialize database repository on first use"""
        if self._db_repo is None:
            self._db_repo = DBRepository()
        return self._db_repo

    def close(self):
        """Close database connection if it was created"""
        if self._db_repo is not None:
            self._db_repo.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed"""
        self.close()
        return False

    def summarize_hits(self, records):
        # summary[日付][対戦相手][試合番号][打種][選手] = 本数
        summary = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(dict)
                )
            )
        )

        for r in records:
            for hit_type, count in {
                "2塁打": r.double,
                "3塁打": r.triple,
                "本塁打": r.homerun,
            }.items():
                if count > 0:
                    if r.player not in summary[r.date][r.opponent][r.game_number][hit_type]:
                        summary[r.date][r.opponent][r.game_number][hit_type][r.player] = 0
                    summary[r.date][r.opponent][r.game_number][hit_type][r.player] += count

        return summary
    
    def import_to_db(self, records):
        self.logger.info("DB登録処理開始")
        db_repo = self._get_db_repo()
        db_repo.insert_players(records)   # ① 先に選手を登録
        db_repo.insert_records(records)   # ② 試合データを登録
        self.logger.info("DB登録処理完了")

    def get_batting_stats_list(self) -> list[dict]:
        """DBから選手別打撃成績を取得して返す"""
        self.logger.info("打撃成績リスト取得開始")
        db_repo = self._get_db_repo()
        stats = db_repo.fetch_batting_stats()
        self.logger.info("打撃成績リスト取得完了: %d 件", len(stats))
        return stats

