"""External events — holidays, weather, local events, school calendar, payday effects."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Float, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExternalEvent(Base):
    __tablename__ = "external_events"
    __table_args__ = (
        Index("ix_ext_event_date_type", "event_date", "event_type"),
        Index("ix_ext_event_location", "location_id", "event_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # NULL location_id = applies to all locations in region

    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: holiday, local_event, weather, school_calendar, payday, sports, concert, convention
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    impact_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Multiplier: 1.0 = normal, 1.2 = +20%, 0.8 = -20%
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Weather payload: {"temp_high": 82, "precip_chance": 0.6, "condition": "rain"}
    # Event payload: {"venue": "...", "expected_attendance": 5000, "distance_miles": 2.3}
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
