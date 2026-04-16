"""Forecast run — one row per model execution per location."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    __table_args__ = (
        Index("ix_fcrun_location_ts", "location_id", "as_of_ts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    as_of_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Model info (denormalized for fast reads)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_family: Mapped[str] = mapped_column(String(20), nullable=False)  # baseline | ml
    model_champion: Mapped[bool] = mapped_column(Boolean, default=True)

    # Data basis
    real_history_days: Mapped[int] = mapped_column(Integer, default=0)
    synthetic_history_days: Mapped[int] = mapped_column(Integer, default=0)
    aggregate_days_used: Mapped[int] = mapped_column(Integer, default=0)
    max_actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Source coverage
    source_coverage_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # {"pos": false, "labor": false, "holidays": true, "weather": false, ...}

    status: Mapped[str] = mapped_column(String(30), nullable=False)  # ready | degraded | insufficient_history
    degraded_reasons_json: Mapped[list] = mapped_column(JSONB, default=list)

    run_notes_json: Mapped[list] = mapped_column(JSONB, default=list)
    generated_by: Mapped[str] = mapped_column(String(20), nullable=False)  # manual | scheduled | api

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    # Relationships
    days: Mapped[list["ForecastDayRow"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    backtest: Mapped["ForecastBacktestSnapshot | None"] = relationship(back_populates="run", uselist=False, cascade="all, delete-orphan")


class ForecastDayRow(Base):
    __tablename__ = "forecast_days"
    __table_args__ = (
        Index("ix_fcday_run", "run_id"),
        Index("ix_fcday_run_date", "run_id", "target_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Confidence
    confidence_score: Mapped[float] = mapped_column(nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(10), nullable=False)  # low | medium | high

    # Core MetricBands stored as 3 columns each
    sales_point: Mapped[float] = mapped_column(nullable=False)
    sales_low: Mapped[float] = mapped_column(nullable=False)
    sales_high: Mapped[float] = mapped_column(nullable=False)

    orders_point: Mapped[float] = mapped_column(nullable=False)
    orders_low: Mapped[float] = mapped_column(nullable=False)
    orders_high: Mapped[float] = mapped_column(nullable=False)

    labor_hours_point: Mapped[float] = mapped_column(nullable=False)
    labor_hours_low: Mapped[float] = mapped_column(nullable=False)
    labor_hours_high: Mapped[float] = mapped_column(nullable=False)

    avg_ticket_point: Mapped[float | None] = mapped_column(nullable=True)
    avg_ticket_low: Mapped[float | None] = mapped_column(nullable=True)
    avg_ticket_high: Mapped[float | None] = mapped_column(nullable=True)

    covers_point: Mapped[int | None] = mapped_column(nullable=True)
    covers_low: Mapped[int | None] = mapped_column(nullable=True)
    covers_high: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    run: Mapped["ForecastRun"] = relationship(back_populates="days")
    channels: Mapped[list["ForecastDayChannel"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    dayparts: Mapped[list["ForecastDayDaypart"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    alerts: Mapped[list["ForecastDayAlert"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    drivers: Mapped[list["ForecastDayDriver"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    recommendations: Mapped[list["ForecastDayRecommendation"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    actuals: Mapped["ForecastDayActuals | None"] = relationship(back_populates="day", uselist=False, cascade="all, delete-orphan")


class ForecastDayChannel(Base):
    __tablename__ = "forecast_day_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    sales_point: Mapped[float] = mapped_column(nullable=False)
    sales_low: Mapped[float] = mapped_column(nullable=False)
    sales_high: Mapped[float] = mapped_column(nullable=False)
    orders_point: Mapped[float] = mapped_column(nullable=False)
    orders_low: Mapped[float] = mapped_column(nullable=False)
    orders_high: Mapped[float] = mapped_column(nullable=False)
    mix_share_point: Mapped[float] = mapped_column(nullable=False)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="channels")


class ForecastDayDaypart(Base):
    __tablename__ = "forecast_day_dayparts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    daypart: Mapped[str] = mapped_column(String(20), nullable=False)
    sales_point: Mapped[float] = mapped_column(nullable=False)
    sales_low: Mapped[float] = mapped_column(nullable=False)
    sales_high: Mapped[float] = mapped_column(nullable=False)
    orders_point: Mapped[float] = mapped_column(nullable=False)
    orders_low: Mapped[float] = mapped_column(nullable=False)
    orders_high: Mapped[float] = mapped_column(nullable=False)
    labor_hours_point: Mapped[float] = mapped_column(nullable=False)
    labor_hours_low: Mapped[float] = mapped_column(nullable=False)
    labor_hours_high: Mapped[float] = mapped_column(nullable=False)
    mix_share_point: Mapped[float] = mapped_column(nullable=False)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="dayparts")


class ForecastDayAlert(Base):
    __tablename__ = "forecast_day_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity_0_to_100: Mapped[float] = mapped_column(nullable=False)
    threshold_band: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="alerts")


class ForecastDayDriver(Base):
    __tablename__ = "forecast_day_drivers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # up | down
    impact_pct: Mapped[float] = mapped_column(nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="drivers")


class ForecastDayRecommendation(Base):
    __tablename__ = "forecast_day_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rec_type: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    delta_value: Mapped[float | None] = mapped_column(nullable=True)
    delta_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="recommendations")


class ForecastDayActuals(Base):
    __tablename__ = "forecast_day_actuals"
    __table_args__ = (
        Index("ix_fcactuals_day", "day_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    sales: Mapped[float] = mapped_column(nullable=False)
    orders: Mapped[int] = mapped_column(nullable=False)
    labor_hours: Mapped[float] = mapped_column(nullable=False)
    avg_ticket: Mapped[float | None] = mapped_column(nullable=True)
    covers: Mapped[int | None] = mapped_column(nullable=True)
    channels_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dayparts_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Evaluation (computed when actuals are filled)
    sales_abs_error: Mapped[float | None] = mapped_column(nullable=True)
    sales_pct_error: Mapped[float | None] = mapped_column(nullable=True)
    orders_abs_error: Mapped[float | None] = mapped_column(nullable=True)
    orders_pct_error: Mapped[float | None] = mapped_column(nullable=True)
    labor_abs_error: Mapped[float | None] = mapped_column(nullable=True)
    labor_pct_error: Mapped[float | None] = mapped_column(nullable=True)
    in_sales_band: Mapped[bool | None] = mapped_column(nullable=True)
    in_orders_band: Mapped[bool | None] = mapped_column(nullable=True)
    in_labor_band: Mapped[bool | None] = mapped_column(nullable=True)
    bias_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)

    day: Mapped["ForecastDayRow"] = relationship(back_populates="actuals")


class ForecastBacktestSnapshot(Base):
    __tablename__ = "forecast_backtest_snapshots"
    __table_args__ = (
        Index("ix_fcbacktest_run", "run_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    history_window_days: Mapped[int] = mapped_column(nullable=False)
    horizon_buckets_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    # [{"bucket": "d1_7", "sales_wape": 0.12, "orders_wape": 0.10, ...}]
    overall_model_score_0_to_100: Mapped[float] = mapped_column(nullable=False)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)

    run: Mapped["ForecastRun"] = relationship(back_populates="backtest")
