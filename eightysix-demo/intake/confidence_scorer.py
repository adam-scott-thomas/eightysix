"""Confidence scoring for the intake pipeline.

Produces a data completeness score (0–100) and per-category confidence ratings.
"""

from __future__ import annotations

from models.canonical import (
    Confidence, ReportType, SheetClassification,
    SalesRecord, LaborRecord, RefundEvent, MenuMixRecord, PunchRecord,
)


# ── Data completeness scoring ─────────────────────────────────────────────

_COMPLETENESS_WEIGHTS = {
    ReportType.SALES_SUMMARY: 20,
    ReportType.SALES_BY_HOUR: 20,  # Alternate to sales_summary
    ReportType.LABOR_SUMMARY: 20,
    ReportType.REFUNDS_VOIDS_COMPS: 20,
    ReportType.MENU_MIX: 15,
    ReportType.PUNCHES: 10,
    ReportType.SCHEDULE: 10,
    ReportType.EMPLOYEE_ROSTER: 5,
}


def data_completeness_score(classifications: list[SheetClassification]) -> int:
    """Score 0–100 based on what report types were recognized."""
    recognized = {c.predicted_type for c in classifications if c.confidence >= 0.4}
    score = 0

    # Sales summary OR sales by hour (not both)
    if ReportType.SALES_SUMMARY in recognized or ReportType.SALES_BY_HOUR in recognized:
        score += 20
    if ReportType.LABOR_SUMMARY in recognized:
        score += 20
    if ReportType.REFUNDS_VOIDS_COMPS in recognized:
        score += 20
    if ReportType.MENU_MIX in recognized:
        score += 15
    if ReportType.PUNCHES in recognized:
        score += 10
    if ReportType.SCHEDULE in recognized:
        score += 10
    # Bonus for employee-linked records
    has_employee_links = any(
        any(m.canonical_field == "employee_id" and m.confidence >= 0.5
            for m in c.column_mappings)
        for c in classifications
    )
    if has_employee_links:
        score += 5

    return min(score, 100)


def completeness_tier(score: int) -> str:
    if score < 40:
        return "insufficient"
    elif score < 65:
        return "limited"
    elif score < 85:
        return "usable"
    else:
        return "strong"


# ── Category confidence ───────────────────────────────────────────────────

def overstaffing_confidence(
    sales: list[SalesRecord],
    labor: list[LaborRecord],
) -> Confidence:
    """Assess confidence for the overstaffing analysis."""
    if not sales or not labor:
        return Confidence.LOW

    has_daily_sales = len(sales) >= 7
    has_daily_labor = len(labor) >= 7
    has_labor_cost = any(r.labor_cost > 0 for r in labor)
    has_labor_hours = any(r.labor_hours > 0 for r in labor)

    if has_daily_sales and has_daily_labor and has_labor_cost:
        return Confidence.HIGH
    elif has_daily_sales and (has_labor_cost or has_labor_hours):
        return Confidence.MEDIUM
    return Confidence.LOW


def refund_abuse_confidence(refunds: list[RefundEvent]) -> Confidence:
    if not refunds:
        return Confidence.LOW

    has_employee = sum(1 for r in refunds if r.employee_id) / len(refunds) > 0.5
    has_enough = len(refunds) >= 20

    if has_employee and has_enough:
        return Confidence.HIGH
    elif has_employee or has_enough:
        return Confidence.MEDIUM
    return Confidence.LOW


def ghost_labor_confidence(
    punches: list[PunchRecord],
    sales: list[SalesRecord],
) -> Confidence:
    if not punches:
        return Confidence.LOW

    has_clock_out = sum(1 for p in punches if p.clock_out) / len(punches) > 0.5
    has_hourly_sales = any(r.hour is not None for r in sales)

    if has_clock_out and has_hourly_sales:
        return Confidence.HIGH
    elif has_clock_out or has_hourly_sales:
        return Confidence.MEDIUM
    return Confidence.LOW


def menu_mix_confidence(records: list[MenuMixRecord]) -> Confidence:
    if not records:
        return Confidence.LOW

    has_margin = sum(1 for r in records if r.estimated_margin is not None or r.food_cost is not None) / len(records) > 0.3
    has_enough_items = len(set(r.item_name for r in records)) >= 5
    has_quantity = sum(1 for r in records if r.quantity_sold > 0) / len(records) > 0.5

    if has_margin and has_enough_items and has_quantity:
        return Confidence.HIGH
    elif has_enough_items and has_quantity:
        return Confidence.MEDIUM
    return Confidence.LOW


def understaffing_confidence(
    sales: list[SalesRecord],
    labor: list[LaborRecord],
) -> Confidence:
    """Understaffing requires hourly granularity to be credible."""
    has_hourly_sales = any(r.hour is not None for r in sales)
    has_labor = len(labor) >= 7

    if has_hourly_sales and has_labor:
        return Confidence.MEDIUM  # Still medium — estimating lost revenue is inherently uncertain
    elif has_hourly_sales or has_labor:
        return Confidence.LOW
    return Confidence.LOW


def overall_confidence(
    category_results: list[tuple[str, float, Confidence]],
) -> Confidence:
    """Weighted overall confidence based on each category's share of total leakage."""
    if not category_results:
        return Confidence.LOW

    total = sum(amount for _, amount, _ in category_results)
    if total <= 0:
        return Confidence.LOW

    conf_values = {"high": 3, "medium": 2, "low": 1}
    weighted_sum = sum(
        (amount / total) * conf_values[conf.value]
        for _, amount, conf in category_results
    )

    if weighted_sum >= 2.5:
        return Confidence.HIGH
    elif weighted_sum >= 1.5:
        return Confidence.MEDIUM
    return Confidence.LOW
