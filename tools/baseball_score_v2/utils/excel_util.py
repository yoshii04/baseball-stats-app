"""Utility functions for Excel data parsing"""

import re
import pandas as pd


def safe_str(value) -> str:
    """
    Safely convert a value to string, handling None, NaN, and datetime objects

    Args:
        value: Value to convert

    Returns:
        String representation of the value, empty string if None/NaN
    """
    if value is None or pd.isna(value):  # NaN/NaT のとき
        return ""
    # 日付列の場合、datetime型ならYYYY-MM-DDに変換
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def safe_game_number(value) -> int:
    """
    Convert game number label to integer.
    e.g. "1試合目" → 1, "2試合目" → 2, 1 → 1

    Returns 1 if value is None, empty, or not parseable.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 1
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return 1
    match = re.search(r"\d+", s)
    if match:
        return int(match.group())
    return 1


def safe_int(value) -> int:
    """
    Safely convert a value to integer, handling None and empty strings

    Args:
        value: Value to convert

    Returns:
        Integer value, 0 if conversion fails or value is None/empty/NaN
    """
    if value is None or str(value).strip() == "" or str(value).lower() == "nan":
        return 0
    return int(float(value))


def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert a value to float, handling None and empty strings

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value, default if conversion fails or value is None/empty/NaN
    """
    if value is None or str(value).strip() == "" or str(value).lower() == "nan":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
