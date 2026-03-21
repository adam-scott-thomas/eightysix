"""Tests for the stub POS provider — uses seed data, no DB required."""
from datetime import datetime, timezone
from app.providers.pos.stub import StubPOSProvider
from app.seed.loader import load_scenario


def test_stub_pos_loads_orders():
    provider = StubPOSProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    # normal_day orders span 2025-03-15T14:00:00Z to 2025-03-16T01:03:00Z
    start = datetime(2025, 3, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 3, 16, 23, 59, tzinfo=timezone.utc)
    orders = provider.fetch_orders("loc-1", start, end)
    assert len(orders) > 0


def test_stub_pos_orders_filtered_by_date():
    provider = StubPOSProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    # Narrow window that should exclude most orders
    start = datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc)
    end = datetime(2025, 3, 15, 14, 30, tzinfo=timezone.utc)
    orders = provider.fetch_orders("loc-1", start, end)
    # Should have some orders but fewer than the full set of 40
    assert len(orders) < 40


def test_stub_pos_menu():
    provider = StubPOSProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    menu = provider.fetch_menu("loc-1")
    assert len(menu) == 15


def test_stub_pos_empty_location():
    provider = StubPOSProvider()
    start = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc)
    assert provider.fetch_orders("unknown", start, end) == []
    assert provider.fetch_menu("unknown") == []


def test_stub_pos_fetch_order_items():
    provider = StubPOSProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    # Get a known order id from the scenario
    order_id = scenario.orders[0].external_order_id
    items = provider.fetch_order_items("loc-1", [order_id])
    assert len(items) > 0
    assert all(oi.external_order_id == order_id for oi in items)


def test_stub_pos_fetch_order_items_empty_location():
    provider = StubPOSProvider()
    assert provider.fetch_order_items("unknown", ["ORD-001"]) == []
