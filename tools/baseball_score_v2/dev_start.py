"""
開発環境の一括起動スクリプト

実行順序:
  1. DB初期化    — docker compose down -v → up db (--wait)
  2. run_all     — validate → generate → import_db
  3. バックエンド — docker compose up backend (--wait)
  4. フロントエンド — npm run dev (フォアグラウンド)

使い方:
    python dev_start.py
    python dev_start.py --skip-init-db   # DB初期化をスキップ（既存データを保持）
    python dev_start.py --skip-run-all   # run_all をスキップ
"""

import argparse
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_DIR = os.path.join(BASE_DIR, "docker")
FRONTEND_DIR = os.path.join(BASE_DIR, "webapp", "frontend")


def load_dotenv(path: str) -> None:
    """docker/.env を読み込み os.environ にセットする（既存の環境変数は上書きしない）"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

SEPARATOR = "=" * 52


def run_step(label: str, cmd: list, cwd: str | None = None, env: dict | None = None) -> bool:
    print(f"\n{SEPARATOR}")
    print(f"  {label}")
    print(SEPARATOR)
    result = subprocess.run(cmd, cwd=cwd or BASE_DIR, env=env)
    if result.returncode == 0:
        print(f"\n[OK] {label}")
        return True
    else:
        print(f"\n[NG] {label}  (終了コード: {result.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="開発環境を一括起動します（DB初期化 → run_all → backend → frontend）"
    )
    parser.add_argument(
        "--skip-init-db",
        action="store_true",
        help="DB初期化をスキップする（既存データを保持したまま起動）",
    )
    parser.add_argument(
        "--skip-run-all",
        action="store_true",
        help="run_all（validate / generate / import_db）をスキップする",
    )
    args = parser.parse_args()

    python = sys.executable

    # docker/.env をローカル実行用に読み込む（CLI ツールが環境変数を必要とするため）
    dotenv_path = os.path.join(DOCKER_DIR, ".env")
    load_dotenv(dotenv_path)
    # run_all はホストから Docker DB に接続するため localhost:5433 に上書き
    # （docker-compose.yml のポートマッピング: 127.0.0.1:5433:5432）
    # ※ os.environ を直接変更すると docker compose にも引き継がれるため、
    #   run_all 専用の env dict を作成して subprocess にのみ渡す
    run_all_env = {**os.environ, "DB_HOST": "localhost", "DB_PORT": "5433"}

    print(SEPARATOR)
    print("  野球スコア 開発環境 一括起動")
    print(SEPARATOR)

    # STEP 1: DB 初期化
    if not args.skip_init_db:
        if not run_step(
            "STEP 1a: DB停止・データ削除 — docker compose down -v",
            ["docker", "compose", "down", "-v"],
            cwd=DOCKER_DIR,
        ):
            sys.exit(1)
        if not run_step(
            "STEP 1b: DB起動 — docker compose up db (--wait)",
            ["docker", "compose", "up", "-d", "--wait", "db"],
            cwd=DOCKER_DIR,
        ):
            sys.exit(1)
    else:
        print("\n  ※ --skip-init-db が指定されたため DB 初期化はスキップします")
        if not run_step(
            "STEP 1: DB起動確認 — docker compose up db (--wait)",
            ["docker", "compose", "up", "-d", "--wait", "db"],
            cwd=DOCKER_DIR,
        ):
            sys.exit(1)

    # STEP 2: run_all
    if not args.skip_run_all:
        if not run_step(
            "STEP 2: run_all — validate → generate → import_db",
            [python, "run_all.py", "--skip-analytics"],
            cwd=BASE_DIR,
            env=run_all_env,
        ):
            sys.exit(1)
    else:
        print("\n  ※ --skip-run-all が指定されたため run_all はスキップします")

    # STEP 3: バックエンド起動（Docker）— --build でイメージを常に再ビルド
    if not run_step(
        "STEP 3: バックエンド起動 — docker compose up backend (--build, --wait)",
        ["docker", "compose", "up", "-d", "--build", "--wait", "backend"],
        cwd=DOCKER_DIR,
    ):
        sys.exit(1)

    # STEP 4: フロントエンド起動（フォアグラウンド）
    print(f"\n{SEPARATOR}")
    print("  STEP 4: フロントエンド起動 — npm run dev")
    print("  http://localhost:5173 で確認できます")
    print("  終了するには Ctrl+C を押してください")
    print(SEPARATOR + "\n")
    subprocess.run(["npm", "run", "dev"], cwd=FRONTEND_DIR)


if __name__ == "__main__":
    main()
