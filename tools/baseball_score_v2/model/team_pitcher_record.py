from dataclasses import dataclass


@dataclass
class TeamPitcherRecord:
    """チーム単位のデータシートの1行分データクラス"""
    date: str
    opponent: str
    pitcher_name: str
    game_number: int = 1
    runs_allowed: int = 0
    earned_runs: int = 0
    innings_pitched: int = 0
    outs: int = 0
