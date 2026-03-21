import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class EmployeeBulkItem(BaseModel):
    external_employee_id: str
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: str = Field(max_length=50)
    hourly_rate: float | None = None


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    external_employee_id: str
    first_name: str
    last_name: str
    role: str
    hourly_rate: float | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
