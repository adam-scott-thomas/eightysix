from datetime import datetime
from app.schemas.dto import OrderDTO, OrderItemDTO, MenuItemDTO
from app.seed.loader import ScenarioData

class StubPOSProvider:
    def __init__(self):
        self._scenarios: dict[str, ScenarioData] = {}  # keyed by location_id

    def load_scenario(self, location_id: str, scenario: ScenarioData) -> None:
        self._scenarios[location_id] = scenario

    def fetch_orders(self, location_id: str, start: datetime, end: datetime) -> list[OrderDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        return [o for o in scenario.orders if start <= o.ordered_at <= end]

    def fetch_menu(self, location_id: str) -> list[MenuItemDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        return scenario.menu_items

    def fetch_order_items(self, location_id: str, order_ids: list[str]) -> list[OrderItemDTO]:
        scenario = self._scenarios.get(location_id)
        if not scenario:
            return []
        order_id_set = set(order_ids)
        return [oi for oi in scenario.order_items if oi.external_order_id in order_id_set]
