import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"
    __table_args__ = (
        Index("ix_snapshots_location_at", "location_id", "snapshot_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dashboard_status: Mapped[str] = mapped_column(String(20), nullable=False)
    readiness_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    completeness_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    throughput_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    staffing_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    menu_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    leakage_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    integrity_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    alerts_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recommendations_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    predictions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    timeline_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
