#!/usr/bin/env python3
"""
試合スコア・打撃成績をExcelに書き込むエントリーポイント

使い方（単一ファイル）:
    python write_score.py --game data/game_inputs/sample.txt --csv data/scores/sample.csv
    python write_score.py --game data/game_inputs/sample.txt  # スコアなし（空欄）で書き込む
    python write_score.py --game ... --csv ... --dry-run
    python write_score.py --game ... --csv ... --start-row 349

使い方（一括処理）:
    python write_score.py --game data/game_inputs/  # ディレクトリ指定で全ファイル処理
    python write_score.py --game data/game_inputs/ --csv-dir /path/to/csv_dir/
"""
import argparse
import glob
import json
import logging
import logging.config
import os
import re
import sys

from app_util import get_our_team_name
from controller.score_controller import ScoreController


def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    config_path = os.path.join(os.path.dirname(__file__), "config", "logging.conf")
    logging.config.fileConfig(config_path, disable_existing_loggers=False)


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args():
    parser = argparse.ArgumentParser(
        description="試合スコア・打撃成績をExcelに書き込む"
    )
    parser.add_argument(
        "--game", required=True,
        help="試合入力テキストファイルのパス、またはディレクトリ (例: data/game_inputs/ または data/game_inputs/sample.txt)"
    )
    parser.add_argument(
        "--csv", required=False, default=None,
        help="スコアCSVファイルのパス（単一ファイル指定時のみ）"
    )
    parser.add_argument(
        "--csv-dir", required=False, default=None,
        help="スコアCSVファイルが格納されているディレクトリ（一括処理時に自動マッチング）"
    )
    parser.add_argument(
        "--start-row", type=int, default=None,
        help="書き込み開始行（省略時は自動検出）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="書き込まず内容のみ確認表示する"
    )
    return parser.parse_args()


def find_matching_csv(game_file: str, csv_dir: str) -> str | None:
    """
    ゲームファイル名（YYYY-MM-DD_相手チーム_N.txt）からCSVを自動マッチングする。
    CSVファイル名のパターン: *_YYYY-MM-DD_N.csv
    """
    basename = os.path.basename(game_file)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})_.*?_(\d+)\.txt$", basename)
    if not m:
        return None
    date_str, game_num = m.group(1), m.group(2)
    pattern = os.path.join(csv_dir, f"*_{date_str}_{game_num}.csv")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None


def process_single_game(
    controller: ScoreController,
    game_file: str,
    csv_file: str | None,
    excel_path: str,
    sheet_name: str,
    our_team: str,
    start_row: int | None,
    dry_run: bool,
    logger,
) -> None:
    logger.info("処理中: game=%s, csv=%s", game_file, csv_file or "(なし)")
    print(f"\n--- {os.path.basename(game_file)} ---")
    try:
        written_row = controller.write_game(
            game_file=game_file,
            csv_file=csv_file,
            excel_path=excel_path,
            sheet_name=sheet_name,
            our_team=our_team,
            start_row=start_row,
            dry_run=dry_run,
        )
        if written_row is None:
            print("スキップ: 対象外の日付、またはすでにExcelに書き込み済みです。")
            logger.info("スキップ: %s", os.path.basename(game_file))
            return
        if dry_run:
            print("DRY RUN 完了。")
        else:
            print(f"書き込み完了: 行 {written_row}〜{written_row + 5}")
        logger.info("完了: 開始行=%d", written_row)
    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません: {e}", file=sys.stderr)
        logger.error("ファイルが見つかりません: %s", e)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        logger.error("値エラー: %s", e)
    except Exception as e:
        print(f"エラー: 予期しないエラーが発生しました: {e}", file=sys.stderr)
        logger.error("予期しないエラー: %s", e, exc_info=True)


def main():
    setup_logging()
    logger = logging.getLogger("app.write_score")

    args = parse_args()

    try:
        config = load_config()
    except FileNotFoundError:
        print("エラー: config.json が見つかりません。", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"エラー: config.json の形式が不正です: {e}", file=sys.stderr)
        sys.exit(1)

    score_excel_file = config.get("score_excel_file")
    score_sheet_name = config.get("score_sheet_name")
    try:
        our_team_name = get_our_team_name(config)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    if not score_excel_file:
        print("エラー: config.json に 'score_excel_file' が設定されていません。", file=sys.stderr)
        sys.exit(1)
    if not score_sheet_name:
        print("エラー: config.json に 'score_sheet_name' が設定されていません。", file=sys.stderr)
        sys.exit(1)

    controller = ScoreController()

    # ディレクトリ指定の場合は一括処理
    if os.path.isdir(args.game):
        game_files = sorted(glob.glob(os.path.join(args.game, "*.txt")))
        if not game_files:
            print(f"エラー: {args.game} に .txt ファイルが見つかりません。", file=sys.stderr)
            sys.exit(1)

        print(f"{len(game_files)} 件のゲームファイルを処理します。")
        logger.info("一括処理開始: %d 件", len(game_files))

        for game_file in game_files:
            csv_file = None
            if args.csv_dir:
                csv_file = find_matching_csv(game_file, args.csv_dir)
                if csv_file:
                    logger.info("CSVマッチング: %s → %s", os.path.basename(game_file), os.path.basename(csv_file))

            process_single_game(
                controller, game_file, csv_file,
                score_excel_file, score_sheet_name, our_team_name,
                args.start_row, args.dry_run, logger,
            )

        print(f"\n一括処理完了: {len(game_files)} 件")
        if args.dry_run:
            print("DRY RUN モードでした。実際に書き込む場合は --dry-run を外してください。")

    # 単一ファイル指定の場合
    else:
        logger.info("スコア書き込み開始: game=%s, csv=%s", args.game, args.csv or "(なし)")

        csv_file = args.csv
        if csv_file is None and args.csv_dir:
            csv_file = find_matching_csv(args.game, args.csv_dir)
            if csv_file:
                logger.info("CSVマッチング: %s", os.path.basename(csv_file))

        try:
            written_row = controller.write_game(
                game_file=args.game,
                csv_file=csv_file,
                excel_path=score_excel_file,
                sheet_name=score_sheet_name,
                our_team=our_team_name,
                start_row=args.start_row,
                dry_run=args.dry_run,
            )
            if written_row is None:
                print("スキップ: 対象外の日付、またはすでにExcelに書き込み済みです。")
                logger.info("スキップ: %s", args.game)
            elif args.dry_run:
                print(f"\nDRY RUN 完了。実際に書き込む場合は --dry-run を外して実行してください。")
            else:
                print(f"書き込み完了: {score_excel_file} (行 {written_row}〜{written_row + 5})")
            if written_row is not None:
                logger.info("スコア書き込み完了: 開始行=%d", written_row)
        except FileNotFoundError as e:
            print(f"エラー: ファイルが見つかりません: {e}", file=sys.stderr)
            logger.error("ファイルが見つかりません: %s", e)
            sys.exit(1)
        except ValueError as e:
            print(f"エラー: {e}", file=sys.stderr)
            logger.error("値エラー: %s", e)
            sys.exit(1)
        except Exception as e:
            print(f"エラー: 予期しないエラーが発生しました: {e}", file=sys.stderr)
            logger.error("予期しないエラー: %s", e, exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
