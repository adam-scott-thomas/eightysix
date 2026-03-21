"""Readiness service — checks which data domains are populated."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.employee_repo import EmployeeRepository
from app.repositories.location_repo import LocationRepository
from app.repositories.menu_repo import MenuRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.shift_repo import ShiftRepository


QUICK_WIN_REQUIREMENTS = {
    "staffing": ["location", "orders", "shifts"],
    "labor": ["location", "orders", "shifts", "employees"],
    "leakage": ["location", "orders"],
    "menu": ["location", "orders", "menu"],
    "rush": ["location", "orders"],
    "integrity": ["location", "shifts", "employees"],
}


class ReadinessService:
    def __init__(self, db: AsyncSession):
        self.location_repo = LocationRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.menu_repo = MenuRepository(db)
        self.order_repo = OrderRepository(db)
        self.shift_repo = ShiftRepository(db)

    async def check_readiness(
        self, location_id: uuid.UUID, day_start: datetime, day_end: datetime
    ) -> dict:
        domains = {}

        # Location check
        loc = await self.location_repo.get_by_id(location_id)
        domains["location"] = loc is not None and loc.is_active

        # Menu check
        menu_items = await self.menu_repo.get_active_by_location(location_id)
        domains["menu"] = len(menu_items) >= 1

        # Orders check
        order_count = await self.order_repo.get_order_count(location_id, day_start, day_end)
        domains["orders"] = order_count >= 1

        # Shifts check
        shifts = await self.shift_repo.get_by_time_range(location_id, day_start, day_end)
        domains["shifts"] = len(shifts) >= 1

        # Employees check
        employees = await self.employee_repo.get_active_by_location(location_id)
        domains["employees"] = len(employees) >= 1

        # Compute results
        populated = [k for k, v in domains.items() if v]
        missing = [k for k, v in domains.items() if not v]
        completeness = len(populated) / len(domains) if domains else 0

        # Which quick wins can run?
        available_quick_wins = []
        for qw, reqs in QUICK_WIN_REQUIREMENTS.items():
            if all(domains.get(r, False) for r in reqs):
                available_quick_wins.append(qw)

        if len(populated) == len(domains):
            status = "ready"
        elif len(populated) >= 2:
            status = "partial"
        else:
            status = "insufficient"

        return {
            "status": status,
            "completeness_score": round(completeness, 2),
            "missing_domains": missing,
            "available_quick_wins": available_quick_wins,
            "domains": domains,
        }
