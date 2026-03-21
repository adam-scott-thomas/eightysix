import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.db.models.location import Location
from app.repositories.location_repo import LocationRepository
from app.schemas.location import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = LocationRepository(db)
    return await repo.list(limit=limit, offset=offset)


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    body: LocationCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = LocationRepository(db)
    loc = Location(**body.model_dump())
    return await repo.create(loc)


@router.get("/{id}", response_model=LocationResponse)
async def get_location(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = LocationRepository(db)
    loc = await repo.get_by_id(id)
    if not loc:
        raise NotFoundError("Location", str(id))
    return loc


@router.patch("/{id}", response_model=LocationResponse)
async def update_location(
    id: uuid.UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = LocationRepository(db)
    loc = await repo.get_by_id(id)
    if not loc:
        raise NotFoundError("Location", str(id))
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(loc, key, value)
    await db.flush()
    return loc
