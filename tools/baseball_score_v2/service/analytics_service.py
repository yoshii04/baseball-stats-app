"""Analytics service: calculation logic for cumulative stats and derived metrics"""
from collections import defaultdict


class AnalyticsService:

    def calculate_cumulative_stats(self, game_log: list[dict]) -> list[dict]:
        """
        試合ログに累積打率・累積OPSを付加して返す。
        player_nameでグループ化し、game_date/game_number順で累積集計する。
        """
        player_rows: dict[str, list[dict]] = defaultdict(list)
        for row in game_log:
            player_rows[row["player_name"]].append(row)

        result = []
        for player_name in sorted(player_rows.keys()):
            cum_ab = 0
            cum_hits = 0
            cum_on_base = 0
            cum_on_base_opp = 0
            cum_total_bases = 0

            for game in player_rows[player_name]:
                cum_ab += game["at_bat_count"]
                cum_hits += game["hit_count"]
                cum_on_base += game["on_base"]
                cum_on_base_opp += game["on_base_opportunity"]
                cum_total_bases += (
                    game["hit_count"]
                    + game["double_hit"]
                    + 2 * game["triple"]
                    + 3 * game["homerun"]
                )

                cum_avg = round(cum_hits / cum_ab, 3) if cum_ab > 0 else None
                cum_obp = round(cum_on_base / cum_on_base_opp, 3) if cum_on_base_opp > 0 else None
                cum_slg = round(cum_total_bases / cum_ab, 3) if cum_ab > 0 else None
                cum_ops = (
                    round(cum_obp + cum_slg, 3)
                    if (cum_obp is not None and cum_slg is not None)
                    else None
                )

                result.append({
                    **game,
                    "cum_avg": cum_avg,
                    "cum_ops": cum_ops,
                })

        return result

    def calculate_direction_pct(self, direction_rows: list[dict]) -> list[dict]:
        """
        打球方向の各列にパーセンテージを付加して返す。
        """
        result = []
        for row in direction_rows:
            total = (
                row["right_9"]
                + row["right_center"]
                + row["center_field"]
                + row["left_center"]
                + row["left_7"]
            )

            def pct(val: int) -> float:
                return round(val / total * 100, 1) if total > 0 else 0.0

            result.append({
                **row,
                "total": total,
                "pct_right_9": pct(row["right_9"]),
                "pct_right_center": pct(row["right_center"]),
                "pct_center": pct(row["center_field"]),
                "pct_left_center": pct(row["left_center"]),
                "pct_left_7": pct(row["left_7"]),
            })

        return result
