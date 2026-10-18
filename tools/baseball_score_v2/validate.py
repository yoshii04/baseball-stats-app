"""
データ入力バリデーション

ExcelデータをDB登録前に検証し、入力ミスを事前に検出します。

使い方:
    python validate.py              # WARNING / ERROR を表示（ERROR があれば終了コード 1）
    python validate.py --strict     # WARNING も ERROR として扱う
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime

from app_util import get_team_data_sheet_name, load_config, setup_logging
from model.batting_record import BattingRecord
from repository.batting_repository import BattingRepository
from repository.pitcher_repository import PitcherRepository
from repository.team_pitcher_repository import TeamPitcherRepository

SEPARATOR = "=" * 52


@dataclass
class Issue:
    level: str  # "ERROR" or "WARNING"
    check: str
    message: str


def _batting_key(r: BattingRecord) -> str:
    return f"date={r.date}, 対戦={r.opponent}, game={r.game_number}, 選手={r.player}"


# ---------------------------------------------------------------------------
# チェック関数
# ---------------------------------------------------------------------------

def check_batting_stats(records: list[BattingRecord]) -> list[Issue]:
    """打撃内訳の整合性チェック（ERROR）"""
    issues = []
    for r in records:
        key = _batting_key(r)
        extra_bases = r.double + r.triple + r.homerun
        if extra_bases > r.hit_count:
            issues.append(Issue(
                "ERROR", "打撃内訳",
                f"{key} — 長打計({extra_bases}) > 安打({r.hit_count})"
            ))
        if r.hit_count > r.at_bat_count:
            issues.append(Issue(
                "ERROR", "打撃内訳",
                f"{key} — 安打({r.hit_count}) > 打数({r.at_bat_count})"
            ))
        if r.strike_out > r.at_bat_count:
            issues.append(Issue(
                "ERROR", "打撃内訳",
                f"{key} — 三振({r.strike_out}) > 打数({r.at_bat_count})"
            ))
        if r.on_base_opportunity > 0 and r.on_base > r.on_base_opportunity:
            issues.append(Issue(
                "ERROR", "打撃内訳",
                f"{key} — 出塁({r.on_base}) > 出塁機会({r.on_base_opportunity})"
            ))
    return issues



def check_date_format(records: list[BattingRecord]) -> list[Issue]:
    """日付フォーマット異常チェック（WARNING）"""
    issues = []
    bad_dates: set[str] = set()
    for r in records:
        if r.date in bad_dates:
            continue
        valid = False
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
            try:
                datetime.strptime(r.date, fmt)
                valid = True
                break
            except ValueError:
                continue
        if not valid:
            bad_dates.add(r.date)
            issues.append(Issue(
                "WARNING", "日付フォーマット",
                f"日付 '{r.date}' を解析できません"
            ))
    return issues


def check_opponent_name_variants(records: list[BattingRecord]) -> list[Issue]:
    """対戦相手名の揺れチェック（WARNING）

    スペース・全角スペース・全角英数字を正規化して同一視できる名前を検出します。
    """
    issues = []
    # 正規化: 前後スペース除去 + 連続スペースを1つに
    def normalize(name: str) -> str:
        s = name.strip()
        s = re.sub(r"[\s\u3000]+", " ", s)  # 全角スペースも含めて1スペースに
        return s

    variant_map: dict[str, set[str]] = {}
    for r in records:
        norm = normalize(r.opponent)
        if norm not in variant_map:
            variant_map[norm] = set()
        variant_map[norm].add(r.opponent)

    for norm, variants in variant_map.items():
        if len(variants) > 1:
            variants_str = ", ".join(f"'{v}'" for v in sorted(variants))
            issues.append(Issue(
                "WARNING", "対戦相手名の揺れ",
                f"正規化後 '{norm}' に複数の表記: {variants_str}"
            ))
    return issues


def check_pitcher_in_team_data(
    pitcher_records,
    team_pitcher_records,
) -> list[Issue]:
    """投手名がチーム単位シートに存在するかチェック（WARNING）"""
    issues = []
    team_pitcher_names = {r.pitcher_name for r in team_pitcher_records}
    unknown: set[str] = set()
    for r in pitcher_records:
        if r.pitcher_name not in team_pitcher_names and r.pitcher_name not in unknown:
            unknown.add(r.pitcher_name)
            issues.append(Issue(
                "WARNING", "投手名チェック",
                f"投手 '{r.pitcher_name}' がチーム単位シートに存在しません"
            ))
    return issues


# ---------------------------------------------------------------------------
# 表示・集計
# ---------------------------------------------------------------------------

def _print_issues(issues: list[Issue]) -> None:
    for issue in issues:
        prefix = f"[{issue.level}]"
        print(f"  {prefix:<10} [{issue.check}] {issue.message}")


def run_validation(strict: bool = False) -> int:
    """バリデーションを実行し、終了コードを返す（0=OK, 1=NG）"""
    setup_logging()
    config = load_config()

    excel_file = config["excel_file"]
    sheet_name = config["sheet_name"]
    pitcher_sheet = config.get("pitcher_sheet_name", "データ入力シート(相手攻撃)")
    team_sheet = get_team_data_sheet_name(config)

    print(SEPARATOR)
    print("  データ入力バリデーション")
    print(SEPARATOR)
    print(f"  Excel  : {excel_file}")
    print(f"  打撃シート: {sheet_name}")
    print(f"  投手シート: {pitcher_sheet}")
    print(f"  チームシート: {team_sheet}")
    print()

    # --- データ読み込み ---
    batting_repo = BattingRepository()
    batting_records = batting_repo.load_records(excel_file, sheet_name)
    print(f"  打撃レコード: {len(batting_records)} 件")

    pitcher_repo = PitcherRepository()
    pitcher_records = pitcher_repo.load_records(excel_file, pitcher_sheet)
    print(f"  投手レコード: {len(pitcher_records)} 件")

    team_pitcher_repo = TeamPitcherRepository()
    team_pitcher_records = team_pitcher_repo.load_records(excel_file, team_sheet)
    print(f"  チーム投手レコード: {len(team_pitcher_records)} 件")
    print()

    # --- チェック実行 ---
    all_issues: list[Issue] = []
    all_issues += check_batting_stats(batting_records)
    all_issues += check_date_format(batting_records)
    all_issues += check_opponent_name_variants(batting_records)
    all_issues += check_pitcher_in_team_data(pitcher_records, team_pitcher_records)

    if strict:
        for issue in all_issues:
            issue.level = "ERROR"

    errors = [i for i in all_issues if i.level == "ERROR"]
    warnings = [i for i in all_issues if i.level == "WARNING"]

    # --- 結果表示 ---
    if errors:
        print(f"  [ERROR] {len(errors)} 件")
        _print_issues(errors)
        print()
    if warnings:
        print(f"  [WARNING] {len(warnings)} 件")
        _print_issues(warnings)
        print()

    if not all_issues:
        print("  問題は検出されませんでした。")
        print()

    print(SEPARATOR)
    if errors:
        print(f"  バリデーション失敗: ERROR {len(errors)} 件, WARNING {len(warnings)} 件")
        print(SEPARATOR)
        return 1
    elif warnings:
        print(f"  バリデーション完了（WARNING {len(warnings)} 件）")
        print(SEPARATOR)
        return 0
    else:
        print("  バリデーション完了（問題なし）")
        print(SEPARATOR)
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Excelデータを検証してDB登録前の入力ミスを検出します"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="WARNING も ERROR として扱い、終了コード 1 を返す",
    )
    args = parser.parse_args()

    try:
        exit_code = run_validation(strict=args.strict)
    except FileNotFoundError as e:
        print(f"[ERROR] 設定ファイルが見つかりません: {e}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] 設定ファイルの形式が不正です: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 予期しないエラーが発生しました: {e}")
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
