"""Daily rollup of location metrics — the core feature table for forecasting."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyAggregate(Base):
    __tablename__ = "daily_aggregates"
    __table_args__ = (
        Index("ix_daily_agg_location_date", "location_id", "agg_date", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agg_date: Mapped[date] = mapped_column(Date, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon, 6=Sun

    # Revenue
    net_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gross_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    refund_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    comp_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    void_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    avg_ticket: Mapped[float] = mapped_column(Numeric(8, 2), default=0)

    # Orders
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    orders_dine_in: Mapped[int] = mapped_column(Integer, default=0)
    orders_takeout: Mapped[int] = mapped_column(Integer, default=0)
    orders_delivery: Mapped[int] = mapped_column(Integer, default=0)
    orders_drive_through: Mapped[int] = mapped_column(Integer, default=0)
    covers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Labor
    total_labor_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    total_labor_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    labor_hours_kitchen: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_foh: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_bar: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_delivery: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_manager: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_cost_ratio: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Daypart breakdown (JSONB)
    # {"breakfast": {"sales": N, "orders": N}, "lunch": {...}, "dinner": {...}, "late": {...}}
    daypart_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Top SKUs (JSONB — top 50 items by units sold)
    # [{"item_name": "...", "units_sold": N, "revenue": N, "category": "..."}]
    top_skus_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Category breakdown
    # {"entrees": {"units": N, "revenue": N}, "appetizers": {...}, ...}
    category_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
