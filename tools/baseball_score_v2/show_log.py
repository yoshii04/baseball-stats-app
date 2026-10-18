"""
実行履歴ビューア

logs/run_history.jsonl に記録されたステップ実行履歴を表示します。

使い方:
    python show_log.py                          # 全履歴を表示
    python show_log.py --date 2026-03-25        # 指定日付のみ
    python show_log.py --step import_db         # ステップ名で絞り込み
    python show_log.py --last 20                # 最新20件
    python show_log.py --date 2026-03-25 --step generate --last 5
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.run_logger import read_logs

SEPARATOR = "=" * 70

STATUS_SYMBOL = {
    "OK":   "[OK]  ",
    "NG":   "[NG]  ",
    "SKIP": "[SKIP]",
}

STATUS_LABEL = {
    "OK":   "成功",
    "NG":   "失敗",
    "SKIP": "スキップ",
}


def format_timestamp(ts: str) -> str:
    """ISO 形式のタイムスタンプを読みやすい形式に変換する。"""
    try:
        date, time = ts[:10], ts[11:19]
        return f"{date} {time}"
    except Exception:
        return ts


def print_records(records: list[dict]) -> None:
    if not records:
        print("  (該当する履歴がありません)")
        return

    current_run_id = None
    for r in records:
        run_id = r.get("run_id", "")
        if run_id != current_run_id:
            current_run_id = run_id
            print(f"\n  実行ID: {run_id}")
            print("  " + "-" * 66)

        ts      = format_timestamp(r.get("timestamp", ""))
        step    = r.get("step", "")
        label   = r.get("label", step)
        status  = r.get("status", "")
        year    = r.get("year")
        rc      = r.get("returncode")
        error   = r.get("error")

        symbol  = STATUS_SYMBOL.get(status, f"[{status}]")
        year_str = f"  year={year}" if year is not None else ""
        rc_str   = f"  rc={rc}"     if rc   is not None else ""

        print(f"  {symbol}  {ts}  {label}{year_str}{rc_str}")

        if error:
            print(f"           エラー: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="run_all.py の実行履歴を表示します"
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="指定日付の履歴のみ表示",
    )
    parser.add_argument(
        "--step",
        choices=["validate", "generate", "import_db", "analytics"],
        help="ステップ名で絞り込み",
    )
    parser.add_argument(
        "--last",
        type=int,
        metavar="N",
        help="最新 N 件のみ表示",
    )
    args = parser.parse_args()

    records = read_logs(date=args.date, step=args.step, last=args.last)

    print(SEPARATOR)
    print("  野球スコア — 実行履歴")

    filters = []
    if args.date:
        filters.append(f"日付={args.date}")
    if args.step:
        filters.append(f"ステップ={args.step}")
    if args.last:
        filters.append(f"最新{args.last}件")
    if filters:
        print(f"  フィルター: {' / '.join(filters)}")

    print(SEPARATOR)

    print_records(records)

    print(f"\n  合計 {len(records)} 件")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
