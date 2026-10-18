"""投手関連エンドポイント"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from database import TEAM_NAME, get_cursor

router = APIRouter(dependencies=[Depends(verify_token)])

# ---------- 投手一覧（年度別シーズン集計） ----------

_PITCHER_STATS_SQL_BASE = """
    SELECT
        p.player_id,
        p.player_name,
        COUNT(DISTINCT ps.game_id)                                      AS game_count,
        COALESCE(SUM(ps.batters_faced), 0)                             AS batters_faced,
        COALESCE(SUM(ps.pitch_count), 0)                               AS pitch_count,
        COALESCE(SUM(ps.hits_allowed), 0)                              AS hits_allowed,
        COALESCE(SUM(ps.homerun_allowed), 0)                           AS homerun_allowed,
        COALESCE(SUM(ps.walks_allowed), 0)                             AS walks_allowed,
        COALESCE(SUM(ps.strikeouts), 0)                                AS strikeouts,
        COALESCE(SUM(ps.runs_allowed), 0)                              AS runs_allowed,
        COALESCE(SUM(ps.earned_runs), 0)                               AS earned_runs,
        COALESCE(SUM(ps.innings_pitched), 0) * 3
            + COALESCE(SUM(ps.outs), 0)                                AS total_outs
    FROM pitcher_stats ps
    JOIN players p ON ps.pitcher_id = p.player_id
    JOIN teams t   ON p.team_id     = t.team_id
    JOIN games g   ON ps.game_id    = g.game_id
    WHERE t.team_name = %s
"""

_TEAM_GAMES_SQL_BASE = """
    SELECT COUNT(DISTINCT g.game_id) AS total_games
    FROM games g
    JOIN teams t ON g.home_team_id = t.team_id
    WHERE t.team_name = %s
"""


def _build_pitcher_row(row: dict, total_outs_key: bool = True) -> dict:
    """共通の投手成績計算（IP・ERA・WHIP）を付与する"""
    r = dict(row)
    total_outs = r.get("total_outs", 0) or 0
    r["ip"] = f"{total_outs // 3}.{total_outs % 3}"
    er = r.get("earned_runs", 0) or 0
    r["era"] = round(er * 27 / total_outs, 2) if total_outs > 0 else None
    bf = r.get("batters_faced", 0) or 0
    h = r.get("hits_allowed", 0) or 0
    w = r.get("walks_allowed", 0) or 0
    r["whip"] = round((h + w) / bf * 3, 2) if bf > 0 else None
    return r


@router.get("")
def list_pitchers(year: Optional[int] = None):
    """投手一覧（シーズン集計成績付き・防御率順・規定投球回判定付き）"""
    games_query = _TEAM_GAMES_SQL_BASE
    games_params: list = [TEAM_NAME]
    if year is not None:
        games_query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        games_params.append(year)

    pitchers_query = _PITCHER_STATS_SQL_BASE
    pitchers_params: list = [TEAM_NAME]
    if year is not None:
        pitchers_query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        pitchers_params.append(year)
    pitchers_query += " GROUP BY p.player_id, p.player_name"

    with get_cursor() as cur:
        cur.execute(games_query, games_params)
        team_row = cur.fetchone()
        total_games = team_row["total_games"] if team_row else 0
        qualifying_outs = total_games * 3  # 試合数×1イニング = 試合数×3アウト

        cur.execute(pitchers_query, pitchers_params)
        rows = cur.fetchall()

    result = []
    for row in rows:
        r = _build_pitcher_row(dict(row))
        r["qualified"] = (r.get("total_outs", 0) or 0) >= qualifying_outs
        result.append(r)

    # 防御率昇順（ERA が None の投手は末尾）
    result.sort(key=lambda x: (x["era"] is None, x["era"] or 0))

    return {
        "total_games": total_games,
        "qualifying_innings": total_games,
        "pitchers": result,
    }


# ---------- 投手別 試合ごとの成績一覧 ----------

@router.get("/{pitcher_id}/stats")
def get_pitcher_stats(pitcher_id: int, year: Optional[int] = None):
    """投手の試合別成績一覧"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT player_id FROM players WHERE player_id = %s",
            (pitcher_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="投手が見つかりません")

        query = """
            SELECT
                g.game_id,
                g.game_date,
                t_opp.team_name                         AS opponent,
                g.game_number,
                COALESCE(ps.batters_faced, 0)           AS batters_faced,
                COALESCE(ps.pitch_count, 0)             AS pitch_count,
                COALESCE(ps.hits_allowed, 0)            AS hits_allowed,
                COALESCE(ps.homerun_allowed, 0)         AS homerun_allowed,
                COALESCE(ps.walks_allowed, 0)           AS walks_allowed,
                COALESCE(ps.strikeouts, 0)              AS strikeouts,
                COALESCE(ps.runs_allowed, 0)            AS runs_allowed,
                COALESCE(ps.earned_runs, 0)             AS earned_runs,
                COALESCE(ps.innings_pitched, 0)         AS innings_pitched,
                COALESCE(ps.outs, 0)                    AS outs
            FROM pitcher_stats ps
            JOIN games g      ON ps.game_id        = g.game_id
            JOIN teams t_opp  ON g.away_team_id    = t_opp.team_id
            WHERE ps.pitcher_id = %s
        """
        params: list = [pitcher_id]
        if year is not None:
            query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
            params.append(year)
        query += " ORDER BY g.game_date, g.game_number"

        cur.execute(query, params)
        rows = cur.fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["game_date"] = str(r["game_date"])
        ip_full = r.pop("innings_pitched")
        ip_outs = r.pop("outs")
        total_outs = ip_full * 3 + ip_outs
        r["total_outs"] = total_outs
        r = _build_pitcher_row(r)
        result.append(r)

    return result
