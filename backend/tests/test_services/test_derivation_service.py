"""Integration tests for DerivationService — verifies computed metrics from seed data."""
import uuid
from datetime import timedelta

import pytest

from app.db.models.order import Order
from app.services.derivation_service import DerivationService
from app.rules.staffing_rules import StaffingResult
from app.rules.labor_rules import LaborResult
from app.rules.leakage_rules import LeakageResult
from app.rules.menu_rules import MenuResult
from app.rules.rush_rules import RushResult
from tests.conftest import SCENARIO_DATE

# Derivation 'now' at 20:00 so orders (14:00-23:00) are partially in window
NOW = SCENARIO_DATE.replace(hour=20)
DAY_START = SCENARIO_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
DAY_END = DAY_START + timedelta(days=1)


class TestDerivationService:
    async def test_compute_revenue(self, db, location, seed_orders, seed_shifts):
        """10 orders x $18 = $180 revenue."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        assert result["revenue_today"] == 180.00

    async def test_compute_labor_cost(self, db, location, seed_orders, seed_shifts):
        """3 shifts x 10 hours each; Maria $16, James $17, Jake $15 = 160+170+150 = $480."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        assert result["total_labor_hours"] == 30.0
        assert result["labor_cost_estimate"] == 480.00

    async def test_compute_staffing_pressure(self, db, location, seed_orders, seed_shifts):
        """With all shifts having clock_out set, active_staff_count = 0.
        Staffing uses 2-hour rolling window. 0 active staff -> critical_understaffed."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        staffing: StaffingResult = result["staffing"]
        assert isinstance(staffing, StaffingResult)
        # All shifts have clock_out, so active_staff_count is 0
        assert result["active_staff_count"] == 0
        assert staffing.staffing_pressure == "critical_understaffed"

    async def test_compute_leakage_zero(self, db, location, seed_orders, seed_shifts):
        """No refunds in seed data -> refund_rate 0, no spike."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        leakage: LeakageResult = result["leakage"]
        assert isinstance(leakage, LeakageResult)
        assert leakage.refund_rate == 0
        assert leakage.spike_detected is False

    async def test_compute_with_refunds(self, db, location, seed_orders, seed_shifts):
        """Set refund amounts on orders and verify leakage detection."""
        # Modify 3 orders to have refund amounts (3 x $10 = $30 on $180 = 16.7%)
        from sqlalchemy import select
        stmt = select(Order).where(Order.location_id == location.id).limit(3)
        result = await db.execute(stmt)
        orders = list(result.scalars().all())
        for order in orders:
            order.refund_amount = 10.00
        await db.flush()

        svc = DerivationService(db)
        derivations = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        leakage: LeakageResult = derivations["leakage"]
        assert leakage.refund_rate > 0
        assert leakage.spike_detected is True
        assert leakage.loss_estimate == 30.00

    async def test_compute_menu_performance(self, db, location, seed_orders, seed_shifts):
        """Verify top sellers are correctly identified from order items."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        menu: MenuResult = result["menu"]
        assert isinstance(menu, MenuResult)
        assert len(menu.top_sellers) > 0
        # Classic Burger should be top seller (10 units x $13 = $130)
        top_names = [s.item_name for s in menu.top_sellers]
        assert "Classic Burger" in top_names

    async def test_compute_returns_all_keys(self, db, location, seed_orders, seed_shifts):
        """Verify the returned dict has all expected top-level keys."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        expected_keys = {
            "revenue_today",
            "projected_eod_revenue",
            "avg_ticket",
            "orders_per_hour",
            "active_staff_count",
            "total_labor_hours",
            "sales_per_labor_hour",
            "labor_cost_estimate",
            "labor_cost_ratio",
            "staffing",
            "labor",
            "leakage",
            "menu",
            "rush",
            "integrity",
            "avg_prep_time",
            "backlog_risk",
        }
        assert expected_keys.issubset(set(result.keys()))

    async def test_compute_avg_ticket(self, db, location, seed_orders, seed_shifts):
        """10 orders x $18 = $180, avg ticket = $18."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        assert result["avg_ticket"] == 18.00

    async def test_compute_labor_cost_ratio(self, db, location, seed_orders, seed_shifts):
        """Labor $480 / Revenue $180 = 2.6667 ratio."""
        svc = DerivationService(db)
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        labor: LaborResult = result["labor"]
        assert isinstance(labor, LaborResult)
        # LCR > 0.35 so should be critical
        assert labor.severity == "critical"
        assert result["labor_cost_ratio"] > 2.0

    async def test_compute_empty_location(self, db, location):
        """Location with no data should return empty dict."""
        svc = DerivationService(db)
        # Use a location with no orders, shifts, etc.
        result = await svc.compute_all(location.id, NOW, DAY_START, DAY_END)
        # Should still return a dict (location exists), but with 0 revenue
        assert result["revenue_today"] == 0
        assert result["total_labor_hours"] == 0

    async def test_compute_nonexistent_location(self, db):
        """Nonexistent location should raise NotFoundError."""
        from app.core.exceptions import NotFoundError
        svc = DerivationService(db)
        fake_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        with pytest.raises(NotFoundError):
            await svc.compute_all(fake_id, NOW, DAY_START, DAY_END)
