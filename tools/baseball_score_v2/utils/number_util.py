"""Utility functions for number and inning conversions"""


def to_marunum(value) -> str:
    """
    Convert number to Japanese circled digit (①-⑨)

    Args:
        value: Number to convert (int, float, or numeric string)

    Returns:
        Circled digit character (①-⑨) or original string if conversion fails
    """
    try:
        num = int(float(value))
        if 1 <= num <= 9:
            # Unicode circled numbers: ① (U+2460) to ⑨ (U+2468)
            return chr(0x2460 + num - 1)
        else:
            return str(value).strip()
    except (ValueError, TypeError):
        return str(value).strip() if value is not None else ""


def marunum_to_int(inning_str: str) -> int:
    """
    Convert inning string to integer, handling Unicode circled numbers ①-⑨

    Args:
        inning_str: Inning string (e.g., "①", "①回", "1回", "5")

    Returns:
        Integer inning number (1-9+)

    Raises:
        ValueError: If the string cannot be converted to an integer
    """
    s = str(inning_str).replace("回", "").strip()

    # Unicode circled numbers ①-⑨ (U+2460-U+2468)
    if len(s) == 1 and "\u2460" <= s <= "\u2468":
        return ord(s) - 0x2460 + 1

    return int(s)
