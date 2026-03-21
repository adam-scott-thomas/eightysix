import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItemBulk(BaseModel):
    external_item_id: str
    quantity: int = Field(ge=1)
    line_total: float


class OrderBulkItem(BaseModel):
    external_order_id: str
    employee_external_id: str | None = None
    ordered_at: datetime
    order_total: float
    channel: str | None = None
    refund_amount: float = 0
    comp_amount: float = 0
    void_amount: float = 0
    prep_time_seconds: int | None = None
    items: list[OrderItemBulk] = []


class OrderResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    external_order_id: str
    employee_id: uuid.UUID | None
    ordered_at: datetime
    order_total: float
    channel: str | None
    refund_amount: float
    comp_amount: float
    void_amount: float
    prep_time_seconds: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
