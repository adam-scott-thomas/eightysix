import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.repositories.recommendation_repo import RecommendationRepository
from app.schemas.recommendation import RecommendationResponse

router = APIRouter(tags=["recommendations"])


@router.get(
    "/api/v1/locations/{location_id}/recommendations",
    response_model=list[RecommendationResponse],
)
async def list_recommendations(
    location_id: uuid.UUID,
    status: str = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = RecommendationRepository(db)
    return await repo.get_by_status(location_id, status)


@router.patch("/api/v1/recommendations/{id}/apply", response_model=RecommendationResponse)
async def apply_recommendation(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = RecommendationRepository(db)
    rec = await repo.get_by_id(id)
    if not rec:
        raise NotFoundError("Recommendation", str(id))
    rec.status = "applied"
    rec.applied_at = datetime.now(timezone.utc)
    await db.flush()
    return rec


@router.patch("/api/v1/recommendations/{id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = RecommendationRepository(db)
    rec = await repo.get_by_id(id)
    if not rec:
        raise NotFoundError("Recommendation", str(id))
    rec.status = "dismissed"
    rec.dismissed_at = datetime.now(timezone.utc)
    await db.flush()
    return rec
