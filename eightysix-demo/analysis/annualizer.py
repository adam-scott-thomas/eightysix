"""Annualization logic with guardrails.

Case A: Full year → sum directly.
Case B: Partial year → (observed / days_covered) × 365.
Refuses to annualize < 30 days.
"""

from __future__ import annotations

from models.results import CategoryResult


MIN_DAYS_FOR_ANNUALIZATION = 30


def annualize(result: CategoryResult, days_covered: int) -> float:
    """Annualize an observed leakage amount.

    Returns annualized estimate, or observed amount if annualization
    is not appropriate.
    """
    observed = result.observed_impact
    if observed <= 0:
        return 0.0

    if days_covered >= 365:
        return observed

    if days_covered < MIN_DAYS_FOR_ANNUALIZATION:
        # Cannot annualize — return observed with no extrapolation
        return observed

    return (observed / days_covered) * 365


def can_annualize(days_covered: int) -> bool:
    return days_covered >= MIN_DAYS_FOR_ANNUALIZATION
