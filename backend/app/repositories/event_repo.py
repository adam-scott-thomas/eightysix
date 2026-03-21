import uuid
from datetime import datetime

from sqlalchemy import select

from app.db.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    async def get_by_time_range(
        self, location_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Event]:
        stmt = select(Event).where(
            Event.location_id == location_id,
            Event.started_at >= start,
            Event.started_at <= end,
        ).order_by(Event.started_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
