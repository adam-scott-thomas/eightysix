"""Rule 6: Possible remote punch-in / integrity checks."""
from dataclasses import dataclass

from app.rules.thresholds import IntegrityThresholds, DEFAULT_THRESHOLDS


@dataclass
class IntegrityCheckResult:
    shift_id: str
    employee_id: str
    employee_name: str
    fraud_risk_score: float
    geofence_violation: bool
    device_mismatch: bool
    staff_discrepancy: bool
    severity: str  # none, review, high
    flag_type: str  # remote_punch, ghost_shift, device_mismatch, staff_discrepancy
    evidence: dict
    title: str
    message: str | None = None


def evaluate_punch_integrity(
    shift_id: str,
    employee_id: str,
    employee_name: str,
    geofence_match: bool | None,
    device_fingerprint: str | None,
    known_device_fingerprints: list[str],
    ip_address: str | None,
    geo_lat: float | None,
    geo_lng: float | None,
    active_shift_count: int,
    manager_reported_count: int | None,
    thresholds: IntegrityThresholds | None = None,
) -> IntegrityCheckResult:
    t = thresholds or DEFAULT_THRESHOLDS.integrity

    geofence_violation = geofence_match is False
    device_mismatch = (
        device_fingerprint is not None
        and device_fingerprint not in known_device_fingerprints
    )
    staff_discrepancy = (
        manager_reported_count is not None
        and abs(active_shift_count - manager_reported_count) > 0
    )

    # Composite fraud risk score
    score = 0.0
    if geofence_violation:
        score += t.geofence_weight
    if device_mismatch:
        score += t.device_mismatch_weight
    if staff_discrepancy:
        score += t.staff_discrepancy_weight

    # Determine severity
    if score > t.high_confidence_score:
        severity = "high"
    elif score > t.review_score:
        severity = "review"
    else:
        severity = "none"

    # Determine flag type
    if geofence_violation:
        flag_type = "remote_punch"
    elif device_mismatch:
        flag_type = "device_mismatch"
    elif staff_discrepancy:
        flag_type = "staff_discrepancy"
    else:
        flag_type = "remote_punch"

    # Build evidence
    evidence = {
        "geofence_match": geofence_match,
        "ip_address": ip_address,
        "device_known": not device_mismatch if device_fingerprint else None,
        "device_fingerprint": device_fingerprint,
        "geo_lat": geo_lat,
        "geo_lng": geo_lng,
        "staff_discrepancy": abs(active_shift_count - (manager_reported_count or active_shift_count)),
        "active_shift_count": active_shift_count,
        "manager_reported_count": manager_reported_count,
    }

    title = f"Suspicious punch-in: {employee_name}"
    message = None
    if severity != "none":
        parts = []
        if geofence_violation:
            parts.append("clock-in outside geofence")
        if device_mismatch:
            parts.append("unrecognized device")
        if staff_discrepancy:
            parts.append(f"staff count mismatch ({active_shift_count} active vs {manager_reported_count} reported)")
        message = f"Review suspicious punch — {', '.join(parts)}"

    return IntegrityCheckResult(
        shift_id=shift_id,
        employee_id=employee_id,
        employee_name=employee_name,
        fraud_risk_score=round(score, 2),
        geofence_violation=geofence_violation,
        device_mismatch=device_mismatch,
        staff_discrepancy=staff_discrepancy,
        severity=severity,
        flag_type=flag_type,
        evidence=evidence,
        title=title,
        message=message,
    )


def evaluate_ghost_shift(
    shift_id: str,
    employee_id: str,
    employee_name: str,
    orders_by_employee: int,
    shift_hours: float,
    has_manager_confirmation: bool,
) -> IntegrityCheckResult | None:
    """Flag shifts with no associated orders and no manager confirmation."""
    if orders_by_employee > 0 or has_manager_confirmation:
        return None

    if shift_hours < 1.0:
        return None

    score = 0.7 if shift_hours >= 4.0 else 0.5
    severity = "review" if score >= 0.5 else "none"

    return IntegrityCheckResult(
        shift_id=shift_id,
        employee_id=employee_id,
        employee_name=employee_name,
        fraud_risk_score=score,
        geofence_violation=False,
        device_mismatch=False,
        staff_discrepancy=False,
        severity=severity,
        flag_type="ghost_shift",
        evidence={
            "orders_during_shift": orders_by_employee,
            "shift_hours": round(shift_hours, 2),
            "manager_confirmation": has_manager_confirmation,
        },
        title=f"Ghost shift: {employee_name}",
        message=f"{employee_name} clocked {shift_hours:.1f}h with 0 orders and no manager confirmation",
    )
