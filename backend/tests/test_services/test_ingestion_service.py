"""Integration tests for IngestionService — upsert logic, idempotency, FK resolution."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, func

from app.db.models.order_item import OrderItem
from app.repositories.employee_repo import EmployeeRepository
from app.schemas.dto import EmployeeDTO, MenuItemDTO, OrderDTO, OrderItemDTO, ShiftDTO
from app.services.ingestion_service import IngestionService
from tests.conftest import SCENARIO_DATE


class TestIngestionService:
    async def test_ingest_employees_creates(self, db, location):
        svc = IngestionService(db)
        dtos = [EmployeeDTO(external_employee_id="E1", first_name="Test", last_name="User", role="floor")]
        summary = await svc._ingest_employees(location.id, dtos)
        assert summary.created == 1
        assert summary.updated == 0

    async def test_ingest_employees_upsert_idempotent(self, db, location):
        svc = IngestionService(db)
        dto = [EmployeeDTO(external_employee_id="E1", first_name="Test", last_name="User", role="floor")]
        await svc._ingest_employees(location.id, dto)
        # Re-ingest same employee
        summary2 = await svc._ingest_employees(location.id, dto)
        assert summary2.created == 0
        assert summary2.updated == 1

    async def test_ingest_employees_updates_fields(self, db, location):
        svc = IngestionService(db)
        dto1 = [EmployeeDTO(external_employee_id="E1", first_name="Test", last_name="User", role="floor", hourly_rate=15.0)]
        await svc._ingest_employees(location.id, dto1)
        dto2 = [EmployeeDTO(external_employee_id="E1", first_name="Test", last_name="User", role="kitchen", hourly_rate=18.0)]
        await svc._ingest_employees(location.id, dto2)
        repo = EmployeeRepository(db)
        emp = await repo.get_by_external_id(location.id, "E1")
        assert emp.role == "kitchen"
        assert float(emp.hourly_rate) == 18.0

    async def test_ingest_menu_items_creates(self, db, location):
        svc = IngestionService(db)
        dtos = [MenuItemDTO(external_item_id="M1", item_name="Burger", price=13.0)]
        summary = await svc._ingest_menu_items(location.id, dtos)
        assert summary.created == 1

    async def test_ingest_menu_items_idempotent(self, db, location):
        svc = IngestionService(db)
        dto = [MenuItemDTO(external_item_id="M1", item_name="Burger", price=13.0)]
        await svc._ingest_menu_items(location.id, dto)
        s2 = await svc._ingest_menu_items(location.id, dto)
        assert s2.updated == 1
        assert s2.created == 0

    async def test_ingest_orders_creates(self, db, location, seed_employees):
        svc = IngestionService(db)
        dtos = [OrderDTO(
            external_order_id="O1",
            employee_external_id="EMP-001",
            ordered_at=SCENARIO_DATE.replace(hour=14),
            order_total=18.00,
        )]
        summary = await svc._ingest_orders(location.id, dtos)
        assert summary.created == 1

    async def test_ingest_orders_idempotent(self, db, location, seed_employees):
        svc = IngestionService(db)
        dto = [OrderDTO(
            external_order_id="O1",
            employee_external_id="EMP-001",
            ordered_at=SCENARIO_DATE.replace(hour=14),
            order_total=18.00,
        )]
        await svc._ingest_orders(location.id, dto)
        s2 = await svc._ingest_orders(location.id, dto)
        assert s2.updated == 1
        assert s2.created == 0

    async def test_ingest_order_items_dedup(self, db, location, seed_employees, seed_menu):
        """Re-ingesting order items should delete old ones and recreate, not duplicate."""
        svc = IngestionService(db)
        # Create an order first
        await svc._ingest_orders(location.id, [OrderDTO(
            external_order_id="O1",
            ordered_at=SCENARIO_DATE.replace(hour=14),
            order_total=18.00,
        )])
        oi_dto = [OrderItemDTO(external_order_id="O1", external_item_id="ITEM-001", quantity=1, line_total=13.00)]
        s1 = await svc._ingest_order_items(location.id, oi_dto)
        assert s1.created == 1
        # Re-ingest same order items
        s2 = await svc._ingest_order_items(location.id, oi_dto)
        assert s2.created == 1  # deleted + recreated
        # Check only 1 order_item exists, not 2
        count = await db.execute(select(func.count()).select_from(OrderItem))
        assert count.scalar_one() == 1

    async def test_ingest_shifts_creates(self, db, location, seed_employees):
        svc = IngestionService(db)
        dtos = [ShiftDTO(
            external_shift_id="S1",
            employee_external_id="EMP-001",
            clock_in=SCENARIO_DATE.replace(hour=10),
            clock_out=SCENARIO_DATE.replace(hour=18),
            source_type="stub",
        )]
        summary = await svc._ingest_shifts(location.id, dtos)
        assert summary.created == 1

    async def test_ingest_shifts_skips_unknown_employee(self, db, location):
        svc = IngestionService(db)
        dtos = [ShiftDTO(
            employee_external_id="UNKNOWN",
            clock_in=SCENARIO_DATE.replace(hour=10),
            source_type="stub",
        )]
        summary = await svc._ingest_shifts(location.id, dtos)
        assert summary.skipped == 1

    async def test_ensure_location_creates(self, db):
        svc = IngestionService(db)
        loc = await svc.ensure_location({"name": "New Place", "timezone": "America/New_York"})
        assert loc.name == "New Place"

    async def test_ensure_location_idempotent(self, db, location):
        svc = IngestionService(db)
        loc = await svc.ensure_location({"name": "Test Grill", "timezone": "America/Detroit"})
        assert loc.id == location.id

    async def test_ingest_multiple_employees(self, db, location):
        """Batch create multiple employees in one call."""
        svc = IngestionService(db)
        dtos = [
            EmployeeDTO(external_employee_id="E1", first_name="A", last_name="B", role="floor"),
            EmployeeDTO(external_employee_id="E2", first_name="C", last_name="D", role="kitchen"),
            EmployeeDTO(external_employee_id="E3", first_name="E", last_name="F", role="floor"),
        ]
        summary = await svc._ingest_employees(location.id, dtos)
        assert summary.created == 3
        assert summary.updated == 0
        assert summary.skipped == 0

    async def test_ingest_orders_without_employee(self, db, location):
        """Orders without employee_external_id should still be created."""
        svc = IngestionService(db)
        dtos = [OrderDTO(
            external_order_id="O-NOEMP",
            ordered_at=SCENARIO_DATE.replace(hour=14),
            order_total=25.00,
        )]
        summary = await svc._ingest_orders(location.id, dtos)
        assert summary.created == 1

    async def test_ingest_order_items_skips_missing_menu(self, db, location, seed_employees):
        """Order items referencing a non-existent menu item should be skipped."""
        svc = IngestionService(db)
        await svc._ingest_orders(location.id, [OrderDTO(
            external_order_id="O1",
            ordered_at=SCENARIO_DATE.replace(hour=14),
            order_total=18.00,
        )])
        oi_dto = [OrderItemDTO(external_order_id="O1", external_item_id="NONEXISTENT", quantity=1, line_total=13.00)]
        s = await svc._ingest_order_items(location.id, oi_dto)
        assert s.skipped == 1
        assert s.created == 0
