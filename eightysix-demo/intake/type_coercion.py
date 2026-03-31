"""Coerce raw string values into typed Python values.

Handles the endless parade of real-world formats:
- Dates: 03/14/2025, 2025-03-14, March 14 2025, 14-Mar-25, etc.
- Currency: $4,200.50, 4200.50, $4,200, (4200.50), -$42.50
- Percentages: 28%, 0.28, 28.5 %
- Times: 6:30 PM, 18:30, 6:30:00 PM
- Booleans: yes/no, true/false, y/n, 1/0
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Optional


# ── Date parsing ──────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    # ISO: 2025-03-14, 2025/03/14
    (r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", "ymd"),
    # US: 03/14/2025, 03-14-2025, 3/14/25
    (r"(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", "mdy"),
    # Named month: Mar 14, 2025 / March 14, 2025 / 14-Mar-25
    (r"(\w{3,9})\s+(\d{1,2}),?\s+(\d{2,4})", "Mdy"),
    (r"(\d{1,2})[-\s](\w{3,9})[-\s](\d{2,4})", "dMy"),
]

_MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _expand_year(y: int) -> int:
    if y < 100:
        return 2000 + y if y < 70 else 1900 + y
    return y


def parse_date(value: str) -> Optional[date]:
    """Try to parse a string into a date. Returns None on failure."""
    value = value.strip()
    if not value:
        return None

    for pattern, fmt in _DATE_PATTERNS:
        m = re.match(pattern, value)
        if not m:
            continue
        try:
            a, b, c = m.group(1), m.group(2), m.group(3)
            if fmt == "ymd":
                return date(_expand_year(int(a)), int(b), int(c))
            elif fmt == "mdy":
                return date(_expand_year(int(c)), int(a), int(b))
            elif fmt == "Mdy":
                month = _MONTH_NAMES.get(a.lower()[:3])
                if month:
                    return date(_expand_year(int(c)), month, int(b))
            elif fmt == "dMy":
                month = _MONTH_NAMES.get(b.lower()[:3])
                if month:
                    return date(_expand_year(int(c)), month, int(a))
        except (ValueError, KeyError):
            continue

    return None


# ── Datetime parsing ──────────────────────────────────────────────────────

_TIME_12H = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)", re.IGNORECASE)
_TIME_24H = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def parse_time(value: str) -> Optional[time]:
    value = value.strip()
    m = _TIME_12H.search(value)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        s = int(m.group(3)) if m.group(3) else 0
        ampm = m.group(4).upper()
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
        return time(h, mi, s)

    m = _TIME_24H.search(value)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        s = int(m.group(3)) if m.group(3) else 0
        if 0 <= h < 24:
            return time(h, mi, s)

    return None


def parse_datetime(value: str) -> Optional[datetime]:
    """Try to parse a datetime from various formats."""
    value = value.strip()
    if not value:
        return None

    # Try splitting on space/T — date part + time part
    parts = re.split(r"[T\s]+", value, maxsplit=1)
    d = parse_date(parts[0])
    if d is None:
        return None

    if len(parts) > 1:
        t = parse_time(parts[1])
        if t:
            return datetime.combine(d, t)

    return datetime.combine(d, time(0, 0))


# ── Currency ──────────────────────────────────────────────────────────────

_CURRENCY_RE = re.compile(r"[($)\s,]")
_PARENS_NEGATIVE = re.compile(r"^\((.+)\)$")


def parse_currency(value: str) -> Optional[float]:
    """Parse a currency string into a float. Handles $, commas, parentheses for negatives."""
    value = value.strip()
    if not value or value == "-":
        return None

    negative = False
    m = _PARENS_NEGATIVE.match(value)
    if m:
        value = m.group(1)
        negative = True

    if value.startswith("-"):
        negative = True
        value = value[1:]

    cleaned = _CURRENCY_RE.sub("", value)
    # Remove trailing % if someone put currency in a percent column
    cleaned = cleaned.rstrip("%")

    try:
        result = float(cleaned)
        return -result if negative else result
    except ValueError:
        return None


# ── Percentage ────────────────────────────────────────────────────────────

def parse_percentage(value: str) -> Optional[float]:
    """Parse a percentage. Returns as decimal (28% → 0.28)."""
    value = value.strip()
    if not value:
        return None

    if "%" in value:
        cleaned = value.replace("%", "").replace(",", "").strip()
        try:
            return float(cleaned) / 100.0
        except ValueError:
            return None

    try:
        v = float(value.replace(",", ""))
        # If > 1, assume it's already a whole-number percentage
        if v > 1.0:
            return v / 100.0
        return v
    except ValueError:
        return None


# ── General number ────────────────────────────────────────────────────────

def parse_number(value: str) -> Optional[float]:
    """Parse a general number, stripping commas and whitespace."""
    value = value.strip().replace(",", "").replace(" ", "")
    if not value or value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> Optional[int]:
    f = parse_number(value)
    if f is not None:
        return int(round(f))
    return None


# ── Sniffers (detect what a column contains) ──────────────────────────────

def looks_like_date(values: list[str], threshold: float = 0.5) -> bool:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False
    hits = sum(1 for v in non_empty if parse_date(v) is not None)
    return hits / len(non_empty) >= threshold


def looks_like_currency(values: list[str], threshold: float = 0.5) -> bool:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False
    hits = sum(1 for v in non_empty if parse_currency(v) is not None)
    has_dollar = any("$" in v for v in non_empty)
    rate = hits / len(non_empty)
    return rate >= threshold and (has_dollar or rate >= 0.7)


def looks_like_datetime(values: list[str], threshold: float = 0.5) -> bool:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False
    hits = sum(1 for v in non_empty if parse_datetime(v) is not None)
    has_time = any(re.search(r"\d{1,2}:\d{2}", v) for v in non_empty)
    return hits / len(non_empty) >= threshold and has_time


def looks_like_employee(values: list[str], threshold: float = 0.5) -> bool:
    """Check if values look like person names or employee IDs."""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False

    name_pattern = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$")
    id_pattern = re.compile(r"^(?:EMP|emp|E|e)[-_]?\d+$")

    hits = sum(1 for v in non_empty if name_pattern.match(v) or id_pattern.match(v))
    # Also count if most values are unique-ish short strings (not numbers)
    unique_ratio = len(set(non_empty)) / len(non_empty) if non_empty else 0
    text_ratio = sum(1 for v in non_empty if not re.match(r'^[\d$,.%-]+$', v)) / len(non_empty)

    if hits / len(non_empty) >= threshold:
        return True
    # Heuristic: many unique text values in a column = probably names
    return unique_ratio > 0.3 and text_ratio > 0.8 and len(non_empty) > 5


def looks_like_item_name(values: list[str], threshold: float = 0.5) -> bool:
    """Check if values look like menu item names."""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False

    text_count = sum(1 for v in non_empty if not re.match(r'^[\d$,.%-]+$', v))
    avg_len = sum(len(v) for v in non_empty) / len(non_empty)
    # Item names: mostly text, medium length, some repetition
    unique_ratio = len(set(v.lower() for v in non_empty)) / len(non_empty)

    return (text_count / len(non_empty) > 0.8
            and 3 < avg_len < 50
            and unique_ratio < 0.7)  # Items repeat more than employee names
