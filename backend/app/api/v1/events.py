import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.event import Event
from app.repositories.event_repo import EventRepository
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/api/v1/locations/{location_id}/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    location_id: uuid.UUID,
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = EventRepository(db)
    event = Event(location_id=location_id, **body.model_dump())
    return await repo.create(event)


@router.get("", response_model=list[EventResponse])
async def list_events(
    location_id: uuid.UUID,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = EventRepository(db)
    if start and end:
        return await repo.get_by_time_range(location_id, start, end)
    return await repo.list(limit=limit, offset=offset, location_id=location_id)
