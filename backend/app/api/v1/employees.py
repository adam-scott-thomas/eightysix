import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.employee_repo import EmployeeRepository
from app.schemas.dto import EmployeeDTO
from app.schemas.employee import EmployeeBulkItem, EmployeeResponse
from app.services.ingestion_service import IngestionService
from app.api.v1._recompute import maybe_recompute

router = APIRouter(prefix="/api/v1/locations/{location_id}/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    location_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = EmployeeRepository(db)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)


@router.post("/bulk")
async def bulk_create_employees(
    location_id: uuid.UUID,
    items: list[EmployeeBulkItem],
    recompute: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ingestion = IngestionService(db)
    dtos = [
        EmployeeDTO(
            external_employee_id=item.external_employee_id,
            first_name=item.first_name,
            last_name=item.last_name,
            role=item.role,
            hourly_rate=item.hourly_rate,
        )
        for item in items
    ]
    summary = await ingestion._ingest_employees(location_id, dtos)
    result = summary.model_dump()
    snapshot = await maybe_recompute(db, location_id, recompute)
    if snapshot:
        result["dashboard"] = snapshot
    return result
