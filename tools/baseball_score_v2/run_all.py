"""
試合後ワークフロー統合コマンド

validate → generate → import_db → analytics を順次実行します。

使い方:
    python run_all.py [--year 2026] [--skip-validate] [--skip-analytics]
"""
import argparse
import datetime
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.run_logger import log_run

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEPARATOR = "=" * 52


def run_step(
    label: str,
    cmd: list,
    *,
    run_id: str,
    step: str,
    year: int | None = None,
    warn_on_fail: bool = False,
) -> bool:
    """ステップを実行し、成否を返す。

    warn_on_fail=True の場合、失敗しても [WARN] を表示して True を返す（処理続行）。
    """
    print(f"\n{SEPARATOR}")
    print(f"  {label}")
    print(SEPARATOR)
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode == 0:
        print(f"\n[OK] {label}")
        log_run(run_id=run_id, step=step, label=label, status="OK",
                year=year, returncode=result.returncode)
        return True
    elif warn_on_fail:
        print(f"\n[WARN] {label}  (終了コード: {result.returncode}) — 警告のみ、処理を続行します")
        log_run(run_id=run_id, step=step, label=label, status="WARN",
                year=year, returncode=result.returncode)
        return True
    else:
        print(f"\n[NG] {label}  (終了コード: {result.returncode})")
        log_run(run_id=run_id, step=step, label=label, status="NG",
                year=year, returncode=result.returncode)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="試合後ワークフローを一括実行します（generate → import_db → analytics）"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.date.today().year,
        help="analytics の対象年度（デフォルト: 当年）",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="validate ステップをスキップする",
    )
    parser.add_argument(
        "--skip-analytics",
        action="store_true",
        help="analytics ステップをスキップする",
    )
    args = parser.parse_args()

    python = sys.executable
    now = datetime.datetime.now()
    run_id = f"run_{now.strftime('%Y%m%d_%H%M%S')}"

    # (label, cmd, step_name)
    steps = []
    if not args.skip_validate:
        steps.append((
            "STEP 1: validate    — データ入力バリデーション",
            [python, "validate.py"],
            "validate",
            True,   # warn_on_fail: 失敗しても WARNING で続行
        ))
    else:
        print("  ※ --skip-validate が指定されたため validate はスキップします")
        log_run(run_id=run_id, step="validate",
                label="STEP 1: validate    — データ入力バリデーション",
                status="SKIP", year=args.year)

    steps += [
        (
            "STEP 2: generate    — 集計表示・試合入力ファイル生成",
            [python, "generate.py"],
            "generate",
            False,
        ),
        (
            "STEP 3: import_db   — DB登録",
            [python, "import_db.py"],
            "import_db",
            False,
        ),
    ]
    if not args.skip_analytics:
        steps.append((
            f"STEP 4: analytics   — 分析Excel出力 (year={args.year})",
            [python, "analytics.py", "--year", str(args.year)],
            "analytics",
            False,
        ))
    else:
        print("  ※ --skip-analytics が指定されたため analytics はスキップします")
        log_run(run_id=run_id, step="analytics",
                label="STEP 4: analytics   — 分析Excel出力",
                status="SKIP", year=args.year)

    print(SEPARATOR)
    print("  野球スコア ワークフロー一括実行")
    print(SEPARATOR)

    for label, cmd, step_name, warn_on_fail in steps:
        ok = run_step(label, cmd, run_id=run_id, step=step_name, year=args.year,
                      warn_on_fail=warn_on_fail)
        if not ok:
            print(f"\n処理を中断しました: {label}")
            print("詳細は logs/app.log を確認してください。")
            sys.exit(1)

    print(f"\n{SEPARATOR}")
    print("  全ステップが正常に完了しました")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
