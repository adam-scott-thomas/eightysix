"""Leakage Category 3: Ghost / low-productivity labor detection.

Detect paid labor blocks with weak sales alignment:
- Shifts with near-zero sales during the hours worked
- Long paid presence with minimal output
- Suspicious clock patterns
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from models.canonical import PunchRecord, SalesRecord, LaborRecord, Confidence
from models.results import GhostLaborResult


# Default loaded hourly labor cost when actual wage unknown
DEFAULT_HOURLY_COST = 16.00

# Threshold: if an employee's hours have < this ratio of expected sales per labor hour, flag
LOW_PRODUCTIVITY_THRESHOLD = 0.15  # 15% of average sales-per-labor-hour


def analyze_ghost_labor(
    punches: list[PunchRecord],
    sales: list[SalesRecord],
    labor: list[LaborRecord],
    confidence: Confidence = Confidence.MEDIUM,
    default_hourly_cost: float = DEFAULT_HOURLY_COST,
) -> GhostLaborResult:
    """Detect ghost shifts and low-productivity labor."""

    if not punches:
        # Fall back to labor records if available
        return _analyze_from_labor_records(labor, sales, confidence, default_hourly_cost)

    # Build hourly sales map — if no hourly data, fall back to labor-record analysis
    hourly_sales = _build_hourly_sales(sales)
    if not hourly_sales:
        return _analyze_from_labor_records(labor, sales, confidence, default_hourly_cost)
    daily_sales: dict[date, float] = defaultdict(float)
    for s in sales:
        daily_sales[s.date] += s.net_sales or s.gross_sales

    suspect_shifts: list[dict] = []
    total_suspect_hours = 0.0
    total_suspect_cost = 0.0

    for punch in punches:
        if punch.clock_out is None:
            continue

        hours = (punch.clock_out - punch.clock_in).total_seconds() / 3600.0
        if hours < 0.5:
            continue  # Ignore very short shifts

        punch_date = punch.clock_in.date()

        # Check if there were sales during this employee's shift hours
        shift_sales = _sales_during_shift(
            hourly_sales, punch_date,
            punch.clock_in.hour, punch.clock_out.hour
        )
        day_total_sales = daily_sales.get(punch_date, 0.0)

        # Estimate expected productivity
        # If we have total daily labor hours, compute avg sales per labor hour
        daily_labor_hrs = sum(
            l.labor_hours for l in labor if l.date == punch_date
        )
        if daily_labor_hrs > 0 and day_total_sales > 0:
            avg_splh = day_total_sales / daily_labor_hrs
            expected_sales = avg_splh * hours
            if shift_sales < expected_sales * LOW_PRODUCTIVITY_THRESHOLD:
                cost = hours * default_hourly_cost
                suspect_shifts.append({
                    "employee_id": punch.employee_id,
                    "date": str(punch_date),
                    "clock_in": str(punch.clock_in),
                    "clock_out": str(punch.clock_out),
                    "hours": round(hours, 2),
                    "shift_sales": round(shift_sales, 2),
                    "expected_sales": round(expected_sales, 2),
                    "estimated_cost": round(cost, 2),
                })
                total_suspect_hours += hours
                total_suspect_cost += cost
        elif shift_sales == 0 and hours >= 4 and hourly_sales:
            # Only flag if we actually HAVE hourly sales data and this shift had zero
            cost = hours * default_hourly_cost
            suspect_shifts.append({
                "employee_id": punch.employee_id,
                "date": str(punch_date),
                "clock_in": str(punch.clock_in),
                "clock_out": str(punch.clock_out),
                "hours": round(hours, 2),
                "shift_sales": 0.0,
                "note": "zero sales during shift hours",
                "estimated_cost": round(cost, 2),
            })
            total_suspect_hours += hours
            total_suspect_cost += cost

    if not suspect_shifts:
        return GhostLaborResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=confidence,
            explanation="No ghost or low-productivity shifts detected.",
        )

    return GhostLaborResult(
        estimated_annual_impact=total_suspect_cost,
        observed_impact=total_suspect_cost,
        confidence=confidence,
        explanation=(
            f"Found {len(suspect_shifts)} suspect shift(s) totaling "
            f"{total_suspect_hours:.1f} hours and ~${total_suspect_cost:,.0f} in labor cost "
            f"with minimal or zero corresponding sales."
        ),
        evidence=suspect_shifts[:20],
        suspect_shifts=len(suspect_shifts),
        total_suspect_hours=total_suspect_hours,
        total_suspect_cost=total_suspect_cost,
    )


def _analyze_from_labor_records(
    labor: list[LaborRecord],
    sales: list[SalesRecord],
    confidence: Confidence,
    default_hourly_cost: float,
) -> GhostLaborResult:
    """Fallback: detect ghost labor from aggregated labor + sales records (no punch data)."""
    if not labor or not sales:
        return GhostLaborResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="No punch or labor data available for ghost labor analysis.",
        )

    # Compare scheduled vs actual hours if available
    days_with_excess: list[dict] = []
    total_excess_cost = 0.0

    labor_by_date: dict[date, float] = defaultdict(float)
    scheduled_by_date: dict[date, float] = defaultdict(float)
    sales_by_date: dict[date, float] = defaultdict(float)

    for l in labor:
        labor_by_date[l.date] += l.labor_hours
        if l.scheduled_hours:
            scheduled_by_date[l.date] += l.scheduled_hours
    for s in sales:
        sales_by_date[s.date] += s.net_sales or s.gross_sales

    for d in sorted(set(labor_by_date) & set(sales_by_date)):
        actual = labor_by_date[d]
        scheduled = scheduled_by_date.get(d, 0.0)
        day_sales = sales_by_date[d]

        if day_sales <= 0 and actual > 2:
            # Labor on a zero-sales day
            cost = actual * default_hourly_cost
            days_with_excess.append({
                "date": str(d),
                "actual_hours": round(actual, 2),
                "sales": 0.0,
                "estimated_cost": round(cost, 2),
                "note": "labor on zero-sales day",
            })
            total_excess_cost += cost
        elif scheduled > 0 and actual > scheduled * 1.3:
            # >30% over scheduled
            excess_hours = actual - scheduled
            cost = excess_hours * default_hourly_cost
            days_with_excess.append({
                "date": str(d),
                "actual_hours": round(actual, 2),
                "scheduled_hours": round(scheduled, 2),
                "excess_hours": round(excess_hours, 2),
                "estimated_cost": round(cost, 2),
            })
            total_excess_cost += cost

    return GhostLaborResult(
        estimated_annual_impact=total_excess_cost,
        observed_impact=total_excess_cost,
        confidence=Confidence.LOW if not days_with_excess else confidence,
        explanation=(
            f"Found {len(days_with_excess)} day(s) with suspected ghost/excess labor, "
            f"estimated cost: ${total_excess_cost:,.0f}."
            if days_with_excess else
            "No ghost labor patterns detected from available data."
        ),
        evidence=days_with_excess[:20],
        suspect_shifts=len(days_with_excess),
        total_suspect_hours=sum(d.get("excess_hours", d.get("actual_hours", 0)) for d in days_with_excess),
        total_suspect_cost=total_excess_cost,
    )


def _build_hourly_sales(sales: list[SalesRecord]) -> dict[tuple[date, int], float]:
    """Build {(date, hour): sales} map from hourly sales records."""
    result: dict[tuple[date, int], float] = {}
    for s in sales:
        if s.hour is not None:
            key = (s.date, s.hour)
            result[key] = result.get(key, 0.0) + (s.net_sales or s.gross_sales)
    return result


def _sales_during_shift(
    hourly_sales: dict[tuple[date, int], float],
    shift_date: date,
    start_hour: int,
    end_hour: int,
) -> float:
    """Sum sales during a shift's hours."""
    if not hourly_sales:
        return 0.0  # Can't determine — return 0 (will be noted as low-confidence)

    total = 0.0
    for h in range(start_hour, min(end_hour + 1, 24)):
        total += hourly_sales.get((shift_date, h), 0.0)
    return total
