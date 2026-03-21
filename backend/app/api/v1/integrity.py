import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.repositories.integrity_repo import IntegrityFlagRepository
from app.schemas.integrity import IntegrityFlagResponse, ReviewRequest

router = APIRouter(tags=["integrity"])


@router.get(
    "/api/v1/locations/{location_id}/integrity-flags",
    response_model=list[IntegrityFlagResponse],
)
async def list_integrity_flags(
    location_id: uuid.UUID,
    status: str = Query(default="open"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = IntegrityFlagRepository(db)
    return await repo.get_by_status(location_id, status)


@router.patch("/api/v1/integrity-flags/{id}/review", response_model=IntegrityFlagResponse)
async def review_integrity_flag(
    id: uuid.UUID,
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = IntegrityFlagRepository(db)
    flag = await repo.get_by_id(id)
    if not flag:
        raise NotFoundError("IntegrityFlag", str(id))
    if body.status not in ("confirmed", "dismissed"):
        from app.core.exceptions import ValidationError
        raise ValidationError("Status must be 'confirmed' or 'dismissed'")
    flag.status = body.status
    flag.resolved_at = datetime.now(timezone.utc)
    if body.notes:
        flag.message = (flag.message or "") + f"\n\nReview notes: {body.notes}"
    await db.flush()
    return flag
