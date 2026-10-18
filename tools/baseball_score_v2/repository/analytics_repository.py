"""Analytics repository: DB queries for Excel analytics output"""
import logging
import psycopg2
from psycopg2.extras import DictCursor
from config.config import DB_CONFIG, TEAM_NAME


class AnalyticsRepository:
    def __init__(self):
        self.logger = logging.getLogger("app.repository")
        try:
            self.conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                dbname=DB_CONFIG["dbname"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                connect_timeout=20,
                sslmode="disable"
            )
            self.logger.info("✓ DB接続成功: %s:%s", DB_CONFIG["host"], DB_CONFIG["port"])
        except Exception as e:
            self.logger.error("✗ DB接続失敗: %s", str(e))
            raise
        self.team_name = TEAM_NAME

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def fetch_player_batting_stats(self, year: int) -> list[dict]:
        """Sheet 1: 選手別打撃成績（年度フィルタ付き）"""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT
                    p.player_name,
                    COUNT(DISTINCT bs.game_id)                                         AS game_count,
                    COALESCE(SUM(bs.at_bat), SUM(bs.on_base_opportunity), 0)           AS at_bat,
                    COALESCE(SUM(bs.at_bat_count), 0)                                  AS at_bat_count,
                    COALESCE(SUM(bs.hit_count), 0)                                     AS hit_count,
                    GREATEST(
                        COALESCE(SUM(bs.hit_count), 0)
                        - COALESCE(SUM(bs.double_hit), 0)
                        - COALESCE(SUM(bs.triple), 0)
                        - COALESCE(SUM(bs.homerun), 0), 0
                    )                                                                   AS single,
                    COALESCE(SUM(bs.double_hit), 0)                                    AS double_hit,
                    COALESCE(SUM(bs.triple), 0)                                        AS triple,
                    COALESCE(SUM(bs.homerun), 0)                                       AS homerun,
                    COALESCE(SUM(bs.rbi), 0)                                           AS rbi,
                    COALESCE(SUM(bs.walk_count), 0)                                    AS walk_count,
                    COALESCE(SUM(bs.strike_out), 0)                                    AS strike_out,
                    COALESCE(SUM(bs.stolen_base), 0)                                   AS stolen_base,
                    ROUND(
                        COALESCE(SUM(bs.hit_count), 0)::numeric
                        / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0), 3
                    )                                                                   AS batting_avg,
                    ROUND(
                        COALESCE(SUM(bs.on_base), 0)::numeric
                        / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0), 3
                    )                                                                   AS on_base_pct,
                    ROUND(
                        (COALESCE(SUM(bs.hit_count), 0)
                         + COALESCE(SUM(bs.double_hit), 0)
                         + 2 * COALESCE(SUM(bs.triple), 0)
                         + 3 * COALESCE(SUM(bs.homerun), 0))::numeric
                        / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0), 3
                    )                                                                   AS slg,
                    ROUND(
                        COALESCE(SUM(bs.on_base), 0)::numeric
                        / NULLIF(COALESCE(SUM(bs.on_base_opportunity), 0), 0)
                        + (COALESCE(SUM(bs.hit_count), 0)
                           + COALESCE(SUM(bs.double_hit), 0)
                           + 2 * COALESCE(SUM(bs.triple), 0)
                           + 3 * COALESCE(SUM(bs.homerun), 0))::numeric
                        / NULLIF(COALESCE(SUM(bs.at_bat_count), 0), 0)
                    , 3)                                                                AS ops
                FROM batting_stats bs
                JOIN players p ON bs.player_id = p.player_id
                JOIN teams t ON p.team_id = t.team_id
                JOIN games g ON bs.game_id = g.game_id
                WHERE EXTRACT(YEAR FROM g.game_date) = %s
                  AND t.team_name = %s
                GROUP BY p.player_id, p.player_name
                ORDER BY ops DESC NULLS LAST
            """, (year, self.team_name))
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def fetch_hit_direction_stats(self, year: int) -> list[dict]:
        """Sheet 2: 打球方向分析"""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT
                    p.player_name,
                    COALESCE(SUM(bs.right_9), 0)       AS right_9,
                    COALESCE(SUM(bs.right_center), 0)  AS right_center,
                    COALESCE(SUM(bs.center), 0)        AS center_field,
                    COALESCE(SUM(bs.left_center), 0)   AS left_center,
                    COALESCE(SUM(bs.left_7), 0)        AS left_7
                FROM batting_stats bs
                JOIN players p ON bs.player_id = p.player_id
                JOIN teams t ON p.team_id = t.team_id
                JOIN games g ON bs.game_id = g.game_id
                WHERE EXTRACT(YEAR FROM g.game_date) = %s
                  AND t.team_name = %s
                GROUP BY p.player_id, p.player_name
                ORDER BY p.player_name
            """, (year, self.team_name))
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def fetch_player_game_log(self, year: int) -> list[dict]:
        """Sheet 3: 選手別試合ログ（累積成績計算用）"""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT
                    p.player_name,
                    g.game_date,
                    t_opp.team_name                      AS opponent,
                    g.game_number,
                    COALESCE(bs.at_bat_count, 0)         AS at_bat_count,
                    COALESCE(bs.hit_count, 0)            AS hit_count,
                    COALESCE(bs.double_hit, 0)           AS double_hit,
                    COALESCE(bs.triple, 0)               AS triple,
                    COALESCE(bs.homerun, 0)              AS homerun,
                    COALESCE(bs.walk_count, 0)           AS walk_count,
                    COALESCE(bs.strike_out, 0)           AS strike_out,
                    COALESCE(bs.stolen_base, 0)          AS stolen_base,
                    COALESCE(bs.on_base_opportunity, 0)  AS on_base_opportunity,
                    COALESCE(bs.on_base, 0)              AS on_base
                FROM batting_stats bs
                JOIN players p ON bs.player_id = p.player_id
                JOIN teams t ON p.team_id = t.team_id
                JOIN games g ON bs.game_id = g.game_id
                JOIN teams t_opp ON g.away_team_id = t_opp.team_id
                WHERE EXTRACT(YEAR FROM g.game_date) = %s
                  AND t.team_name = %s
                ORDER BY p.player_name, g.game_date, g.game_number
            """, (year, self.team_name))
            rows = cur.fetchall()
        return [dict(row) for row in rows]
