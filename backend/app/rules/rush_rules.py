"""Rule 5: Rush / bottleneck detection."""
from dataclasses import dataclass

from app.rules.thresholds import RushThresholds, DEFAULT_THRESHOLDS


@dataclass
class RushResult:
    order_velocity: float  # orders/hour based on 30min window
    avg_prep_time: float  # seconds
    prep_time_trend: str  # rising, stable, falling
    prep_time_change_pct: float
    backlog_risk: float
    severity: str  # normal, warning, critical
    alert_message: str | None = None
    recommendation: str | None = None


def evaluate_rush(
    orders_in_window: int,
    window_minutes: float,
    avg_prep_time_seconds: float,
    prior_avg_prep_time_seconds: float | None,
    active_kitchen_staff: int,
    top_seller_name: str | None = None,
    thresholds: RushThresholds | None = None,
) -> RushResult:
    t = thresholds or DEFAULT_THRESHOLDS.rush

    # Annualize to hourly rate
    if window_minutes > 0:
        order_velocity = (orders_in_window / window_minutes) * 60
    else:
        order_velocity = 0

    # Prep time trend
    if prior_avg_prep_time_seconds and prior_avg_prep_time_seconds > 0:
        change_pct = (avg_prep_time_seconds - prior_avg_prep_time_seconds) / prior_avg_prep_time_seconds
    else:
        change_pct = 0

    if change_pct > t.prep_time_rise_alert_pct:
        trend = "rising"
    elif change_pct < -t.prep_time_rise_alert_pct:
        trend = "falling"
    else:
        trend = "stable"

    # Backlog risk
    if active_kitchen_staff > 0 and avg_prep_time_seconds > 0:
        backlog_risk = (order_velocity * avg_prep_time_seconds) / (active_kitchen_staff * 3600)
    else:
        backlog_risk = 0 if order_velocity == 0 else 1.0

    # Severity
    messages = []
    rec = None

    if backlog_risk > t.backlog_risk_critical:
        severity = "critical"
        messages.append(f"Rush critical — backlog risk at {backlog_risk:.2f}")
        if top_seller_name:
            rec = f"Prep more {top_seller_name} now and add 1 kitchen support"
        else:
            rec = "Add 1 kitchen support immediately"
    elif backlog_risk > t.backlog_risk_warning:
        severity = "warning"
        messages.append("Rush incoming — backlog building")
        rec = "Add 1 kitchen support"
    else:
        severity = "normal"

    if trend == "rising" and change_pct > t.prep_time_rise_alert_pct:
        if severity == "normal":
            severity = "warning"
        messages.append(f"Prep times rising {change_pct:.0%} over prior window")

    return RushResult(
        order_velocity=round(order_velocity, 1),
        avg_prep_time=round(avg_prep_time_seconds, 1),
        prep_time_trend=trend,
        prep_time_change_pct=round(change_pct, 4),
        backlog_risk=round(backlog_risk, 4),
        severity=severity,
        alert_message="; ".join(messages) if messages else None,
        recommendation=rec,
    )
