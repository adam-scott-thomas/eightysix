"""Leakage Category 1: Overstaffing detection.

Detect days/shifts where labor cost is disproportionate to sales volume.

Core: actual_labor_pct vs target → excess × sales = estimated leakage.
Also uses intra-restaurant baseline (similar weekdays, same dayparts).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from models.canonical import SalesRecord, LaborRecord, Confidence
from models.results import OverstaffingResult


# Default target: 28% labor cost ratio
DEFAULT_TARGET_LABOR_PCT = 0.28


def analyze_overstaffing(
    sales: list[SalesRecord],
    labor: list[LaborRecord],
    target_labor_pct: float = DEFAULT_TARGET_LABOR_PCT,
    confidence: Confidence = Confidence.MEDIUM,
) -> OverstaffingResult:
    """Detect overstaffing by comparing labor cost ratio to target and internal baseline."""

    # Aggregate by date
    sales_by_date: dict[date, float] = defaultdict(float)
    labor_by_date: dict[date, float] = defaultdict(float)

    for s in sales:
        sales_by_date[s.date] += s.net_sales or s.gross_sales
    for l in labor:
        labor_by_date[l.date] += l.labor_cost

    # Find days with both sales and labor data
    common_dates = sorted(set(sales_by_date) & set(labor_by_date))
    if not common_dates:
        return OverstaffingResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="Insufficient overlapping sales and labor data.",
        )

    # Compute per-day excess
    total_excess = 0.0
    excess_days = 0
    excess_pcts: list[float] = []
    worst_day = ""
    worst_excess = 0.0

    # Also compute intra-restaurant baseline (peer comparison by weekday)
    weekday_ratios: dict[int, list[float]] = defaultdict(list)

    for d in common_dates:
        day_sales = sales_by_date[d]
        day_labor = labor_by_date[d]

        if day_sales <= 0:
            continue

        ratio = day_labor / day_sales
        weekday_ratios[d.weekday()].append(ratio)

    # Compute weekday baseline (median ratio per weekday)
    weekday_baseline: dict[int, float] = {}
    for wd, ratios in weekday_ratios.items():
        sorted_ratios = sorted(ratios)
        mid = len(sorted_ratios) // 2
        weekday_baseline[wd] = sorted_ratios[mid]

    # Now compute excess using both fixed target and weekday baseline
    evidence: list[dict] = []

    for d in common_dates:
        day_sales = sales_by_date[d]
        day_labor = labor_by_date[d]

        if day_sales <= 0:
            continue

        actual_pct = day_labor / day_sales
        baseline = min(target_labor_pct, weekday_baseline.get(d.weekday(), target_labor_pct))
        excess_pct = max(0.0, actual_pct - baseline)

        if excess_pct > 0:
            excess = day_sales * excess_pct
            total_excess += excess
            excess_days += 1
            excess_pcts.append(excess_pct)

            if excess > worst_excess:
                worst_excess = excess
                worst_day = str(d)

            evidence.append({
                "date": str(d),
                "sales": round(day_sales, 2),
                "labor_cost": round(day_labor, 2),
                "actual_labor_pct": round(actual_pct, 4),
                "baseline_pct": round(baseline, 4),
                "excess_pct": round(excess_pct, 4),
                "excess_dollars": round(excess, 2),
            })

    avg_excess_pct = sum(excess_pcts) / len(excess_pcts) if excess_pcts else 0.0

    return OverstaffingResult(
        estimated_annual_impact=total_excess,  # Annualized later by aggregator
        observed_impact=total_excess,
        confidence=confidence,
        explanation=(
            f"Found {excess_days} days where labor cost exceeded baseline. "
            f"Average excess: {avg_excess_pct:.1%}. "
            f"Total observed overstaffing leakage: ${total_excess:,.0f}."
        ),
        evidence=evidence[:20],  # Cap evidence for readability
        excess_labor_days=excess_days,
        avg_excess_pct=avg_excess_pct,
        worst_day=worst_day,
        worst_day_excess=worst_excess,
    )
