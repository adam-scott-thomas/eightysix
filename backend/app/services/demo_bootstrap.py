"""Bootstrap a demo location with pre-loaded scenario data."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.loader import load_scenario
from app.services.ingestion_service import IngestionService
from app.services.snapshot_service import SnapshotService
from app.services.date_utils import detect_data_date_range


async def bootstrap_demo_location(
    db: AsyncSession,
    restaurant_name: str = "Demo Restaurant",
    scenario: str = "normal_day",
) -> dict:
    """Create a location, load scenario data, recompute dashboard.

    Returns dict with location_id and dashboard snapshot.
    Idempotent — if location with this name exists, reuses it.
    """
    scenario_data = load_scenario(scenario)

    # Override the location name from the scenario
    scenario_data.location["name"] = restaurant_name

    ingestion = IngestionService(db)
    location = await ingestion.ensure_location(scenario_data.location)
    location_id = location.id

    await ingestion.ingest_scenario(location_id, scenario_data)
    await db.flush()

    now, day_start, day_end = await detect_data_date_range(db, location_id)
    snapshot_service = SnapshotService(db)
    dashboard = await snapshot_service.recompute(location_id, now, day_start, day_end)

    return {
        "location_id": str(location_id),
        "dashboard": dashboard,
    }
