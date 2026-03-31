"""Detect the date range covered by extracted records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from models.canonical import SalesRecord, LaborRecord, RefundEvent, MenuMixRecord, PunchRecord


@dataclass
class DateRange:
    start: date
    end: date
    days_covered: int
    gaps: list[tuple[date, date]]  # Contiguous missing ranges

    @property
    def total_span_days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def coverage_ratio(self) -> float:
        if self.total_span_days == 0:
            return 0.0
        return self.days_covered / self.total_span_days

    @property
    def can_annualize(self) -> bool:
        return self.days_covered >= 30


def detect_date_range(
    sales: list[SalesRecord] | None = None,
    labor: list[LaborRecord] | None = None,
    refunds: list[RefundEvent] | None = None,
    menu_mix: list[MenuMixRecord] | None = None,
    punches: list[PunchRecord] | None = None,
) -> Optional[DateRange]:
    """Determine the date range covered across all record types."""
    all_dates: set[date] = set()

    if sales:
        all_dates.update(r.date for r in sales)
    if labor:
        all_dates.update(r.date for r in labor)
    if refunds:
        all_dates.update(r.timestamp.date() for r in refunds)
    if menu_mix:
        all_dates.update(r.date for r in menu_mix if r.date.year > 1971)
    if punches:
        all_dates.update(r.clock_in.date() for r in punches)

    if not all_dates:
        return None

    sorted_dates = sorted(all_dates)
    start = sorted_dates[0]
    end = sorted_dates[-1]

    # Find gaps (missing days)
    gaps: list[tuple[date, date]] = []
    all_days = set()
    current = start
    from datetime import timedelta
    while current <= end:
        all_days.add(current)
        current += timedelta(days=1)

    missing = sorted(all_days - all_dates)
    if missing:
        gap_start = missing[0]
        gap_end = missing[0]
        for d in missing[1:]:
            if (d - gap_end).days == 1:
                gap_end = d
            else:
                gaps.append((gap_start, gap_end))
                gap_start = d
                gap_end = d
        gaps.append((gap_start, gap_end))

    return DateRange(
        start=start,
        end=end,
        days_covered=len(all_dates),
        gaps=gaps,
    )
