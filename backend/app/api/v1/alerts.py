import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertResponse

router = APIRouter(tags=["alerts"])


@router.get(
    "/api/v1/locations/{location_id}/alerts",
    response_model=list[AlertResponse],
)
async def list_alerts(
    location_id: uuid.UUID,
    status: str = Query(default="active"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(db)
    return await repo.get_by_status(location_id, status)


@router.patch("/api/v1/alerts/{id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = AlertRepository(db)
    alert = await repo.get_by_id(id)
    if not alert:
        raise NotFoundError("Alert", str(id))
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    return alert


@router.patch("/api/v1/alerts/{id}/resolve", response_model=AlertResponse)
async def resolve_alert(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = AlertRepository(db)
    alert = await repo.get_by_id(id)
    if not alert:
        raise NotFoundError("Alert", str(id))
    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return alert
