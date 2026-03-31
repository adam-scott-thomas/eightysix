"""Industry benchmark baselines by restaurant type.

These are reference ranges for contextualizing leakage estimates.
Sources: NRA, Toast Restaurant Trends, industry averages.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Benchmark:
    restaurant_type: str
    target_labor_pct: float       # Healthy labor cost ratio
    warning_labor_pct: float      # Warning threshold
    avg_refund_rate: float        # Normal refund rate
    high_refund_rate: float       # Concerning refund rate
    avg_food_cost_pct: float      # Typical food cost
    avg_ticket: float             # Average ticket
    avg_orders_per_day: int       # Typical daily orders
    typical_leakage_pct: float    # Industry avg leakage as % of revenue


BENCHMARKS: dict[str, Benchmark] = {
    "qsr": Benchmark(
        restaurant_type="Quick Service / Fast Casual",
        target_labor_pct=0.25,
        warning_labor_pct=0.30,
        avg_refund_rate=0.02,
        high_refund_rate=0.04,
        avg_food_cost_pct=0.30,
        avg_ticket=12.00,
        avg_orders_per_day=300,
        typical_leakage_pct=0.04,
    ),
    "casual_dining": Benchmark(
        restaurant_type="Casual Dining",
        target_labor_pct=0.28,
        warning_labor_pct=0.33,
        avg_refund_rate=0.025,
        high_refund_rate=0.05,
        avg_food_cost_pct=0.32,
        avg_ticket=22.00,
        avg_orders_per_day=200,
        typical_leakage_pct=0.05,
    ),
    "fine_dining": Benchmark(
        restaurant_type="Fine Dining",
        target_labor_pct=0.32,
        warning_labor_pct=0.38,
        avg_refund_rate=0.015,
        high_refund_rate=0.03,
        avg_food_cost_pct=0.35,
        avg_ticket=65.00,
        avg_orders_per_day=80,
        typical_leakage_pct=0.03,
    ),
    "bar_grill": Benchmark(
        restaurant_type="Bar & Grill",
        target_labor_pct=0.26,
        warning_labor_pct=0.32,
        avg_refund_rate=0.03,
        high_refund_rate=0.06,
        avg_food_cost_pct=0.28,
        avg_ticket=18.00,
        avg_orders_per_day=180,
        typical_leakage_pct=0.06,
    ),
    "pizza": Benchmark(
        restaurant_type="Pizza / Delivery-Heavy",
        target_labor_pct=0.24,
        warning_labor_pct=0.29,
        avg_refund_rate=0.025,
        high_refund_rate=0.05,
        avg_food_cost_pct=0.28,
        avg_ticket=25.00,
        avg_orders_per_day=150,
        typical_leakage_pct=0.04,
    ),
}


def get_benchmark(restaurant_type: str) -> Benchmark:
    """Get benchmark for a restaurant type. Defaults to casual_dining."""
    return BENCHMARKS.get(restaurant_type, BENCHMARKS["casual_dining"])


def contextualize_leakage(
    annual_leakage: float,
    annual_revenue: float,
    restaurant_type: str = "casual_dining",
) -> dict:
    """Compare leakage estimate against industry benchmarks."""
    bench = get_benchmark(restaurant_type)

    if annual_revenue <= 0:
        return {
            "benchmark": bench.restaurant_type,
            "typical_leakage_pct": bench.typical_leakage_pct,
            "note": "Revenue data insufficient for comparison.",
        }

    actual_pct = annual_leakage / annual_revenue
    typical_loss = annual_revenue * bench.typical_leakage_pct

    comparison = "below"
    if actual_pct > bench.typical_leakage_pct * 1.5:
        comparison = "significantly above"
    elif actual_pct > bench.typical_leakage_pct:
        comparison = "above"

    return {
        "benchmark": bench.restaurant_type,
        "actual_leakage_pct": round(actual_pct, 4),
        "typical_leakage_pct": bench.typical_leakage_pct,
        "typical_annual_loss": round(typical_loss, 0),
        "comparison": comparison,
        "note": (
            f"Your estimated leakage ({actual_pct:.1%}) is {comparison} the "
            f"industry average ({bench.typical_leakage_pct:.1%}) for {bench.restaurant_type}."
        ),
    }
