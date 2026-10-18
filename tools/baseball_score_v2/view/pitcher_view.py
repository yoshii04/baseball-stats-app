import logging


class PitcherView:
    def __init__(self):
        self.logger = logging.getLogger("app.view")

    @staticmethod
    def _format_innings(innings: int, outs: int) -> str:
        """イニング数を X.Y 形式（野球表記）で返す"""
        return f"{innings}.{outs}"

    def display_summary(self, summary: dict):
        """投手別・試合別の成績サマリーをコンソール表示"""
        print("=== 投手成績サマリー ===")
        for (date, opponent, game_number), pitchers in sorted(summary.items()):
            print(f"\n{date} vs {opponent} 第{game_number}試合")
            print(f"  {'投手名':<12} {'IP':<6} {'対戦':<5} {'投球':<5} {'被安打':<6} {'被本塁打':<7} {'与四死球':<7} {'奪三振':<6} {'失点':<4} {'自責点':<5}")
            print("  " + "-" * 72)
            for pitcher_name, s in pitchers.items():
                ip_str = self._format_innings(s["innings_pitched"], s["outs"])
                print(
                    f"  {pitcher_name:<12}"
                    f" {ip_str:>5}"
                    f" {s['batters_faced']:>4}"
                    f" {s['pitch_count']:>4}"
                    f" {s['hits_allowed']:>5}"
                    f" {s['homerun_allowed']:>6}"
                    f" {s['walks_allowed']:>6}"
                    f" {s['strikeouts']:>5}"
                    f" {s['runs_allowed']:>3}"
                    f" {s['earned_runs']:>4}"
                )
