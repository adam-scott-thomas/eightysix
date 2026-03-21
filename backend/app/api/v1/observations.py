import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.observation import Observation
from app.repositories.observation_repo import ObservationRepository
from app.schemas.observation import ObservationCreate, ObservationResponse

router = APIRouter(prefix="/api/v1/locations/{location_id}/observations", tags=["observations"])

VALID_METRIC_KEYS = {"oven_efficiency", "manager_staff_count", "inventory_low", "rush_severity", "custom"}


@router.post("", response_model=ObservationResponse, status_code=201)
async def create_observation(
    location_id: uuid.UUID,
    body: ObservationCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.metric_key not in VALID_METRIC_KEYS:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Invalid metric_key. Valid: {VALID_METRIC_KEYS}")

    repo = ObservationRepository(db)
    obs = Observation(
        location_id=location_id,
        **body.model_dump(),
    )
    return await repo.create(obs)


@router.get("", response_model=list[ObservationResponse])
async def list_observations(
    location_id: uuid.UUID,
    metric_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = ObservationRepository(db)
    if metric_key:
        return await repo.get_by_metric(location_id, metric_key)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)
