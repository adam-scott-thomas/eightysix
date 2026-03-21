"""Tests for the /health endpoint."""
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


class TestHealth:
    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert "version" in data

    async def test_health_returns_db_status(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "db" in data
        assert data["db"] in ("connected", "disconnected")

    async def test_health_ok_when_db_connected(self, client):
        resp = await client.get("/health")
        data = resp.json()
        # In-memory SQLite should always be connected
        assert data["db"] == "connected"
        assert data["status"] == "ok"

    async def test_health_returns_version_string(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
