"""Generate 8 weeks of synthetic daily historical data for forecast demos.

Creates realistic variation by weekday, with seasonal patterns and
occasional noise. Each day gets orders, shifts, and menu activity
so the forecast engine has enough signal to produce non-zero predictions.
"""
import random
from datetime import date, datetime, time, timedelta, timezone

from app.schemas.dto import EmployeeDTO, MenuItemDTO, OrderDTO, OrderItemDTO, ShiftDTO

# Weekday traffic multipliers (Mon=0 through Sun=6)
DOW_MULTIPLIERS = {
    0: 0.75,   # Monday — slowest
    1: 0.80,   # Tuesday
    2: 0.85,   # Wednesday
    3: 0.90,   # Thursday
    4: 1.20,   # Friday — busy
    5: 1.30,   # Saturday — busiest
    6: 1.00,   # Sunday — brunch bump
}

# Channel probabilities by weekday
DOW_CHANNELS = {
    0: {"dine_in": 0.55, "takeout": 0.25, "delivery": 0.20},
    1: {"dine_in": 0.55, "takeout": 0.25, "delivery": 0.20},
    2: {"dine_in": 0.55, "takeout": 0.25, "delivery": 0.20},
    3: {"dine_in": 0.55, "takeout": 0.25, "delivery": 0.20},
    4: {"dine_in": 0.60, "takeout": 0.20, "delivery": 0.20},
    5: {"dine_in": 0.65, "takeout": 0.20, "delivery": 0.15},
    6: {"dine_in": 0.50, "takeout": 0.30, "delivery": 0.20},
}

_FIRST_NAMES = [
    "Alex", "Jordan", "Sam", "Casey", "Morgan", "Riley",
    "Quinn", "Avery", "Taylor", "Jamie", "Drew", "Blake",
]
_LAST_NAMES = [
    "Smith", "Garcia", "Kim", "Patel", "Brown",
    "Davis", "Wilson", "Lee", "Martin", "Clark",
]

_BASE_MENU = [
    ("Classic Burger", "entrees", 1.00, 0.32),
    ("Grilled Chicken", "entrees", 0.95, 0.30),
    ("Caesar Salad", "entrees", 0.75, 0.25),
    ("Ribeye Steak", "entrees", 1.60, 0.38),
    ("Fish & Chips", "entrees", 1.10, 0.33),
    ("Pasta Primavera", "entrees", 0.90, 0.28),
    ("Cup of Soup", "sides", 0.45, 0.20),
    ("French Fries", "sides", 0.35, 0.15),
    ("Wings Basket", "appetizers", 0.70, 0.30),
    ("Cheesecake", "desserts", 0.55, 0.22),
]


