"""Tests for /api/v1/demo endpoints (scenario lifecycle)."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

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


async def _reset_via_delete(db):
    """Reset all tables using DELETE (SQLite-compatible, unlike TRUNCATE)."""
    tables = [
        "dashboard_snapshots", "recommendations", "alerts", "integrity_flags",
        "events", "observations", "order_items", "orders", "shifts",
        "menu_items", "employees", "locations",
    ]
    for table in tables:
        await db.execute(text(f"DELETE FROM {table}"))
    await db.flush()


class TestDemo:
    async def test_demo_lifecycle(self, client, db, admin_headers, auth_headers):
        """Full happy-path: reset -> load scenario -> verify loaded."""
        # Reset using SQLite-compatible DELETE
        await _reset_via_delete(db)

        # Load scenario
        load_resp = await client.post("/api/v1/demo/load-scenario", json={
            "scenario": "normal_day",
        }, headers=admin_headers)
        assert load_resp.status_code == 200
        load_data = load_resp.json()
        assert load_data["status"] == "loaded"
        assert "location_id" in load_data
        assert load_data["scenario"] == "normal_day"
        assert "ingestion" in load_data

        location_id = load_data["location_id"]

        # Verify the location was created (locations requires auth_headers)
        loc_resp = await client.get("/api/v1/locations", headers=auth_headers)
        assert loc_resp.status_code == 200
        locations = loc_resp.json()
        assert any(loc["id"] == location_id for loc in locations)

        # Verify ingestion summary has all domains
        ingestion = load_data["ingestion"]
        for key in ("employees", "menu_items", "orders", "order_items", "shifts"):
            assert key in ingestion
            assert ingestion[key]["created"] > 0

    async def test_load_invalid_scenario(self, client, admin_headers):
        """POST /demo/load-scenario with a bad scenario name raises ValueError.

        The seed loader raises ValueError for unknown scenarios. Through httpx's
        ASGITransport, server-side exceptions propagate directly rather than
        being converted to HTTP 500 responses.
        """
        with pytest.raises(ValueError, match="Unknown scenario"):
            await client.post("/api/v1/demo/load-scenario", json={
                "scenario": "nonexistent_scenario",
            }, headers=admin_headers)

    async def test_reset_clears_data(self, client, db, admin_headers, auth_headers):
        """Load a scenario, reset, then verify locations list is empty."""
        # Load a scenario
        load_resp = await client.post("/api/v1/demo/load-scenario", json={
            "scenario": "normal_day",
        }, headers=admin_headers)
        assert load_resp.status_code == 200

        # Verify locations exist (locations requires auth_headers)
        locations_resp = await client.get("/api/v1/locations", headers=auth_headers)
        assert len(locations_resp.json()) >= 1

        # Reset using SQLite-compatible DELETE
        await _reset_via_delete(db)

        # Verify locations are now empty
        locations_resp = await client.get("/api/v1/locations", headers=auth_headers)
        assert resp_is_empty_list(locations_resp)

    async def test_get_scenarios(self, client, admin_headers):
        """GET /demo/scenarios returns the list of 8 valid scenarios."""
        resp = await client.get("/api/v1/demo/scenarios", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "scenarios" in data
        scenarios = data["scenarios"]
        assert isinstance(scenarios, list)
        assert len(scenarios) == 8
        assert "normal_day" in scenarios
        assert "dinner_rush" in scenarios
        assert "understaffed" in scenarios

    async def test_load_scenario_returns_ingestion_summary(self, client, db, admin_headers):
        """The load-scenario response includes ingestion summary with counts."""
        await _reset_via_delete(db)
        resp = await client.post("/api/v1/demo/load-scenario", json={
            "scenario": "dinner_rush",
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "ingestion" in data
        ingestion = data["ingestion"]
        # Each domain should have created/updated/skipped counts
        for key in ("employees", "menu_items", "orders", "order_items", "shifts"):
            assert key in ingestion
            assert "created" in ingestion[key]

    async def test_recompute_requires_location_id(self, client, admin_headers):
        """POST /demo/recompute without location_id returns 422."""
        resp = await client.post("/api/v1/demo/recompute", json={}, headers=admin_headers)
        assert resp.status_code == 422


def resp_is_empty_list(resp) -> bool:
    """Helper: check that the response is a 200 with an empty list."""
    return resp.status_code == 200 and resp.json() == []
