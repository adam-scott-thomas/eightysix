"""Forecast endpoints — generate, backfill aggregates, retrieve latest."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.forecast_service import ForecastService
from app.services.aggregation_service import AggregationService

router = APIRouter(prefix="/api/v1/locations/{location_id}/forecast", tags=["forecast"])


@router.post("/generate")
async def generate_forecast(
    location_id: uuid.UUID,
    horizon_days: int = Query(default=28, ge=1, le=28),
    db: AsyncSession = Depends(get_db),
):
    """Generate forecasts for the next N days using baseline model."""
    service = ForecastService(db)
    results = await service.generate_forecast(location_id, horizon_days)
    return {"forecasts": results, "count": len(results), "model": "baseline_v1"}


@router.post("/backfill-aggregates")
async def backfill_aggregates(
    location_id: uuid.UUID,
    days: int = Query(default=56, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Backfill daily aggregates from existing order/shift data."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    service = AggregationService(db)
    count = await service.backfill(location_id, start_date, end_date)
    return {"status": "backfilled", "days_processed": count}


@router.get("")
async def get_forecast(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get latest forecast run for a location."""
    service = ForecastService(db)
    results = await service.get_latest_forecast(location_id)
    return {"forecasts": results, "count": len(results)}
