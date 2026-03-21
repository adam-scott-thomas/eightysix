import uuid
from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    alert_type: str
    severity: str
    status: str
    title: str
    message: str | None
    evidence_json: dict | None
    triggered_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    ttl_minutes: int | None

    model_config = {"from_attributes": True}
