"""DTOs shared between providers and ingestion layer."""
from datetime import datetime
from pydantic import BaseModel


class OrderDTO(BaseModel):
    external_order_id: str
    employee_external_id: str | None = None
    ordered_at: datetime
    order_total: float
    channel: str | None = None
    refund_amount: float = 0
    comp_amount: float = 0
    void_amount: float = 0
    prep_time_seconds: int | None = None


class OrderItemDTO(BaseModel):
    external_order_id: str
    external_item_id: str
    quantity: int
    line_total: float


class MenuItemDTO(BaseModel):
    external_item_id: str
    item_name: str
    category: str | None = None
    price: float
    estimated_food_cost: float | None = None


class EmployeeDTO(BaseModel):
    external_employee_id: str
    first_name: str
    last_name: str
    role: str
    hourly_rate: float | None = None


class ShiftDTO(BaseModel):
    external_shift_id: str | None = None
    employee_external_id: str
    clock_in: datetime
    clock_out: datetime | None = None
    role_during_shift: str | None = None
    source_type: str = "stub"
    ip_address: str | None = None
    device_fingerprint: str | None = None
    geo_lat: float | None = None
    geo_lng: float | None = None
    geofence_match: bool | None = None
