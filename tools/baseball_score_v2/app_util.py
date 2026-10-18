import json
import logging
import logging.config
import os
import subprocess


def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    config_path = os.path.join(os.path.dirname(__file__), "config", "logging.conf")
    logging.config.fileConfig(config_path, disable_existing_loggers=False)


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# チーム単位のデータシート名の既定値（config.json の team_data_sheet_name で上書きする）
DEFAULT_TEAM_DATA_SHEET_NAME = "チーム単位のデータ"


def get_team_data_sheet_name(config: dict) -> str:
    """config.json からチーム単位のデータシート名を取得する。未設定なら既定値。"""
    return config.get("team_data_sheet_name", DEFAULT_TEAM_DATA_SHEET_NAME)


def get_our_team_name(config: dict) -> str:
    """自チーム名を取得する。

    config.json の our_team_name を優先し、未設定なら環境変数 TEAM_NAME を使う。
    どちらも未設定の場合は ValueError。
    """
    name = config.get("our_team_name") or os.environ.get("TEAM_NAME")
    if not name:
        raise ValueError(
            "自チーム名が未設定です。config.json の 'our_team_name' "
            "または環境変数 TEAM_NAME を設定してください。"
        )
    return name


def setup_docker_and_db():
    """Docker Compose で db コンテナを起動する。

    既に起動済みの場合は何もしない（データは削除しない）。
    db サービスのみを起動し、healthcheck が通るまで待機する
    （--wait オプション、Docker Compose v2.1+）。
    バックエンドコンテナは `docker compose up -d` で別途起動すること。
    """
    logger = logging.getLogger("app.main")
    docker_dir = os.path.join(os.path.dirname(__file__), "docker")
    docker_dir = os.path.abspath(docker_dir)

    logger.info("Docker Compose 起動確認中...")

    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--wait", "db"],
            cwd=docker_dir,
            check=True,
            capture_output=True
        )
        logger.info("Docker Compose 起動完了（db）")

    except subprocess.CalledProcessError as e:
        logger.error(f"Docker Compose 起動エラー: {e}")
        raise
    except Exception as e:
        logger.error(f"予期しない Docker Compose エラー: {e}")
        raise
