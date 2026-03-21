"""Tests for the stub labor provider — uses seed data, no DB required."""
from datetime import datetime, timezone
from app.providers.labor.stub import StubLaborProvider
from app.seed.loader import load_scenario


def test_stub_labor_loads_employees():
    provider = StubLaborProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    employees = provider.fetch_employees("loc-1")
    assert len(employees) == 5


def test_stub_labor_loads_shifts():
    provider = StubLaborProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    start = datetime(2025, 3, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 3, 16, 23, 59, tzinfo=timezone.utc)
    shifts = provider.fetch_shifts("loc-1", start, end)
    assert len(shifts) > 0


def test_stub_labor_empty_location():
    provider = StubLaborProvider()
    assert provider.fetch_employees("unknown") == []


def test_stub_labor_empty_shifts():
    provider = StubLaborProvider()
    start = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc)
    assert provider.fetch_shifts("unknown", start, end) == []


def test_stub_labor_fetch_active_shifts():
    provider = StubLaborProvider()
    scenario = load_scenario("normal_day")
    provider.load_scenario("loc-1", scenario)

    # Active shifts are those with clock_out=None
    active = provider.fetch_active_shifts("loc-1")
    for shift in active:
        assert shift.clock_out is None


def test_stub_labor_fetch_active_shifts_empty_location():
    provider = StubLaborProvider()
    assert provider.fetch_active_shifts("unknown") == []
