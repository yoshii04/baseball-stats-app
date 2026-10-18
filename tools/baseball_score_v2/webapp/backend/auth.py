"""Google OAuth トークン検証モジュール"""
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

ALLOWED_EMAILS = set(
    e.strip()
    for e in os.environ.get("ALLOWED_EMAILS", "").split(",")
    if e.strip()
)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# デモモード: 認証を行わない。合成データによる画面確認（demo/docker-compose.yml）専用。
DEMO_MODE = os.environ.get("DEMO_MODE", "").strip().lower() == "true"
if DEMO_MODE and os.environ.get("ENV", "development") == "production":
    raise RuntimeError("DEMO_MODE は認証を無効にするため、ENV=production では使えません")

security = HTTPBearer(auto_error=not DEMO_MODE)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if DEMO_MODE:
        return {"email": "demo@example.com"}
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID が設定されていません")
    try:
        idinfo = id_token.verify_oauth2_token(
            credentials.credentials, grequests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        if ALLOWED_EMAILS and email not in ALLOWED_EMAILS:
            raise HTTPException(status_code=403, detail="アクセス権限がありません")
        return idinfo
    except ValueError:
        raise HTTPException(status_code=401, detail="無効なトークンです")
