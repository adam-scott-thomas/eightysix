"""Leakage Category 5: Understaffing with revenue loss.

Detect likely lost revenue when sales spikes coincide with weak staffing.
Only included when hourly granularity exists.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from models.canonical import SalesRecord, LaborRecord, Confidence
from models.results import UnderstaffingResult


# If throughput drops >15% during peak vs. similar peak with better staffing, flag
THROUGHPUT_DROP_THRESHOLD = 0.15


def analyze_understaffing(
    sales: list[SalesRecord],
    labor: list[LaborRecord],
    confidence: Confidence = Confidence.LOW,
) -> UnderstaffingResult:
    """Detect understaffing-driven revenue loss. Requires hourly sales data."""

    hourly_sales = [s for s in sales if s.hour is not None]
    if not hourly_sales:
        return UnderstaffingResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="No hourly sales data available. Cannot assess understaffing impact.",
        )

    # Build peak-hour profile per weekday
    # Peak hours = hours that typically do >15% of daily sales
    daily_totals: dict[date, float] = defaultdict(float)
    hourly_data: dict[date, dict[int, float]] = defaultdict(lambda: defaultdict(float))

    for s in hourly_sales:
        daily_totals[s.date] += s.net_sales or s.gross_sales
        hourly_data[s.date][s.hour] += s.net_sales or s.gross_sales

    if not daily_totals:
        return UnderstaffingResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="Insufficient hourly sales data for understaffing analysis.",
        )

    # Group by weekday
    weekday_profiles: dict[int, list[dict[int, float]]] = defaultdict(list)
    for d, hours_map in hourly_data.items():
        weekday_profiles[d.weekday()].append(dict(hours_map))

    # For each weekday, find the "good" days (top quartile by total sales)
    # and "bad" days (bottom quartile) — compare peak-hour throughput
    labor_by_date: dict[date, float] = defaultdict(float)
    for l in labor:
        labor_by_date[l.date] += l.labor_hours

    evidence: list[dict] = []
    total_lost = 0.0
    lost_days = 0
    peak_hours_affected: set[int] = set()

    for weekday, profiles in weekday_profiles.items():
        if len(profiles) < 4:
            continue

        # Sort days by total sales
        day_totals = []
        for d in sorted(hourly_data.keys()):
            if d.weekday() == weekday:
                day_totals.append((d, daily_totals[d]))
        day_totals.sort(key=lambda x: x[1])

        # Top quartile = "good" days, bottom quartile = "weak" days
        q = max(1, len(day_totals) // 4)
        weak_days = day_totals[:q]
        good_days = day_totals[-q:]

        good_avg_total = sum(t for _, t in good_days) / len(good_days)
        if good_avg_total <= 0:
            continue

        # Compare peak-hour performance
        for d, total in weak_days:
            labor_hrs = labor_by_date.get(d, 0)
            good_avg_labor = sum(labor_by_date.get(gd, 0) for gd, _ in good_days) / len(good_days) if good_days else 0

            if good_avg_labor > 0 and labor_hrs < good_avg_labor * 0.75:
                # Understaffed: <75% of good-day labor
                drop = (good_avg_total - total) / good_avg_total
                if drop > THROUGHPUT_DROP_THRESHOLD:
                    estimated_lost = good_avg_total - total
                    total_lost += estimated_lost
                    lost_days += 1

                    # Find which hours underperformed
                    for h, h_sales in hourly_data[d].items():
                        good_h_avg = sum(
                            hourly_data.get(gd, {}).get(h, 0)
                            for gd, _ in good_days
                        ) / len(good_days)
                        if good_h_avg > 0 and h_sales < good_h_avg * 0.7:
                            peak_hours_affected.add(h)

                    evidence.append({
                        "date": str(d),
                        "daily_sales": round(total, 2),
                        "good_day_avg": round(good_avg_total, 2),
                        "throughput_drop": round(drop, 4),
                        "labor_hours": round(labor_hrs, 2),
                        "good_day_avg_labor": round(good_avg_labor, 2),
                        "estimated_lost_revenue": round(estimated_lost, 2),
                    })

    return UnderstaffingResult(
        estimated_annual_impact=total_lost,
        observed_impact=total_lost,
        confidence=confidence,
        explanation=(
            f"Found {lost_days} day(s) where understaffing likely reduced revenue. "
            f"Estimated lost revenue: ${total_lost:,.0f}."
            if total_lost > 0 else
            "No clear understaffing-driven revenue loss detected."
        ),
        evidence=evidence[:20],
        lost_revenue_days=lost_days,
        avg_throughput_drop_pct=(
            sum(e["throughput_drop"] for e in evidence) / len(evidence)
            if evidence else 0.0
        ),
        peak_hours_affected=[f"{h}:00" for h in sorted(peak_hours_affected)],
    )
