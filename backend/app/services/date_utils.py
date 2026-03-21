"""Utilities for detecting data date ranges — critical for demo scenarios with historical dates."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.db.models.shift import Shift


async def detect_data_date_range(
    db: AsyncSession, location_id: uuid.UUID
) -> tuple[datetime, datetime, datetime]:
    """Detect the date range of data for a location.

    Returns (now, day_start, day_end) where:
    - If data exists: 'now' is set to the latest order/shift timestamp,
      day_start/end bracket the data's day
    - If no data: falls back to actual UTC now
    """
    # Find the latest order timestamp
    latest_order = await db.execute(
        select(func.max(Order.ordered_at)).where(Order.location_id == location_id)
    )
    max_order_at = latest_order.scalar_one_or_none()

    # Find the latest shift clock_in
    latest_shift = await db.execute(
        select(func.max(Shift.clock_in)).where(Shift.location_id == location_id)
    )
    max_shift_at = latest_shift.scalar_one_or_none()

    # Pick the latest timestamp from the data
    candidates = [t for t in [max_order_at, max_shift_at] if t is not None]

    if not candidates:
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        return now, day_start, day_end

    data_latest = max(candidates)
    # Ensure timezone-aware
    if data_latest.tzinfo is None:
        data_latest = data_latest.replace(tzinfo=timezone.utc)

    # Use the data's day as the window
    day_start = data_latest.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    # 'now' should be the latest data point (simulating "current time" within the scenario)
    now = data_latest

    return now, day_start, day_end
