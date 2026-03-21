import uuid
from datetime import datetime
from pydantic import BaseModel


class EventCreate(BaseModel):
    event_type: str
    severity: str = "info"
    started_at: datetime
    ended_at: datetime | None = None
    payload_json: dict | None = None
    source_type: str = "manual"
    entered_by: uuid.UUID | None = None


class EventResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    event_type: str
    severity: str
    started_at: datetime
    ended_at: datetime | None
    payload_json: dict | None
    source_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
