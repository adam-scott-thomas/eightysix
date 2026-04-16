"""Feature registry — catalog of all forecast features with availability and targeting.

Features are organized by group:
  A: Shipping now (calendar + historical aggregates + operational context)
  B: POS integrations (transaction quality + demand composition + marketplace)
  C: Labor/scheduling
  D: Weather/events

Each feature has:
  - key: unique identifier used in code and drivers
  - label: human-readable name
  - group: A/B/C/D
  - available: whether the data source is wired
  - targets: which forecast targets use this feature
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FeatureGroup(str, Enum):
    A = "shipping_now"
    B = "pos_integrations"
    C = "labor_scheduling"
    D = "weather_events"


class ForecastTarget(str, Enum):
    sales = "sales"
    orders = "orders"
    labor = "labor"
    items = "items"


@dataclass
class FeatureDef:
    key: str
    label: str
    group: FeatureGroup
    available: bool
    targets: list[ForecastTarget] = field(default_factory=list)
    source: str = ""  # where it comes from (e.g. "daily_aggregates", "external_events")


# ── Group A: Shipping now ──────────────────────────────────────────────────

_GROUP_A = [
    # Calendar
    FeatureDef("dow", "Day of week", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor, ForecastTarget.items], "calendar"),
    FeatureDef("weekend_flag", "Weekend flag", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor], "calendar"),
    FeatureDef("week_of_month", "Week of month", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "calendar"),
    FeatureDef("month", "Month", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.items], "calendar"),
    FeatureDef("week_of_year", "Week of year", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.items], "calendar"),
    FeatureDef("payday_flag", "Payday flag", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "external_events"),
    FeatureDef("pre_post_payday", "Pre/post payday flag", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "external_events"),
    FeatureDef("holiday_flag", "Holiday flag", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor, ForecastTarget.items], "external_events"),
    FeatureDef("holiday_type", "Holiday type", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "external_events"),
    FeatureDef("holiday_uplift", "Holiday uplift/downlift estimate", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "external_events"),

    # Historical aggregates
    FeatureDef("trailing_7d_sales", "Trailing 7-day sales avg", FeatureGroup.A, True, [ForecastTarget.sales], "daily_aggregates"),
    FeatureDef("trailing_14d_sales", "Trailing 14-day sales avg", FeatureGroup.A, True, [ForecastTarget.sales], "daily_aggregates"),
    FeatureDef("trailing_28d_sales", "Trailing 28-day sales avg", FeatureGroup.A, True, [ForecastTarget.sales], "daily_aggregates"),
    FeatureDef("trailing_7d_orders", "Trailing 7-day orders avg", FeatureGroup.A, True, [ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("trailing_14d_orders", "Trailing 14-day orders avg", FeatureGroup.A, True, [ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("trailing_28d_orders", "Trailing 28-day orders avg", FeatureGroup.A, True, [ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("trailing_7d_labor", "Trailing 7-day labor avg", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("trailing_14d_labor", "Trailing 14-day labor avg", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("trailing_28d_labor", "Trailing 28-day labor avg", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("same_dow_avg_4w", "Same weekday avg (4 weeks)", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("same_dow_avg_8w", "Same weekday avg (8 weeks)", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("recent_trend_slope", "Recent trend slope", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("avg_ticket_7d", "Avg ticket trailing 7d", FeatureGroup.A, True, [ForecastTarget.sales], "daily_aggregates"),
    FeatureDef("avg_ticket_28d", "Avg ticket trailing 28d", FeatureGroup.A, True, [ForecastTarget.sales], "daily_aggregates"),
    FeatureDef("channel_mix_7d", "Channel mix trailing 7d", FeatureGroup.A, True, [ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("channel_mix_28d", "Channel mix trailing 28d", FeatureGroup.A, True, [ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("daypart_mix_7d", "Daypart mix trailing 7d", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("daypart_mix_28d", "Daypart mix trailing 28d", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders], "daily_aggregates"),
    FeatureDef("labor_per_order_7d", "Labor hours per order trailing 7d", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("labor_per_order_28d", "Labor hours per order trailing 28d", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("labor_per_100_sales_7d", "Labor hours per $100 sales trailing 7d", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),
    FeatureDef("labor_per_100_sales_28d", "Labor hours per $100 sales trailing 28d", FeatureGroup.A, True, [ForecastTarget.labor], "daily_aggregates"),

    # Operational context
    FeatureDef("open_hours", "Open hours", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor], "location"),
    FeatureDef("closed_day_flag", "Closed/shortened day flag", FeatureGroup.A, True, [ForecastTarget.sales, ForecastTarget.orders, ForecastTarget.labor], "store_context"),
    FeatureDef("partial_day_flag", "Partial day flag (today)", FeatureGroup.A, True, [ForecastTarget.sales], "runtime"),
    FeatureDef("history_depth", "History depth (days)", FeatureGroup.A, True, [], "daily_aggregates"),
    FeatureDef("synthetic_ratio", "Synthetic vs real basis ratio", FeatureGroup.A, True, [], "runtime"),
]

# ── Group B: POS integrations ─────────────────────────────────────────────

_GROUP_B = [
    # Transaction quality
    FeatureDef("discount_rate", "Discount rate", FeatureGroup.B, False, [ForecastTarget.sales], "orders"),
    FeatureDef("refund_rate", "Refund rate", FeatureGroup.B, False, [ForecastTarget.sales], "orders"),
    FeatureDef("void_rate", "Void rate", FeatureGroup.B, False, [ForecastTarget.sales], "orders"),
    FeatureDef("comp_rate", "Comp rate", FeatureGroup.B, False, [ForecastTarget.sales], "orders"),
    FeatureDef("tender_mix", "Tender mix", FeatureGroup.B, False, [ForecastTarget.sales], "orders"),
    FeatureDef("check_split_freq", "Check split frequency", FeatureGroup.B, False, [ForecastTarget.orders], "orders"),

    # Demand composition
    FeatureDef("category_mix", "Category mix", FeatureGroup.B, False, [ForecastTarget.items], "order_items"),
    FeatureDef("top_item_velocity", "Top item velocity", FeatureGroup.B, False, [ForecastTarget.items], "order_items"),
    FeatureDef("modifier_attachment_rate", "Modifier/add-on attachment rate", FeatureGroup.B, False, [ForecastTarget.items], "order_items"),
    FeatureDef("delivery_source_mix", "Delivery source mix", FeatureGroup.B, False, [ForecastTarget.orders], "orders"),
    FeatureDef("large_order_count", "Large order count", FeatureGroup.B, False, [ForecastTarget.sales, ForecastTarget.orders], "orders"),
    FeatureDef("eightysix_count", "86 count / item unavailable", FeatureGroup.B, False, [ForecastTarget.items], "events"),

    # Marketplace
    FeatureDef("doordash_share", "DoorDash order share", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
    FeatureDef("ubereats_share", "Uber Eats order share", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
    FeatureDef("grubhub_share", "Grubhub order share", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
    FeatureDef("marketplace_pause", "Marketplace pause/unpause windows", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
    FeatureDef("delivery_sla_degradation", "Delivery SLA degradation", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
    FeatureDef("marketplace_promo_flags", "Marketplace promo flags", FeatureGroup.B, False, [ForecastTarget.orders], "marketplace"),
]

# ── Group C: Labor/scheduling ─────────────────────────────────────────────

_GROUP_C = [
    FeatureDef("scheduled_hours_by_role", "Scheduled hours by role", FeatureGroup.C, False, [ForecastTarget.labor], "schedule"),
    FeatureDef("actual_hours_by_role", "Actual hours by role", FeatureGroup.C, False, [ForecastTarget.labor], "shifts"),
    FeatureDef("overtime_rate", "Overtime rate", FeatureGroup.C, False, [ForecastTarget.labor], "shifts"),
    FeatureDef("late_noshow_rate", "Late/no-show rate", FeatureGroup.C, False, [ForecastTarget.labor], "shifts"),
    FeatureDef("manager_coverage", "Manager coverage", FeatureGroup.C, False, [ForecastTarget.labor], "shifts"),
    FeatureDef("labor_cost_per_hour_role", "Labor cost per hour by role", FeatureGroup.C, False, [ForecastTarget.labor], "employees"),
    FeatureDef("hist_understaff_by_daypart", "Historical understaff incidents by daypart", FeatureGroup.C, False, [ForecastTarget.labor], "alerts"),
]

# ── Group D: Weather/events ───────────────────────────────────────────────

_GROUP_D = [
    FeatureDef("temperature_band", "Temperature band", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "weather"),
    FeatureDef("rain_snow_prob", "Rain/snow probability", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "weather"),
    FeatureDef("severe_weather_flag", "Severe weather flag", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "weather"),
    FeatureDef("local_event_attendance", "Local event attendance estimate", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "events"),
    FeatureDef("sports_game_flag", "Sports game flag", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "events"),
    FeatureDef("concert_convention_flag", "Concert/convention flag", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "events"),
    FeatureDef("school_in_out", "School in/out", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "school_calendar"),
    FeatureDef("tourism_intensity", "Tourism/holiday weekend intensity", FeatureGroup.D, False, [ForecastTarget.sales, ForecastTarget.orders], "events"),
]


# ── Registry ───────────────────────────────────────────────────────────────

ALL_FEATURES: list[FeatureDef] = _GROUP_A + _GROUP_B + _GROUP_C + _GROUP_D

FEATURE_MAP: dict[str, FeatureDef] = {f.key: f for f in ALL_FEATURES}


def get_available_features() -> list[FeatureDef]:
    """Return features that have their data source wired."""
    return [f for f in ALL_FEATURES if f.available]


def get_features_for_target(target: ForecastTarget) -> list[FeatureDef]:
    """Return available features that apply to a specific forecast target."""
    return [f for f in ALL_FEATURES if f.available and target in f.targets]


def get_source_coverage() -> dict[str, bool]:
    """Determine source coverage based on which feature groups are available."""
    groups_available = {g: False for g in FeatureGroup}
    for f in ALL_FEATURES:
        if f.available:
            groups_available[f.group] = True

    return {
        "pos": groups_available[FeatureGroup.B],
        "labor": groups_available[FeatureGroup.C],
        "holidays": any(f.available for f in ALL_FEATURES if f.key in ("holiday_flag", "holiday_type", "holiday_uplift")),
        "weather": any(f.available for f in ALL_FEATURES if f.key in ("temperature_band", "rain_snow_prob")),
        "marketplaces": any(f.available for f in ALL_FEATURES if f.key in ("doordash_share", "ubereats_share")),
        "events": any(f.available for f in ALL_FEATURES if f.key in ("local_event_attendance", "sports_game_flag")),
    }
