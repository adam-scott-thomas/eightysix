"""Leakage Category 2: Refund / Void / Comp concentration detection.

Find employees with disproportionate refund activity compared to peers.
Excess = actual refunds - (peer median rate × employee's volume).
"""

from __future__ import annotations

from collections import defaultdict

from models.canonical import RefundEvent, SalesRecord, Confidence
from models.results import RefundAbuseResult


def analyze_refund_abuse(
    refunds: list[RefundEvent],
    sales: list[SalesRecord],
    confidence: Confidence = Confidence.MEDIUM,
) -> RefundAbuseResult:
    """Detect suspicious refund/void/comp concentration by employee."""

    if not refunds:
        return RefundAbuseResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="No refund/void/comp data available.",
        )

    total_refunds = sum(r.amount for r in refunds)
    total_sales = sum(s.net_sales or s.gross_sales for s in sales) if sales else 0.0

    # Group refunds by employee
    by_employee: dict[str, float] = defaultdict(float)
    by_employee_count: dict[str, int] = defaultdict(int)
    unlinked_total = 0.0

    for r in refunds:
        if r.employee_id:
            by_employee[r.employee_id] += r.amount
            by_employee_count[r.employee_id] += 1
        else:
            unlinked_total += r.amount

    if not by_employee:
        # No employee-linked refunds — can only report total
        return RefundAbuseResult(
            estimated_annual_impact=0.0,
            observed_impact=total_refunds,
            confidence=Confidence.LOW,
            explanation=(
                f"Total refunds/voids/comps: ${total_refunds:,.0f}, but no employee linkage available. "
                "Cannot determine concentration."
            ),
        )

    # Compute peer median rate
    employee_amounts = sorted(by_employee.values())
    mid = len(employee_amounts) // 2
    median_amount = employee_amounts[mid]

    # Find employees significantly above median
    flagged: list[dict] = []
    total_excess = 0.0

    for emp_id, emp_total in sorted(by_employee.items(), key=lambda x: x[1], reverse=True):
        # "Expected" = median amount for a peer
        excess = max(0.0, emp_total - median_amount)
        share = emp_total / total_refunds if total_refunds > 0 else 0.0

        # Flag if > 1.5x median OR > 25% share of all refunds
        if emp_total > median_amount * 1.5 or share > 0.25:
            flagged.append({
                "employee_id": emp_id,
                "total_refunds": round(emp_total, 2),
                "refund_count": by_employee_count[emp_id],
                "share_of_total": round(share, 4),
                "excess_vs_median": round(excess, 2),
            })
            total_excess += excess

    # Overall refund rate
    refund_rate = total_refunds / total_sales if total_sales > 0 else 0.0
    peer_median_rate = median_amount / (total_sales / len(by_employee)) if total_sales > 0 and by_employee else 0.0

    explanation_parts = [
        f"Total refunds/voids/comps: ${total_refunds:,.0f}",
        f"({refund_rate:.1%} of sales)" if total_sales > 0 else "",
    ]
    if flagged:
        explanation_parts.append(
            f"{len(flagged)} employee(s) flagged for disproportionate refund activity. "
            f"Excess above peer median: ${total_excess:,.0f}."
        )
    else:
        explanation_parts.append("No employees showed disproportionate concentration.")

    return RefundAbuseResult(
        estimated_annual_impact=total_excess,
        observed_impact=total_excess,
        confidence=confidence,
        explanation=" ".join(p for p in explanation_parts if p),
        evidence=[{"flagged_employees": flagged}] if flagged else [],
        flagged_employees=flagged,
        total_excess_refunds=total_excess,
        peer_median_rate=peer_median_rate,
    )
