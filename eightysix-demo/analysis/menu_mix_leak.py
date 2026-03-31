"""Leakage Category 4: Menu mix margin leakage.

Detect bad sales mix where low-margin items dominate while
higher-margin alternatives underperform.

Estimated gain = achievable mix shift × margin delta.
"""

from __future__ import annotations

from collections import defaultdict

from models.canonical import MenuMixRecord, Confidence
from models.results import MenuMixResult


# If margin data is absent, use category-based estimates
_DEFAULT_MARGINS: dict[str, float] = {
    "beverage": 0.75, "drink": 0.75, "beer": 0.70, "wine": 0.65,
    "appetizer": 0.55, "starter": 0.55,
    "dessert": 0.60,
    "side": 0.55,
    "entree": 0.30, "main": 0.30,
}

# Assume 10% of low-margin volume could shift to better-margin alternative
MIX_SHIFT_PCT = 0.10


def analyze_menu_mix(
    records: list[MenuMixRecord],
    confidence: Confidence = Confidence.MEDIUM,
) -> MenuMixResult:
    """Detect menu mix margin leakage."""

    if not records:
        return MenuMixResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="No menu mix data available.",
        )

    # Aggregate by item
    item_data: dict[str, dict] = defaultdict(lambda: {
        "quantity": 0, "revenue": 0.0, "margin": None, "category": None,
    })

    for r in records:
        d = item_data[r.item_name]
        d["quantity"] += r.quantity_sold
        d["revenue"] += r.revenue
        if r.estimated_margin is not None:
            d["margin"] = r.estimated_margin
        if r.category:
            d["category"] = r.category

    # Fill in missing margins from category defaults
    for item_name, d in item_data.items():
        if d["margin"] is None and d["category"]:
            cat = d["category"].lower()
            for key, default_margin in _DEFAULT_MARGINS.items():
                if key in cat:
                    d["margin"] = default_margin
                    break

    # Separate items with margin data
    items_with_margin = {
        name: d for name, d in item_data.items()
        if d["margin"] is not None and d["quantity"] > 0
    }

    if len(items_with_margin) < 3:
        return MenuMixResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=Confidence.LOW,
            explanation="Insufficient margin data to analyze menu mix leakage.",
        )

    # Classify items
    total_qty = sum(d["quantity"] for d in items_with_margin.values())
    total_rev = sum(d["revenue"] for d in items_with_margin.values())
    avg_margin = sum(
        d["margin"] * d["revenue"] for d in items_with_margin.values()
    ) / total_rev if total_rev > 0 else 0.0

    low_margin_high_volume: list[dict] = []
    high_margin_low_volume: list[dict] = []

    for name, d in items_with_margin.items():
        qty_share = d["quantity"] / total_qty if total_qty > 0 else 0
        is_high_volume = qty_share > (1.0 / len(items_with_margin))
        is_low_margin = d["margin"] < avg_margin * 0.8
        is_high_margin = d["margin"] > avg_margin * 1.2
        is_low_volume = qty_share < (0.5 / len(items_with_margin))

        entry = {
            "item_name": name,
            "quantity": d["quantity"],
            "revenue": round(d["revenue"], 2),
            "margin": round(d["margin"], 4),
            "qty_share": round(qty_share, 4),
        }

        if is_low_margin and is_high_volume:
            low_margin_high_volume.append(entry)
        elif is_high_margin and is_low_volume:
            high_margin_low_volume.append(entry)

    # Estimate margin gain from mix shift
    if not low_margin_high_volume or not high_margin_low_volume:
        return MenuMixResult(
            estimated_annual_impact=0.0,
            observed_impact=0.0,
            confidence=confidence,
            explanation="Menu mix is relatively balanced. No significant margin leakage detected.",
            low_margin_high_volume=low_margin_high_volume,
            high_margin_low_volume=high_margin_low_volume,
        )

    # Calculate potential gain
    low_margin_revenue = sum(d["revenue"] for d in low_margin_high_volume)
    low_margin_avg = sum(d["margin"] * d["revenue"] for d in low_margin_high_volume) / low_margin_revenue if low_margin_revenue > 0 else 0.0
    high_margin_avg = sum(d["margin"] * d["revenue"] for d in high_margin_low_volume) / sum(d["revenue"] for d in high_margin_low_volume) if high_margin_low_volume else 0.0

    margin_delta = high_margin_avg - low_margin_avg
    shiftable_revenue = low_margin_revenue * MIX_SHIFT_PCT
    estimated_gain = shiftable_revenue * margin_delta

    if estimated_gain < 0:
        estimated_gain = 0.0

    return MenuMixResult(
        estimated_annual_impact=estimated_gain,
        observed_impact=estimated_gain,
        confidence=confidence,
        explanation=(
            f"Found {len(low_margin_high_volume)} high-volume low-margin item(s) and "
            f"{len(high_margin_low_volume)} high-margin underperformer(s). "
            f"Shifting {MIX_SHIFT_PCT:.0%} of low-margin volume to better alternatives "
            f"could recover ~${estimated_gain:,.0f} in margin."
        ),
        evidence=[{
            "low_margin_items": low_margin_high_volume,
            "high_margin_items": high_margin_low_volume,
            "margin_delta": round(margin_delta, 4),
            "shiftable_revenue": round(shiftable_revenue, 2),
        }],
        low_margin_high_volume=low_margin_high_volume,
        high_margin_low_volume=high_margin_low_volume,
        potential_mix_shift_pct=MIX_SHIFT_PCT,
    )
