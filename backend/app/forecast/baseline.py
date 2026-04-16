"""Baseline forecast model — stupid-simple on purpose.

Algorithm:
1. Weighted average: 60% last-4-weeks same-weekday, 40% last-8-weeks
2. Trend adjustment: apply weekly slope
3. Event/holiday multiplier
4. Weather modifier (weeks 1-2 only)
5. Confidence bands: tighter for near-term, wider for far-term
"""
from __future__ import annotations

from dataclasses import dataclass

from app.forecast.features import DayFeatures


@dataclass
class ForecastResult:
    """Output of the baseline model for one day."""
    expected_sales: float
    expected_orders: int
    sales_low: float
    sales_high: float
    confidence_level: float
    orders_by_channel: dict
    daypart: dict
    labor_hours: dict
    top_skus: list
    risk_flags: list
    explanation: str
    purchasing: list


MODEL_VERSION = "baseline_v1"

DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def forecast_day(features: DayFeatures) -> ForecastResult:
    """Produce a forecast for one day from its feature vector."""
    # 1. Weighted baseline
    avg_4w = features.same_dow_avg_4w
    avg_8w = features.same_dow_avg_8w
    orders_4w = features.same_dow_orders_4w
    orders_8w = features.same_dow_orders_8w

    if avg_4w is not None and avg_8w is not None:
        base_sales = 0.6 * avg_4w + 0.4 * avg_8w
    elif avg_4w is not None:
        base_sales = avg_4w
    elif avg_8w is not None:
        base_sales = avg_8w
    else:
        base_sales = 0

    if orders_4w is not None and orders_8w is not None:
        base_orders = 0.6 * orders_4w + 0.4 * orders_8w
    elif orders_4w is not None:
        base_orders = orders_4w
    elif orders_8w is not None:
        base_orders = orders_8w
    else:
        base_orders = 0

    # 2. Trend adjustment
    weeks_ahead = max(features.horizon_days / 7, 0)
    base_sales += features.trend_slope_sales * weeks_ahead
    base_orders += features.trend_slope_orders * weeks_ahead

    # 3. Event multiplier
    base_sales *= features.event_multiplier
    base_orders *= features.event_multiplier

    # 4. Weather modifier (near-term only)
    weather_mod = 1.0
    if features.weather and features.horizon_days <= 14:
        weather_mod = _weather_multiplier(features.weather)
        base_sales *= weather_mod
        base_orders *= weather_mod

    # 5. Confidence bands
    base_sales = max(base_sales, 0)
    base_orders = max(base_orders, 0)

    if features.horizon_days <= 14:
        band_pct = 0.10 + (features.horizon_days / 14) * 0.05  # 10-15%
        confidence = 0.80
    else:
        band_pct = 0.15 + ((features.horizon_days - 14) / 14) * 0.10  # 15-25%
        confidence = 0.70

    sales_low = base_sales * (1 - band_pct)
    sales_high = base_sales * (1 + band_pct)

    # Channel breakdown
    expected_orders_int = max(round(base_orders), 0)
    orders_by_channel = {}
    if features.channel_mix and expected_orders_int > 0:
        for ch, ratio in features.channel_mix.items():
            orders_by_channel[ch] = round(expected_orders_int * ratio)

    # Daypart breakdown
    daypart = {}
    if features.daypart_avg:
        total_dp_sales = sum(v["sales"] for v in features.daypart_avg.values())
        for dp, vals in features.daypart_avg.items():
            ratio = vals["sales"] / total_dp_sales if total_dp_sales > 0 else 0.25
            daypart[dp] = {
                "sales": round(base_sales * ratio, 2),
                "orders": round(expected_orders_int * ratio),
            }

    # Labor hours recommendation
    labor_hours = {}
    if features.labor_hours_by_role_avg:
        if features.same_dow_avg_4w and features.same_dow_avg_4w > 0:
            scale = base_sales / features.same_dow_avg_4w
        else:
            scale = 1.0
        for role, hours in features.labor_hours_by_role_avg.items():
            labor_hours[role] = round(hours * scale, 1)
        labor_hours["total"] = round(sum(labor_hours.values()), 1)

    # Top SKU demand
    top_skus = []
    if features.top_skus_avg:
        if features.same_dow_orders_4w and features.same_dow_orders_4w > 0:
            sku_scale = base_orders / features.same_dow_orders_4w
        else:
            sku_scale = 1.0
        for sku in features.top_skus_avg[:50]:
            top_skus.append({
                "item_name": sku["item_name"],
                "expected_units": max(round(sku["expected_units"] * sku_scale), 0),
                "category": sku["category"],
            })

    # Risk flags
    risk_flags = _compute_risk_flags(features, base_sales, labor_hours)

    # Explanation
    explanation = _build_explanation(features, base_sales, weather_mod)

    # Purchasing signals
    purchasing = _compute_purchasing(features, top_skus)

    return ForecastResult(
        expected_sales=round(base_sales, 2),
        expected_orders=expected_orders_int,
        sales_low=round(sales_low, 2),
        sales_high=round(sales_high, 2),
        confidence_level=confidence,
        orders_by_channel=orders_by_channel,
        daypart=daypart,
        labor_hours=labor_hours,
        top_skus=top_skus,
        risk_flags=risk_flags,
        explanation=explanation,
        purchasing=purchasing,
    )


