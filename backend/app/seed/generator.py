"""Generate synthetic scenario data from minimal walk-in inputs."""
import random
from datetime import datetime, timedelta, timezone

from app.schemas.dto import EmployeeDTO, MenuItemDTO, OrderDTO, OrderItemDTO, ShiftDTO
from app.seed.loader import ScenarioData

_FIRST_NAMES = [
    "Alex", "Jordan", "Sam", "Casey", "Morgan", "Riley",
    "Quinn", "Avery", "Taylor", "Jamie", "Drew", "Blake",
]
_LAST_NAMES = [
    "Smith", "Garcia", "Kim", "Patel", "Brown",
    "Davis", "Wilson", "Lee", "Martin", "Clark",
]

# (name, category, relative_price_factor, food_cost_ratio)
_BASE_MENU = [
    ("Classic Burger", "entree", 1.00, 0.32),
    ("Grilled Chicken", "entree", 0.95, 0.30),
    ("Caesar Salad", "entree", 0.75, 0.25),
    ("Ribeye Steak", "entree", 1.60, 0.38),
    ("Fish & Chips", "entree", 1.10, 0.33),
    ("Pasta Primavera", "entree", 0.90, 0.28),
    ("Cup of Soup", "side", 0.45, 0.20),
    ("French Fries", "side", 0.35, 0.15),
    ("Wings Basket", "appetizer", 0.70, 0.30),
    ("Cheesecake", "dessert", 0.55, 0.22),
]


def generate_assessment_scenario(
    staff_count: int,
    orders_today: int,
    avg_ticket: float,
    restaurant_name: str = "Your Restaurant",
) -> ScenarioData:
    """Build a full ScenarioData from 3 walk-in inputs."""
    now = datetime.now(timezone.utc)
    open_time = now - timedelta(hours=8)

    # -- Location --
    location = {
        "name": restaurant_name,
        "timezone": "America/New_York",
        "business_hours": {
            d: {"open": "06:00", "close": "23:00"}
            for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
        },
        "default_hourly_rate": 15.00,
    }

    # -- Employees --
    kitchen_count = max(1, staff_count // 2)
    employees: list[EmployeeDTO] = []
    for i in range(staff_count):
        role = "kitchen" if i < kitchen_count else "floor"
        employees.append(EmployeeDTO(
            external_employee_id=f"QA-EMP-{i + 1:03d}",
            first_name=_FIRST_NAMES[i % len(_FIRST_NAMES)],
            last_name=_LAST_NAMES[i % len(_LAST_NAMES)],
            role=role,
            hourly_rate=16.00 if role == "kitchen" else 14.00,
        ))

    # -- Menu items (prices scaled so avg order ≈ avg_ticket) --
    # Distribution [30% 1-item, 50% 2-item, 20% 3-item] → avg 1.9 items/order
    # Account for average price factor across menu (items are sampled uniformly)
    avg_factor = sum(f for _, _, f, _ in _BASE_MENU) / len(_BASE_MENU)
    base_price = avg_ticket / (1.9 * avg_factor)
    menu_items: list[MenuItemDTO] = []
    for idx, (name, category, factor, cost_ratio) in enumerate(_BASE_MENU):
        price = round(base_price * factor, 2)
        menu_items.append(MenuItemDTO(
            external_item_id=f"QA-ITEM-{idx + 1:03d}",
            item_name=name,
            category=category,
            price=price,
            estimated_food_cost=round(price * cost_ratio, 2),
        ))

    # -- Orders + order items --
    elapsed = max(60, int((now - open_time).total_seconds()))
    orders: list[OrderDTO] = []
    order_items: list[OrderItemDTO] = []

    for i in range(orders_today):
        # Triangular distribution biased toward midday
        t = (random.random() + random.random()) / 2.0
        order_time = open_time + timedelta(seconds=int(t * elapsed))

        n_items = random.choices([1, 2, 3], weights=[30, 50, 20])[0]
        chosen = random.sample(range(len(_BASE_MENU)), min(n_items, len(_BASE_MENU)))

        order_total = 0.0
        oid = f"QA-ORD-{i + 1:04d}"
        for item_idx in chosen:
            mi = menu_items[item_idx]
            line = round(mi.price, 2)
            order_total += line
            order_items.append(OrderItemDTO(
                external_order_id=oid,
                external_item_id=mi.external_item_id,
                quantity=1,
                line_total=line,
            ))

        emp = employees[i % len(employees)]
        refund = round(order_total * 0.15, 2) if random.random() < 0.02 else 0.0

        orders.append(OrderDTO(
            external_order_id=oid,
            employee_external_id=emp.external_employee_id,
            ordered_at=order_time,
            order_total=round(order_total, 2),
            channel="dine-in",
            refund_amount=refund,
            prep_time_seconds=random.randint(180, 600),
        ))

    # -- Shifts (all currently active, staggered starts) --
    shifts: list[ShiftDTO] = []
    for i, emp in enumerate(employees):
        clock_in = open_time if i < len(employees) // 2 else open_time + timedelta(hours=random.randint(1, 3))
        shifts.append(ShiftDTO(
            external_shift_id=f"QA-SHIFT-{i + 1:03d}",
            employee_external_id=emp.external_employee_id,
            clock_in=clock_in,
            clock_out=None,
            role_during_shift=emp.role,
            source_type="manual",
            geofence_match=True,
            device_fingerprint=f"device-qa-{i + 1}",
        ))

    # Build raw dict for ScenarioData constructor
    raw = {
        "location": location,
        "employees": [e.model_dump() for e in employees],
        "menu_items": [m.model_dump() for m in menu_items],
        "orders": [o.model_dump() for o in orders],
        "order_items": [oi.model_dump() for oi in order_items],
        "shifts": [s.model_dump() for s in shifts],
    }
    return ScenarioData(raw)
