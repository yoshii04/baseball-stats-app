from dataclasses import dataclass


@dataclass
class BattingRecord:
    """Data class for a single batting record from the Excel file"""
    date: str
    opponent: str
    player: str
    game_number: int = 1
    double: int = 0
    triple: int = 0
    homerun: int = 0
    at_bat_count: int = 0
    hit_count: int = 0
    walk_count: int = 0
    strike_out: int = 0
    stolen_base: int = 0
    on_base_opportunity: int = 0
    on_base: int = 0
    right_9: int = 0
    right_center: int = 0
    center: int = 0
    left_center: int = 0
    left_7: int = 0

    def __post_init__(self):
        """Validate record after initialization"""
        if not isinstance(self.game_number, int) or self.game_number < 1:
            raise ValueError(f"game_number must be positive integer, got {self.game_number}")
        if not isinstance(self.double, int) or self.double < 0:
            raise ValueError(f"double must be non-negative integer, got {self.double}")
        if not isinstance(self.triple, int) or self.triple < 0:
            raise ValueError(f"triple must be non-negative integer, got {self.triple}")
        if not isinstance(self.homerun, int) or self.homerun < 0:
            raise ValueError(f"homerun must be non-negative integer, got {self.homerun}")
        if not isinstance(self.at_bat_count, int) or self.at_bat_count < 0:
            raise ValueError(f"at_bat_count must be non-negative integer, got {self.at_bat_count}")
        if not isinstance(self.hit_count, int) or self.hit_count < 0:
            raise ValueError(f"hit_count must be non-negative integer, got {self.hit_count}")
        if not isinstance(self.walk_count, int) or self.walk_count < 0:
            raise ValueError(f"walk_count must be non-negative integer, got {self.walk_count}")
        if not isinstance(self.strike_out, int) or self.strike_out < 0:
            raise ValueError(f"strike_out must be non-negative integer, got {self.strike_out}")
        if not isinstance(self.stolen_base, int) or self.stolen_base < 0:
            raise ValueError(f"stolen_base must be non-negative integer, got {self.stolen_base}")
        if not isinstance(self.on_base_opportunity, int) or self.on_base_opportunity < 0:
            raise ValueError(f"on_base_opportunity must be non-negative integer, got {self.on_base_opportunity}")
        if not isinstance(self.on_base, int) or self.on_base < 0:
            raise ValueError(f"on_base must be non-negative integer, got {self.on_base}")
