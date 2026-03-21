import uuid

from sqlalchemy import select

from app.db.models.observation import Observation
from app.repositories.base import BaseRepository


class ObservationRepository(BaseRepository[Observation]):
    model = Observation

    async def get_by_metric(
        self, location_id: uuid.UUID, metric_key: str
    ) -> list[Observation]:
        stmt = select(Observation).where(
            Observation.location_id == location_id,
            Observation.metric_key == metric_key,
        ).order_by(Observation.observed_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
