"""Analytics controller: orchestrates data fetch → calculation → Excel output"""
import logging

from repository.analytics_repository import AnalyticsRepository
from service.analytics_service import AnalyticsService
from repository.analytics_excel_writer import AnalyticsExcelWriter


class AnalyticsController:
    def __init__(self):
        self.logger = logging.getLogger("app.controller")
        self.repo = AnalyticsRepository()
        self.service = AnalyticsService()

    def close(self):
        self.repo.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def generate_analytics(self, year: int, output_path: str) -> None:
        """年度指定で分析Excelを生成する"""
        self.logger.info("分析Excel生成開始: year=%d, output=%s", year, output_path)
        writer = AnalyticsExcelWriter(output_path)

        # Sheet 1: 選手別打撃成績
        try:
            stats = self.repo.fetch_player_batting_stats(year)
            if stats:
                writer.write_player_batting_stats(stats)
                self.logger.info("Sheet 1 完了: %d 選手", len(stats))
            else:
                self.logger.warning("Sheet 1: %d年のデータが見つかりません", year)
        except Exception as e:
            self.logger.error("Sheet 1 エラー: %s", e)

        # Sheet 2: 打球方向分析
        try:
            direction_raw = self.repo.fetch_hit_direction_stats(year)
            if direction_raw:
                direction = self.service.calculate_direction_pct(direction_raw)
                writer.write_hit_direction(direction)
                self.logger.info("Sheet 2 完了: %d 選手", len(direction))
            else:
                self.logger.warning("Sheet 2: %d年のデータが見つかりません", year)
        except Exception as e:
            self.logger.error("Sheet 2 エラー: %s", e)

        # Sheet 3: 選手別成績推移
        try:
            game_log = self.repo.fetch_player_game_log(year)
            if game_log:
                cumulative = self.service.calculate_cumulative_stats(game_log)
                writer.write_player_progress(cumulative)
                self.logger.info("Sheet 3 完了: %d 件", len(cumulative))
            else:
                self.logger.warning("Sheet 3: %d年のデータが見つかりません", year)
        except Exception as e:
            self.logger.error("Sheet 3 エラー: %s", e)

        writer.save()
        self.logger.info("分析Excel生成完了: %s", output_path)
