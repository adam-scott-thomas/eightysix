import uuid

from sqlalchemy import select

from app.db.models.menu_item import MenuItem
from app.repositories.base import BaseRepository


class MenuRepository(BaseRepository[MenuItem]):
    model = MenuItem

    async def get_by_external_id(self, location_id: uuid.UUID, external_id: str) -> MenuItem | None:
        stmt = select(MenuItem).where(
            MenuItem.location_id == location_id,
            MenuItem.external_item_id == external_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_location(self, location_id: uuid.UUID) -> list[MenuItem]:
        stmt = select(MenuItem).where(
            MenuItem.location_id == location_id,
            MenuItem.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
