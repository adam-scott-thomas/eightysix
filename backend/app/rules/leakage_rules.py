"""Rule 3: Refund / comp leakage detection."""
from dataclasses import dataclass

from app.rules.thresholds import LeakageThresholds, DEFAULT_THRESHOLDS


@dataclass
class EmployeeRefundInfo:
    employee_id: str
    employee_name: str
    refund_total: float
    share: float  # fraction of total refunds


@dataclass
class LeakageResult:
    refund_total: float
    comp_total: float
    void_total: float
    loss_estimate: float
    refund_rate: float
    severity: str  # normal, spike, critical
    spike_detected: bool
    suspicious_employee: EmployeeRefundInfo | None = None
    alert_message: str | None = None


def evaluate_leakage(
    gross_revenue: float,
    refund_total: float,
    comp_total: float,
    void_total: float,
    employee_refunds: dict[str, dict] | None = None,
    thresholds: LeakageThresholds | None = None,
) -> LeakageResult:
    """
    employee_refunds: {employee_id: {"name": str, "amount": float}}
    """
    t = thresholds or DEFAULT_THRESHOLDS.leakage

    loss = refund_total + comp_total + void_total

    if gross_revenue <= 0:
        return LeakageResult(
            refund_total=round(refund_total, 2),
            comp_total=round(comp_total, 2),
            void_total=round(void_total, 2),
            loss_estimate=round(loss, 2),
            refund_rate=0,
            severity="normal",
            spike_detected=False,
        )

    rate = loss / gross_revenue

    if rate > t.spike_refund_rate:
        severity = "critical"
        spike = True
        msg = f"Refund/comp/void rate at {rate:.1%} of revenue — critical threshold exceeded"
    elif rate > t.normal_refund_rate:
        severity = "spike"
        spike = True
        msg = f"Refund/comp/void rate at {rate:.1%} of revenue — elevated"
    else:
        severity = "normal"
        spike = False
        msg = None

    # Check employee concentration
    suspicious = None
    if employee_refunds and loss > 0:
        for emp_id, info in employee_refunds.items():
            share = info["amount"] / loss if loss > 0 else 0
            if share >= t.suspicious_employee_concentration:
                suspicious = EmployeeRefundInfo(
                    employee_id=emp_id,
                    employee_name=info["name"],
                    refund_total=round(info["amount"], 2),
                    share=round(share, 4),
                )
                if msg:
                    msg += f". {info['name']} responsible for {share:.0%} of losses"
                else:
                    msg = f"Suspicious: {info['name']} responsible for {share:.0%} of losses"
                break

    return LeakageResult(
        refund_total=round(refund_total, 2),
        comp_total=round(comp_total, 2),
        void_total=round(void_total, 2),
        loss_estimate=round(loss, 2),
        refund_rate=round(rate, 4),
        severity=severity,
        spike_detected=spike,
        suspicious_employee=suspicious,
        alert_message=msg,
    )
