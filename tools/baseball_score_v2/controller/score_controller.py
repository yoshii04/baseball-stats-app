"""試合スコア書き込みコントローラー"""
import datetime
import logging
from model.game_record import GameRecord
from utils.game_input_parser import parse_game_file, parse_score_csv
from repository.score_excel_writer import ScoreExcelWriter

# この日付以降のデータのみExcelに書き込む
GAME_INPUT_CUTOFF_DATE = datetime.date(2026, 4, 18)


class ScoreController:
    """試合スコアと打撃成績をExcelに書き込むコントローラー"""

    def __init__(self):
        self.logger = logging.getLogger("app.score_controller")
        self.writer = ScoreExcelWriter()

    def write_game(
        self,
        game_file: str,
        csv_file: str,
        excel_path: str,
        sheet_name: str,
        our_team: str,
        start_row: int = None,
        dry_run: bool = False,
    ) -> int | None:
        """
        試合入力ファイルとスコアCSVを読み込み、Excelに書き込む。
        csv_file が None の場合はスコアを空欄で書き込む。

        Returns:
            書き込んだ開始行番号。スキップの場合は None を返す。
        """
        self.logger.info("試合入力ファイル読み込み: %s", game_file)
        game_data = parse_game_file(game_file)

        # 日付フィルター: GAME_INPUT_CUTOFF_DATE 未満はスキップ
        game_date = datetime.date.fromisoformat(game_data["date"])
        if game_date < GAME_INPUT_CUTOFF_DATE:
            self.logger.info(
                "スキップ: %s は %s より前のため処理しません",
                game_data["date"], GAME_INPUT_CUTOFF_DATE,
            )
            return None

        if csv_file is not None:
            self.logger.info("スコアCSV読み込み: %s", csv_file)
            score_data = parse_score_csv(csv_file)
            our_innings = score_data["our_innings"]
            opp_innings = score_data["opp_innings"]
            our_total = score_data["our_total"]
            opp_total = score_data["opp_total"]
            # CSVの行順を優先（1行目のチーム名を上段、2行目を下段に使用）
            csv_our_team = score_data["our_team"]
            opp_team = score_data["opp_team"]
            # サヨナラ自動検出: CSVの合計値が "2X" のようにXで終わる場合は自動でサヨナラフラグを立てる
            is_sayonara = game_data.get("is_sayonara", False)
            if not is_sayonara:
                if isinstance(opp_total, str) and opp_total.upper().endswith("X"):
                    is_sayonara = True
                    self.logger.info("サヨナラを自動検出: opp_total=%s", opp_total)
                elif isinstance(our_total, str) and our_total.upper().endswith("X"):
                    is_sayonara = True
                    self.logger.info("サヨナラを自動検出: our_total=%s", our_total)
        else:
            self.logger.info("スコアCSV未指定: スコアは空欄で書き込みます")
            our_innings = None
            opp_innings = None
            our_total = None
            opp_total = None
            csv_our_team = our_team
            opp_team = ""
            is_sayonara = game_data.get("is_sayonara", False)

        game = GameRecord(
            date=game_data["date"],
            opponent=game_data["opponent"],
            game_number=game_data["game_number"],
            venue=game_data["venue"],
            pitcher=game_data["pitcher"],
            our_innings=our_innings,
            opp_innings=opp_innings,
            our_total=our_total,
            opp_total=opp_total,
            our_team=csv_our_team,
            opp_team=opp_team,
            doubles=game_data["doubles"],
            triples=game_data["triples"],
            homeruns=game_data["homeruns"],
            is_sayonara=is_sayonara,
        )

        self.logger.info(
            "GameRecord 構築完了: %s vs %s (%s)",
            game.our_team, game.opp_team, game.date,
        )

        written_row = self.writer.write_game(
            excel_path=excel_path,
            sheet_name=sheet_name,
            game=game,
            start_row=start_row,
            dry_run=dry_run,
        )

        return written_row