def generate_history(
    weeks: int = 8,
    base_orders_per_day: int = 180,
    avg_ticket: float = 28.00,
    staff_count: int = 8,
    restaurant_name: str = "Demo Restaurant",
) -> dict:
    """Generate multi-week historical data.

    Returns a dict with:
    - location: dict
    - employees: list[dict]
    - menu_items: list[dict]
    - daily_data: list of {date, orders, order_items, shifts}
    """
    today = date.today()
    start_date = today - timedelta(days=weeks * 7)

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
    employees = []
    for i in range(staff_count):
        role = "kitchen" if i < kitchen_count else "floor"
        employees.append({
            "external_employee_id": f"HIST-EMP-{i + 1:03d}",
            "first_name": _FIRST_NAMES[i % len(_FIRST_NAMES)],
            "last_name": _LAST_NAMES[i % len(_LAST_NAMES)],
            "role": role,
            "hourly_rate": 16.00 if role == "kitchen" else 14.00,
        })

    # -- Menu items --
    avg_factor = sum(f for _, _, f, _ in _BASE_MENU) / len(_BASE_MENU)
    base_price = avg_ticket / (1.9 * avg_factor)
    menu_items = []
    for idx, (name, category, factor, cost_ratio) in enumerate(_BASE_MENU):
        price = round(base_price * factor, 2)
        menu_items.append({
            "external_item_id": f"HIST-ITEM-{idx + 1:03d}",
            "item_name": name,
            "category": category,
            "price": price,
            "estimated_food_cost": round(price * cost_ratio, 2),
        })

    # -- Generate daily data --
    daily_data = []
    trend = 1.0  # Slight upward trend over 8 weeks

    current = start_date
    day_idx = 0
    while current <= today:
        dow = current.weekday()
        dow_mult = DOW_MULTIPLIERS[dow]
        channels = DOW_CHANNELS[dow]

        # Add some weekly trend (+0.3% per week)
        week_num = day_idx // 7
        trend = 1.0 + (week_num * 0.003)

        # Daily noise: ±10%
        noise = 1.0 + random.uniform(-0.10, 0.10)

        day_orders_count = max(10, round(base_orders_per_day * dow_mult * trend * noise))

        # Generate orders
        day_open = datetime.combine(current, time(6, 0), tzinfo=timezone.utc)
        day_close = datetime.combine(current, time(23, 0), tzinfo=timezone.utc)
        total_seconds = int((day_close - day_open).total_seconds())

        orders = []
        order_items = []

        for i in range(day_orders_count):
            # Time distribution: breakfast 10%, lunch 35%, dinner 40%, late 15%
            r = random.random()
            if r < 0.10:  # breakfast 6-11
                t_offset = random.randint(0, 5 * 3600)
            elif r < 0.45:  # lunch 11-15
                t_offset = random.randint(5 * 3600, 9 * 3600)
            elif r < 0.85:  # dinner 15-21
                t_offset = random.randint(9 * 3600, 15 * 3600)
            else:  # late 21-23
                t_offset = random.randint(15 * 3600, total_seconds)

            order_time = day_open + timedelta(seconds=t_offset)

            # Channel
            ch_r = random.random()
            if ch_r < channels["dine_in"]:
                channel = "dine_in"
            elif ch_r < channels["dine_in"] + channels["takeout"]:
                channel = "takeout"
            else:
                channel = "delivery"

            # Items
            n_items = random.choices([1, 2, 3], weights=[30, 50, 20])[0]
            chosen = random.sample(range(len(_BASE_MENU)), min(n_items, len(_BASE_MENU)))

            order_total = 0.0
            oid = f"HIST-ORD-{current.isoformat()}-{i + 1:04d}"
            for item_idx in chosen:
                mi = menu_items[item_idx]
                line = round(mi["price"], 2)
                order_total += line
                order_items.append({
                    "external_order_id": oid,
                    "external_item_id": mi["external_item_id"],
                    "quantity": 1,
                    "line_total": line,
                })

            emp = employees[i % len(employees)]
            refund = round(order_total * 0.15, 2) if random.random() < 0.02 else 0.0

            orders.append({
                "external_order_id": oid,
                "employee_external_id": emp["external_employee_id"],
                "ordered_at": order_time.isoformat(),
                "order_total": round(order_total, 2),
                "channel": channel,
                "refund_amount": refund,
                "prep_time_seconds": random.randint(180, 600),
            })

        # Shifts — vary count by weekday
        shift_count = max(3, round(staff_count * dow_mult))
        shifts = []
        for i in range(min(shift_count, len(employees))):
            emp = employees[i]
            # Stagger starts
            if i < shift_count // 2:
                clock_in = day_open + timedelta(minutes=random.randint(0, 30))
            else:
                clock_in = day_open + timedelta(hours=random.randint(3, 5), minutes=random.randint(0, 30))

            clock_out = clock_in + timedelta(hours=random.randint(6, 9))
            if clock_out > day_close:
                clock_out = day_close

            shifts.append({
                "external_shift_id": f"HIST-SHIFT-{current.isoformat()}-{i + 1:03d}",
                "employee_external_id": emp["external_employee_id"],
                "clock_in": clock_in.isoformat(),
                "clock_out": clock_out.isoformat(),
                "role_during_shift": emp["role"],
                "source_type": "manual",
                "geofence_match": True,
                "device_fingerprint": f"device-hist-{i + 1}",
            })

        daily_data.append({
            "date": current,
            "orders": orders,
            "order_items": order_items,
            "shifts": shifts,
        })

        current += timedelta(days=1)
        day_idx += 1

    return {
        "location": location,
        "employees": employees,
        "menu_items": menu_items,
        "daily_data": daily_data,
    }
