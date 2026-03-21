"""Integration tests for AlertService — alert generation, dedup, and TTL expiry."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.alert import Alert
from app.repositories.alert_repo import AlertRepository
from app.rules.staffing_rules import StaffingResult
from app.rules.labor_rules import LaborResult
from app.rules.leakage_rules import LeakageResult
from app.rules.rush_rules import RushResult
from app.services.alert_service import AlertService
from tests.conftest import SCENARIO_DATE

NOW = SCENARIO_DATE.replace(hour=20)


def _balanced_derivations():
    """Return derivation dict that should NOT trigger any alerts."""
    return {
        "staffing": StaffingResult(
            orders_per_labor_hour=6.0,
            staffing_pressure="balanced",
            active_staff=3,
            orders_in_window=12,
            recommendation=None,
            confidence=0.0,
        ),
        "labor": LaborResult(
            labor_cost_estimate=200.0,
            sales_per_labor_hour=30.0,
            labor_cost_ratio=0.25,
            severity="healthy",
        ),
        "leakage": LeakageResult(
            refund_total=0,
            comp_total=0,
            void_total=0,
            loss_estimate=0,
            refund_rate=0,
            severity="normal",
            spike_detected=False,
        ),
        "rush": RushResult(
            order_velocity=10.0,
            avg_prep_time=300.0,
            prep_time_trend="stable",
            prep_time_change_pct=0.0,
            backlog_risk=0.3,
            severity="normal",
        ),
        "integrity": [],
    }


def _understaffed_derivations():
    """Return derivation dict that triggers an understaffed alert."""
    return {
        "staffing": StaffingResult(
            orders_per_labor_hour=18.0,
            staffing_pressure="critical_understaffed",
            active_staff=1,
            orders_in_window=36,
            recommendation="Add 3 staff immediately",
            confidence=0.9,
        ),
        "labor": LaborResult(
            labor_cost_estimate=100.0,
            sales_per_labor_hour=50.0,
            labor_cost_ratio=0.20,
            severity="healthy",
        ),
        "leakage": LeakageResult(
            refund_total=0,
            comp_total=0,
            void_total=0,
            loss_estimate=0,
            refund_rate=0,
            severity="normal",
            spike_detected=False,
        ),
        "rush": RushResult(
            order_velocity=10.0,
            avg_prep_time=300.0,
            prep_time_trend="stable",
            prep_time_change_pct=0.0,
            backlog_risk=0.3,
            severity="normal",
        ),
        "integrity": [],
    }


class TestAlertService:
    async def test_no_alerts_when_balanced(self, db, location):
        """Balanced derivations should produce no alerts."""
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, _balanced_derivations(), NOW)
        assert len(alerts) == 0

    async def test_understaffed_alert(self, db, location):
        """Critical understaffed derivation should create an alert."""
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, _understaffed_derivations(), NOW)
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == "understaffed"
        assert alert.severity == "critical"
        assert alert.status == "active"
        assert "18.0" in alert.title

    async def test_alert_dedup(self, db, location):
        """Running alert generation twice should not create duplicates."""
        svc = AlertService(db)
        derivations = _understaffed_derivations()
        alerts1 = await svc.generate_alerts(location.id, derivations, NOW)
        assert len(alerts1) == 1
        alerts2 = await svc.generate_alerts(location.id, derivations, NOW)
        assert len(alerts2) == 0

        # Verify only one active alert in the database
        repo = AlertRepository(db)
        all_active = await repo.get_active_by_location(location.id)
        assert len(all_active) == 1

    async def test_ttl_expiry(self, db, location):
        """Alert with ttl_minutes should auto-resolve when time passes."""
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, _understaffed_derivations(), NOW)
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.ttl_minutes == 60

        # Advance time past the TTL
        future = NOW + timedelta(minutes=61)
        repo = AlertRepository(db)
        expired_count = await repo.expire_ttl_alerts(future)
        assert expired_count == 1

        # Alert should now be resolved
        active = await repo.get_active_by_location(location.id)
        assert len(active) == 0

    async def test_labor_warning_alert(self, db, location):
        """High labor cost ratio should create a labor_warning alert."""
        derivations = _balanced_derivations()
        derivations["labor"] = LaborResult(
            labor_cost_estimate=500.0,
            sales_per_labor_hour=10.0,
            labor_cost_ratio=0.50,
            severity="critical",
            alert_message="Labor cost running at 50% of revenue",
        )
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, derivations, NOW)
        types = [a.alert_type for a in alerts]
        assert "labor_warning" in types

    async def test_refund_spike_alert(self, db, location):
        """Leakage spike should create a refund_spike alert."""
        derivations = _balanced_derivations()
        derivations["leakage"] = LeakageResult(
            refund_total=50.0,
            comp_total=0,
            void_total=0,
            loss_estimate=50.0,
            refund_rate=0.10,
            severity="critical",
            spike_detected=True,
            alert_message="Refund rate critical",
        )
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, derivations, NOW)
        types = [a.alert_type for a in alerts]
        assert "refund_spike" in types

    async def test_multiple_alert_types(self, db, location):
        """Multiple issues should create multiple alerts."""
        derivations = _understaffed_derivations()
        derivations["labor"] = LaborResult(
            labor_cost_estimate=500.0,
            sales_per_labor_hour=10.0,
            labor_cost_ratio=0.50,
            severity="critical",
            alert_message="Labor cost running at 50% of revenue",
        )
        svc = AlertService(db)
        alerts = await svc.generate_alerts(location.id, derivations, NOW)
        types = {a.alert_type for a in alerts}
        assert "understaffed" in types
        assert "labor_warning" in types
