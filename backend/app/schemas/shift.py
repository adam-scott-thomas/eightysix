import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ShiftBulkItem(BaseModel):
    external_shift_id: str | None = None
    employee_external_id: str
    clock_in: datetime
    clock_out: datetime | None = None
    role_during_shift: str | None = None
    source_type: str = "manual"
    ip_address: str | None = None
    device_fingerprint: str | None = None
    geo_lat: float | None = None
    geo_lng: float | None = None
    geofence_match: bool | None = None


class ShiftResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    employee_id: uuid.UUID
    external_shift_id: str | None
    clock_in: datetime
    clock_out: datetime | None
    role_during_shift: str | None
    source_type: str
    ip_address: str | None
    device_fingerprint: str | None
    geo_lat: float | None
    geo_lng: float | None
    geofence_match: bool | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
