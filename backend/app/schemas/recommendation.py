import uuid
from datetime import datetime
from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    alert_id: uuid.UUID | None
    category: str
    status: str
    title: str
    reason: str
    action_description: str | None
    confidence: float
    estimated_impact_json: dict | None
    expires_at: datetime | None
    created_at: datetime
    applied_at: datetime | None
    dismissed_at: datetime | None

    model_config = {"from_attributes": True}
