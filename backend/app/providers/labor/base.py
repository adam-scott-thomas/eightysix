from datetime import datetime
from typing import Protocol

from app.schemas.dto import EmployeeDTO, ShiftDTO


class LaborProvider(Protocol):
    def fetch_employees(self, location_id: str) -> list[EmployeeDTO]: ...

    def fetch_shifts(
        self, location_id: str, start: datetime, end: datetime
    ) -> list[ShiftDTO]: ...

    def fetch_active_shifts(self, location_id: str) -> list[ShiftDTO]: ...
