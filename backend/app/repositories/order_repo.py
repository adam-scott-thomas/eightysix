import uuid
from datetime import datetime

from sqlalchemy import select, func

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def get_by_external_id(self, location_id: uuid.UUID, external_id: str) -> Order | None:
        stmt = select(Order).where(
            Order.location_id == location_id,
            Order.external_order_id == external_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_time_range(
        self, location_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Order]:
        stmt = select(Order).where(
            Order.location_id == location_id,
            Order.ordered_at >= start,
            Order.ordered_at <= end,
        ).order_by(Order.ordered_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_revenue_today(self, location_id: uuid.UUID, day_start: datetime, day_end: datetime) -> float:
        stmt = select(func.coalesce(func.sum(Order.order_total), 0)).where(
            Order.location_id == location_id,
            Order.ordered_at >= day_start,
            Order.ordered_at <= day_end,
        )
        result = await self.db.execute(stmt)
        return float(result.scalar_one())

    async def get_order_count(self, location_id: uuid.UUID, start: datetime, end: datetime) -> int:
        stmt = select(func.count()).select_from(Order).where(
            Order.location_id == location_id,
            Order.ordered_at >= start,
            Order.ordered_at <= end,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()


class OrderItemRepository(BaseRepository[OrderItem]):
    model = OrderItem

    async def get_by_order_ids(self, order_ids: list[uuid.UUID]) -> list[OrderItem]:
        if not order_ids:
            return []
        stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
