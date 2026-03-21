import uuid
from datetime import datetime
from pydantic import BaseModel


class IntegrityFlagResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    employee_id: uuid.UUID | None
    shift_id: uuid.UUID | None
    flag_type: str
    severity: str
    confidence: float
    status: str
    title: str
    message: str | None
    evidence_json: dict
    fraud_risk_score: float | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    status: str  # confirmed or dismissed
    notes: str | None = None
