from dataclasses import dataclass, field


@dataclass
class GameRecord:
    """試合スコアと打撃成績を保持するデータクラス"""
    date: str            # "2026-07-21"
    opponent: str
    game_number: int
    venue: str = ""
    pitcher: str = ""
    our_innings: list = None   # 9要素（各回の得点）。None の場合はスコアなし（空欄）
    opp_innings: list = None   # 9要素（各回の得点）。None の場合はスコアなし（空欄）
    our_total: int | str = None   # 通常は int。コールドゲーム等で "6X" のような文字列になる場合あり
    opp_total: int | str = None   # 同上
    our_team: str = ""   # 自チーム名（config.json の our_team_name / 環境変数 TEAM_NAME）
    opp_team: str = ""   # CSV から取得
    doubles: list = field(default_factory=list)
    triples: list = field(default_factory=list)
    homeruns: list = field(default_factory=list)
    is_sayonara: bool = False   # サヨナラ勝ちフラグ（M列合計のX表記に使用）
