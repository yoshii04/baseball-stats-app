"""
DBに打撃成績・投手成績・チーム成績（試合一覧）をすべて登録

使い方:
    python import_db.py
"""
import json
import logging
import openpyxl
import psycopg2
from psycopg2.extras import DictCursor

from app_util import get_team_data_sheet_name, setup_logging, load_config, setup_docker_and_db
from config.config import DB_CONFIG, TEAM_NAME
from controller.batting_controller import BattingController
from repository.pitcher_repository import PitcherRepository
from repository.team_pitcher_repository import TeamPitcherRepository
from service.pitcher_service import PitcherService
from view.pitcher_view import PitcherView

GAME_LIST_SHEET = "2025年度\u3000試合の一覧"

# シート列インデックス（0始まり）
_COL_DATE = 1
_COL_GAME_NUMBER = 2
_COL_OPPONENT = 3
_COL_HOME_SCORE = 4
_COL_AWAY_SCORE = 5
_COL_RESULT = 6


def _read_game_list(excel_file: str, sheet_name: str) -> list[dict]:
    """Excelの試合一覧シートを読み込んでリストで返す"""
    wb = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
    ws = wb[sheet_name]

    records = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 4:
            continue  # タイトル行・ヘッダー行をスキップ
        game_date = row[_COL_DATE]
        if game_date is None:
            continue  # 空行はスキップ
        records.append({
            "game_date": game_date.date() if hasattr(game_date, "date") else game_date,
            "game_number": int(row[_COL_GAME_NUMBER]) if row[_COL_GAME_NUMBER] is not None else 1,
            "opponent": str(row[_COL_OPPONENT]) if row[_COL_OPPONENT] is not None else "",
            "home_score": int(row[_COL_HOME_SCORE]) if row[_COL_HOME_SCORE] is not None else None,
            "away_score": int(row[_COL_AWAY_SCORE]) if row[_COL_AWAY_SCORE] is not None else None,
            "result": str(row[_COL_RESULT]) if row[_COL_RESULT] is not None else None,
        })

    wb.close()
    return records


def _get_or_create_team(cur, team_name: str) -> int:
    """チーム名からteam_idを取得、なければ挿入して返す"""
    cur.execute("SELECT team_id FROM teams WHERE team_name = %s", (team_name,))
    row = cur.fetchone()
    if row:
        return row["team_id"]
    cur.execute(
        "INSERT INTO teams (team_name) VALUES (%s) RETURNING team_id",
        (team_name,)
    )
    return cur.fetchone()["team_id"]


def _import_game_list(records: list[dict]) -> None:
    """試合一覧をDBに取込む（home_score/away_score/resultをUPDATE）"""
    logger = logging.getLogger("app.import_db")

    conn = psycopg2.connect(**DB_CONFIG, connect_timeout=20, sslmode="disable")
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            our_team_id = _get_or_create_team(cur, TEAM_NAME)

            updated = 0
            inserted = 0
            for rec in records:
                opponent_team_id = _get_or_create_team(cur, rec["opponent"])

                cur.execute(
                    """
                    SELECT game_id FROM games
                    WHERE game_date = %s
                      AND home_team_id = %s
                      AND away_team_id = %s
                      AND game_number = %s
                    """,
                    (rec["game_date"], our_team_id, opponent_team_id, rec["game_number"]),
                )
                row = cur.fetchone()

                if row:
                    cur.execute(
                        """
                        UPDATE games
                        SET home_score = %s, away_score = %s, result = %s
                        WHERE game_id = %s
                        """,
                        (rec["home_score"], rec["away_score"], rec["result"], row["game_id"]),
                    )
                    updated += 1
                else:
                    cur.execute(
                        """
                        INSERT INTO games (game_date, home_team_id, away_team_id, game_number,
                                           home_score, away_score, result)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            rec["game_date"], our_team_id, opponent_team_id, rec["game_number"],
                            rec["home_score"], rec["away_score"], rec["result"],
                        ),
                    )
                    inserted += 1

        conn.commit()
        logger.info("チーム成績取込完了: 更新 %d 件、新規挿入 %d 件", updated, inserted)
        print(f"チーム成績取込完了: 更新 {updated} 件、新規挿入 {inserted} 件")
    finally:
        conn.close()


def main():
    setup_logging()
    logger = logging.getLogger("app.main")

    try:
        config = load_config()
        excel_file = config["excel_file"]
        sheet_name = config["sheet_name"]
        pitcher_sheet = config.get("pitcher_sheet_name", "データ入力シート(相手攻撃)")
        team_sheet = get_team_data_sheet_name(config)
        game_list_sheet = config.get("game_list_sheet_name", GAME_LIST_SHEET)

        setup_docker_and_db()

        # 1. 打撃成績
        logger.info("打撃成績 DB登録 開始")
        controller = BattingController()
        try:
            records = controller.load_records(excel_file, sheet_name)
            controller.import_to_db(records)
            controller.show_batting_stats_list()
        finally:
            controller.service.close()
        logger.info("打撃成績 DB登録 完了")

        # 2. 投手成績
        logger.info("投手成績 DB登録 開始")
        repo = PitcherRepository()
        team_repo = TeamPitcherRepository()
        service = PitcherService()
        view = PitcherView()
        try:
            pitcher_records = repo.load_records(excel_file, pitcher_sheet)
            team_records = team_repo.load_records(excel_file, team_sheet)
            summary = service.summarize(pitcher_records, team_records)
            view.display_summary(summary)
            service.import_to_db(pitcher_records, team_records)
            print("\n投手成績のDB登録が完了しました。")
        finally:
            service.close()
        logger.info("投手成績 DB登録 完了")

        # 3. チーム成績（試合一覧）
        logger.info("チーム成績（試合一覧） DB登録 開始")
        game_records = _read_game_list(excel_file, game_list_sheet)
        _import_game_list(game_records)
        logger.info("チーム成績（試合一覧） DB登録 完了")

        logger.info("import_db 全処理完了")

    except FileNotFoundError as e:
        logger.error("設定ファイルが見つかりません: %s", e)
        raise
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("設定ファイルの形式が不正です: %s", e)
        raise
    except Exception as e:
        logger.error("予期しないエラーが発生しました: %s", e)
        raise


if __name__ == "__main__":
    main()
