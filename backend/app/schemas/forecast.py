"""Forecast contract v1 — canonical API + DB shape.

Every type here maps 1:1 to the spec. The baseline engine, ML engine,
API layer, and frontend all speak this contract.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────


class ModelFamily(str, Enum):
    baseline = "baseline"
    ml = "ml"


class ForecastStatus(str, Enum):
    ready = "ready"
    degraded = "degraded"
    insufficient_history = "insufficient_history"


class ConfidenceBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Channel(str, Enum):
    dine_in = "dine_in"
    pickup = "pickup"
    delivery = "delivery"
    drive_thru = "drive_thru"
    other = "other"


class Daypart(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    afternoon = "afternoon"
    dinner = "dinner"
    late_night = "late_night"


class AlertType(str, Enum):
    understaff_risk = "understaff_risk"
    overstaff_risk = "overstaff_risk"
    slow_day_risk = "slow_day_risk"
    stockout_risk = "stockout_risk"
    delivery_spike_risk = "delivery_spike_risk"
    data_quality_warning = "data_quality_warning"


class AlertThresholdBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DriverSource(str, Enum):
    calendar = "calendar"
    history = "history"
    holiday = "holiday"
    weather = "weather"
    events = "events"
    labor = "labor"
    marketplace = "marketplace"


class RecommendationType(str, Enum):
    adjust_labor = "adjust_labor"
    increase_purchase = "increase_purchase"
    decrease_purchase = "decrease_purchase"
    prep_more = "prep_more"
    pause_discount = "pause_discount"
    run_promo = "run_promo"


class RecommendationPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BiasDirection(str, Enum):
    high = "high"
    low = "low"
    neutral = "neutral"


class HorizonBucket(str, Enum):
    d1_7 = "d1_7"
    d8_14 = "d8_14"
    d15_28 = "d15_28"


class GeneratedBy(str, Enum):
    manual = "manual"
    scheduled = "scheduled"
    api = "api"


# ── Value types ────────────────────────────────────────────────────────────


class MetricBand(BaseModel):
    point: float
    low: float
    high: float


class ModelInfo(BaseModel):
    name: str  # "baseline_v1", "ml_v1", etc.
    version: str
    family: ModelFamily
    champion: bool


class DataBasis(BaseModel):
    real_history_days: int
    synthetic_history_days: int
    aggregate_days_used: int
    max_actual_date: date | None = None


class SourceCoverage(BaseModel):
    pos: bool = False
    labor: bool = False
    holidays: bool = False
    weather: bool = False
    marketplaces: bool = False
    events: bool = False


class Confidence(BaseModel):
    score_0_to_1: float = Field(ge=0, le=1)
    band: ConfidenceBand


# ── Day-level types ────────────────────────────────────────────────────────


class ChannelForecast(BaseModel):
    channel: Channel
    sales: MetricBand
    orders: MetricBand
    mix_share_point: float


class DaypartForecast(BaseModel):
    daypart: Daypart
    sales: MetricBand
    orders: MetricBand
    labor_hours: MetricBand
    mix_share_point: float


class ForecastAlert(BaseModel):
    type: AlertType
    severity_0_to_100: float = Field(ge=0, le=100)
    threshold_band: AlertThresholdBand
    message: str


class ForecastDriver(BaseModel):
    feature_key: str
    label: str
    direction: Literal["up", "down"]
    impact_pct: float
    rank: int
    source: DriverSource


class ForecastRecommendation(BaseModel):
    type: RecommendationType
    priority: RecommendationPriority
    message: str
    delta_value: float | None = None
    delta_unit: Literal["hours", "percent", "units", "dollars"] | None = None


class DayActuals(BaseModel):
    sales: float
    orders: int
    labor_hours: float
    avg_ticket: float | None = None
    covers: int | None = None
    channels: dict[str, dict[str, float]] | None = None
    dayparts: dict[str, dict[str, float]] | None = None


class DayEvaluation(BaseModel):
    sales_abs_error: float
    sales_pct_error: float
    orders_abs_error: float
    orders_pct_error: float
    labor_abs_error: float
    labor_pct_error: float
    in_sales_band: bool
    in_orders_band: bool
    in_labor_band: bool
    bias_direction: BiasDirection


# ── Scoring types ──────────────────────────────────────────────────────────


class HorizonScore(BaseModel):
    bucket: HorizonBucket
    sales_wape: float
    orders_wape: float
    labor_wmae: float
    bias: float
    interval_coverage: float
    channel_mix_error: float
    daypart_mix_error: float
    score_0_to_100: float


class BacktestSnapshot(BaseModel):
    scored_at: datetime
    history_window_days: int
    horizon_buckets: list[HorizonScore]
    overall_model_score_0_to_100: float
    promoted: bool


# ── ForecastDay ────────────────────────────────────────────────────────────


class ForecastDay(BaseModel):
    date: date
    day_of_week: int = Field(ge=0, le=6)
    horizon_days: int

    confidence: Confidence

    sales: MetricBand
    orders: MetricBand
    labor_hours: MetricBand

    avg_ticket: MetricBand | None = None
    covers: MetricBand | None = None

    channels: list[ChannelForecast] = []
    dayparts: list[DaypartForecast] = []

    alerts: list[ForecastAlert] = []
    drivers: list[ForecastDriver] = []
    recommendations: list[ForecastRecommendation] = []

    actuals: DayActuals | None = None
    evaluation: DayEvaluation | None = None


# ── ForecastRun (top-level) ────────────────────────────────────────────────


class ForecastRun(BaseModel):
    id: str
    location_id: str

    as_of_ts: datetime
    forecast_start_date: date
    forecast_end_date: date

    model: ModelInfo
    data_basis: DataBasis
    source_coverage: SourceCoverage

    status: ForecastStatus
    degraded_reasons: list[str] = []

    run_notes: list[str] = []
    generated_by: GeneratedBy

    days: list[ForecastDay] = []
    backtest_snapshot: BacktestSnapshot | None = None
