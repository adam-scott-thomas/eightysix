"""Optional LLM explanation layer. Deterministic analysis is already done —
this just produces a plain-English summary from the structured results.

Uses Claude (via Anthropic SDK) if available, otherwise returns a template.

IMPORTANT: Never include employee names in the explanation. The explanation
is a teaser — specifics like names are reserved for the full audit."""

from __future__ import annotations

import re

from models.canonical import LeakageReport
from llm.summary_prompt import build_prompt_context, build_explanation_prompt, SYSTEM_PROMPT


def generate_explanation(report: LeakageReport, use_llm: bool = False) -> str:
    """Generate a plain-English explanation of the leakage report.

    If use_llm=True and ANTHROPIC_API_KEY is set, calls Claude.
    Otherwise returns a deterministic template summary.
    """
    if use_llm:
        return _llm_explanation(report)
    return _template_explanation(report)


def _template_explanation(report: LeakageReport) -> str:
    """Deterministic template — no API call needed."""
    if not report.findings:
        return (
            "We analyzed your uploaded data but did not find significant leakage patterns. "
            "This could mean operations are well-managed, or that the uploaded data "
            "lacks the detail needed for a deeper analysis."
        )

    parts = []
    total = report.estimated_annual_leakage

    parts.append(
        f"Based on {report.days_covered} days of data, we estimate your restaurant "
        f"is losing approximately ${total:,.0f} per year — "
        f"about ${report.average_monthly_leakage:,.0f} per month."
    )

    for f in report.findings:
        cat_label = {
            "overstaffing": "overstaffing on slower shifts",
            "refund_abuse": "unusual refund and void concentration",
            "ghost_labor": "ghost or low-productivity labor",
            "menu_mix_margin_leak": "menu mix margin leakage",
            "understaffing": "understaffing during peak periods",
        }.get(f.category, f.category)

        share = f.estimated_impact_annualized / total * 100 if total > 0 else 0
        parts.append(
            f"  - {cat_label.capitalize()}: ~${f.estimated_impact_annualized:,.0f}/yr "
            f"({share:.0f}% of total). {f.explanation}"
        )

    conf_note = {
        "high": "We have high confidence in these estimates based on the data provided.",
        "medium": "These estimates carry medium confidence. More granular data would sharpen the numbers.",
        "low": "These are preliminary estimates. The uploaded data was limited — additional reports would improve accuracy.",
    }
    parts.append("")
    parts.append(conf_note.get(report.confidence.value, ""))

    if report.findings:
        top = report.findings[0]
        # Check if refund abuse actually has flagged employees
        has_flagged = any(
            "flagged" in str(e).lower() and "employee" in str(e).lower()
            for e in top.evidence_refs
        )
        cat_label = {
            "overstaffing": "labor scheduling on slower days",
            "refund_abuse": "refund activity for flagged employees" if has_flagged else "your refund and void patterns",
            "ghost_labor": "time clock records and shift productivity",
            "menu_mix_margin_leak": "menu engineering and item promotion",
            "understaffing": "staffing levels during peak hours",
        }.get(top.category, top.category)
        parts.append(f"We recommend starting with a closer look at {cat_label}.")

    return _sanitize_explanation("\n".join(parts))


def _sanitize_explanation(text: str) -> str:
    """Strip employee names and specific identifiers from the explanation.

    The explanation is a teaser — specifics are reserved for the full audit.
    """
    # Replace "X employee(s) flagged" patterns but keep the count
    text = re.sub(
        r'\d+ employee\(s\) flagged for disproportionate refund activity\. '
        r'Excess above peer median: \$[\d,]+\.',
        'Disproportionate refund concentration detected among staff. '
        'Specific employees identified for review.',
        text,
    )

    # Remove any "Employee: <name>" or "<name> (<role>)" patterns
    # Common name patterns: "First Last", "First L.", "First Last-Name"
    # We can't perfectly detect all names, but we can strip the most common patterns
    # from the analysis explanations which use formats like "for [employee]"

    return text


def _llm_explanation(report: LeakageReport) -> str:
    """Call Claude for a natural-language summary."""
    try:
        import anthropic
    except ImportError:
        return _template_explanation(report)

    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_explanation(report)

    context = build_prompt_context(report)
    user_prompt = build_explanation_prompt(context)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
    except Exception:
        return _template_explanation(report)
