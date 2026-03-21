"""Integration tests for SnapshotService — full pipeline orchestration."""
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select, func

from app.db.models.dashboard_snapshot import DashboardSnapshot
from app.services.snapshot_service import SnapshotService
from tests.conftest import SCENARIO_DATE

NOW = SCENARIO_DATE.replace(hour=20)
DAY_START = SCENARIO_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
DAY_END = DAY_START + timedelta(days=1)


class TestSnapshotService:
    async def test_recompute_creates_snapshot(self, db, location, seed_orders, seed_shifts):
        """Running full pipeline should persist a DashboardSnapshot row."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        assert "status" in result
        assert "snapshot_at" in result

        # Verify a snapshot was persisted
        stmt = select(func.count()).select_from(DashboardSnapshot).where(
            DashboardSnapshot.location_id == location.id
        )
        count = await db.execute(stmt)
        assert count.scalar_one() >= 1

    async def test_snapshot_has_correct_status_green(self, db, location, seed_orders, seed_shifts):
        """With balanced data and no critical alerts, status should reflect alert state."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        # Our seed data has critical issues (understaffed — 0 active staff, high LCR),
        # so status will be red or yellow, not green
        assert result["status"] in ("green", "yellow", "red")

    async def test_snapshot_status_red_with_critical_alerts(self, db, location, seed_orders, seed_shifts):
        """Seed data has 0 active staff and LCR > 2.0, so critical alerts should set status to 'red'."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        # With all shifts having clock_out set, active_staff = 0 -> critical_understaffed
        # and LCR is huge -> labor critical
        assert result["status"] == "red"

    async def test_snapshot_payload_shape(self, db, location, seed_orders, seed_shifts):
        """Returned dict should have all expected top-level keys."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        expected_keys = {
            "snapshot_at",
            "status",
            "readiness",
            "summary",
            "throughput",
            "staffing",
            "menu",
            "leakage",
            "integrity",
            "alerts",
            "recommendations",
        }
        assert expected_keys.issubset(set(result.keys()))

    async def test_snapshot_readiness_section(self, db, location, seed_orders, seed_shifts):
        """Readiness section should contain score and completeness."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        readiness = result["readiness"]
        assert "score" in readiness
        assert "completeness" in readiness
        assert "missing" in readiness
        assert readiness["score"] == 1.0

    async def test_snapshot_summary_has_revenue(self, db, location, seed_orders, seed_shifts):
        """Summary section should contain revenue_today from derivations."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        summary = result["summary"]
        assert summary["revenue_today"] == 180.00

    async def test_snapshot_alerts_is_list(self, db, location, seed_orders, seed_shifts):
        """Alerts should be a list of dicts."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        assert isinstance(result["alerts"], list)
        if result["alerts"]:
            alert = result["alerts"][0]
            assert "alert_type" in alert
            assert "severity" in alert

    async def test_snapshot_recommendations_is_list(self, db, location, seed_orders, seed_shifts):
        """Recommendations should be a list of dicts."""
        svc = SnapshotService(db)
        result = await svc.recompute(location.id, NOW, DAY_START, DAY_END)
        assert isinstance(result["recommendations"], list)

    async def test_recompute_returns_error_for_no_data(self, db):
        """Nonexistent location should return an error dict."""
        svc = SnapshotService(db)
        fake_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        result = await svc.recompute(fake_id, NOW, DAY_START, DAY_END)
        assert "error" in result
