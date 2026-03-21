"""Rule 2: Labor leakage detection."""
from dataclasses import dataclass

from app.rules.thresholds import LaborThresholds, DEFAULT_THRESHOLDS


@dataclass
class LaborResult:
    labor_cost_estimate: float
    sales_per_labor_hour: float
    labor_cost_ratio: float
    severity: str  # healthy, warning, critical
    alert_message: str | None = None


def evaluate_labor(
    total_labor_hours: float,
    total_labor_cost: float,
    revenue_today: float,
    thresholds: LaborThresholds | None = None,
) -> LaborResult:
    t = thresholds or DEFAULT_THRESHOLDS.labor

    if revenue_today <= 0:
        return LaborResult(
            labor_cost_estimate=round(total_labor_cost, 2),
            sales_per_labor_hour=0,
            labor_cost_ratio=1.0 if total_labor_cost > 0 else 0,
            severity="critical" if total_labor_cost > 0 else "healthy",
            alert_message="No revenue recorded but labor costs accruing" if total_labor_cost > 0 else None,
        )

    splh = revenue_today / total_labor_hours if total_labor_hours > 0 else 0
    lcr = total_labor_cost / revenue_today

    if lcr > t.warning_ratio:
        severity = "critical"
        msg = f"Labor cost running at {lcr:.0%} of revenue"
    elif lcr > t.healthy_ratio:
        severity = "warning"
        msg = f"Labor cost running at {lcr:.0%} of revenue"
    else:
        severity = "healthy"
        msg = None

    return LaborResult(
        labor_cost_estimate=round(total_labor_cost, 2),
        sales_per_labor_hour=round(splh, 2),
        labor_cost_ratio=round(lcr, 4),
        severity=severity,
        alert_message=msg,
    )
