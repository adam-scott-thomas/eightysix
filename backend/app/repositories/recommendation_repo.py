import uuid
from datetime import datetime

from sqlalchemy import select

from app.db.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    async def get_pending_by_location(self, location_id: uuid.UUID) -> list[Recommendation]:
        stmt = select(Recommendation).where(
            Recommendation.location_id == location_id,
            Recommendation.status == "pending",
        ).order_by(Recommendation.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, location_id: uuid.UUID, status: str) -> list[Recommendation]:
        stmt = select(Recommendation).where(
            Recommendation.location_id == location_id,
            Recommendation.status == status,
        ).order_by(Recommendation.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def expire_stale(self, now: datetime) -> int:
        stmt = select(Recommendation).where(
            Recommendation.status == "pending",
            Recommendation.expires_at.isnot(None),
            Recommendation.expires_at <= now,
        )
        result = await self.db.execute(stmt)
        recs = list(result.scalars().all())
        for rec in recs:
            rec.status = "expired"
        if recs:
            await self.db.flush()
        return len(recs)
