"""Tests for /api/v1/locations/{location_id}/dashboard endpoints."""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import create_app


@pytest.fixture
def app_instance(db):
    application = create_app()

    async def override_get_db():
        yield db

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture
async def client(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestDashboard:
    async def test_readiness_with_data(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """GET /dashboard/readiness with seeded data returns ready or partial."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/dashboard/readiness", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready", "partial")
        assert "completeness_score" in data
        assert "domains" in data

    async def test_current_404_before_recompute(self, client, auth_headers, location):
        """GET /dashboard/current before any recompute returns 404."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/dashboard/current", headers=auth_headers)
        assert resp.status_code == 404

    async def test_recompute_returns_snapshot(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """POST /dashboard/recompute returns a snapshot with all expected keys."""
        loc_id = str(location.id)
        resp = await client.post(f"/api/v1/locations/{loc_id}/dashboard/recompute", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = [
            "snapshot_at", "status", "readiness", "summary",
            "throughput", "staffing", "menu", "leakage",
            "integrity", "alerts", "recommendations",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    async def test_current_after_recompute(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """After recompute, GET /dashboard/current returns the snapshot."""
        loc_id = str(location.id)

        # First recompute
        recompute_resp = await client.post(
            f"/api/v1/locations/{loc_id}/dashboard/recompute", headers=auth_headers
        )
        assert recompute_resp.status_code == 200

        # Then fetch current
        resp = await client.get(f"/api/v1/locations/{loc_id}/dashboard/current", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "summary" in data
        assert "throughput" in data

    async def test_timeline_empty(self, client, auth_headers, location):
        """GET /dashboard/timeline with no snapshots returns an empty array."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/dashboard/timeline", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_timeline_after_recompute(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """After recompute, timeline includes at least one snapshot."""
        loc_id = str(location.id)
        await client.post(f"/api/v1/locations/{loc_id}/dashboard/recompute", headers=auth_headers)

        resp = await client.get(f"/api/v1/locations/{loc_id}/dashboard/timeline", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "snapshot_at" in data[0]
        assert "status" in data[0]

    async def test_export_json(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """GET /dashboard/export?format=json returns a JSON attachment."""
        loc_id = str(location.id)
        # Need a snapshot first
        await client.post(f"/api/v1/locations/{loc_id}/dashboard/recompute", headers=auth_headers)

        resp = await client.get(
            f"/api/v1/locations/{loc_id}/dashboard/export",
            params={"format": "json"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "content-disposition" in resp.headers
        assert "attachment" in resp.headers["content-disposition"]
        # Body should be valid JSON
        data = resp.json()
        assert "exported_at" in data
        assert "summary" in data

    async def test_export_csv(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """GET /dashboard/export?format=csv returns a CSV attachment."""
        loc_id = str(location.id)
        await client.post(f"/api/v1/locations/{loc_id}/dashboard/recompute", headers=auth_headers)

        resp = await client.get(
            f"/api/v1/locations/{loc_id}/dashboard/export",
            params={"format": "csv"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "content-disposition" in resp.headers
        assert "attachment" in resp.headers["content-disposition"]
        # Body should contain CSV header row
        content = resp.text
        assert "Metric" in content
        assert "Value" in content
