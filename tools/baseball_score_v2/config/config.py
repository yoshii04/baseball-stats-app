# config/config.py
import os

DB_CONFIG = {
    "host":     os.environ["DB_HOST"],
    "port":     int(os.environ.get("DB_PORT", "5432")),
    "user":     os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "dbname":   os.environ["DB_NAME"],
}

TEAM_NAME = os.environ.get("TEAM_NAME", "Default Team")
