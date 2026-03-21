import uuid

from sqlalchemy import select

from app.db.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    async def get_by_external_id(self, location_id: uuid.UUID, external_id: str) -> Employee | None:
        stmt = select(Employee).where(
            Employee.location_id == location_id,
            Employee.external_employee_id == external_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_location(self, location_id: uuid.UUID) -> list[Employee]:
        stmt = select(Employee).where(
            Employee.location_id == location_id,
            Employee.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
