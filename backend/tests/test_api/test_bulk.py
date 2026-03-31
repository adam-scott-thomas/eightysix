"""Tests for bulk input endpoints (/employees/bulk, /menu-items/bulk, /orders/bulk, /shifts/bulk)."""
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


EMPLOYEE_PAYLOADS = [
    {
        "external_employee_id": "EMP-100",
        "first_name": "Alice",
        "last_name": "Smith",
        "role": "floor",
        "hourly_rate": 16.00,
    },
    {
        "external_employee_id": "EMP-101",
        "first_name": "Bob",
        "last_name": "Jones",
        "role": "kitchen",
        "hourly_rate": 17.50,
    },
]

MENU_PAYLOADS = [
    {
        "external_item_id": "MENU-100",
        "item_name": "Margherita Pizza",
        "category": "entrees",
        "price": 14.00,
        "estimated_food_cost": 3.50,
    },
    {
        "external_item_id": "MENU-101",
        "item_name": "Garlic Bread",
        "category": "sides",
        "price": 5.50,
        "estimated_food_cost": 1.00,
    },
]


class TestBulk:
    async def test_bulk_employees(self, client, auth_headers, location):
        """POST /employees/bulk with 2 employees returns created: 2."""
        loc_id = str(location.id)
        resp = await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 2
        assert data["updated"] == 0

    async def test_bulk_employees_idempotent(self, client, auth_headers, location):
        """POST same employee data twice — second call updates, not creates."""
        loc_id = str(location.id)

        # First call
        resp1 = await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )
        assert resp1.json()["created"] == 2

        # Second call with same data
        resp2 = await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )
        data2 = resp2.json()
        assert data2["updated"] == 2
        assert data2["created"] == 0

    async def test_bulk_menu_items(self, client, auth_headers, location):
        """POST /menu-items/bulk creates menu items."""
        loc_id = str(location.id)
        resp = await client.post(
            f"/api/v1/locations/{loc_id}/menu-items/bulk",
            json=MENU_PAYLOADS,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 2

    async def test_bulk_orders_with_items(self, client, auth_headers, location):
        """POST /orders/bulk with nested order items creates both."""
        loc_id = str(location.id)

        # Need employees and menu items first for FK resolution
        await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/locations/{loc_id}/menu-items/bulk",
            json=MENU_PAYLOADS,
            headers=auth_headers,
        )

        order_payloads = [
            {
                "external_order_id": "ORD-100",
                "employee_external_id": "EMP-100",
                "ordered_at": "2025-03-15T18:00:00Z",
                "order_total": 19.50,
                "channel": "dine_in",
                "refund_amount": 0,
                "comp_amount": 0,
                "void_amount": 0,
                "prep_time_seconds": 420,
                "items": [
                    {"external_item_id": "MENU-100", "quantity": 1, "line_total": 14.00},
                    {"external_item_id": "MENU-101", "quantity": 1, "line_total": 5.50},
                ],
            },
        ]

        resp = await client.post(
            f"/api/v1/locations/{loc_id}/orders/bulk",
            json=order_payloads,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["orders"]["created"] == 1
        assert data["order_items"]["created"] == 2

    async def test_bulk_shifts(self, client, auth_headers, location):
        """POST /shifts/bulk creates shifts."""
        loc_id = str(location.id)

        # Need employees first
        await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )

        shift_payloads = [
            {
                "external_shift_id": "SHIFT-100",
                "employee_external_id": "EMP-100",
                "clock_in": "2025-03-15T10:00:00Z",
                "clock_out": "2025-03-15T18:00:00Z",
                "role_during_shift": "floor",
                "source_type": "manual",
            },
            {
                "external_shift_id": "SHIFT-101",
                "employee_external_id": "EMP-101",
                "clock_in": "2025-03-15T11:00:00Z",
                "clock_out": "2025-03-15T20:00:00Z",
                "role_during_shift": "kitchen",
                "source_type": "manual",
            },
        ]

        resp = await client.post(
            f"/api/v1/locations/{loc_id}/shifts/bulk",
            json=shift_payloads,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 2

    async def test_bulk_with_recompute(
        self, client, auth_headers, location, seed_employees, seed_menu, seed_orders, seed_shifts
    ):
        """POST /employees/bulk?recompute=true includes dashboard in response.

        Uses conftest fixtures to pre-populate data so the recompute has
        tz-aware datetimes in the session cache (orders/shifts created via
        fixtures bypass SQLite's naive datetime storage). The recompute is
        triggered via the employees bulk endpoint since it doesn't ingest
        new orders through SQLite.
        """
        loc_id = str(location.id)

        # Trigger recompute via a lightweight employee bulk update
        resp = await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            params={"recompute": "true"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboard" in data
        assert "status" in data["dashboard"]

    async def test_bulk_orders_dedup(self, client, auth_headers, location):
        """POST orders twice with same external IDs — same count in DB, second call updates."""
        loc_id = str(location.id)

        await client.post(
            f"/api/v1/locations/{loc_id}/employees/bulk",
            json=EMPLOYEE_PAYLOADS,
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/locations/{loc_id}/menu-items/bulk",
            json=MENU_PAYLOADS,
            headers=auth_headers,
        )

        order_payloads = [
            {
                "external_order_id": "ORD-300",
                "employee_external_id": "EMP-100",
                "ordered_at": "2025-03-15T15:00:00Z",
                "order_total": 14.00,
                "channel": "dine_in",
                "items": [],
            },
            {
                "external_order_id": "ORD-301",
                "employee_external_id": "EMP-101",
                "ordered_at": "2025-03-15T15:30:00Z",
                "order_total": 5.50,
                "channel": "takeout",
                "items": [],
            },
        ]

        # First call
        resp1 = await client.post(
            f"/api/v1/locations/{loc_id}/orders/bulk",
            json=order_payloads,
            headers=auth_headers,
        )
        assert resp1.json()["orders"]["created"] == 2

        # Second call with same data — should update, not create
        resp2 = await client.post(
            f"/api/v1/locations/{loc_id}/orders/bulk",
            json=order_payloads,
            headers=auth_headers,
        )
        assert resp2.json()["orders"]["updated"] == 2
        assert resp2.json()["orders"]["created"] == 0
