import logging
import pandas as pd
from model.team_pitcher_record import TeamPitcherRecord
from utils.excel_util import safe_str, safe_int, safe_game_number


class TeamPitcherRepository:
    """「チーム単位のデータ」シートを読み込むリポジトリ"""

    def __init__(self):
        self.logger = logging.getLogger("app.repository")

    def load_records(self, excel_file: str, sheet_name: str) -> list[TeamPitcherRecord]:
        records = []
        self.logger.info("Excelファイル読み込み開始（チーム投手）: %s (%s)", excel_file, sheet_name)

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            header=0,
        )
        self.logger.info("読み込み列（チーム投手）: %s", df.columns.tolist())

        for _, row in df.iterrows():
            date = safe_str(row.get("日付"))
            opponent = safe_str(row.get("対戦相手"))
            pitcher_name = safe_str(row.get("選手名"))

            if not date or not opponent or not pitcher_name:
                continue

            # 試合回数列は改行含む "試合\n回数" → pandas が読み込むと改行が含まれる場合がある
            game_number_raw = row.get("試合\n回数")
            game_number = safe_game_number(game_number_raw)

            record = TeamPitcherRecord(
                date=date,
                opponent=opponent,
                pitcher_name=pitcher_name,
                game_number=game_number,
                runs_allowed=safe_int(row.get("失点")),
                earned_runs=safe_int(row.get("自責点")),
                innings_pitched=safe_int(row.get("イニング")),
                outs=safe_int(row.get("アウト")),
            )
            records.append(record)

        self.logger.info("Excelファイル読み込み完了（チーム投手）: %d 件", len(records))
        return records
