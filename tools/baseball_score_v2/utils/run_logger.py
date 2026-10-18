"""
実行ログ管理モジュール

logs/run_history.jsonl に JSON Lines 形式でステップ実行履歴を記録します。

レコード形式:
    {
        "timestamp":  "2026-03-25T15:30:00.123456",
        "run_id":     "run_20260325_153000",
        "step":       "import_db",
        "label":      "STEP 3: import_db — DB登録",
        "status":     "OK",        # "OK" | "NG" | "SKIP"
        "year":       2026,        # analytics の対象年度（任意）
        "returncode": 0,           # サブプロセスの終了コード（任意）
        "error":      null         # エラーメッセージ（任意）
    }
"""
import json
import os
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_FILE = os.path.join(_BASE_DIR, "logs", "run_history.jsonl")


def _ensure_log_dir():
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)


def log_run(
    *,
    run_id: str,
    step: str,
    label: str,
    status: str,
    year: int | None = None,
    returncode: int | None = None,
    error: str | None = None,
) -> None:
    """実行結果を run_history.jsonl に1行追記する。"""
    _ensure_log_dir()
    record = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,
        "step": step,
        "label": label,
        "status": status,
        "year": year,
        "returncode": returncode,
        "error": error,
    }
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_logs(
    *,
    date: str | None = None,
    step: str | None = None,
    last: int | None = None,
) -> list[dict]:
    """
    run_history.jsonl を読み込み、フィルタリングしたレコードリストを返す。

    Args:
        date: "YYYY-MM-DD" 形式で絞り込む（timestamp の日付部分と比較）
        step: ステップ名で絞り込む（validate / generate / import_db / analytics）
        last: 最新 N 件のみ返す
    """
    if not os.path.exists(_LOG_FILE):
        return []

    records = []
    with open(_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if date:
        records = [r for r in records if r.get("timestamp", "").startswith(date)]

    if step:
        records = [r for r in records if r.get("step") == step]

    if last is not None:
        records = records[-last:]

    return records
