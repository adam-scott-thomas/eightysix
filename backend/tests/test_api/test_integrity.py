"""Tests for integrity flag endpoints."""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.integrity_flag import IntegrityFlag
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


async def _create_flag(db: AsyncSession, location_id: uuid.UUID) -> IntegrityFlag:
    """Directly insert an integrity flag via the DB session."""
    flag = IntegrityFlag(
        location_id=location_id,
        flag_type="ghost_shift",
        severity="high",
        confidence=0.92,
        status="open",
        title="Possible ghost shift detected",
        message="Employee clocked in but no orders assigned during shift",
        evidence_json={
            "employee_id": str(uuid.uuid4()),
            "shift_hours": 8,
            "orders_during_shift": 0,
        },
        fraud_risk_score=0.75,
        created_at=datetime.now(timezone.utc),
    )
    db.add(flag)
    await db.flush()
    return flag


class TestIntegrity:
    async def test_list_flags_empty(self, client, auth_headers, location):
        """GET integrity-flags with no data returns an empty list."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/integrity-flags", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_flags_with_data(self, client, auth_headers, db, location):
        """After creating a flag, it appears in the open flags list."""
        await _create_flag(db, location.id)
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/integrity-flags", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["flag_type"] == "ghost_shift"
        assert data[0]["status"] == "open"

    async def test_review_flag_confirmed(self, client, auth_headers, db, location):
        """PATCH /integrity-flags/{id}/review with status=confirmed updates the flag."""
        flag = await _create_flag(db, location.id)
        flag_id = str(flag.id)

        resp = await client.patch(f"/api/v1/integrity-flags/{flag_id}/review", json={
            "status": "confirmed",
            "notes": "Verified: employee was not on site.",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["resolved_at"] is not None
        assert "Review notes:" in data["message"]

    async def test_review_flag_dismissed(self, client, auth_headers, db, location):
        """PATCH /integrity-flags/{id}/review with status=dismissed updates the flag."""
        flag = await _create_flag(db, location.id)
        flag_id = str(flag.id)

        resp = await client.patch(f"/api/v1/integrity-flags/{flag_id}/review", json={
            "status": "dismissed",
            "notes": "False positive — employee was training.",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dismissed"

    async def test_review_flag_invalid_status(self, client, auth_headers, db, location):
        """PATCH review with an invalid status returns 422."""
        flag = await _create_flag(db, location.id)
        flag_id = str(flag.id)

        resp = await client.patch(f"/api/v1/integrity-flags/{flag_id}/review", json={
            "status": "invalid_status",
        }, headers=auth_headers)
        assert resp.status_code == 422

    async def test_review_nonexistent_flag(self, client, auth_headers):
        """PATCH review on a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/integrity-flags/{random_id}/review", json={
            "status": "confirmed",
        }, headers=auth_headers)
        assert resp.status_code == 404

    async def test_reviewed_flag_not_in_open_list(self, client, auth_headers, db, location):
        """After confirming a flag, it no longer appears in the open list."""
        flag = await _create_flag(db, location.id)
        flag_id = str(flag.id)
        loc_id = str(location.id)

        await client.patch(f"/api/v1/integrity-flags/{flag_id}/review", json={
            "status": "confirmed",
        }, headers=auth_headers)

        resp = await client.get(f"/api/v1/locations/{loc_id}/integrity-flags", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
