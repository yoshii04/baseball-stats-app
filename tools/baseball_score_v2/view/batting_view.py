import logging
from utils.number_util import to_marunum


class BattingView:
    def __init__(self):
        self.logger = logging.getLogger("app.view")

    def display_summary(self, summary):
        for date, opponents in summary.items():
            for opponent, games in opponents.items():
                for game_number, hit_types in games.items():
                    header = f"{date} {opponent} {game_number}試合目"
                    print(header)

                    for hit_type, players in hit_types.items():
                        parts = []
                        for player, count in players.items():
                            if count == 1:
                                parts.append(player)
                            else:
                                parts.append(f"{player}{to_marunum(str(count))}")
                        print(f"　{hit_type}：" + "、".join(parts))

    def display_batting_stats(self, stats: list[dict]) -> None:
        """選手別打撃成績をコンソールに表示する（OPS順）"""
        print("=== 打撃成績リスト ===")
        print(f"{'名前':<14}{'OPS':>6}{'打率':>6}{'本塁打':>5}{'3塁打':>5}{'2塁打':>5}{'安打':>4}{'盗塁':>4}{'四死球':>5}{'三振':>4}")
        print("-" * 62)
        if not stats:
            print("(データなし)")
            return
        for row in stats:
            ops_str        = f"{row['ops']:.3f}"         if row['ops']         is not None else "-.---"
            batting_avg_str = f"{row['batting_avg']:.3f}"[1:] if row['batting_avg'] is not None else "----"

            print(
                f"{row['player_name']:<14}"
                f"{ops_str:>6}"
                f"{batting_avg_str:>6}"
                f"{row['homerun']:>5}"
                f"{row['triple']:>5}"
                f"{row['double_hit']:>5}"
                f"{row['hit_count']:>4}"
                f"{row['stolen_base']:>4}"
                f"{row['walk_count']:>5}"
                f"{row['strike_out']:>4}"
            )
