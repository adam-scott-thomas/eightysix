import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    name: str = Field(max_length=255)
    timezone: str = Field(max_length=50, examples=["America/Detroit"])
    business_hours_json: dict | None = None
    default_hourly_rate: float = 15.00


class LocationUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    business_hours_json: dict | None = None
    default_hourly_rate: float | None = None
    is_active: bool | None = None


class LocationResponse(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str
    business_hours_json: dict | None
    default_hourly_rate: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
