import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("location_id", "external_order_id", name="uq_order_location_external"),
        Index("ix_orders_location_ordered_at", "location_id", "ordered_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    external_order_id: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    refund_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    comp_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    void_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    prep_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
