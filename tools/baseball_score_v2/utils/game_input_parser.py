"""試合入力ファイルとスコアCSVのパーサー"""
import csv
import datetime
import logging
from pathlib import Path

logger = logging.getLogger("app.parser")

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def parse_game_file(txt_path: str) -> dict:
    """
    試合入力テキストファイルを読み込んで辞書を返す。

    フォーマット例:
        date: 2026-07-21
        opponent: 相手A高校
        game_number: 1
        venue: サンプルグラウンド
        pitcher: 投手A（6回）、投手B（3回）
        doubles: 選手A、選手B、選手C
        triples: 選手D
        homeruns:
    """
    result = {
        "date": "",
        "opponent": "",
        "game_number": 1,
        "venue": "",
        "pitcher": "",
        "doubles": [],
        "triples": [],
        "homeruns": [],
        "is_sayonara": False,
    }

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if key == "date":
                result["date"] = value
            elif key == "opponent":
                result["opponent"] = value
            elif key == "game_number":
                result["game_number"] = int(value) if value else 1
            elif key == "venue":
                result["venue"] = value
            elif key == "pitcher":
                result["pitcher"] = value
            elif key == "doubles":
                result["doubles"] = _parse_name_list(value)
            elif key == "triples":
                result["triples"] = _parse_name_list(value)
            elif key == "homeruns":
                result["homeruns"] = _parse_name_list(value)
            elif key == "is_sayonara":
                result["is_sayonara"] = value.lower() in ("true", "yes", "1")

    return result


def parse_score_csv(csv_path: str) -> dict:
    """
    スコアCSVファイルを読み込んで得点情報を返す。
    CSVの行順をそのまま維持する（1行目→上段、2行目→下段）。

    CSVフォーマット:
        チーム名,1,2,3,4,5,6,7,8,9,合計
        自チーム名,2,0,4,1,1,0,2,1,2,13
        相手チーム名,3,0,2,0,0,2,0,0,1,8

    Returns:
        {
            "our_innings": [2, 0, 4, 1, 1, 0, 2, 1, 2],  # CSV 1行目
            "opp_innings": [3, 0, 2, 0, 0, 2, 0, 0, 1],  # CSV 2行目
            "our_total": 13,
            "opp_total": 8,
            "our_team": "自チーム名",  # CSV 1行目のチーム名
            "opp_team": "相手チーム名",  # CSV 2行目のチーム名
        }
    """
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header row
        for row in reader:
            if row:
                rows.append(row)

    if len(rows) < 2:
        raise ValueError(f"スコアCSVには2行のデータが必要です: {csv_path}")

    # CSVの行順をそのまま使用する（チーム名による並べ替えはしない）
    our_row = rows[0]
    opp_row = rows[1]

    def parse_innings(row):
        # row[0]=チーム名, row[1..9]=各回, row[-1]=合計
        innings = []
        for i in range(1, 10):
            if i < len(row):
                val = row[i].strip()
                if val.isdigit():
                    innings.append(int(val))
                elif val:  # "X" など非数値・非空の場合はそのまま保持
                    innings.append(val)
                else:
                    innings.append(0)
            else:
                innings.append(0)
        total_val = row[-1].strip() if len(row) > 1 else "0"
        if total_val.lstrip("-").isdigit():
            total = int(total_val)
        elif total_val:  # "6X" "7X" など非数値の場合はそのまま保持
            total = total_val
        else:
            total = 0
        return innings, total

    our_innings, our_total = parse_innings(our_row)
    opp_innings, opp_total = parse_innings(opp_row)

    return {
        "our_innings": our_innings,
        "opp_innings": opp_innings,
        "our_total": our_total,
        "opp_total": opp_total,
        "our_team": our_row[0].strip(),
        "opp_team": opp_row[0].strip(),
    }


def format_date_ja(date_str: str) -> str:
    """
    "2026-07-21" → "2026年7月21日（月）" 形式に変換する。
    """
    dt = datetime.date.fromisoformat(date_str)
    weekday = WEEKDAY_JA[dt.weekday()]
    return f"{dt.year}年{dt.month}月{dt.day}日（{weekday}）"


def _parse_name_list(value: str) -> list:
    """
    "選手A、選手B、選手C" や "選手A,選手B,選手C" をリストに変換する。
    空文字列の場合は空リストを返す。
    """
    if not value:
        return []
    # 全角読点・半角カンマの両方に対応
    value = value.replace("、", ",").replace("　", " ")
    return [name.strip() for name in value.split(",") if name.strip()]
