"""Demo control endpoints — reset, load scenario, sync, recompute."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db


def _check_demo_mode():
    """Dependency that blocks all demo endpoints when DEMO_MODE is off."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=404, detail="Not found")
from app.providers.registry import get_pos_provider, get_labor_provider
from app.schemas.demo import LoadScenarioRequest, QuickAssessRequest, RecomputeRequest, SyncRequest
from app.seed.generator import generate_assessment_scenario
from app.seed.loader import load_scenario, list_scenarios
from app.services.date_utils import detect_data_date_range
from app.services.ingestion_service import IngestionService
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1/demo", tags=["demo"], dependencies=[Depends(_check_demo_mode)])

TRUNCATE_TABLES = [
    "forecasts", "daily_aggregates", "store_context",
    "dashboard_snapshots", "recommendations", "alerts", "integrity_flags",
    "events", "observations", "order_items", "orders", "shifts",
    "menu_items", "employees", "locations",
]


@router.post("/reset")
async def reset_data(db: AsyncSession = Depends(get_db)):
    for table in TRUNCATE_TABLES:
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    return {"status": "reset"}


@router.post("/load-scenario")
async def load_scenario_endpoint(
    req: LoadScenarioRequest,
    db: AsyncSession = Depends(get_db),
):
    scenario_data = load_scenario(req.scenario)
    ingestion = IngestionService(db)

    # Create or find location
    location = await ingestion.ensure_location(scenario_data.location)
    location_id = location.id

    # Ingest all data
    results = await ingestion.ingest_scenario(location_id, scenario_data)

    return {
        "status": "loaded",
        "scenario": req.scenario,
        "location_id": str(location_id),
        "ingestion": {k: v.model_dump() for k, v in results.items()},
    }


@router.post("/sync")
async def sync_providers(
    req: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    location_id = uuid.UUID(req.location_id)
    ingestion = IngestionService(db)

    pos = get_pos_provider()
    labor = get_labor_provider()

    # Use data-aware date range instead of "today"
    now, day_start, day_end = await detect_data_date_range(db, location_id)

    orders = pos.fetch_orders(str(location_id), day_start, day_end)
    menu_items = pos.fetch_menu(str(location_id))
    order_ids = [o.external_order_id for o in orders]
    order_items = pos.fetch_order_items(str(location_id), order_ids)

    employees = labor.fetch_employees(str(location_id))
    shifts = labor.fetch_shifts(str(location_id), day_start, day_end)

    results = await ingestion.ingest_from_providers(
        location_id=location_id,
        orders=orders,
        order_items=order_items,
        menu_items=menu_items,
        employees=employees,
        shifts=shifts,
    )

    return {
        "status": "synced",
        "location_id": str(location_id),
        "ingestion": {k: v.model_dump() for k, v in results.items()},
    }


@router.post("/recompute")
async def recompute(
    req: RecomputeRequest,
    db: AsyncSession = Depends(get_db),
):
    location_id = uuid.UUID(req.location_id)
    now, day_start, day_end = await detect_data_date_range(db, location_id)

    snapshot_service = SnapshotService(db)
    result = await snapshot_service.recompute(location_id, now, day_start, day_end)
    return result


@router.post("/quick-assess")
async def quick_assess(
    req: QuickAssessRequest,
    db: AsyncSession = Depends(get_db),
):
    """3 inputs → full dashboard. Walk-in sales demo."""
    # 1. Reset
    for table in TRUNCATE_TABLES:
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

    # 2. Generate synthetic scenario from the 3 inputs
    scenario_data = generate_assessment_scenario(
        staff_count=req.staff_count,
        orders_per_day=req.orders_per_day,
        avg_ticket=req.avg_ticket,
        restaurant_name=req.restaurant_name,
    )

    # 3. Ingest
    ingestion = IngestionService(db)
    location = await ingestion.ensure_location(scenario_data.location)
    location_id = location.id
    await ingestion.ingest_scenario(location_id, scenario_data)
    await db.flush()

    # 4. Recompute full pipeline
    now, day_start, day_end = await detect_data_date_range(db, location_id)
    snapshot_service = SnapshotService(db)
    dashboard = await snapshot_service.recompute(location_id, now, day_start, day_end)

    return {
        "status": "assessed",
        "location_id": str(location_id),
        "dashboard": dashboard,
    }


@router.get("/scenarios")
async def get_scenarios():
    return {"scenarios": list_scenarios()}


@router.post("/bootstrap")
async def bootstrap(db: AsyncSession = Depends(get_db)):
    """Generate 8 weeks of synthetic history for the demo location.

    Creates a location, populates 56 days of orders/shifts, backfills
    daily aggregates, and recomputes the dashboard. Takes ~30-60 seconds.
    """
    from sqlalchemy import select, func
    from app.db.models.location import Location
    count = (await db.execute(select(func.count()).select_from(Location))).scalar()
    if count > 0:
        raise HTTPException(400, "Demo data already exists. Reset first.")

    from app.services.demo_bootstrap import bootstrap_demo_location
    result = await bootstrap_demo_location(db)
    return {"status": "bootstrapped", **result}
