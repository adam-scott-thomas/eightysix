"""Rule 1: Overstaffed / understaffed detection."""
from dataclasses import dataclass

from app.rules.thresholds import StaffingThresholds, DEFAULT_THRESHOLDS


@dataclass
class StaffingResult:
    orders_per_labor_hour: float
    staffing_pressure: str  # critical_understaffed, understaffed, balanced, overstaffed, critical_overstaffed
    active_staff: int
    orders_in_window: int
    recommendation: str | None = None
    confidence: float = 0.0
    estimated_impact: str | None = None


def evaluate_staffing(
    orders_in_window: int,
    active_staff: int,
    window_hours: float = 2.0,
    thresholds: StaffingThresholds | None = None,
) -> StaffingResult:
    t = thresholds or DEFAULT_THRESHOLDS.staffing

    if active_staff == 0:
        return StaffingResult(
            orders_per_labor_hour=float(orders_in_window) / window_hours if window_hours > 0 else 0,
            staffing_pressure="critical_understaffed",
            active_staff=0,
            orders_in_window=orders_in_window,
            recommendation="No staff on shift — immediate staffing needed",
            confidence=1.0,
            estimated_impact="All orders unattended",
        )

    oplh = orders_in_window / (active_staff * window_hours) if window_hours > 0 else 0

    if oplh > t.critical_understaffed_oplh:
        pressure = "critical_understaffed"
        needed = max(1, round(orders_in_window / (t.balanced_upper_oplh * window_hours)) - active_staff)
        rec = f"Add {needed} staff immediately"
        confidence = min(1.0, (oplh - t.critical_understaffed_oplh) / 5 + 0.8)
        impact = f"Orders per labor hour at {oplh:.1f}, target is {t.balanced_upper_oplh:.0f}"
    elif oplh > t.understaffed_oplh:
        pressure = "understaffed"
        rec = "Add 1 staff"
        confidence = 0.7
        impact = f"Orders per labor hour at {oplh:.1f}, approaching critical"
    elif oplh >= t.balanced_lower_oplh:
        pressure = "balanced"
        rec = None
        confidence = 0.0
        impact = None
    elif oplh >= t.critical_overstaffed_oplh:
        pressure = "overstaffed"
        excess = max(1, active_staff - round(orders_in_window / (t.balanced_lower_oplh * window_hours)))
        rec = f"Reduce floor staffing by {excess}"
        confidence = 0.6
        impact = f"Orders per labor hour at {oplh:.1f}, staff underutilized"
    else:
        pressure = "critical_overstaffed"
        excess = max(1, active_staff - round(orders_in_window / (t.balanced_lower_oplh * window_hours)))
        rec = f"Reduce floor staffing by {excess}"
        confidence = min(1.0, (t.critical_overstaffed_oplh - oplh) / 2 + 0.8)
        impact = f"Orders per labor hour at {oplh:.1f}, severe overstaffing"

    return StaffingResult(
        orders_per_labor_hour=round(oplh, 2),
        staffing_pressure=pressure,
        active_staff=active_staff,
        orders_in_window=orders_in_window,
        recommendation=rec,
        confidence=round(confidence, 2),
        estimated_impact=impact,
    )
