"""分析データエンドポイント"""
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends

from auth import verify_token
from database import TEAM_NAME, get_cursor

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("/hit-direction")
def get_hit_direction(year: Optional[int] = None, player_id: Optional[int] = None):
    """打球方向集計（選手別・パーセンテージ付き）"""
    query = """
            SELECT
                p.player_id,
                p.player_name,
                COALESCE(SUM(bs.right_9), 0)        AS right_9,
                COALESCE(SUM(bs.right_center), 0)   AS right_center,
                COALESCE(SUM(bs.center), 0)         AS center_field,
                COALESCE(SUM(bs.left_center), 0)    AS left_center,
                COALESCE(SUM(bs.left_7), 0)         AS left_7
            FROM batting_stats bs
            JOIN players p ON bs.player_id = p.player_id
            JOIN teams t   ON p.team_id    = t.team_id
            JOIN games g   ON bs.game_id   = g.game_id
            WHERE t.team_name = %s
    """
    params: list = [TEAM_NAME]
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    if player_id is not None:
        query += " AND p.player_id = %s"
        params.append(player_id)
    query += " GROUP BY p.player_id, p.player_name ORDER BY p.player_name"
    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    result = []
    for row in rows:
        r = dict(row)
        total = (
            r["right_9"] + r["right_center"] + r["center_field"]
            + r["left_center"] + r["left_7"]
        )
        def pct(val: int) -> float:
            return round(val / total * 100, 1) if total > 0 else 0.0
        r["total"] = total
        r["pct_right_9"]      = pct(r["right_9"])
        r["pct_right_center"] = pct(r["right_center"])
        r["pct_center"]       = pct(r["center_field"])
        r["pct_left_center"]  = pct(r["left_center"])
        r["pct_left_7"]       = pct(r["left_7"])
        result.append(r)
    return result


@router.get("/batting-trend")
def get_batting_trend(year: Optional[int] = None, player_id: Optional[int] = None):
    """打率・OPS累積推移（全選手 or 特定選手）"""
    query = """
        SELECT
            p.player_id,
            p.player_name,
            g.game_date,
            t_opp.team_name                         AS opponent,
            g.game_number,
            COALESCE(bs.at_bat_count, 0)            AS at_bat_count,
            COALESCE(bs.hit_count, 0)               AS hit_count,
            COALESCE(bs.double_hit, 0)              AS double_hit,
            COALESCE(bs.triple, 0)                  AS triple,
            COALESCE(bs.homerun, 0)                 AS homerun,
            COALESCE(bs.on_base_opportunity, 0)     AS on_base_opportunity,
            COALESCE(bs.on_base, 0)                 AS on_base
        FROM batting_stats bs
        JOIN players p   ON bs.player_id      = p.player_id
        JOIN teams t     ON p.team_id         = t.team_id
        JOIN games g     ON bs.game_id        = g.game_id
        JOIN teams t_opp ON g.away_team_id    = t_opp.team_id
        WHERE t.team_name = %s
    """
    params: list = [TEAM_NAME]
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    if player_id is not None:
        query += " AND p.player_id = %s"
        params.append(player_id)
    query += " ORDER BY p.player_name, g.game_date, g.game_number"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    # 選手ごとに累積打率・OPS を計算
    player_data: dict[str, list] = defaultdict(list)
    for row in rows:
        r = dict(row)
        r["game_date"] = str(r["game_date"])
        player_data[r["player_name"]].append(r)

    result = []
    for player_name in sorted(player_data.keys()):
        cum_ab = cum_hits = cum_on_base = cum_opp = cum_bases = 0
        for game in player_data[player_name]:
            cum_ab    += game["at_bat_count"]
            cum_hits  += game["hit_count"]
            cum_on_base += game["on_base"]
            cum_opp   += game["on_base_opportunity"]
            cum_bases += (
                game["hit_count"]
                + game["double_hit"]
                + 2 * game["triple"]
                + 3 * game["homerun"]
            )
            obp = round(cum_on_base / cum_opp, 3) if cum_opp > 0 else None
            slg = round(cum_bases / cum_ab, 3) if cum_ab > 0 else None
            game["cum_avg"] = round(cum_hits / cum_ab, 3) if cum_ab > 0 else None
            game["cum_ops"] = round(obp + slg, 3) if (obp is not None and slg is not None) else None
            result.append(game)

    return result
