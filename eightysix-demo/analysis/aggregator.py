"""Aggregate all category results into the final LeakageReport."""

from __future__ import annotations

from models.canonical import Confidence, LeakageReport, LeakageFinding
from models.results import CategoryResult
from analysis.annualizer import annualize, can_annualize
from intake.confidence_scorer import overall_confidence
from intake.date_range_detector import DateRange


def aggregate(
    results: list[CategoryResult],
    date_range: DateRange | None,
    data_completeness_score: int,
    intake_metadata: dict,
) -> LeakageReport:
    """Combine all category results into a single LeakageReport."""

    days = date_range.days_covered if date_range else 0
    do_annualize = can_annualize(days)

    findings: list[LeakageFinding] = []
    category_totals: list[tuple[str, float, Confidence]] = []

    for i, result in enumerate(results):
        if result.observed_impact <= 0:
            continue

        annual = annualize(result, days) if do_annualize else result.observed_impact

        findings.append(LeakageFinding(
            finding_id=f"lf_{i + 1:03d}",
            category=result.category,
            estimated_impact_observed=round(result.observed_impact, 2),
            estimated_impact_annualized=round(annual, 2),
            confidence=result.confidence,
            explanation=result.explanation,
            evidence_refs=[str(e) for e in result.evidence[:5]],
            detail=result.detail,
        ))

        category_totals.append((result.category, annual, result.confidence))

    # Sort by impact
    findings.sort(key=lambda f: f.estimated_impact_annualized, reverse=True)
    category_totals.sort(key=lambda x: x[1], reverse=True)

    total_annual = sum(f.estimated_impact_annualized for f in findings)
    monthly_avg = total_annual / 12.0 if total_annual > 0 else 0.0

    top_categories = [
        {"category": cat, "estimated_annual_impact": round(amt, 2)}
        for cat, amt, _ in category_totals[:3]
    ]

    conf = overall_confidence(category_totals)

    warnings: list[str] = []
    if not do_annualize and days > 0:
        warnings.append(
            f"Only {days} days of data — insufficient for annualized estimate. "
            "Showing observed totals only."
        )
    if data_completeness_score < 40:
        warnings.append(
            "Data completeness is low. Estimates may be unreliable."
        )

    return LeakageReport(
        date_range_start=date_range.start if date_range else None,
        date_range_end=date_range.end if date_range else None,
        days_covered=days,
        estimated_annual_leakage=round(total_annual, 2),
        average_monthly_leakage=round(monthly_avg, 2),
        top_categories=top_categories,
        confidence=conf,
        findings=findings,
        data_completeness_score=data_completeness_score,
        intake_metadata=intake_metadata,
        warnings=warnings,
    )
