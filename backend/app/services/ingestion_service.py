"""Ingestion service — maps DTOs to models, upserts on composite keys."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.employee import Employee
from app.db.models.location import Location
from app.db.models.menu_item import MenuItem
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.shift import Shift
from app.repositories.employee_repo import EmployeeRepository
from app.repositories.location_repo import LocationRepository
from app.repositories.menu_repo import MenuRepository
from app.repositories.order_repo import OrderRepository, OrderItemRepository
from app.repositories.shift_repo import ShiftRepository
from app.schemas.common import IngestionSummary
from app.schemas.dto import (
    EmployeeDTO,
    MenuItemDTO,
    OrderDTO,
    OrderItemDTO,
    ShiftDTO,
)
from app.seed.loader import ScenarioData


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.location_repo = LocationRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.menu_repo = MenuRepository(db)
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.shift_repo = ShiftRepository(db)

    async def ingest_scenario(
        self, location_id: uuid.UUID, scenario: ScenarioData
    ) -> dict[str, IngestionSummary]:
        """Ingest all data from a scenario. Returns per-entity summaries."""
        results = {}

        results["employees"] = await self._ingest_employees(location_id, scenario.employees)
        results["menu_items"] = await self._ingest_menu_items(location_id, scenario.menu_items)
        results["orders"] = await self._ingest_orders(location_id, scenario.orders)
        results["order_items"] = await self._ingest_order_items(location_id, scenario.order_items)
        results["shifts"] = await self._ingest_shifts(location_id, scenario.shifts)

        return results

    async def ingest_from_providers(
        self,
        location_id: uuid.UUID,
        orders: list[OrderDTO],
        order_items: list[OrderItemDTO],
        menu_items: list[MenuItemDTO],
        employees: list[EmployeeDTO],
        shifts: list[ShiftDTO],
    ) -> dict[str, IngestionSummary]:
        """Ingest data fetched from providers."""
        results = {}

        results["employees"] = await self._ingest_employees(location_id, employees)
        results["menu_items"] = await self._ingest_menu_items(location_id, menu_items)
        results["orders"] = await self._ingest_orders(location_id, orders)
        results["order_items"] = await self._ingest_order_items(location_id, order_items)
        results["shifts"] = await self._ingest_shifts(location_id, shifts)

        return results

    async def ensure_location(self, location_data: dict) -> Location:
        """Create or return existing location from scenario location data."""
        locations = await self.location_repo.list(limit=1, name=location_data["name"])
        if locations:
            return locations[0]

        loc = Location(
            name=location_data["name"],
            timezone=location_data["timezone"],
            business_hours_json=location_data.get("business_hours"),
            default_hourly_rate=location_data.get("default_hourly_rate", 15.00),
        )
        return await self.location_repo.create(loc)

    # -- Private ingestion methods --

    async def _ingest_employees(
        self, location_id: uuid.UUID, employees: list[EmployeeDTO]
    ) -> IngestionSummary:
        summary = IngestionSummary()
        for dto in employees:
            existing = await self.employee_repo.get_by_external_id(
                location_id, dto.external_employee_id
            )
            if existing:
                existing.first_name = dto.first_name
                existing.last_name = dto.last_name
                existing.role = dto.role
                existing.hourly_rate = dto.hourly_rate
                existing.is_active = True
                summary.updated += 1
            else:
                emp = Employee(
                    location_id=location_id,
                    external_employee_id=dto.external_employee_id,
                    first_name=dto.first_name,
                    last_name=dto.last_name,
                    role=dto.role,
                    hourly_rate=dto.hourly_rate,
                )
                self.db.add(emp)
                summary.created += 1
        await self.db.flush()
        return summary

    async def _ingest_menu_items(
        self, location_id: uuid.UUID, menu_items: list[MenuItemDTO]
    ) -> IngestionSummary:
        summary = IngestionSummary()
        for dto in menu_items:
            existing = await self.menu_repo.get_by_external_id(
                location_id, dto.external_item_id
            )
            if existing:
                existing.item_name = dto.item_name
                existing.category = dto.category
                existing.price = dto.price
                existing.estimated_food_cost = dto.estimated_food_cost
                existing.is_active = True
                summary.updated += 1
            else:
                item = MenuItem(
                    location_id=location_id,
                    external_item_id=dto.external_item_id,
                    item_name=dto.item_name,
                    category=dto.category,
                    price=dto.price,
                    estimated_food_cost=dto.estimated_food_cost,
                )
                self.db.add(item)
                summary.created += 1
        await self.db.flush()
        return summary

    async def _ingest_orders(
        self, location_id: uuid.UUID, orders: list[OrderDTO]
    ) -> IngestionSummary:
        summary = IngestionSummary()
        for dto in orders:
            existing = await self.order_repo.get_by_external_id(
                location_id, dto.external_order_id
            )

            # Resolve employee FK if provided
            employee_id = None
            if dto.employee_external_id:
                emp = await self.employee_repo.get_by_external_id(
                    location_id, dto.employee_external_id
                )
                if emp:
                    employee_id = emp.id

            if existing:
                existing.employee_id = employee_id
                existing.ordered_at = dto.ordered_at
                existing.order_total = dto.order_total
                existing.channel = dto.channel
                existing.refund_amount = dto.refund_amount
                existing.comp_amount = dto.comp_amount
                existing.void_amount = dto.void_amount
                existing.prep_time_seconds = dto.prep_time_seconds
                summary.updated += 1
            else:
                order = Order(
                    location_id=location_id,
                    external_order_id=dto.external_order_id,
                    employee_id=employee_id,
                    ordered_at=dto.ordered_at,
                    order_total=dto.order_total,
                    channel=dto.channel,
                    refund_amount=dto.refund_amount,
                    comp_amount=dto.comp_amount,
                    void_amount=dto.void_amount,
                    prep_time_seconds=dto.prep_time_seconds,
                )
                self.db.add(order)
                summary.created += 1
        await self.db.flush()
        return summary

    async def _ingest_order_items(
        self, location_id: uuid.UUID, order_items: list[OrderItemDTO]
    ) -> IngestionSummary:
        from sqlalchemy import delete

        summary = IngestionSummary()

        # Build lookup caches
        order_cache: dict[str, uuid.UUID] = {}
        menu_cache: dict[str, uuid.UUID] = {}
        cleared_orders: set[uuid.UUID] = set()

        for dto in order_items:
            # Resolve order FK
            if dto.external_order_id not in order_cache:
                order = await self.order_repo.get_by_external_id(
                    location_id, dto.external_order_id
                )
                if order:
                    order_cache[dto.external_order_id] = order.id

            # Resolve menu item FK
            if dto.external_item_id not in menu_cache:
                item = await self.menu_repo.get_by_external_id(
                    location_id, dto.external_item_id
                )
                if item:
                    menu_cache[dto.external_item_id] = item.id

            order_id = order_cache.get(dto.external_order_id)
            menu_item_id = menu_cache.get(dto.external_item_id)

            if not order_id or not menu_item_id:
                summary.skipped += 1
                continue

            # Delete existing order_items for this order on first encounter
            if order_id not in cleared_orders:
                await self.db.execute(
                    delete(OrderItem).where(OrderItem.order_id == order_id)
                )
                cleared_orders.add(order_id)

            oi = OrderItem(
                order_id=order_id,
                menu_item_id=menu_item_id,
                quantity=dto.quantity,
                line_total=dto.line_total,
            )
            self.db.add(oi)
            summary.created += 1

        await self.db.flush()
        return summary

    async def _ingest_shifts(
        self, location_id: uuid.UUID, shifts: list[ShiftDTO]
    ) -> IngestionSummary:
        summary = IngestionSummary()
        for dto in shifts:
            # Resolve employee FK
            emp = await self.employee_repo.get_by_external_id(
                location_id, dto.employee_external_id
            )
            if not emp:
                summary.skipped += 1
                continue

            existing = None
            if dto.external_shift_id:
                existing = await self.shift_repo.get_by_external_id(
                    location_id, dto.external_shift_id
                )

            if existing:
                existing.employee_id = emp.id
                existing.clock_in = dto.clock_in
                existing.clock_out = dto.clock_out
                existing.role_during_shift = dto.role_during_shift
                existing.source_type = dto.source_type
                existing.ip_address = dto.ip_address
                existing.device_fingerprint = dto.device_fingerprint
                existing.geo_lat = dto.geo_lat
                existing.geo_lng = dto.geo_lng
                existing.geofence_match = dto.geofence_match
                summary.updated += 1
            else:
                shift = Shift(
                    location_id=location_id,
                    employee_id=emp.id,
                    external_shift_id=dto.external_shift_id,
                    clock_in=dto.clock_in,
                    clock_out=dto.clock_out,
                    role_during_shift=dto.role_during_shift,
                    source_type=dto.source_type,
                    ip_address=dto.ip_address,
                    device_fingerprint=dto.device_fingerprint,
                    geo_lat=dto.geo_lat,
                    geo_lng=dto.geo_lng,
                    geofence_match=dto.geofence_match,
                )
                self.db.add(shift)
                summary.created += 1

        await self.db.flush()
        return summary
