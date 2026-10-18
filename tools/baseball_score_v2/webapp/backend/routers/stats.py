"""成績統計エンドポイント"""
from typing import Optional

from fastapi import APIRouter, Depends

from auth import verify_token
from database import TEAM_NAME, get_cursor

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("/season")
def get_season_stats(year: Optional[int] = None):
    """チームシーズン集計（試合数・チーム打率・OPS等）"""
    query = """
        SELECT
            COUNT(DISTINCT g.game_id)                                           AS game_count,
            COALESCE(SUM(bs.hit_count), 0)                                      AS total_hits,
            COALESCE(SUM(bs.homerun), 0)                                        AS total_homerun,
            COALESCE(SUM(bs.rbi), 0)                                            AS total_rbi,
            COALESCE(SUM(bs.stolen_base), 0)                                    AS total_stolen_base,
            ROUND(
                COALESCE(SUM(bs.hit_count), 0)::numeric
                / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0), 3
            )::float                                                            AS team_batting_avg,
            ROUND(
                COALESCE(SUM(bs.on_base), 0)::numeric
                / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0), 3
            )::float                                                            AS team_on_base_pct,
            ROUND(
                COALESCE(SUM(bs.on_base), 0)::numeric
                / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0)
                + (COALESCE(SUM(bs.hit_count), 0)
                   + COALESCE(SUM(bs.double_hit), 0)
                   + 2 * COALESCE(SUM(bs.triple), 0)
                   + 3 * COALESCE(SUM(bs.homerun), 0))::numeric
                / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0)
            , 3)::float                                                         AS team_ops
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
    with get_cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return dict(row) if row else {}


@router.get("/team-batting")
def get_team_batting(year: Optional[int] = None):
    """チーム打撃成績（詳細集計）"""
    where = "WHERE t.team_name = %s"
    params: list = [TEAM_NAME]
    if year is not None:
        where += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)

    batting_cols = """
            COUNT(DISTINCT g.game_id)                                           AS game_count,
            COALESCE(SUM(bs.on_base_opportunity), 0)                            AS plate_appearance,
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
            COALESCE(SUM(bs.walk_count), 0)                                     AS walk_count,
            COALESCE(SUM(bs.strike_out), 0)                                     AS strike_out,
            COALESCE(SUM(bs.stolen_base), 0)                                    AS stolen_base,
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
            , 3)::float                                                         AS ops"""

    from_join = """
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.player_id
        JOIN teams t   ON p.team_id    = t.team_id
        JOIN games g   ON bs.game_id   = g.game_id"""

    query_total = f"SELECT {batting_cols} {from_join} {where}"
    query_by_num = f"""
        SELECT g.game_number, {batting_cols} {from_join} {where}
        GROUP BY g.game_number
        ORDER BY g.game_number
    """
    with get_cursor() as cur:
        cur.execute(query_total, params)
        row = cur.fetchone()
        cur.execute(query_by_num, params)
        by_game_number = [dict(r) for r in cur.fetchall()]
    result = dict(row) if row else {}
    result["by_game_number"] = by_game_number
    return result


def _compute_pitching_derived(r: dict) -> dict:
    total_outs = r.get("total_outs", 0) or 0
    r["ip"] = f"{total_outs // 3}.{total_outs % 3}"
    er = r.get("earned_runs", 0) or 0
    r["era"] = round(er * 27 / total_outs, 2) if total_outs > 0 else None
    bf = r.get("batters_faced", 0) or 0
    h = r.get("hits_allowed", 0) or 0
    w = r.get("walks_allowed", 0) or 0
    r["whip"] = round((h + w) / bf * 3, 2) if bf > 0 else None
    return r


@router.get("/team-pitching")
def get_team_pitching(year: Optional[int] = None):
    """チーム投手成績（詳細集計）"""
    where = "WHERE t.team_name = %s"
    params: list = [TEAM_NAME]
    if year is not None:
        where += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)

    pitching_cols = """
            COUNT(DISTINCT ps.game_id)                                          AS game_count,
            COALESCE(SUM(ps.batters_faced), 0)                                  AS batters_faced,
            COALESCE(SUM(ps.pitch_count), 0)                                    AS pitch_count,
            COALESCE(SUM(ps.hits_allowed), 0)                                   AS hits_allowed,
            COALESCE(SUM(ps.homerun_allowed), 0)                                AS homerun_allowed,
            COALESCE(SUM(ps.walks_allowed), 0)                                  AS walks_allowed,
            COALESCE(SUM(ps.strikeouts), 0)                                     AS strikeouts,
            COALESCE(SUM(ps.runs_allowed), 0)                                   AS runs_allowed,
            COALESCE(SUM(ps.earned_runs), 0)                                    AS earned_runs,
            COALESCE(SUM(ps.innings_pitched), 0) * 3
                + COALESCE(SUM(ps.outs), 0)                                     AS total_outs"""

    from_join = """
        FROM pitcher_stats ps
        JOIN players p ON ps.pitcher_id = p.player_id
        JOIN teams t   ON p.team_id     = t.team_id
        JOIN games g   ON ps.game_id    = g.game_id"""

    query_total = f"SELECT {pitching_cols} {from_join} {where}"
    query_by_num = f"""
        SELECT g.game_number, {pitching_cols} {from_join} {where}
        GROUP BY g.game_number
        ORDER BY g.game_number
    """
    with get_cursor() as cur:
        cur.execute(query_total, params)
        row = cur.fetchone()
        cur.execute(query_by_num, params)
        by_game_number = [_compute_pitching_derived(dict(r)) for r in cur.fetchall()]
    if not row:
        return {}
    r = _compute_pitching_derived(dict(row))
    r["by_game_number"] = by_game_number
    return r


@router.get("/team-record")
def get_team_record(year: Optional[int] = None):
    """チーム戦績（勝敗・得点・失点）"""
    where = "WHERE t.team_name = %s"
    params: list = [TEAM_NAME]
    if year is not None:
        where += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)

    record_cols = """
            COUNT(*)                                                            AS game_count,
            COUNT(*) FILTER (WHERE g.result = '〇')                             AS wins,
            COUNT(*) FILTER (WHERE g.result = '×')                             AS losses,
            COUNT(*) FILTER (WHERE g.result = '△')                             AS draws,
            COALESCE(SUM(g.home_score), 0)                                      AS runs_scored,
            COALESCE(SUM(g.away_score), 0)                                      AS runs_allowed"""

    query_total = f"""
        SELECT {record_cols}
        FROM games g
        JOIN teams t ON g.home_team_id = t.team_id
        {where}
    """
    query_by_num = f"""
        SELECT
            g.game_number, {record_cols}
        FROM games g
        JOIN teams t ON g.home_team_id = t.team_id
        {where}
        GROUP BY g.game_number
        ORDER BY g.game_number
    """
    with get_cursor() as cur:
        cur.execute(query_total, params)
        row = cur.fetchone()
        cur.execute(query_by_num, params)
        by_game_number = [dict(r) for r in cur.fetchall()]
    result = dict(row) if row else {}
    result["by_game_number"] = by_game_number
    return result


@router.get("/ranking")
def get_ops_ranking(year: Optional[int] = None, limit: int = 10):
    """OPSランキング"""
    query = """
        SELECT
            p.player_id,
            p.player_name,
            COALESCE(SUM(bs.at_bat_count), 0)                                   AS at_bat_count,
            COALESCE(SUM(bs.hit_count), 0)                                      AS hit_count,
            COALESCE(SUM(bs.homerun), 0)                                        AS homerun,
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
    params: list = [TEAM_NAME]
    if year is not None:
        query += " AND EXTRACT(YEAR FROM g.game_date) = %s"
        params.append(year)
    query += " GROUP BY p.player_id, p.player_name ORDER BY ops DESC NULLS LAST LIMIT %s"
    params.append(limit)
    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
