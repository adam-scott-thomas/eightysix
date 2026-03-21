"""Tests for rush rules — pure unit tests, no DB or async."""
from app.rules.rush_rules import evaluate_rush


def test_normal_rush():
    # velocity = (5/30)*60 = 10/hr
    # backlog = (10 * 300) / (2 * 3600) = 3000/7200 = 0.4167 — <= 0.6 normal
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=300,
        prior_avg_prep_time_seconds=280,
        active_kitchen_staff=2,
    )
    assert result.severity == "normal"
    assert result.backlog_risk < 0.6


def test_warning_rush():
    # velocity = (9/30)*60 = 18/hr
    # backlog = (18 * 300) / (2 * 3600) = 5400/7200 = 0.75 — > 0.6 and <= 0.8 warning
    result = evaluate_rush(
        orders_in_window=9,
        window_minutes=30,
        avg_prep_time_seconds=300,
        prior_avg_prep_time_seconds=280,
        active_kitchen_staff=2,
    )
    assert result.severity == "warning"
    assert 0.6 < result.backlog_risk <= 0.8


def test_critical_rush():
    # velocity = (20/30)*60 = 40/hr
    # backlog = (40 * 600) / (2 * 3600) = 24000/7200 = 3.333 — > 0.8 critical
    result = evaluate_rush(
        orders_in_window=20,
        window_minutes=30,
        avg_prep_time_seconds=600,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=2,
    )
    assert result.severity == "critical"
    assert result.backlog_risk > 0.8
    assert result.recommendation is not None


def test_prep_time_rising():
    # change = (400 - 300) / 300 = 0.3333 — > 0.20 rising
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=400,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=3,
    )
    assert result.prep_time_trend == "rising"
    assert result.prep_time_change_pct > 0.20


def test_prep_time_stable():
    # change = (310 - 300) / 300 = 0.0333 — within +/- 0.20 stable
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=310,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=3,
    )
    assert result.prep_time_trend == "stable"


def test_prep_time_falling():
    # change = (200 - 300) / 300 = -0.3333 — < -0.20 falling
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=200,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=3,
    )
    assert result.prep_time_trend == "falling"


def test_no_prior_prep_time():
    # No prior → change_pct = 0, trend = stable
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=300,
        prior_avg_prep_time_seconds=None,
        active_kitchen_staff=2,
    )
    assert result.prep_time_trend == "stable"
    assert result.prep_time_change_pct == 0


def test_order_velocity_calculation():
    # velocity = (10/30)*60 = 20.0 orders/hr
    result = evaluate_rush(
        orders_in_window=10,
        window_minutes=30,
        avg_prep_time_seconds=300,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=3,
    )
    assert result.order_velocity == 20.0


def test_rising_prep_time_escalates_normal_to_warning():
    # backlog = (10 * 300) / (3 * 3600) = 3000/10800 = 0.2778 — normal by backlog
    # but prep time change = (400-300)/300 = 0.333 > 0.20 → rising → escalates to warning
    result = evaluate_rush(
        orders_in_window=5,
        window_minutes=30,
        avg_prep_time_seconds=400,
        prior_avg_prep_time_seconds=300,
        active_kitchen_staff=3,
    )
    assert result.severity == "warning"
    assert result.prep_time_trend == "rising"
