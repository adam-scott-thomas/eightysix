"""Rule 4: Menu performance analysis."""
from dataclasses import dataclass


@dataclass
class MenuItemPerformance:
    item_name: str
    menu_item_id: str
    units_sold: int
    revenue: float
    revenue_contribution: float
    margin_band: str | None
    category: str  # star, workhorse, puzzle, dog


@dataclass
class AttachSuggestion:
    anchor_item: str
    suggested_item: str
    message: str


@dataclass
class MenuResult:
    top_sellers: list[MenuItemPerformance]
    bottom_sellers: list[MenuItemPerformance]
    workhorse_items: list[MenuItemPerformance]
    dog_items: list[MenuItemPerformance]
    attach_rate_suggestions: list[AttachSuggestion]


def classify_margin_band(price: float, food_cost: float | None) -> str:
    if food_cost is None:
        return "unknown"
    if price <= 0:
        return "unknown"
    margin_pct = (price - food_cost) / price
    if margin_pct >= 0.60:
        return "high"
    elif margin_pct >= 0.40:
        return "medium"
    else:
        return "low"


def evaluate_menu(
    item_sales: list[dict],
    total_revenue: float,
) -> MenuResult:
    """
    item_sales: list of {
        "menu_item_id": str, "item_name": str, "units_sold": int,
        "revenue": float, "price": float,
        "estimated_food_cost": float|None, "margin_band": str|None
    }
    """
    if not item_sales:
        return MenuResult([], [], [], [], [])

    # Compute margin bands if not set
    for item in item_sales:
        if not item.get("margin_band"):
            item["margin_band"] = classify_margin_band(
                item["price"], item.get("estimated_food_cost")
            )

    # Compute revenue contribution
    for item in item_sales:
        item["revenue_contribution"] = item["revenue"] / total_revenue if total_revenue > 0 else 0

    # Sort by units sold
    sorted_items = sorted(item_sales, key=lambda x: x["units_sold"], reverse=True)

    # Median as volume threshold
    volumes = [i["units_sold"] for i in sorted_items if i["units_sold"] > 0]
    median_vol = sorted(volumes)[len(volumes) // 2] if volumes else 1

    performances = []
    for item in sorted_items:
        high_volume = item["units_sold"] >= median_vol
        high_margin = item["margin_band"] in ("high", "medium")

        if high_volume and high_margin:
            cat = "star"
        elif high_volume and not high_margin:
            cat = "workhorse"
        elif not high_volume and high_margin:
            cat = "puzzle"
        else:
            cat = "dog"

        performances.append(MenuItemPerformance(
            item_name=item["item_name"],
            menu_item_id=item["menu_item_id"],
            units_sold=item["units_sold"],
            revenue=round(item["revenue"], 2),
            revenue_contribution=round(item["revenue_contribution"], 4),
            margin_band=item["margin_band"],
            category=cat,
        ))

    top_sellers = performances[:5]
    bottom_sellers = [p for p in performances if p.units_sold > 0][-5:]
    workhorse_items = [p for p in performances if p.category == "workhorse"]
    dog_items = [p for p in performances if p.category == "dog"]

    # Attach rate suggestions: top 3 sellers vs items rarely bought together
    attach_suggestions = []
    if len(performances) >= 5:
        top3_names = [p.item_name for p in performances[:3]]
        # Suggest pairing top sellers with puzzle items
        puzzles = [p for p in performances if p.category == "puzzle"]
        for anchor in top3_names[:2]:
            for puzzle in puzzles[:1]:
                attach_suggestions.append(AttachSuggestion(
                    anchor_item=anchor,
                    suggested_item=puzzle.item_name,
                    message=f"Customers who order {anchor} rarely add {puzzle.item_name} — consider combo",
                ))

    return MenuResult(
        top_sellers=top_sellers,
        bottom_sellers=bottom_sellers,
        workhorse_items=workhorse_items,
        dog_items=dog_items,
        attach_rate_suggestions=attach_suggestions,
    )
