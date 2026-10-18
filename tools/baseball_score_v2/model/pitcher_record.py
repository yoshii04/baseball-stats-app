from dataclasses import dataclass


@dataclass
class PitcherRecord:
    """1打席分の投手成績データクラス"""
    date: str
    opponent: str
    pitcher_name: str
    game_number: int = 1
    pitch_count: int = 0
    homerun_allowed: int = 0
    walks_allowed: int = 0
    strikeouts: int = 0
    hits_allowed: int = 0
    runs_allowed: int = 0
    right_9: int = 0
    right_center: int = 0
    center: int = 0
    left_center: int = 0
    left_7: int = 0
