import uuid

from sqlalchemy import select

from app.db.models.integrity_flag import IntegrityFlag
from app.repositories.base import BaseRepository


class IntegrityFlagRepository(BaseRepository[IntegrityFlag]):
    model = IntegrityFlag

    async def get_open_by_location(self, location_id: uuid.UUID) -> list[IntegrityFlag]:
        stmt = select(IntegrityFlag).where(
            IntegrityFlag.location_id == location_id,
            IntegrityFlag.status == "open",
        ).order_by(IntegrityFlag.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, location_id: uuid.UUID, status: str) -> list[IntegrityFlag]:
        stmt = select(IntegrityFlag).where(
            IntegrityFlag.location_id == location_id,
            IntegrityFlag.status == status,
        ).order_by(IntegrityFlag.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_shift(self, shift_id: uuid.UUID) -> list[IntegrityFlag]:
        stmt = select(IntegrityFlag).where(IntegrityFlag.shift_id == shift_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
