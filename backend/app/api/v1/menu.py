import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.menu_repo import MenuRepository
from app.schemas.dto import MenuItemDTO
from app.schemas.menu import MenuItemBulkItem, MenuItemResponse
from app.services.ingestion_service import IngestionService
from app.api.v1._recompute import maybe_recompute

router = APIRouter(prefix="/api/v1/locations/{location_id}/menu-items", tags=["menu"])


@router.get("", response_model=list[MenuItemResponse])
async def list_menu_items(
    location_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = MenuRepository(db)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)


@router.post("/bulk")
async def bulk_create_menu_items(
    location_id: uuid.UUID,
    items: list[MenuItemBulkItem],
    recompute: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ingestion = IngestionService(db)
    dtos = [
        MenuItemDTO(
            external_item_id=item.external_item_id,
            item_name=item.item_name,
            category=item.category,
            price=item.price,
            estimated_food_cost=item.estimated_food_cost,
        )
        for item in items
    ]
    summary = await ingestion._ingest_menu_items(location_id, dtos)
    result = summary.model_dump()
    snapshot = await maybe_recompute(db, location_id, recompute)
    if snapshot:
        result["dashboard"] = snapshot
    return result
