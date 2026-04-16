"""US holiday calendar with restaurant-specific impact estimates.

No external dependencies — holidays are hardcoded with known dates.
Generates ExternalEvent records for a given year.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.db.models.external_event import ExternalEvent

# (month, day_or_rule, name, impact_multiplier, is_recurring)
# impact: 1.0 = normal, 0.3 = very slow, 1.5 = very busy
# Rules: "first_mon_sep" = Labor Day, etc.

FIXED_HOLIDAYS = [
    (1, 1, "New Year's Day", 0.50, True),
    (2, 14, "Valentine's Day", 1.35, True),
    (3, 17, "St. Patrick's Day", 1.20, True),
    (5, 5, "Cinco de Mayo", 1.25, True),
    (7, 4, "Independence Day", 0.60, True),
    (10, 31, "Halloween", 0.85, True),
    (12, 24, "Christmas Eve", 0.40, True),
    (12, 25, "Christmas Day", 0.20, True),
    (12, 31, "New Year's Eve", 1.40, True),
]

# Super Bowl Sunday — first Sunday in February (approximate)
# Mother's Day — second Sunday in May
# Father's Day — third Sunday in June
# Thanksgiving — fourth Thursday in November


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Find the nth occurrence of a weekday in a month. weekday: 0=Mon, 6=Sun."""
    first = date(year, month, 1)
    # Find first occurrence
    diff = (weekday - first.weekday()) % 7
    first_occ = first + timedelta(days=diff)
    return first_occ + timedelta(weeks=n - 1)


def _easter(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def generate_holiday_events(
    year: int,
    location_id: uuid.UUID | None = None,
) -> list[ExternalEvent]:
    """Generate ExternalEvent objects for all major US holidays in a year."""
    events: list[ExternalEvent] = []

    # Fixed-date holidays
    for month, day, name, impact, recurring in FIXED_HOLIDAYS:
        try:
            d = date(year, month, day)
        except ValueError:
            continue
        events.append(ExternalEvent(
            location_id=location_id,
            event_date=d,
            event_type="holiday",
            name=name,
            impact_estimate=impact,
            confidence=0.9,
            is_recurring=recurring,
        ))

    # Floating holidays
    floating = [
        # Super Bowl Sunday — typically first Sunday of February
        (_nth_weekday(year, 2, 6, 1), "Super Bowl Sunday", 1.40),
        # President's Day — third Monday of February
        (_nth_weekday(year, 2, 0, 3), "Presidents' Day", 0.80),
        # Easter Sunday
        (_easter(year), "Easter Sunday", 0.50),
        # Mother's Day — second Sunday of May
        (_nth_weekday(year, 5, 6, 2), "Mother's Day", 1.50),
        # Memorial Day — last Monday of May
        (_last_weekday(year, 5, 0), "Memorial Day", 0.65),
        # Father's Day — third Sunday of June
        (_nth_weekday(year, 6, 6, 3), "Father's Day", 1.30),
        # Labor Day — first Monday of September
        (_nth_weekday(year, 9, 0, 1), "Labor Day", 0.60),
        # Columbus/Indigenous Peoples' Day — second Monday of October
        (_nth_weekday(year, 10, 0, 2), "Columbus Day", 0.85),
        # Veterans Day — Nov 11
        (date(year, 11, 11), "Veterans Day", 0.80),
        # Thanksgiving — fourth Thursday of November
        (_nth_weekday(year, 11, 3, 4), "Thanksgiving", 0.25),
        # Black Friday — day after Thanksgiving
        (_nth_weekday(year, 11, 3, 4) + timedelta(days=1), "Black Friday", 0.70),
    ]

    for d, name, impact in floating:
        events.append(ExternalEvent(
            location_id=location_id,
            event_date=d,
            event_type="holiday",
            name=name,
            impact_estimate=impact,
            confidence=0.85,
            is_recurring=True,
        ))

    # Payday effects — 1st and 15th of each month
    for month in range(1, 13):
        for day in (1, 15):
            try:
                d = date(year, month, day)
            except ValueError:
                continue
            events.append(ExternalEvent(
                location_id=location_id,
                event_date=d,
                event_type="payday",
                name=f"Payday ({d.strftime('%b %d')})",
                impact_estimate=1.08,
                confidence=0.6,
                is_recurring=True,
            ))

    return events


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Find the last occurrence of a weekday in a month."""
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    diff = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=diff)
