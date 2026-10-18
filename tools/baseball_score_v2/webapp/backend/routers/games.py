"""試合関連エンドポイント"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from database import TEAM_NAME, get_cursor

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("")
def list_games(year: Optional[int] = None, month: Optional[int] = None):
    """試合一覧（年度・月フィルタ対応）"""
    query = """
        SELECT
            g.game_id,
            g.game_date,
            g.game_number,
            t_home.team_name  AS home_team,
            t_away.team_name  AS away_team,
            g.home_score,
            g.away_score,
            g.result
        FROM games g
        JOIN teams t_home ON g.home_team_id = t_home.team_id
        JOIN teams t_away ON g.away_team_id = t_away.team_id
        WHERE 1=1
    """
    params: list = []
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    if month is not None:
        query += " AND EXTRACT(MONTH FROM g.game_date) = %s"
        params.append(month)
    query += " ORDER BY g.game_date, g.game_number"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {**dict(row), "game_date": str(row["game_date"])}
        for row in rows
    ]


@router.get("/{game_id}")
def get_game(game_id: int):
    """試合詳細（出場選手の打撃成績付き）"""
    with get_cursor() as cur:
        # 試合基本情報
        cur.execute(
            """
            SELECT
                g.game_id,
                g.game_date,
                g.game_number,
                t_home.team_name  AS home_team,
                t_away.team_name  AS away_team,
                g.home_score,
                g.away_score,
                g.result
            FROM games g
            JOIN teams t_home ON g.home_team_id = t_home.team_id
            JOIN teams t_away ON g.away_team_id = t_away.team_id
            WHERE g.game_id = %s
            """,
            (game_id,),
        )
        game_row = cur.fetchone()
        if not game_row:
            raise HTTPException(status_code=404, detail="試合が見つかりません")

        # 選手別打撃成績
        cur.execute(
            """
            SELECT
                p.player_id,
                p.player_name,
                COALESCE(bs.at_bat_count, 0)                                AS at_bat_count,
                COALESCE(bs.hit_count, 0)                                   AS hit_count,
                COALESCE(bs.double_hit, 0)                                  AS double_hit,
                COALESCE(bs.triple, 0)                                      AS triple,
                COALESCE(bs.homerun, 0)                                     AS homerun,
                COALESCE(bs.rbi, 0)                                         AS rbi,
                COALESCE(bs.walk_count, 0)                                  AS walk_count,
                COALESCE(bs.strike_out, 0)                                  AS strike_out,
                COALESCE(bs.stolen_base, 0)                                 AS stolen_base,
                CASE
                    WHEN COALESCE(bs.at_bat_count, 0) > 0
                    THEN ROUND(bs.hit_count::numeric / bs.at_bat_count, 3)::float
                    ELSE NULL
                END                                                         AS batting_avg
            FROM batting_stats bs
            JOIN players p ON bs.player_id = p.player_id
            JOIN teams t   ON p.team_id    = t.team_id
            WHERE bs.game_id = %s
              AND t.team_name = %s
            ORDER BY p.player_name
            """,
            (game_id, TEAM_NAME),
        )
        players = [dict(row) for row in cur.fetchall()]

    result = dict(game_row)
    result["game_date"] = str(result["game_date"])
    result["players"] = players
    return result
