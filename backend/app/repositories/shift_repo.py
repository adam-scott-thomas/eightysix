import uuid
from datetime import datetime

from sqlalchemy import select

from app.db.models.shift import Shift
from app.repositories.base import BaseRepository


class ShiftRepository(BaseRepository[Shift]):
    model = Shift

    async def get_by_external_id(self, location_id: uuid.UUID, external_id: str) -> Shift | None:
        if not external_id:
            return None
        stmt = select(Shift).where(
            Shift.location_id == location_id,
            Shift.external_shift_id == external_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_shifts(self, location_id: uuid.UUID) -> list[Shift]:
        stmt = select(Shift).where(
            Shift.location_id == location_id,
            Shift.clock_out.is_(None),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self, location_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Shift]:
        stmt = select(Shift).where(
            Shift.location_id == location_id,
            Shift.clock_in >= start,
            Shift.clock_in <= end,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_employee(self, employee_id: uuid.UUID, start: datetime, end: datetime) -> list[Shift]:
        stmt = select(Shift).where(
            Shift.employee_id == employee_id,
            Shift.clock_in >= start,
            Shift.clock_in <= end,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
