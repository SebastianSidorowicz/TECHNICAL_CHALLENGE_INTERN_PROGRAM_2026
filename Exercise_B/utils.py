"""
Utility functions for field normalization and validation.
Handles parsing of season/episode numbers, dates, and string normalization.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def normalize_string(value: str) -> str:
    """Trim and collapse internal whitespace."""
    return re.sub(r"\s+", " ", value.strip())


def normalize_for_comparison(value: str) -> str:
    """Lowercase + collapse whitespace for duplicate-key comparisons."""
    return normalize_string(value).lower()


def parse_number(raw: str) -> Tuple[Optional[int], bool]:
    """
    Parse a season or episode number from a raw string.

    Only accepts plain non-negative integers (e.g. "3", "12").
    Anything else — "one", "3.5", "--2", "abc", "abc2" — is invalid → 0.

    Returns:
        (value, was_corrected)
        - Empty/missing field → (None, False)   caller will default to 0
        - Valid integer       → (int,  False)
        - Invalid / non-numeric → (0,  True)
    """
    if not raw or not raw.strip():
        return None, False  # absent field, not an error

    cleaned = normalize_string(raw)

    # Accept ONLY a plain non-negative integer — nothing else
    if re.fullmatch(r"\d+", cleaned):
        return int(cleaned), False

    # Everything else (floats, words, symbols, mixed) is invalid
    return 0, True


def parse_air_date(raw: str) -> Tuple[str, bool]:
    """
    Validate an air date string.

    Only accepts the standard ISO format YYYY-MM-DD.
    Anything else — wrong format, impossible date, free text — → "Unknown".

    Returns:
        (date_string_or_"Unknown", was_corrected)
        - Empty/missing → ("Unknown", False)   absent, not an error
        - Valid ISO date → (date_str, False)
        - Invalid        → ("Unknown", True)
    """
    if not raw or not raw.strip():
        return "Unknown", False  # absent field, not an error

    cleaned = normalize_string(raw)

    # Supported formats, all normalized to YYYY-MM-DD on output.
    formats = [
        "%Y-%m-%d",   # 2022-05-03  (ISO canonical)
        "%Y/%m/%d",   # 2022/05/03  or  2022/5/3
        "%d-%m-%Y",   # 03-05-2022
        "%d/%m/%Y",   # 03/05/2022
        "%m/%d/%Y",   # 05/03/2022
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            max_year = datetime.now().year
            if dt.year < 1888 or dt.year > max_year:
                return "Unknown", True
            normalized = dt.strftime("%Y-%m-%d")
            was_corrected = normalized != cleaned
            return normalized, was_corrected
        except ValueError:
            continue

    return "Unknown", True


def is_effectively_missing(value: str, missing_sentinel: str) -> bool:
    """Return True if value equals the sentinel for 'unknown/missing'."""
    return normalize_for_comparison(value) == normalize_for_comparison(missing_sentinel)