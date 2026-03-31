"""Generate the owner-facing report — the sales pitch number."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date

from models.canonical import LeakageReport


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()
        return super().default(o)


def to_owner_json(report: LeakageReport) -> dict:
    """Produce the clean owner-facing output."""
    return {
        "date_range_start": report.date_range_start.isoformat() if report.date_range_start else None,
        "date_range_end": report.date_range_end.isoformat() if report.date_range_end else None,
        "days_covered": report.days_covered,
        "estimated_annual_leakage": report.estimated_annual_leakage,
        "average_monthly_leakage": report.average_monthly_leakage,
        "top_categories": report.top_categories,
        "confidence": report.confidence.value,
    }


def to_internal_json(report: LeakageReport) -> dict:
    """Produce the full internal report with evidence trail."""
    d = asdict(report)
    # Convert enums to strings
    d["confidence"] = report.confidence.value
    for f in d.get("findings", []):
        if hasattr(f.get("confidence"), "value"):
            f["confidence"] = f["confidence"].value
    return json.loads(json.dumps(d, cls=_Encoder))


def to_text_summary(report: LeakageReport) -> str:
    """Human-readable summary for terminal or email."""
    lines = [
        f"{'=' * 50}",
        f"  EIGHTYSIX — LEAKAGE ESTIMATE",
        f"{'=' * 50}",
        "",
    ]

    if report.date_range_start and report.date_range_end:
        lines.append(f"  Period: {report.date_range_start} to {report.date_range_end}")
        lines.append(f"  Days covered: {report.days_covered}")
    lines.append(f"  Data completeness: {report.data_completeness_score}/100")
    lines.append("")

    lines.append(f"  Estimated annual leakage:  ${report.estimated_annual_leakage:>10,.0f}")
    lines.append(f"  Average monthly leakage:   ${report.average_monthly_leakage:>10,.0f}")
    lines.append("")

    if report.top_categories:
        lines.append("  Top sources:")
        for i, cat in enumerate(report.top_categories, 1):
            lines.append(f"    {i}. {cat['category']:<30s} ${cat['estimated_annual_impact']:>10,.0f}")
        lines.append("")

    lines.append(f"  Confidence: {report.confidence.value}")
    lines.append("")

    if report.warnings:
        lines.append("  Warnings:")
        for w in report.warnings:
            lines.append(f"    - {w}")
        lines.append("")

    if report.findings:
        lines.append(f"  Detailed findings: {len(report.findings)}")
        for f in report.findings:
            lines.append(f"    [{f.confidence.value}] {f.category}: ${f.estimated_impact_annualized:,.0f}")
            lines.append(f"           {f.explanation}")
        lines.append("")

    lines.append(f"{'=' * 50}")
    return "\n".join(lines)
