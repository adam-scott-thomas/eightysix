"""Integration tests for date_utils — data date range detection."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.date_utils import detect_data_date_range
from tests.conftest import SCENARIO_DATE


class TestDateUtils:
    async def test_detect_with_no_data(self, db, location):
        """No orders or shifts should fall back to now()."""
        now, day_start, day_end = await detect_data_date_range(db, location.id)
        # Should be close to actual UTC now (within a few seconds of test execution)
        actual_now = datetime.now(timezone.utc)
        delta = abs((now - actual_now).total_seconds())
        assert delta < 10  # within 10 seconds
        # day_start should be midnight of the returned 'now'
        assert day_start.hour == 0
        assert day_start.minute == 0
        assert day_end == day_start + timedelta(days=1)

    async def test_detect_with_orders(self, db, location, seed_orders):
        """With orders, should detect the order date range."""
        now, day_start, day_end = await detect_data_date_range(db, location.id)
        # Seed orders span 14:00-23:00 on 2025-03-15, so latest is 23:00
        assert now.year == 2025
        assert now.month == 3
        assert now.day == 15
        assert now.hour == 23  # last order at 23:00
        assert day_start == SCENARIO_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
        assert day_end == day_start + timedelta(days=1)

    async def test_detect_with_shifts_only(self, db, location, seed_shifts):
        """With only shifts (no orders), should detect the shift clock_in range."""
        now, day_start, day_end = await detect_data_date_range(db, location.id)
        # All 3 shifts clock in at 10:00 on 2025-03-15
        assert now.year == 2025
        assert now.month == 3
        assert now.day == 15
        assert now.hour == 10  # all shifts clock_in at 10:00
        assert day_start == SCENARIO_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
        assert day_end == day_start + timedelta(days=1)

    async def test_detect_with_orders_and_shifts(self, db, location, seed_orders, seed_shifts):
        """When both orders and shifts exist, should use the latest timestamp."""
        now, day_start, day_end = await detect_data_date_range(db, location.id)
        # Orders go to 23:00, shifts clock_in at 10:00 -> latest is 23:00
        assert now.hour == 23

    async def test_detect_nonexistent_location(self, db):
        """Nonexistent location should fall back to actual now()."""
        fake_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        now, day_start, day_end = await detect_data_date_range(db, fake_id)
        actual_now = datetime.now(timezone.utc)
        delta = abs((now - actual_now).total_seconds())
        assert delta < 10

    async def test_day_boundaries_are_midnight(self, db, location, seed_orders):
        """day_start should be 00:00 and day_end should be 00:00 the next day."""
        now, day_start, day_end = await detect_data_date_range(db, location.id)
        assert day_start.hour == 0
        assert day_start.minute == 0
        assert day_start.second == 0
        assert day_end.hour == 0
        assert day_end.minute == 0
        assert (day_end - day_start).days == 1