def _weather_multiplier(weather: dict) -> float:
    """Estimate weather impact on traffic."""
    mod = 1.0
    precip = weather.get("precip_chance", 0)
    condition = (weather.get("condition") or "").lower()

    if precip > 0.6 or condition in ("rain", "storm", "thunderstorm"):
        mod *= 0.92
    elif precip > 0.3:
        mod *= 0.96

    temp = weather.get("temp_high")
    if temp is not None:
        if temp > 100:
            mod *= 0.90
        elif temp > 95:
            mod *= 0.95
        elif temp < 20:
            mod *= 0.88
        elif temp < 32:
            mod *= 0.93

    return mod


def _compute_risk_flags(features: DayFeatures, base_sales: float, labor_hours: dict) -> list[dict]:
    """Flag staffing, demand, and operational risks."""
    flags = []

    if labor_hours and features.labor_hours_by_role_avg:
        for role in ("kitchen", "foh"):
            recommended = labor_hours.get(role, 0)
            historical = features.labor_hours_by_role_avg.get(role, 0)
            if historical > 0 and recommended > historical * 1.15:
                flags.append({
                    "flag": "understaffed",
                    "message": f"{role.upper()} may need +{round(recommended - historical, 1)}h above recent average",
                    "severity": "warning",
                })

    if features.trend_slope_sales < -50:
        flags.append({
            "flag": "likely_slow_day",
            "message": "Downward trend — consider reducing scheduled hours",
            "severity": "info",
        })

    if features.event_multiplier > 1.15:
        event_names = [e["name"] for e in features.events if (e.get("impact") or 1.0) > 1.0]
        flags.append({
            "flag": "event_spike",
            "message": f"Expected +{round((features.event_multiplier - 1) * 100)}% due to {', '.join(event_names) or 'events'}",
            "severity": "warning",
        })

    if features.event_multiplier < 0.85:
        flags.append({
            "flag": "likely_slow_day",
            "message": f"Expected {round((1 - features.event_multiplier) * 100)}% drop — reduce staffing",
            "severity": "info",
        })

    return flags


def _build_explanation(features: DayFeatures, base_sales: float, weather_mod: float) -> str:
    """Build human-readable 'why' for the forecast."""
    parts = []
    day_name = DOW_NAMES[features.day_of_week]

    if features.same_dow_avg_4w and features.same_dow_avg_4w > 0:
        pct_change = (base_sales - features.same_dow_avg_4w) / features.same_dow_avg_4w * 100
        direction = "up" if pct_change > 0 else "down"
        parts.append(f"{day_name} projected {direction} {abs(pct_change):.0f}% vs recent average")

    for event in features.events:
        if event.get("impact") and event["impact"] != 1.0:
            impact_pct = (event["impact"] - 1) * 100
            parts.append(f"{'+' if impact_pct > 0 else ''}{impact_pct:.0f}% from {event['name']}")

    if weather_mod != 1.0:
        impact_pct = (weather_mod - 1) * 100
        condition = (features.weather or {}).get("condition", "weather")
        parts.append(f"{impact_pct:+.0f}% from {condition}")

    if features.horizon_days > 14:
        parts.append("broader estimate — 3-4 week horizon")

    return ". ".join(parts) if parts else f"Based on recent {day_name} average"


def _compute_purchasing(features: DayFeatures, top_skus: list) -> list[dict]:
    """Suggest purchasing adjustments based on demand changes."""
    signals = []
    if not features.top_skus_avg or not top_skus:
        return signals

    historical = {s["item_name"]: s["expected_units"] for s in features.top_skus_avg[:20]}
    for sku in top_skus[:20]:
        hist = historical.get(sku["item_name"], 0)
        if hist > 0:
            change_pct = (sku["expected_units"] - hist) / hist * 100
            if abs(change_pct) >= 10:
                signals.append({
                    "item": sku["item_name"],
                    "adjustment_pct": round(change_pct),
                    "reason": "event demand" if features.event_multiplier > 1.05 else "trend",
                })

    return signals
