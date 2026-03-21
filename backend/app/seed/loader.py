import json
from pathlib import Path
from app.schemas.dto import OrderDTO, OrderItemDTO, MenuItemDTO, EmployeeDTO, ShiftDTO

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

VALID_SCENARIOS = [
    "normal_day", "dinner_rush", "refund_spike", "suspicious_punch",
    "understaffed", "overstaffed", "ghost_shift", "low_margin_mix",
]

class ScenarioData:
    """Holds all parsed DTOs for a scenario."""
    def __init__(self, raw: dict):
        self.location = raw["location"]
        self.employees = [EmployeeDTO(**e) for e in raw["employees"]]
        self.menu_items = [MenuItemDTO(**m) for m in raw["menu_items"]]
        self.orders = [OrderDTO(**o) for o in raw["orders"]]
        self.order_items = [OrderItemDTO(**oi) for oi in raw["order_items"]]
        self.shifts = [ShiftDTO(**s) for s in raw["shifts"]]
        self.observations = raw.get("observations", [])

def load_scenario(scenario_name: str) -> ScenarioData:
    if scenario_name not in VALID_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Valid: {VALID_SCENARIOS}")
    path = SCENARIOS_DIR / f"{scenario_name}.json"
    with open(path) as f:
        return ScenarioData(json.load(f))

def list_scenarios() -> list[str]:
    return VALID_SCENARIOS
