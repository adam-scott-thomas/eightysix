"""Tests for recommendation endpoints."""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.recommendation import Recommendation
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


async def _create_recommendation(db: AsyncSession, location_id: uuid.UUID) -> Recommendation:
    """Directly insert a recommendation via the DB session."""
    rec = Recommendation(
        location_id=location_id,
        category="staffing",
        status="pending",
        title="Call in additional floor staff",
        reason="Current staffing level is below threshold for projected dinner rush",
        action_description="Schedule one more floor employee for 17:00-22:00",
        confidence=0.85,
        estimated_impact_json={"revenue_uplift": 200, "labor_cost": 120},
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    await db.flush()
    return rec


class TestRecommendations:
    async def test_list_recommendations_empty(self, client, location):
        """GET recommendations with no data returns an empty list."""
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/recommendations")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_recommendations_with_data(self, client, db, location):
        """After creating a recommendation, it appears in the list."""
        await _create_recommendation(db, location.id)
        loc_id = str(location.id)
        resp = await client.get(f"/api/v1/locations/{loc_id}/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["category"] == "staffing"
        assert data[0]["status"] == "pending"

    async def test_apply_recommendation(self, client, db, location):
        """PATCH /recommendations/{id}/apply changes status to applied."""
        rec = await _create_recommendation(db, location.id)
        rec_id = str(rec.id)

        resp = await client.patch(f"/api/v1/recommendations/{rec_id}/apply")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "applied"
        assert data["applied_at"] is not None

    async def test_dismiss_recommendation(self, client, db, location):
        """PATCH /recommendations/{id}/dismiss changes status to dismissed."""
        rec = await _create_recommendation(db, location.id)
        rec_id = str(rec.id)

        resp = await client.patch(f"/api/v1/recommendations/{rec_id}/dismiss")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dismissed"
        assert data["dismissed_at"] is not None

    async def test_nonexistent_recommendation_apply(self, client):
        """PATCH apply on a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/recommendations/{random_id}/apply")
        assert resp.status_code == 404

    async def test_nonexistent_recommendation_dismiss(self, client):
        """PATCH dismiss on a random UUID returns 404."""
        random_id = str(uuid.uuid4())
        resp = await client.patch(f"/api/v1/recommendations/{random_id}/dismiss")
        assert resp.status_code == 404

    async def test_applied_recommendation_not_in_pending_list(self, client, db, location):
        """After applying a recommendation, it no longer appears in the pending list."""
        rec = await _create_recommendation(db, location.id)
        rec_id = str(rec.id)
        loc_id = str(location.id)

        # Apply it
        await client.patch(f"/api/v1/recommendations/{rec_id}/apply")

        # Pending list should be empty (default status filter is 'pending')
        resp = await client.get(f"/api/v1/locations/{loc_id}/recommendations")
        assert resp.status_code == 200
        assert resp.json() == []
