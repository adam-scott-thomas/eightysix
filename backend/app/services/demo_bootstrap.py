"""Bootstrap a demo location with 8 weeks of synthetic history + live dashboard."""
import logging
import uuid
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.history_generator import generate_history
from app.seed.loader import ScenarioData
from app.services.aggregation_service import AggregationService
from app.services.ingestion_service import IngestionService
from app.services.snapshot_service import SnapshotService
from app.services.date_utils import detect_data_date_range

logger = logging.getLogger(__name__)


async def bootstrap_demo_location(
    db: AsyncSession,
    restaurant_name: str = "Demo Restaurant",
) -> dict:
    """Create a location with 8 weeks of history, backfill aggregates, recompute dashboard.

    Returns dict with location_id and dashboard snapshot.
    Idempotent — if location with this name exists, reuses it.
    """
    # Generate 8 weeks of synthetic history
    history = generate_history(
        weeks=8,
        base_orders_per_day=180,
        avg_ticket=28.00,
        staff_count=8,
        restaurant_name=restaurant_name,
    )

    ingestion = IngestionService(db)
    location = await ingestion.ensure_location(history["location"])
    location_id = location.id

    # Ingest employees and menu (once)
    employee_scenario = ScenarioData({
        "location": history["location"],
        "employees": history["employees"],
        "menu_items": history["menu_items"],
        "orders": [],
        "order_items": [],
        "shifts": [],
    })
    await ingestion.ingest_scenario(location_id, employee_scenario)
    await db.flush()

    # Ingest each day's orders and shifts
    day_count = 0
    for day in history["daily_data"]:
        day_scenario = ScenarioData({
            "location": history["location"],
            "employees": [],
            "menu_items": [],
            "orders": day["orders"],
            "order_items": day["order_items"],
            "shifts": day["shifts"],
        })
        await ingestion.ingest_scenario(location_id, day_scenario)
        day_count += 1

        # Flush every 7 days to avoid huge transaction
        if day_count % 7 == 0:
            await db.flush()

    await db.flush()
    logger.info("Ingested %d days of history for %s", day_count, restaurant_name)

    # Backfill daily aggregates for all history
    agg_service = AggregationService(db)
    first_date = history["daily_data"][0]["date"]
    last_date = history["daily_data"][-1]["date"]
    agg_count = await agg_service.backfill(location_id, first_date, last_date)
    await db.flush()
    logger.info("Backfilled %d daily aggregates", agg_count)

    # Recompute current dashboard
    now, day_start, day_end = await detect_data_date_range(db, location_id)
    snapshot_service = SnapshotService(db)
    dashboard = await snapshot_service.recompute(location_id, now, day_start, day_end)

    return {
        "location_id": str(location_id),
        "dashboard": dashboard,
    }
