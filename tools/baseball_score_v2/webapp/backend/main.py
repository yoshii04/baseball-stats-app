"""野球成績 WebAPI - FastAPI エントリーポイント

起動方法:
    cd tools/baseball_score_v2/webapp/backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

API ドキュメント:
    http://localhost:8000/docs
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from database import TEAM_NAME, get_cursor
from routers import analytics, games, history, pitchers, players, stats

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

_env = os.environ.get("ENV", "development")

app = FastAPI(
    title="野球成績 API",
    description=f"{TEAM_NAME} 野球部 成績管理 REST API",
    version="1.0.0",
    docs_url=None if _env == "production" else "/docs",
    redoc_url=None if _env == "production" else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
_allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(players.router,   prefix="/api/players",   tags=["選手"])
app.include_router(games.router,     prefix="/api/games",     tags=["試合"])
app.include_router(stats.router,     prefix="/api/stats",     tags=["成績"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["分析"])
app.include_router(pitchers.router,  prefix="/api/pitchers",  tags=["投手"])
app.include_router(history.router,   prefix="/api/history",   tags=["実行履歴"])


@app.get("/", tags=["ヘルスチェック"])
def root():
    return {"status": "ok", "message": "野球成績 API が起動しています"}


@app.get("/health", tags=["ヘルスチェック"])
def health():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "unreachable"},
        )
