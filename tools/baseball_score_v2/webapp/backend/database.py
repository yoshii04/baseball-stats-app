"""DB接続ヘルパー: 既存の config.config から DB 設定を取得する"""
import os
import sys
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor

# baseball_score_v2/ をパスに追加して既存の config モジュールを再利用
_APP_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from config.config import DB_CONFIG, TEAM_NAME  # noqa: E402


@contextmanager
def get_cursor():
    """DB接続を確立し DictCursor を yield する。終了時に必ずクローズする。"""
    conn = psycopg2.connect(
        **DB_CONFIG,
        connect_timeout=20,
        sslmode=os.environ.get("DB_SSLMODE", "disable"),
    )
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            yield cur
    finally:
        conn.close()
