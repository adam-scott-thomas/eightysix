from datetime import datetime
from app.schemas.dto import EmployeeDTO, ShiftDTO
from app.seed.loader import ScenarioData

class StubLaborProvider:
    def __init__(self):
        self._scenarios: dict[str, ScenarioData] = {}

    def load_scenario(self, location_id: str, scenario: ScenarioData) -> None:
        self._scenarios[location_id] = scenario

    def fetch_employees(self, location_id: str) -> list[EmployeeDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        return scenario.employees

    def fetch_shifts(self, location_id: str, start: datetime, end: datetime) -> list[ShiftDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        return [s for s in scenario.shifts if start <= s.clock_in <= end]

    def fetch_active_shifts(self, location_id: str) -> list[ShiftDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        return [s for s in scenario.shifts if s.clock_out is None]
