import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.dto import OrderDTO, OrderItemDTO
from app.schemas.order import OrderBulkItem, OrderResponse
from app.services.ingestion_service import IngestionService
from app.api.v1._recompute import maybe_recompute

router = APIRouter(prefix="/api/v1/locations/{location_id}/orders", tags=["orders"])


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    location_id: uuid.UUID,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = OrderRepository(db)
    if start and end:
        return await repo.get_by_time_range(location_id, start, end)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)


@router.post("/bulk")
async def bulk_create_orders(
    location_id: uuid.UUID,
    items: list[OrderBulkItem],
    recompute: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ingestion = IngestionService(db)
    order_dtos = [
        OrderDTO(
            external_order_id=item.external_order_id,
            employee_external_id=item.employee_external_id,
            ordered_at=item.ordered_at,
            order_total=item.order_total,
            channel=item.channel,
            refund_amount=item.refund_amount,
            comp_amount=item.comp_amount,
            void_amount=item.void_amount,
            prep_time_seconds=item.prep_time_seconds,
        )
        for item in items
    ]
    order_summary = await ingestion._ingest_orders(location_id, order_dtos)

    # Ingest order items (nested in each order)
    oi_dtos = []
    for item in items:
        for oi in item.items:
            oi_dtos.append(OrderItemDTO(
                external_order_id=item.external_order_id,
                external_item_id=oi.external_item_id,
                quantity=oi.quantity,
                line_total=oi.line_total,
            ))

    oi_summary = await ingestion._ingest_order_items(location_id, oi_dtos)

    result = {
        "orders": order_summary.model_dump(),
        "order_items": oi_summary.model_dump(),
    }
    snapshot = await maybe_recompute(db, location_id, recompute)
    if snapshot:
        result["dashboard"] = snapshot
    return result
