import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class MenuItemBulkItem(BaseModel):
    external_item_id: str
    item_name: str = Field(max_length=255)
    category: str | None = None
    price: float
    estimated_food_cost: float | None = None


class MenuItemResponse(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    external_item_id: str
    item_name: str
    category: str | None
    price: float
    estimated_food_cost: float | None
    margin_band: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
