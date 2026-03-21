"""Integration tests for RecommendationService — recommendation generation from derivations."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.alert import Alert
from app.rules.staffing_rules import StaffingResult
from app.rules.labor_rules import LaborResult
from app.rules.leakage_rules import LeakageResult
from app.rules.menu_rules import MenuResult, MenuItemPerformance, AttachSuggestion
from app.rules.rush_rules import RushResult
from app.services.alert_service import AlertService
from app.services.recommendation_service import RecommendationService
from tests.conftest import SCENARIO_DATE

NOW = SCENARIO_DATE.replace(hour=20)


def _balanced_derivations():
    """Return derivation dict with no issues."""
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
        "menu": MenuResult(
            top_sellers=[],
            bottom_sellers=[],
            workhorse_items=[],
            dog_items=[],
            attach_rate_suggestions=[],
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
    """Return derivation dict with understaffed pressure."""
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
        "menu": MenuResult(
            top_sellers=[],
            bottom_sellers=[],
            workhorse_items=[],
            dog_items=[],
            attach_rate_suggestions=[],
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


class TestRecommendationService:
    async def test_generates_staffing_rec(self, db, location):
        """Understaffed derivation should produce a staffing recommendation."""
        # First create the alert so it can be linked
        alert_svc = AlertService(db)
        derivations = _understaffed_derivations()
        alerts = await alert_svc.generate_alerts(location.id, derivations, NOW)

        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, derivations, alerts, NOW)
        staffing_recs = [r for r in recs if r.category == "staffing"]
        assert len(staffing_recs) >= 1
        rec = staffing_recs[0]
        assert "Add 3 staff immediately" in rec.title
        assert rec.alert_id is not None

    async def test_recommendation_has_expiry(self, db, location):
        """Recommendations should have expires_at set."""
        alert_svc = AlertService(db)
        derivations = _understaffed_derivations()
        alerts = await alert_svc.generate_alerts(location.id, derivations, NOW)

        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, derivations, alerts, NOW)
        for rec in recs:
            assert rec.expires_at is not None
            assert rec.expires_at > NOW

    async def test_no_recs_when_balanced(self, db, location):
        """Balanced derivation should produce no recommendations (or at most menu-only)."""
        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, _balanced_derivations(), [], NOW)
        # No staffing/cost/integrity recs; menu recs only come from workhorse/dog items
        non_menu = [r for r in recs if r.category != "menu"]
        assert len(non_menu) == 0

    async def test_labor_cost_recommendation(self, db, location):
        """High labor cost should produce a cost recommendation."""
        derivations = _balanced_derivations()
        derivations["labor"] = LaborResult(
            labor_cost_estimate=500.0,
            sales_per_labor_hour=10.0,
            labor_cost_ratio=0.50,
            severity="critical",
            alert_message="Labor cost running at 50% of revenue",
        )
        alert_svc = AlertService(db)
        alerts = await alert_svc.generate_alerts(location.id, derivations, NOW)

        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, derivations, alerts, NOW)
        cost_recs = [r for r in recs if r.category == "cost"]
        assert len(cost_recs) == 1
        assert "labor cost" in cost_recs[0].title.lower()

    async def test_menu_recommendations_from_workhorse(self, db, location):
        """Workhorse items should generate menu pricing recommendations."""
        derivations = _balanced_derivations()
        derivations["menu"] = MenuResult(
            top_sellers=[],
            bottom_sellers=[],
            workhorse_items=[
                MenuItemPerformance(
                    item_name="French Fries",
                    menu_item_id="test-1",
                    units_sold=50,
                    revenue=250.0,
                    revenue_contribution=0.4,
                    margin_band="low",
                    category="workhorse",
                ),
            ],
            dog_items=[],
            attach_rate_suggestions=[],
        )
        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, derivations, [], NOW)
        menu_recs = [r for r in recs if r.category == "menu"]
        assert len(menu_recs) >= 1
        assert "French Fries" in menu_recs[0].title

    async def test_recommendation_confidence_set(self, db, location):
        """All recommendations should have a confidence score."""
        alert_svc = AlertService(db)
        derivations = _understaffed_derivations()
        alerts = await alert_svc.generate_alerts(location.id, derivations, NOW)

        rec_svc = RecommendationService(db)
        recs = await rec_svc.generate_recommendations(location.id, derivations, alerts, NOW)
        for rec in recs:
            assert rec.confidence is not None
            assert float(rec.confidence) > 0
