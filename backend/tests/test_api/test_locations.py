"""Tests for /api/v1/locations endpoints."""
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


class TestLocations:
    async def test_list_locations_empty(self, client):
        """GET /api/v1/locations with no data returns an empty list."""
        resp = await client.get("/api/v1/locations")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_location(self, client):
        """POST /api/v1/locations creates a location and returns 201."""
        payload = {
            "name": "Downtown Bistro",
            "timezone": "America/New_York",
            "default_hourly_rate": 18.00,
        }
        resp = await client.post("/api/v1/locations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Downtown Bistro"
        assert data["timezone"] == "America/New_York"
        assert "id" in data
        # Verify the ID is a valid UUID string
        uuid.UUID(data["id"])

    async def test_get_location(self, client):
        """Create a location, then GET it by ID — fields should match."""
        payload = {
            "name": "Harbor Grill",
            "timezone": "America/Chicago",
        }
        create_resp = await client.post("/api/v1/locations", json=payload)
        created = create_resp.json()
        loc_id = created["id"]

        resp = await client.get(f"/api/v1/locations/{loc_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == loc_id
        assert data["name"] == "Harbor Grill"
        assert data["timezone"] == "America/Chicago"

    async def test_patch_location(self, client):
        """PATCH a location's name — name should change."""
        create_resp = await client.post("/api/v1/locations", json={
            "name": "Old Name",
            "timezone": "America/Detroit",
        })
        loc_id = create_resp.json()["id"]

        resp = await client.patch(f"/api/v1/locations/{loc_id}", json={
            "name": "New Name",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_get_nonexistent_location(self, client):
        """GET with a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/locations/{random_id}")
        assert resp.status_code == 404

    async def test_list_locations_after_create(self, client):
        """After creating a location, it appears in the list."""
        await client.post("/api/v1/locations", json={
            "name": "Test Spot",
            "timezone": "UTC",
        })
        resp = await client.get("/api/v1/locations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        names = [loc["name"] for loc in data]
        assert "Test Spot" in names

    async def test_patch_nonexistent_location(self, client):
        """PATCH with a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/locations/{random_id}", json={
            "name": "Should Fail",
        })
        assert resp.status_code == 404
