"""Tests for labor rules — pure unit tests, no DB or async."""
from app.rules.labor_rules import evaluate_labor


def test_healthy_labor():
    # 600 / 3000 = 0.20 ratio — <= 0.30 healthy
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=600, revenue_today=3000)
    assert result.severity == "healthy"
    assert result.labor_cost_ratio == 0.2
    assert result.alert_message is None


def test_warning_labor():
    # 960 / 3000 = 0.32 ratio — > 0.30 and <= 0.35 warning
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=960, revenue_today=3000)
    assert result.severity == "warning"
    assert result.labor_cost_ratio == 0.32
    assert result.alert_message is not None


def test_critical_labor():
    # 1200 / 3000 = 0.40 ratio — > 0.35 critical
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=1200, revenue_today=3000)
    assert result.severity == "critical"
    assert result.labor_cost_ratio == 0.4


def test_no_revenue_with_labor_cost():
    # revenue=0, labor_cost > 0 → severity="critical", ratio=1.0
    result = evaluate_labor(total_labor_hours=8, total_labor_cost=120, revenue_today=0)
    assert result.severity == "critical"
    assert result.labor_cost_ratio == 1.0
    assert result.alert_message is not None


def test_no_revenue_no_labor():
    # revenue=0, labor_cost=0 → severity="healthy", ratio=0
    result = evaluate_labor(total_labor_hours=0, total_labor_cost=0, revenue_today=0)
    assert result.severity == "healthy"
    assert result.labor_cost_ratio == 0
    assert result.alert_message is None


def test_healthy_at_boundary():
    # 900 / 3000 = 0.30 exactly — <= 0.30 healthy
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=900, revenue_today=3000)
    assert result.severity == "healthy"
    assert result.labor_cost_ratio == 0.3


def test_warning_at_boundary():
    # 1050 / 3000 = 0.35 exactly — > 0.30 and <= 0.35 warning
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=1050, revenue_today=3000)
    assert result.severity == "warning"
    assert result.labor_cost_ratio == 0.35


def test_sales_per_labor_hour():
    # 3000 revenue / 40 hours = 75.0 SPLH
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=600, revenue_today=3000)
    assert result.sales_per_labor_hour == 75.0


def test_labor_cost_estimate_preserved():
    result = evaluate_labor(total_labor_hours=40, total_labor_cost=599.99, revenue_today=3000)
    assert result.labor_cost_estimate == 599.99
