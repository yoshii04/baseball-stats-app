"""選手関連エンドポイント"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from database import TEAM_NAME, get_cursor

router = APIRouter(dependencies=[Depends(verify_token)])

# ---------- 選手一覧（年度別シーズン成績付き） ----------

_PLAYER_STATS_SQL_BASE = """
    SELECT
        p.player_id,
        p.player_name,
        COUNT(DISTINCT bs.game_id)                                          AS game_count,
        COALESCE(SUM(bs.at_bat_count), 0)                                   AS at_bat_count,
        COALESCE(SUM(bs.hit_count), 0)                                      AS hit_count,
        GREATEST(
            COALESCE(SUM(bs.hit_count), 0)
            - COALESCE(SUM(bs.double_hit), 0)
            - COALESCE(SUM(bs.triple), 0)
            - COALESCE(SUM(bs.homerun), 0), 0
        )                                                                   AS single,
        COALESCE(SUM(bs.double_hit), 0)                                     AS double_hit,
        COALESCE(SUM(bs.triple), 0)                                         AS triple,
        COALESCE(SUM(bs.homerun), 0)                                        AS homerun,
        COALESCE(SUM(bs.rbi), 0)                                            AS rbi,
        COALESCE(SUM(bs.walk_count), 0)                                     AS walk_count,
        COALESCE(SUM(bs.strike_out), 0)                                     AS strike_out,
        COALESCE(SUM(bs.stolen_base), 0)                                    AS stolen_base,
        COALESCE(SUM(bs.on_base_opportunity), 0)                            AS plate_appearance,
        ROUND(
            COALESCE(SUM(bs.hit_count), 0)::numeric
            / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0), 3
        )::float                                                            AS batting_avg,
        ROUND(
            COALESCE(SUM(bs.on_base), 0)::numeric
            / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0), 3
        )::float                                                            AS on_base_pct,
        ROUND(
            (COALESCE(SUM(bs.hit_count), 0)
             + COALESCE(SUM(bs.double_hit), 0)
             + 2 * COALESCE(SUM(bs.triple), 0)
             + 3 * COALESCE(SUM(bs.homerun), 0))::numeric
            / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0), 3
        )::float                                                            AS slg,
        ROUND(
            COALESCE(SUM(bs.on_base), 0)::numeric
            / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0)
            + (COALESCE(SUM(bs.hit_count), 0)
               + COALESCE(SUM(bs.double_hit), 0)
               + 2 * COALESCE(SUM(bs.triple), 0)
               + 3 * COALESCE(SUM(bs.homerun), 0))::numeric
            / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0)
        , 3)::float                                                         AS ops
    FROM batting_stats bs
    JOIN players p ON bs.player_id = p.player_id
    JOIN teams t   ON p.team_id    = t.team_id
    JOIN games g   ON bs.game_id   = g.game_id
    WHERE t.team_name = %s
"""


@router.get("")
def list_players(year: Optional[int] = None):
    """選手一覧（シーズン集計成績付き）"""
    query = _PLAYER_STATS_SQL_BASE
    params: list = [TEAM_NAME]
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    query += " GROUP BY p.player_id, p.player_name ORDER BY ops DESC NULLS LAST"
    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


# ---------- 選手詳細 ----------

@router.get("/{player_id}")
def get_player(player_id: int):
    """選手基本情報"""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.player_id, p.player_name, t.team_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            WHERE p.player_id = %s
            """,
            (player_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="選手が見つかりません")
    return dict(row)


# ---------- 選手別試合ログ（累積成績付き） ----------

@router.get("/{player_id}/stats")
def get_player_stats(player_id: int, year: Optional[int] = None):
    """選手の試合別成績と累積打率・OPS"""
    query = """
        SELECT
            g.game_id,
            g.game_date,
            t_opp.team_name                             AS opponent,
            g.game_number,
            COALESCE(bs.at_bat_count, 0)                AS at_bat_count,
            COALESCE(bs.hit_count, 0)                   AS hit_count,
            COALESCE(bs.double_hit, 0)                  AS double_hit,
            COALESCE(bs.triple, 0)                      AS triple,
            COALESCE(bs.homerun, 0)                     AS homerun,
            COALESCE(bs.rbi, 0)                         AS rbi,
            COALESCE(bs.walk_count, 0)                  AS walk_count,
            COALESCE(bs.strike_out, 0)                  AS strike_out,
            COALESCE(bs.stolen_base, 0)                 AS stolen_base,
            COALESCE(bs.on_base_opportunity, 0)         AS on_base_opportunity,
            COALESCE(bs.on_base, 0)                     AS on_base
        FROM batting_stats bs
        JOIN games g      ON bs.game_id        = g.game_id
        JOIN teams t_opp  ON g.away_team_id    = t_opp.team_id
        WHERE bs.player_id = %s
    """
    params: list = [player_id]
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    query += " ORDER BY g.game_date, g.game_number"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    cum_ab = cum_hits = cum_on_base = cum_opp = cum_bases = 0
    result = []
    for row in rows:
        r = dict(row)
        r["game_date"] = str(r["game_date"])

        cum_ab    += r["at_bat_count"]
        cum_hits  += r["hit_count"]
        cum_on_base += r["on_base"]
        cum_opp   += r["on_base_opportunity"]
        cum_bases += (
            r["hit_count"]
            + r["double_hit"]
            + 2 * r["triple"]
            + 3 * r["homerun"]
        )

        cum_avg = round(cum_hits / cum_ab, 3) if cum_ab > 0 else None
        obp     = round(cum_on_base / cum_opp, 3) if cum_opp > 0 else None
        slg     = round(cum_bases / cum_ab, 3) if cum_ab > 0 else None
        r["cum_avg"] = cum_avg
        r["cum_ops"] = round(obp + slg, 3) if (obp is not None and slg is not None) else None
        result.append(r)

    return result
