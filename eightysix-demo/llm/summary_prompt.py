"""Build the structured summary that feeds the LLM explanation layer.

Rule: LLM receives computed summaries only. No raw data. No arithmetic."""

from __future__ import annotations

from models.canonical import LeakageReport


def build_prompt_context(report: LeakageReport) -> dict:
    """Build the structured input for the LLM — summaries only, no raw data."""
    return {
        "days_covered": report.days_covered,
        "estimated_annual_leakage": report.estimated_annual_leakage,
        "average_monthly_leakage": report.average_monthly_leakage,
        "top_categories": report.top_categories,
        "confidence": report.confidence.value,
        "data_completeness_score": report.data_completeness_score,
        "notes": report.warnings,
        "findings_summary": [
            {
                "category": f.category,
                "annualized": f.estimated_impact_annualized,
                "confidence": f.confidence.value,
                "explanation": f.explanation,
            }
            for f in report.findings
        ],
    }


SYSTEM_PROMPT = """You are a restaurant operations analyst writing a brief, plain-English
summary of a leakage analysis for a restaurant owner.

Rules:
- Do NOT invent new numbers or categories. Use only the data provided.
- Do NOT add precision beyond what the data supports.
- Do NOT claim exact savings — these are estimates.
- Keep it under 150 words.
- Be direct. Owners are busy.
- If confidence is low, say so clearly.
- Use dollar amounts rounded to nearest hundred.
- Address the owner directly ("your restaurant", "we found").
"""


def build_explanation_prompt(context: dict) -> str:
    """Build the user prompt for the LLM."""
    lines = [
        f"Estimated annual leakage: ${context['estimated_annual_leakage']:,.0f}",
        f"Average monthly: ${context['average_monthly_leakage']:,.0f}",
        f"Based on {context['days_covered']} days of data.",
        f"Confidence: {context['confidence']}.",
        "",
        "Breakdown:",
    ]

    for f in context.get("findings_summary", []):
        lines.append(
            f"- {f['category']}: ${f['annualized']:,.0f}/yr "
            f"({f['confidence']} confidence) — {f['explanation']}"
        )

    if context.get("notes"):
        lines.append("")
        lines.append("Notes:")
        for n in context["notes"]:
            lines.append(f"- {n}")

    lines.append("")
    lines.append(
        "Write a brief owner-facing summary explaining where money is leaking "
        "and what they should look at first."
    )

    return "\n".join(lines)
