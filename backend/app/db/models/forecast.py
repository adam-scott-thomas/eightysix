"""Forecast snapshots — one row per location per target date per model run."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Float, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecast_location_target", "location_id", "target_date"),
        Index("ix_forecast_run", "run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # All forecasts from one run share a run_id

    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1-14 = detailed, 15-28 = broad
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # "baseline_v1", "pooled_v1", etc.

    # Point estimates
    expected_sales: Mapped[float] = mapped_column(Float, nullable=False)
    expected_orders: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_covers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Confidence bands
    sales_low: Mapped[float] = mapped_column(Float, nullable=False)
    sales_high: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.8)
    # 0.8 = 80% of outcomes expected within [low, high]

    # Channel breakdown
    # {"dine_in": N, "takeout": N, "delivery": N}
    orders_by_channel_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Daypart breakdown
    # {"breakfast": {"sales": N, "orders": N}, "lunch": {...}, "dinner": {...}}
    daypart_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Labor recommendation
    # {"kitchen": 24.0, "foh": 32.0, "bar": 8.0, "delivery": 12.0, "total": 76.0}
    labor_hours_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Top SKU demand (top 50)
    # [{"item_name": "...", "expected_units": N, "category": "..."}]
    top_skus_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Risk flags
    # [{"flag": "understaffed", "message": "...", "severity": "warning"}]
    risk_flags_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # "Why" explanation (human-readable)
    explanation: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Purchasing signal
    # [{"item": "chicken", "adjustment_pct": 12, "reason": "game day demand"}]
    purchasing_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
