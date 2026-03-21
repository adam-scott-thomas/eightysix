import uuid
from datetime import datetime
from pydantic import BaseModel


class ObservationCreate(BaseModel):
    metric_key: str
    value_number: float | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_json: dict | None = None
    observed_at: datetime
    source_type: str = "manual"
    source_ref: str | None = None
    entered_by: uuid.UUID | None = None
    confidence: float | None = None
    notes: str | None = None


class ObservationResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    metric_key: str
    value_number: float | None
    value_text: str | None
    value_boolean: bool | None
    value_json: dict | None
    observed_at: datetime
    source_type: str
    confidence: float | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
