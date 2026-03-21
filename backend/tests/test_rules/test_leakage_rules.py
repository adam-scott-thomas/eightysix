"""Tests for leakage rules — pure unit tests, no DB or async."""
from app.rules.leakage_rules import evaluate_leakage


def test_normal_leakage():
    # loss = 50 + 20 + 0 = 70, rate = 70/5000 = 0.014 — <= 0.03 normal
    result = evaluate_leakage(gross_revenue=5000, refund_total=50, comp_total=20, void_total=0)
    assert result.severity == "normal"
    assert not result.spike_detected
    assert result.alert_message is None


def test_spike_leakage():
    # loss = 200 + 50 + 0 = 250, rate = 250/5000 = 0.05 — > 0.03 and <= 0.06 spike
    result = evaluate_leakage(gross_revenue=5000, refund_total=200, comp_total=50, void_total=0)
    assert result.severity == "spike"
    assert result.spike_detected
    assert result.alert_message is not None


def test_critical_leakage():
    # loss = 250 + 100 + 0 = 350, rate = 350/5000 = 0.07 — > 0.06 critical
    result = evaluate_leakage(gross_revenue=5000, refund_total=250, comp_total=100, void_total=0)
    assert result.severity == "critical"
    assert result.spike_detected


def test_suspicious_employee():
    # loss = 250 + 50 + 0 = 300, employee share = 200/300 = 0.6667 — >= 0.40
    emp_refunds = {"emp-1": {"name": "Jake Miller", "amount": 200}}
    result = evaluate_leakage(
        gross_revenue=5000,
        refund_total=250,
        comp_total=50,
        void_total=0,
        employee_refunds=emp_refunds,
    )
    assert result.suspicious_employee is not None
    assert result.suspicious_employee.employee_name == "Jake Miller"
    assert result.suspicious_employee.share >= 0.40


def test_no_suspicious_employee_below_threshold():
    # loss = 250 + 50 + 0 = 300, employee share = 100/300 = 0.333 — < 0.40
    emp_refunds = {"emp-1": {"name": "Jake Miller", "amount": 100}}
    result = evaluate_leakage(
        gross_revenue=5000,
        refund_total=250,
        comp_total=50,
        void_total=0,
        employee_refunds=emp_refunds,
    )
    assert result.suspicious_employee is None


def test_zero_revenue():
    result = evaluate_leakage(gross_revenue=0, refund_total=50, comp_total=0, void_total=0)
    assert result.severity == "normal"
    assert result.refund_rate == 0
    assert not result.spike_detected


def test_loss_estimate_includes_all():
    result = evaluate_leakage(gross_revenue=5000, refund_total=100, comp_total=50, void_total=25)
    assert result.loss_estimate == 175.0


def test_normal_at_boundary():
    # loss = 150, rate = 150/5000 = 0.03 exactly — <= 0.03 normal
    result = evaluate_leakage(gross_revenue=5000, refund_total=150, comp_total=0, void_total=0)
    assert result.severity == "normal"
    assert not result.spike_detected


def test_spike_at_boundary():
    # loss = 300, rate = 300/5000 = 0.06 exactly — > 0.03 but <= 0.06 spike
    result = evaluate_leakage(gross_revenue=5000, refund_total=300, comp_total=0, void_total=0)
    assert result.severity == "spike"
    assert result.spike_detected
