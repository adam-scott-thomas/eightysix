"""Tests for alert endpoints."""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.alert import Alert
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


async def _create_alert(db: AsyncSession, location_id: uuid.UUID) -> Alert:
    """Directly insert an alert via the DB session."""
    alert = Alert(
        location_id=location_id,
        alert_type="understaffed",
        severity="warning",
        status="active",
        title="Understaffed during dinner rush",
        message="Only 1 floor staff scheduled for peak hours",
        evidence_json={"active_staff": 1, "expected": 3},
        triggered_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    await db.flush()
    return alert


class TestAlerts:
    async def test_list_alerts_empty(self, client, location):
        """GET alerts with no data returns an empty list."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_alerts_with_data(self, client, db, location):
        """After creating an alert, it appears in the list."""
        await _create_alert(db, location.id)
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["alert_type"] == "understaffed"
        assert data[0]["status"] == "active"

    async def test_acknowledge_alert(self, client, db, location):
        """PATCH /alerts/{id}/acknowledge changes status to acknowledged."""
        alert = await _create_alert(db, location.id)
        alert_id = str(alert.id)

        resp = await client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "acknowledged"
        assert data["acknowledged_at"] is not None

    async def test_resolve_alert(self, client, db, location):
        """PATCH /alerts/{id}/resolve changes status to resolved."""
        alert = await _create_alert(db, location.id)
        alert_id = str(alert.id)

        resp = await client.patch(f"/api/v1/alerts/{alert_id}/resolve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None

    async def test_nonexistent_alert_acknowledge(self, client):
        """PATCH acknowledge on a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/alerts/{random_id}/acknowledge")
        assert resp.status_code == 404

    async def test_nonexistent_alert_resolve(self, client):
        """PATCH resolve on a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/alerts/{random_id}/resolve")
        assert resp.status_code == 404

    async def test_acknowledge_then_resolve(self, client, db, location):
        """An alert can be acknowledged and then resolved."""
        alert = await _create_alert(db, location.id)
        alert_id = str(alert.id)

        ack_resp = await client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
        assert ack_resp.status_code == 200
        assert ack_resp.json()["status"] == "acknowledged"

        resolve_resp = await client.patch(f"/api/v1/alerts/{alert_id}/resolve")
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resolved"
