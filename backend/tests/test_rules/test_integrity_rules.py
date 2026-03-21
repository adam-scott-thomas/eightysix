"""Tests for integrity rules — pure unit tests, no DB or async."""
from app.rules.integrity_rules import evaluate_punch_integrity, evaluate_ghost_shift


def test_clean_punch():
    # All clean: geofence_match=True, known device, no staff discrepancy
    # score = 0.0, severity = "none"
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="John Doe",
        geofence_match=True,
        device_fingerprint="DEV-001",
        known_device_fingerprints=["DEV-001"],
        ip_address="192.168.1.1",
        geo_lat=42.33,
        geo_lng=-83.05,
        active_shift_count=5,
        manager_reported_count=5,
    )
    assert result.severity == "none"
    assert result.fraud_risk_score == 0.0
    assert result.geofence_violation is False
    assert result.device_mismatch is False
    assert result.staff_discrepancy is False


def test_geofence_violation_only():
    # geofence_match=False → +0.5 score → > 0.5 → "review"
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="Jane Doe",
        geofence_match=False,
        device_fingerprint="DEV-001",
        known_device_fingerprints=["DEV-001"],
        ip_address="192.168.1.1",
        geo_lat=42.33,
        geo_lng=-83.05,
        active_shift_count=5,
        manager_reported_count=5,
    )
    assert result.geofence_violation is True
    assert result.device_mismatch is False
    assert result.fraud_risk_score == 0.5
    # 0.5 is NOT > 0.5, so severity is "none"
    assert result.severity == "none"


def test_geofence_and_device_mismatch():
    # geofence_match=False → +0.5, unknown device → +0.3 = 0.8
    # 0.8 is NOT > 0.8, so severity = "review" (since 0.8 > 0.5)
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="Jane Doe",
        geofence_match=False,
        device_fingerprint="UNKNOWN-X",
        known_device_fingerprints=["DEV-001", "DEV-002"],
        ip_address="203.0.113.50",
        geo_lat=37.77,
        geo_lng=-122.42,
        active_shift_count=5,
        manager_reported_count=5,
    )
    assert result.fraud_risk_score == 0.8
    assert result.severity == "review"  # 0.8 > 0.5 but NOT > 0.8
    assert result.geofence_violation is True
    assert result.device_mismatch is True


def test_all_flags_high_severity():
    # geofence +0.5, device +0.3, staff discrepancy +0.2 = 1.0 → > 0.8 → "high"
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="Jane Doe",
        geofence_match=False,
        device_fingerprint="UNKNOWN-X",
        known_device_fingerprints=["DEV-001"],
        ip_address="203.0.113.50",
        geo_lat=37.77,
        geo_lng=-122.42,
        active_shift_count=5,
        manager_reported_count=3,
    )
    assert result.fraud_risk_score == 1.0
    assert result.severity == "high"
    assert result.geofence_violation is True
    assert result.device_mismatch is True
    assert result.staff_discrepancy is True


def test_device_mismatch_only():
    # Unknown device → +0.3 score. 0.3 is NOT > 0.5 → "none"
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="Bob Smith",
        geofence_match=True,
        device_fingerprint="UNKNOWN-X",
        known_device_fingerprints=["DEV-001"],
        ip_address="192.168.1.1",
        geo_lat=42.33,
        geo_lng=-83.05,
        active_shift_count=5,
        manager_reported_count=5,
    )
    assert result.device_mismatch is True
    assert result.fraud_risk_score == 0.3
    assert result.severity == "none"


def test_staff_discrepancy_only():
    # staff discrepancy → +0.2 score. 0.2 is NOT > 0.5 → "none"
    result = evaluate_punch_integrity(
        shift_id="s1",
        employee_id="e1",
        employee_name="Bob Smith",
        geofence_match=True,
        device_fingerprint="DEV-001",
        known_device_fingerprints=["DEV-001"],
        ip_address="192.168.1.1",
        geo_lat=42.33,
        geo_lng=-83.05,
        active_shift_count=5,
        manager_reported_count=3,
    )
    assert result.staff_discrepancy is True
    assert result.fraud_risk_score == 0.2
    assert result.severity == "none"


def test_ghost_shift_detected():
    # 0 orders, 8h shift, no manager confirmation → flagged
    result = evaluate_ghost_shift(
        shift_id="s1",
        employee_id="e1",
        employee_name="Tyler Reed",
        orders_by_employee=0,
        shift_hours=8.0,
        has_manager_confirmation=False,
    )
    assert result is not None
    assert result.flag_type == "ghost_shift"
    assert result.fraud_risk_score >= 0.5
    # 8h >= 4h so score = 0.7
    assert result.fraud_risk_score == 0.7
    assert result.severity == "review"


def test_ghost_shift_short_shift_flagged():
    # 0 orders, 2h shift (>= 1h), no manager → flagged with score=0.5
    result = evaluate_ghost_shift(
        shift_id="s1",
        employee_id="e1",
        employee_name="Tyler Reed",
        orders_by_employee=0,
        shift_hours=2.0,
        has_manager_confirmation=False,
    )
    assert result is not None
    assert result.fraud_risk_score == 0.5


def test_ghost_shift_very_short_not_flagged():
    # 0 orders, 0.5h shift (< 1h) → not flagged
    result = evaluate_ghost_shift(
        shift_id="s1",
        employee_id="e1",
        employee_name="Tyler Reed",
        orders_by_employee=0,
        shift_hours=0.5,
        has_manager_confirmation=False,
    )
    assert result is None


def test_ghost_shift_not_flagged_with_orders():
    result = evaluate_ghost_shift(
        shift_id="s1",
        employee_id="e1",
        employee_name="Tyler Reed",
        orders_by_employee=5,
        shift_hours=8.0,
        has_manager_confirmation=False,
    )
    assert result is None


def test_ghost_shift_not_flagged_with_manager_confirmation():
    result = evaluate_ghost_shift(
        shift_id="s1",
        employee_id="e1",
        employee_name="Tyler Reed",
        orders_by_employee=0,
        shift_hours=8.0,
        has_manager_confirmation=True,
    )
    assert result is None
