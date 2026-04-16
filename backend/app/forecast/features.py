"""Extract features from daily aggregates for the forecast model."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from dataclasses import dataclass, field

from app.db.models.daily_aggregate import DailyAggregate
from app.db.models.external_event import ExternalEvent


@dataclass
class DayFeatures:
    """Features for one target forecast date."""
    target_date: date
    day_of_week: int  # 0=Mon
    week_of_year: int
    horizon_days: int  # days from today

    # Historical baselines
    same_dow_avg_4w: float | None = None
    same_dow_avg_8w: float | None = None
    same_dow_orders_4w: float | None = None
    same_dow_orders_8w: float | None = None

    # Trend
    trend_slope_sales: float = 0.0
    trend_slope_orders: float = 0.0

    # Channel mix (avg ratios over last 4 weeks)
    channel_mix: dict = field(default_factory=dict)

    # Labor baselines
    labor_hours_by_role_avg: dict = field(default_factory=dict)

    # Daypart baselines
    daypart_avg: dict = field(default_factory=dict)

    # Top SKU demand
    top_skus_avg: list = field(default_factory=list)

    # External signals
    events: list[dict] = field(default_factory=list)
    event_multiplier: float = 1.0
    weather: dict | None = None
    is_holiday: bool = False


def extract_features(
    aggregates: list[DailyAggregate],
    external_events: list[ExternalEvent],
    target_dates: list[date],
    today: date,
) -> list[DayFeatures]:
    """Build feature vectors for each target date from historical aggregates."""
    by_dow: dict[int, list[DailyAggregate]] = defaultdict(list)
    for agg in sorted(aggregates, key=lambda a: a.agg_date, reverse=True):
        by_dow[agg.day_of_week].append(agg)

    events_by_date: dict[date, list[ExternalEvent]] = defaultdict(list)
    for ev in external_events:
        events_by_date[ev.event_date].append(ev)

    features = []
    for td in target_dates:
        horizon = (td - today).days
        dow = td.weekday()
        woy = td.isocalendar()[1]

        f = DayFeatures(
            target_date=td,
            day_of_week=dow,
            week_of_year=woy,
            horizon_days=horizon,
        )

        same_dow = by_dow.get(dow, [])
        recent_4w = [a for a in same_dow if 0 < (td - a.agg_date).days <= 28]
        recent_8w = [a for a in same_dow if 0 < (td - a.agg_date).days <= 56]

        if recent_4w:
            f.same_dow_avg_4w = sum(float(a.net_sales) for a in recent_4w) / len(recent_4w)
            f.same_dow_orders_4w = sum(a.order_count for a in recent_4w) / len(recent_4w)
        if recent_8w:
            f.same_dow_avg_8w = sum(float(a.net_sales) for a in recent_8w) / len(recent_8w)
            f.same_dow_orders_8w = sum(a.order_count for a in recent_8w) / len(recent_8w)

        # Trend slope over weekly same-weekday values
        if len(recent_4w) >= 2:
            points = [(i, float(a.net_sales)) for i, a in enumerate(reversed(recent_4w))]
            f.trend_slope_sales = _linear_slope(points)
            order_points = [(i, float(a.order_count)) for i, a in enumerate(reversed(recent_4w))]
            f.trend_slope_orders = _linear_slope(order_points)

        # Channel mix from all recent days (not just same weekday)
        all_recent = [a for a in aggregates if 0 < (td - a.agg_date).days <= 28]
        if all_recent:
            total_orders = sum(a.order_count for a in all_recent)
            if total_orders > 0:
                f.channel_mix = {
                    "dine_in": sum(a.orders_dine_in for a in all_recent) / total_orders,
                    "takeout": sum(a.orders_takeout for a in all_recent) / total_orders,
                    "delivery": sum(a.orders_delivery for a in all_recent) / total_orders,
                    "drive_through": sum(a.orders_drive_through for a in all_recent) / total_orders,
                }

        # Labor hours by role (avg same weekday last 4w)
        if recent_4w:
            f.labor_hours_by_role_avg = {
                "kitchen": sum(float(a.labor_hours_kitchen) for a in recent_4w) / len(recent_4w),
                "foh": sum(float(a.labor_hours_foh) for a in recent_4w) / len(recent_4w),
                "bar": sum(float(a.labor_hours_bar) for a in recent_4w) / len(recent_4w),
                "delivery": sum(float(a.labor_hours_delivery) for a in recent_4w) / len(recent_4w),
                "manager": sum(float(a.labor_hours_manager) for a in recent_4w) / len(recent_4w),
            }

        # Daypart avg
        if recent_4w:
            dp_sums: dict[str, dict] = defaultdict(lambda: {"sales": 0.0, "orders": 0})
            dp_count = 0
            for a in recent_4w:
                if a.daypart_json:
                    dp_count += 1
                    for dp, vals in a.daypart_json.items():
                        dp_sums[dp]["sales"] += vals.get("sales", 0)
                        dp_sums[dp]["orders"] += vals.get("orders", 0)
            if dp_count:
                f.daypart_avg = {
                    dp: {"sales": v["sales"] / dp_count, "orders": v["orders"] / dp_count}
                    for dp, v in dp_sums.items()
                }

        # Top SKU demand
        if recent_4w:
            sku_totals: dict[str, dict] = defaultdict(lambda: {"units": 0, "category": ""})
            for a in recent_4w:
                for sku in (a.top_skus_json or []):
                    sku_totals[sku["item_name"]]["units"] += sku["units_sold"]
                    sku_totals[sku["item_name"]]["category"] = sku.get("category", "")
            f.top_skus_avg = sorted(
                [{"item_name": k, "expected_units": round(v["units"] / len(recent_4w)), "category": v["category"]}
                 for k, v in sku_totals.items()],
                key=lambda x: x["expected_units"],
                reverse=True,
            )[:50]

        # External events
        day_events = events_by_date.get(td, [])
        f.events = [{"name": e.name, "type": e.event_type, "impact": e.impact_estimate} for e in day_events]
        f.is_holiday = any(e.event_type == "holiday" for e in day_events)

        multiplier = 1.0
        for e in day_events:
            if e.impact_estimate is not None:
                multiplier *= e.impact_estimate
        f.event_multiplier = multiplier

        weather_events = [e for e in day_events if e.event_type == "weather"]
        if weather_events and horizon <= 14:
            f.weather = weather_events[0].payload_json

        features.append(f)

    return features


def _linear_slope(points: list[tuple[int, float]]) -> float:
    """Simple linear regression slope from (x, y) pairs."""
    n = len(points)
    if n < 2:
        return 0.0
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] ** 2 for p in points)
    denom = n * sum_xx - sum_x ** 2
    if denom == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom
