"""
Excel読み込み・集計表示・試合入力ファイル生成

使い方:
    python generate.py
"""
import json
import logging
import os
from app_util import get_team_data_sheet_name, setup_logging, load_config
from controller.batting_controller import BattingController
from repository.pitcher_repository import PitcherRepository
from repository.team_pitcher_repository import TeamPitcherRepository
from service.pitcher_service import PitcherService
from view.pitcher_view import PitcherView


def main():
    setup_logging()
    logger = logging.getLogger("app.main")

    try:
        config = load_config()
        excel_file = config["excel_file"]
        sheet_name = config["sheet_name"]
        pitcher_sheet = config.get("pitcher_sheet_name", "データ入力シート(相手攻撃)")
        team_sheet = get_team_data_sheet_name(config)
        game_inputs_dir = os.path.join(os.path.dirname(__file__), "data", "game_inputs")

        logger.info("generate 開始")

        # チーム単位シートから投手情報を読み込んで pitcher_map を構築
        team_repo = TeamPitcherRepository()
        team_records = team_repo.load_records(excel_file, team_sheet)
        pitcher_map: dict = {}
        for tr in team_records:
            key = (tr.date, tr.opponent, tr.game_number)
            if key not in pitcher_map:
                pitcher_map[key] = []
            pitcher_map[key].append((tr.pitcher_name, tr.innings_pitched, tr.outs))

        # 打撃成績: 集計表示・試合入力ファイル生成
        controller = BattingController()
        try:
            records = controller.load_records(excel_file, sheet_name)
            controller.show_summary(records)
            generated = controller.export_game_inputs(records, game_inputs_dir, pitcher_map=pitcher_map)
            print(f"\n試合入力ファイルを {len(generated)} 件生成しました（既存ファイルはスキップ）: {game_inputs_dir}")
        finally:
            controller.service.close()

        # 投手成績: 集計表示
        repo = PitcherRepository()
        service = PitcherService()
        view = PitcherView()
        pitcher_records = repo.load_records(excel_file, pitcher_sheet)
        summary = service.summarize(pitcher_records, team_records)
        view.display_summary(summary)

        logger.info("generate 完了")

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
