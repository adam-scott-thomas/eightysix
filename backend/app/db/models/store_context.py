"""Store-level context events that affect forecasts — closures, promos, menu changes, etc."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StoreContext(Base):
    __tablename__ = "store_context"
    __table_args__ = (
        Index("ix_store_ctx_location_date", "location_id", "context_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    context_date: Mapped[date] = mapped_column(Date, nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: hours_change, closure, promo, menu_change, pricing_change, special_event, staffing_change
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
