"""Tests for staffing rules — pure unit tests, no DB or async."""
from app.rules.staffing_rules import evaluate_staffing


def test_balanced_staffing():
    # 16 / (2 * 2.0) = 4.0 OPLH — exactly at balanced_lower_oplh (>= 4)
    result = evaluate_staffing(orders_in_window=16, active_staff=2, window_hours=2.0)
    assert result.staffing_pressure == "balanced"
    assert result.orders_per_labor_hour == 4.0
    assert result.recommendation is None
    assert result.confidence == 0.0


def test_critical_understaffed():
    # 40 / (1 * 2.0) = 20.0 OPLH — > 15 threshold
    result = evaluate_staffing(orders_in_window=40, active_staff=1, window_hours=2.0)
    assert result.staffing_pressure == "critical_understaffed"
    assert result.orders_per_labor_hour == 20.0
    assert result.recommendation is not None
    assert result.confidence >= 0.8


def test_understaffed():
    # 24 / (1 * 2.0) = 12.0 OPLH — > 10 but <= 15
    result = evaluate_staffing(orders_in_window=24, active_staff=1, window_hours=2.0)
    assert result.staffing_pressure == "understaffed"
    assert result.orders_per_labor_hour == 12.0
    assert result.confidence == 0.7


def test_overstaffed():
    # 20 / (4 * 2.0) = 2.5 OPLH — >= 2 but < 4
    result = evaluate_staffing(orders_in_window=20, active_staff=4, window_hours=2.0)
    assert result.staffing_pressure == "overstaffed"
    assert result.orders_per_labor_hour == 2.5
    assert result.recommendation is not None


def test_critical_overstaffed():
    # 4 / (4 * 2.0) = 0.5 OPLH — < 2
    result = evaluate_staffing(orders_in_window=4, active_staff=4, window_hours=2.0)
    assert result.staffing_pressure == "critical_overstaffed"
    assert result.orders_per_labor_hour == 0.5
    assert result.recommendation is not None
    assert result.confidence >= 0.8


def test_zero_staff():
    result = evaluate_staffing(orders_in_window=10, active_staff=0, window_hours=2.0)
    assert result.staffing_pressure == "critical_understaffed"
    assert result.confidence == 1.0
    assert result.active_staff == 0
    assert result.recommendation == "No staff on shift — immediate staffing needed"


def test_balanced_upper_bound():
    # 18 / (1 * 2.0) = 9.0 OPLH — >= 4 and <= 10, balanced
    result = evaluate_staffing(orders_in_window=18, active_staff=1, window_hours=2.0)
    assert result.staffing_pressure == "balanced"
    assert result.orders_per_labor_hour == 9.0


def test_understaffed_at_boundary():
    # 21 / (1 * 2.0) = 10.5 OPLH — > 10, understaffed
    result = evaluate_staffing(orders_in_window=21, active_staff=1, window_hours=2.0)
    assert result.staffing_pressure == "understaffed"


def test_returns_correct_echo_fields():
    result = evaluate_staffing(orders_in_window=30, active_staff=3, window_hours=2.0)
    assert result.active_staff == 3
    assert result.orders_in_window == 30
