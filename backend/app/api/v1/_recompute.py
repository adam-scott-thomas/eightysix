"""Shared helper for optional auto-recompute after bulk ingestion."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.date_utils import detect_data_date_range
from app.services.snapshot_service import SnapshotService


async def maybe_recompute(db: AsyncSession, location_id: uuid.UUID, do_recompute: bool) -> dict | None:
    if not do_recompute:
        return None
    now, day_start, day_end = await detect_data_date_range(db, location_id)
    service = SnapshotService(db)
    return await service.recompute(location_id, now, day_start, day_end)
