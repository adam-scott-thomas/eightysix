import uuid
from datetime import datetime

from sqlalchemy import select

from app.db.models.dashboard_snapshot import DashboardSnapshot
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository[DashboardSnapshot]):
    model = DashboardSnapshot

    async def get_latest(self, location_id: uuid.UUID) -> DashboardSnapshot | None:
        stmt = (
            select(DashboardSnapshot)
            .where(DashboardSnapshot.location_id == location_id)
            .order_by(DashboardSnapshot.snapshot_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_timeline(
        self, location_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[DashboardSnapshot]:
        stmt = (
            select(DashboardSnapshot)
            .where(
                DashboardSnapshot.location_id == location_id,
                DashboardSnapshot.snapshot_at >= start,
                DashboardSnapshot.snapshot_at <= end,
            )
            .order_by(DashboardSnapshot.snapshot_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
