from datetime import datetime
from typing import Protocol

from app.schemas.dto import MenuItemDTO, OrderDTO, OrderItemDTO


class POSProvider(Protocol):
    def fetch_orders(
        self, location_id: str, start: datetime, end: datetime
    ) -> list[OrderDTO]: ...

    def fetch_menu(self, location_id: str) -> list[MenuItemDTO]: ...

    def fetch_order_items(
        self, location_id: str, order_ids: list[str]
    ) -> list[OrderItemDTO]: ...
