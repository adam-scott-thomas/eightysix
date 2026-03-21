"""Integration tests for ReadinessService — data completeness checks."""
import uuid
from datetime import timedelta

import pytest

from app.services.readiness_service import ReadinessService
from tests.conftest import SCENARIO_DATE

DAY_START = SCENARIO_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
DAY_END = DAY_START + timedelta(days=1)


class TestReadinessService:
    async def test_insufficient_with_no_data(self, db, location):
        """Empty location should report 'insufficient' status."""
        svc = ReadinessService(db)
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        assert result["status"] == "insufficient"
        assert result["completeness_score"] < 1.0
        # Only location domain should be populated
        assert result["domains"]["location"] is True
        assert result["domains"]["orders"] is False
        assert result["domains"]["shifts"] is False
        assert result["domains"]["employees"] is False
        assert result["domains"]["menu"] is False

    async def test_partial_with_only_orders(self, db, location, seed_employees, seed_menu, seed_orders):
        """Location with orders but no shifts should be 'partial'."""
        svc = ReadinessService(db)
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        # Has location, orders, employees, menu — missing shifts
        assert result["status"] == "partial"
        assert "shifts" in result["missing_domains"]
        assert result["domains"]["orders"] is True
        assert result["domains"]["employees"] is True
        assert result["domains"]["menu"] is True

    async def test_ready_with_all_data(self, db, location, seed_orders, seed_shifts):
        """All domains populated should report 'ready' with completeness 1.0."""
        svc = ReadinessService(db)
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        assert result["status"] == "ready"
        assert result["completeness_score"] == 1.0
        assert result["missing_domains"] == []

    async def test_available_quick_wins_with_orders_and_shifts(self, db, location, seed_orders, seed_shifts):
        """With orders + shifts + employees, staffing quick win should be available."""
        svc = ReadinessService(db)
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        assert "staffing" in result["available_quick_wins"]
        assert "leakage" in result["available_quick_wins"]
        assert "rush" in result["available_quick_wins"]

    async def test_menu_quick_win_requires_menu(self, db, location, seed_employees, seed_shifts):
        """Menu quick win should NOT be available without menu items."""
        svc = ReadinessService(db)
        # seed_shifts depends on seed_employees, but no seed_menu or seed_orders
        # Need orders for most quick wins, but menu QW specifically requires menu
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        assert "menu" not in result["available_quick_wins"]

    async def test_completeness_score_fractional(self, db, location, seed_employees):
        """With only location + employees, completeness should be 2/5 = 0.4."""
        svc = ReadinessService(db)
        result = await svc.check_readiness(location.id, DAY_START, DAY_END)
        assert result["completeness_score"] == 0.4
        assert result["status"] == "partial"

    async def test_nonexistent_location(self, db):
        """Querying a nonexistent location should report insufficient."""
        svc = ReadinessService(db)
        fake_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        result = await svc.check_readiness(fake_id, DAY_START, DAY_END)
        assert result["status"] == "insufficient"
        assert result["domains"]["location"] is False
