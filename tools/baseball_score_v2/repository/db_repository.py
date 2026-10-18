import logging
import psycopg2
from psycopg2.extras import DictCursor
from config.config import DB_CONFIG, TEAM_NAME

class DBRepository:
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
            self.logger.info("✓ データベース接続成功: %s:%s", DB_CONFIG["host"], DB_CONFIG["port"])
        except Exception as e:
            self.logger.error("✗ データベース接続失敗: %s", str(e))
            raise
        self.team_name = TEAM_NAME

    def close(self):
        """Close database connection if it's open"""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed"""
        self.close()
        return False



    def get_or_create_team(self, cur, team_name=None):
        """SELECT-first パターン: 既存なら SELECT、なければ INSERT"""
        name = team_name if team_name is not None else self.team_name
        cur.execute("SELECT team_id FROM teams WHERE team_name=%s", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO teams (team_name) VALUES (%s) RETURNING team_id",
            (name,)
        )
        return cur.fetchone()[0]

    def get_or_create_game(self, cur, game_date, home_team_id, away_team_id, game_number=1):
        """SELECT-first パターン: 既存なら SELECT、なければ INSERT"""
        cur.execute("""
            SELECT game_id FROM games
            WHERE game_date=%s AND home_team_id=%s AND away_team_id=%s AND game_number=%s
        """, (game_date, home_team_id, away_team_id, game_number))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("""
            INSERT INTO games (game_date, home_team_id, away_team_id, game_number)
            VALUES (%s, %s, %s, %s) RETURNING game_id
        """, (game_date, home_team_id, away_team_id, game_number))
        return cur.fetchone()[0]

    def get_or_create_player(self, cur, player_name, team_id):
        """SELECT-first パターン: 既存なら SELECT、なければ INSERT"""
        cur.execute("""
            SELECT player_id FROM players
            WHERE player_name=%s AND team_id=%s
        """, (player_name, team_id))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("""
            INSERT INTO players (player_name, team_id) VALUES (%s, %s) RETURNING player_id
        """, (player_name, team_id))
        return cur.fetchone()[0]

    def insert_players(self, records):
        """
        Excelの全選手を事前に登録する
        """
        with self.conn.cursor() as cur:
            team_id = self.get_or_create_team(cur)
            players = set(r.player for r in records if r.player)
            for player in players:
                self.get_or_create_player(cur, player, team_id)
            self.conn.commit()
            self.logger.info("選手登録完了: %d 名", len(players))

    def insert_records(self, records):
        """
        バッティングデータをDBに登録（SELECT-first パターンで ID 飛び番を防止）
        同一選手・同一試合の複数行（回数ごと）は事前に集計してから1件INSERT する
        """
        from collections import defaultdict

        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            team_id = self.get_or_create_team(cur)

            # (player, date, opponent, game_number) → 集計済みStats
            aggregated: dict[tuple, dict] = defaultdict(lambda: {
                "double": 0, "triple": 0, "homerun": 0,
                "at_bat_count": 0, "hit_count": 0, "walk_count": 0,
                "strike_out": 0, "stolen_base": 0,
                "on_base_opportunity": 0, "on_base": 0,
                "right_9": 0, "right_center": 0, "center": 0,
                "left_center": 0, "left_7": 0,
            })

            for record in records:
                key = (record.player, record.date, record.opponent, record.game_number)
                aggregated[key]["double"]             += record.double
                aggregated[key]["triple"]             += record.triple
                aggregated[key]["homerun"]            += record.homerun
                aggregated[key]["at_bat_count"]       += record.at_bat_count
                aggregated[key]["hit_count"]          += record.hit_count
                aggregated[key]["walk_count"]         += record.walk_count
                aggregated[key]["strike_out"]         += record.strike_out
                aggregated[key]["stolen_base"]        += record.stolen_base
                aggregated[key]["on_base_opportunity"] += record.on_base_opportunity
                aggregated[key]["on_base"]            += record.on_base
                aggregated[key]["right_9"]            += record.right_9
                aggregated[key]["right_center"]       += record.right_center
                aggregated[key]["center"]             += record.center
                aggregated[key]["left_center"]        += record.left_center
                aggregated[key]["left_7"]             += record.left_7

            inserted = 0
            for (player_name, date, opponent, game_number), stats in aggregated.items():
                # 選手IDを取得
                cur.execute("""
                    SELECT player_id FROM players WHERE player_name=%s AND team_id=%s
                """, (player_name, team_id))
                row = cur.fetchone()
                if not row:
                    self.logger.warning("選手が未登録のためスキップ: %s", player_name)
                    continue
                player_id = row["player_id"]

                # 相手チーム登録
                away_team_id = self.get_or_create_team(cur, opponent)

                # ゲーム登録
                game_id = self.get_or_create_game(cur, date, team_id, away_team_id, game_number)

                # バッティング成績登録（再インポート時は最新データで上書き）
                cur.execute("""
                    INSERT INTO batting_stats
                      (player_id, game_id, double_hit, triple, homerun,
                       at_bat_count, hit_count, walk_count, strike_out,
                       stolen_base, on_base_opportunity, on_base,
                       right_9, right_center, center, left_center, left_7)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_id, game_id) DO UPDATE SET
                      double_hit          = EXCLUDED.double_hit,
                      triple              = EXCLUDED.triple,
                      homerun             = EXCLUDED.homerun,
                      at_bat_count        = EXCLUDED.at_bat_count,
                      hit_count           = EXCLUDED.hit_count,
                      walk_count          = EXCLUDED.walk_count,
                      strike_out          = EXCLUDED.strike_out,
                      stolen_base         = EXCLUDED.stolen_base,
                      on_base_opportunity = EXCLUDED.on_base_opportunity,
                      on_base             = EXCLUDED.on_base,
                      right_9             = EXCLUDED.right_9,
                      right_center        = EXCLUDED.right_center,
                      center              = EXCLUDED.center,
                      left_center         = EXCLUDED.left_center,
                      left_7              = EXCLUDED.left_7
                """, (player_id, game_id,
                      stats["double"], stats["triple"], stats["homerun"],
                      stats["at_bat_count"], stats["hit_count"], stats["walk_count"],
                      stats["strike_out"], stats["stolen_base"],
                      stats["on_base_opportunity"], stats["on_base"],
                      stats["right_9"], stats["right_center"], stats["center"],
                      stats["left_center"], stats["left_7"]))
                inserted += 1

            self.conn.commit()
            self.logger.info("打撃データ登録完了: %d 件（集計後 %d 件）", len(records), inserted)

    def insert_pitcher_stats(self, cur, pitcher_id: int, game_id: int, stats: dict):
        """投手成績を登録（再インポート時は最新データで上書き）"""
        cur.execute("""
            INSERT INTO pitcher_stats
              (pitcher_id, game_id, batters_faced, pitch_count,
               hits_allowed, homerun_allowed, walks_allowed, strikeouts, runs_allowed,
               right_9, right_center, center, left_center, left_7,
               innings_pitched, outs, earned_runs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (pitcher_id, game_id) DO UPDATE SET
              batters_faced   = EXCLUDED.batters_faced,
              pitch_count     = EXCLUDED.pitch_count,
              hits_allowed    = EXCLUDED.hits_allowed,
              homerun_allowed = EXCLUDED.homerun_allowed,
              walks_allowed   = EXCLUDED.walks_allowed,
              strikeouts      = EXCLUDED.strikeouts,
              runs_allowed    = EXCLUDED.runs_allowed,
              right_9         = EXCLUDED.right_9,
              right_center    = EXCLUDED.right_center,
              center          = EXCLUDED.center,
              left_center     = EXCLUDED.left_center,
              left_7          = EXCLUDED.left_7,
              innings_pitched = EXCLUDED.innings_pitched,
              outs            = EXCLUDED.outs,
              earned_runs     = EXCLUDED.earned_runs
        """, (
            pitcher_id, game_id,
            stats["batters_faced"], stats["pitch_count"],
            stats["hits_allowed"], stats["homerun_allowed"],
            stats["walks_allowed"], stats["strikeouts"], stats["runs_allowed"],
            stats["right_9"], stats["right_center"], stats["center"],
            stats["left_center"], stats["left_7"],
            stats.get("innings_pitched", 0), stats.get("outs", 0), stats.get("earned_runs", 0),
        ))

    def fetch_batting_stats(self) -> list[dict]:
        """選手別打撃成績を集計して返す（OPS順）"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.player_name,
                       SUM(bs.double_hit)           AS double_hit,
                       SUM(bs.triple)               AS triple,
                       SUM(bs.homerun)              AS homerun,
                       SUM(bs.hit_count)            AS hit_count,
                       SUM(bs.stolen_base)          AS stolen_base,
                       SUM(bs.walk_count)           AS walk_count,
                       SUM(bs.strike_out)           AS strike_out,
                       ROUND(
                           SUM(bs.hit_count)::numeric /
                           NULLIF(SUM(bs.at_bat_count), 0), 3
                       )                            AS batting_avg,
                       ROUND(
                           SUM(bs.on_base)::numeric /
                           NULLIF(SUM(bs.on_base_opportunity), 0), 3
                       )                            AS on_base_pct,
                       ROUND(
                           SUM(bs.on_base)::numeric /
                           NULLIF(SUM(bs.on_base_opportunity), 0)
                           +
                           (SUM(bs.hit_count) + SUM(bs.double_hit) + 2 * SUM(bs.triple) + 3 * SUM(bs.homerun))::numeric /
                           NULLIF(SUM(bs.at_bat_count), 0)
                       , 3)                         AS ops
                FROM batting_stats bs
                JOIN players p ON bs.player_id = p.player_id
                GROUP BY p.player_id, p.player_name
                ORDER BY ops DESC NULLS LAST
            """)
            rows = cur.fetchall()
        return [
            {"player_name": row[0], "double_hit": int(row[1]),
             "triple": int(row[2]), "homerun": int(row[3]),
             "hit_count": int(row[4]), "stolen_base": int(row[5]),
             "walk_count": int(row[6]), "strike_out": int(row[7]),
             "batting_avg": row[8], "on_base_pct": row[9], "ops": row[10]}
            for row in rows
        ]
