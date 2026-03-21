import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.shift_repo import ShiftRepository
from app.schemas.dto import ShiftDTO
from app.schemas.shift import ShiftBulkItem, ShiftResponse
from app.services.ingestion_service import IngestionService
from app.api.v1._recompute import maybe_recompute

router = APIRouter(prefix="/api/v1/locations/{location_id}/shifts", tags=["shifts"])


@router.get("", response_model=list[ShiftResponse])
async def list_shifts(
    location_id: uuid.UUID,
    active: bool | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = ShiftRepository(db)
    if active is True:
        return await repo.get_active_shifts(location_id)
    if start and end:
        return await repo.get_by_time_range(location_id, start, end)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)


@router.post("/bulk")
async def bulk_create_shifts(
    location_id: uuid.UUID,
    items: list[ShiftBulkItem],
    recompute: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ingestion = IngestionService(db)
    dtos = [
        ShiftDTO(
            external_shift_id=item.external_shift_id,
            employee_external_id=item.employee_external_id,
            clock_in=item.clock_in,
            clock_out=item.clock_out,
            role_during_shift=item.role_during_shift,
            source_type=item.source_type,
            ip_address=item.ip_address,
            device_fingerprint=item.device_fingerprint,
            geo_lat=item.geo_lat,
            geo_lng=item.geo_lng,
            geofence_match=item.geofence_match,
        )
        for item in items
    ]
    summary = await ingestion._ingest_shifts(location_id, dtos)
    result = summary.model_dump()
    snapshot = await maybe_recompute(db, location_id, recompute)
    if snapshot:
        result["dashboard"] = snapshot
    return result
