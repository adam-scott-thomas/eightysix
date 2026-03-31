import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Set required env vars before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure the backend directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import Base

# Patch SQLite to handle JSONB (renders as JSON)
from sqlalchemy.dialects.sqlite import base as _sqlite_base
_sqlite_base.SQLiteTypeCompiler.visit_JSONB = _sqlite_base.SQLiteTypeCompiler.visit_JSON

# Patch SQLite to store PostgreSQL UUID columns as CHAR(32) text
# Without this, SQLAlchemy stores UUIDs as integers in SQLite, which breaks
# the result processor when reading them back.
_sqlite_base.SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "CHAR(32)"

from app.db.models import *  # noqa: F401,F403 — register all models

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def _register_sqlite_functions(dbapi_conn, connection_record):
    """Register PostgreSQL-compatible functions for SQLite test sessions.

    With aiosqlite, the dbapi_conn is an AsyncAdapt_aiosqlite_connection.
    We unwrap to the underlying sqlite3.Connection (via aiosqlite._connection)
    and register the now() function so server_default=text("now()") works.
    """
    raw = dbapi_conn._connection  # aiosqlite.core.Connection
    inner = raw._connection       # sqlite3.Connection
    if isinstance(inner, sqlite3.Connection):
        inner.create_function("now", 0, lambda: datetime.now(timezone.utc).isoformat())


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Register now() so that server_default=text("now()") works in SQLite
    event.listen(eng.sync_engine, "connect", _register_sqlite_functions)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    """Create a regular test user and return (user, token)."""
    from app.services.auth_service import create_user, create_access_token
    user = await create_user(db, email="test@example.com", password="testpass123", full_name="Test User")
    token = create_access_token(str(user.id), user.role)
    return user, token


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession):
    """Create an admin test user and return (user, token)."""
    from app.services.auth_service import create_user, create_access_token
    user = await create_user(db, email="admin@example.com", password="adminpass123", full_name="Admin User", role="admin")
    token = create_access_token(str(user.id), user.role)
    return user, token


@pytest.fixture
def auth_headers(test_user):
    """Auth headers for a regular user."""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """Auth headers for an admin user."""
    _, token = admin_user
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def location(db: AsyncSession):
    """Create a test location and return it."""
    from app.db.models.location import Location
    loc = Location(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Grill",
        timezone="America/Detroit",
        business_hours_json={
            "mon": {"open": "06:00", "close": "23:00"},
            "tue": {"open": "06:00", "close": "23:00"},
            "wed": {"open": "06:00", "close": "23:00"},
            "thu": {"open": "06:00", "close": "23:00"},
            "fri": {"open": "06:00", "close": "23:00"},
            "sat": {"open": "06:00", "close": "23:00"},
            "sun": {"open": "06:00", "close": "23:00"},
        },
        default_hourly_rate=15.00,
    )
    db.add(loc)
    await db.flush()
    return loc


# -- Seed data helpers --

SCENARIO_DATE = datetime(2025, 3, 15, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def seed_employees(db: AsyncSession, location):
    """Seed 3 employees."""
    from app.db.models.employee import Employee
    employees = []
    for i, (first, last, role, rate) in enumerate([
        ("Maria", "Garcia", "floor", 16.00),
        ("James", "Chen", "kitchen", 17.00),
        ("Jake", "Miller", "floor", 15.00),
    ], start=1):
        emp = Employee(
            location_id=location.id,
            external_employee_id=f"EMP-{i:03d}",
            first_name=first,
            last_name=last,
            role=role,
            hourly_rate=rate,
        )
        db.add(emp)
        employees.append(emp)
    await db.flush()
    return employees


@pytest_asyncio.fixture
async def seed_menu(db: AsyncSession, location):
    """Seed 5 menu items."""
    from app.db.models.menu_item import MenuItem
    items = []
    for ext_id, name, cat, price, cost in [
        ("ITEM-001", "Classic Burger", "entrees", 13.00, 4.50),
        ("ITEM-002", "French Fries", "sides", 5.00, 2.00),
        ("ITEM-003", "Soft Drink", "drinks", 3.00, 0.30),
        ("ITEM-004", "Cheesecake Slice", "desserts", 7.50, 2.00),
        ("ITEM-005", "Caesar Salad", "entrees", 10.00, 2.50),
    ]:
        mi = MenuItem(
            location_id=location.id,
            external_item_id=ext_id,
            item_name=name,
            category=cat,
            price=price,
            estimated_food_cost=cost,
        )
        db.add(mi)
        items.append(mi)
    await db.flush()
    return items


@pytest_asyncio.fixture
async def seed_orders(db: AsyncSession, location, seed_employees, seed_menu):
    """Seed 10 orders across the day with order items."""
    from app.db.models.order import Order
    from app.db.models.order_item import OrderItem
    from datetime import timedelta

    orders = []
    emp = seed_employees[0]
    menu = seed_menu

    for i in range(10):
        hour = 14 + i  # 14:00Z to 23:00Z
        order = Order(
            location_id=location.id,
            external_order_id=f"ORD-{i+1:03d}",
            employee_id=emp.id,
            ordered_at=SCENARIO_DATE.replace(hour=hour),
            order_total=18.00,
            channel="dine_in",
            refund_amount=0,
            comp_amount=0,
            void_amount=0,
            prep_time_seconds=300,
        )
        db.add(order)
        await db.flush()

        # Add 2 order items per order
        oi1 = OrderItem(order_id=order.id, menu_item_id=menu[0].id, quantity=1, line_total=13.00)
        oi2 = OrderItem(order_id=order.id, menu_item_id=menu[1].id, quantity=1, line_total=5.00)
        db.add_all([oi1, oi2])
        orders.append(order)

    await db.flush()
    return orders


@pytest_asyncio.fixture
async def seed_shifts(db: AsyncSession, location, seed_employees):
    """Seed shifts for all employees."""
    from app.db.models.shift import Shift

    shifts = []
    for emp in seed_employees:
        shift = Shift(
            location_id=location.id,
            employee_id=emp.id,
            external_shift_id=f"SHIFT-{emp.external_employee_id}",
            clock_in=SCENARIO_DATE.replace(hour=10),
            clock_out=SCENARIO_DATE.replace(hour=20),
            role_during_shift=emp.role,
            source_type="stub",
        )
        db.add(shift)
        shifts.append(shift)
    await db.flush()
    return shifts
