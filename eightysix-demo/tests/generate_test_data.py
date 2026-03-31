"""Generate realistic test CSV/XLSX files that mimic real restaurant exports.

Creates messy, realistic files — not clean test fixtures.
Run: python tests/generate_test_data.py
"""

import csv
import random
import sys
from datetime import date, timedelta, datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "fixtures"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 90 days of data: Jan 1 – Mar 31, 2025
    start = date(2025, 1, 1)
    days = 90
    employees = [
        "Maria Garcia", "James Wilson", "Sam Patel", "Alex Kim",
        "Jordan Brown", "Casey Davis", "Morgan Lee", "Riley Clark",
        "Quinn Martin", "Taylor Jones",
    ]

    _write_sales_csv(start, days)
    _write_labor_csv(start, days, employees)
    _write_refunds_csv(start, days, employees)
    _write_menu_mix_csv()
    _write_punches_csv(start, days, employees)

    print(f"Test fixtures written to: {OUTPUT_DIR}")


def _write_sales_csv(start: date, days: int):
    """Sales summary with messy headers (mimics Toast export)."""
    path = OUTPUT_DIR / "Daily_Sales_Report_Q1.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        # Title row (junk)
        w.writerow(["Demo Grill — Daily Sales Summary", "", "", "", ""])
        w.writerow([])  # Blank row
        # Headers with inconsistent naming
        w.writerow(["Business Date", "Net Sales", "Order Count", "Delivery Sales $", "Gross Sales"])

        for i in range(days):
            d = start + timedelta(days=i)
            weekday = d.weekday()

            # Base sales by day of week
            base = {0: 3200, 1: 2900, 2: 3100, 3: 3400, 4: 4200, 5: 4800, 6: 3600}
            daily_net = base[weekday] + random.randint(-400, 400)
            orders = int(daily_net / random.uniform(18, 28))
            delivery = round(daily_net * random.uniform(0.15, 0.35), 2)
            gross = round(daily_net * random.uniform(1.02, 1.06), 2)

            # Random date format mix
            if random.random() < 0.3:
                date_str = d.strftime("%m/%d/%Y")
            elif random.random() < 0.5:
                date_str = d.strftime("%Y-%m-%d")
            else:
                date_str = d.strftime("%m/%d/%y")

            # Currency formatting variation
            net_str = f"${daily_net:,.2f}" if random.random() < 0.5 else str(daily_net)
            del_str = f"${delivery:,.2f}" if random.random() < 0.5 else f"{delivery:.2f}"

            w.writerow([date_str, net_str, orders, del_str, f"${gross:,.2f}"])

        # Total row (should be ignored)
        w.writerow(["TOTAL", "$312,450.00", "12,847", "$78,112.50", "$331,197.00"])


def _write_labor_csv(start: date, days: int, employees: list[str]):
    """Labor report with overstaffing baked in."""
    path = OUTPUT_DIR / "labor_cost_report.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Team Member", "Role", "Hours Worked", "Total Pay", "Scheduled Hours"])

        for i in range(days):
            d = start + timedelta(days=i)
            weekday = d.weekday()
            date_str = d.strftime("%m/%d/%Y")

            # How many staff work today
            staff_count = {0: 6, 1: 5, 2: 6, 3: 6, 4: 8, 5: 9, 6: 7}[weekday]

            # Overstaffing: Mondays and Tuesdays get 2 extra staff ~40% of the time
            if weekday in (0, 1) and random.random() < 0.4:
                staff_count += 2

            working = random.sample(employees, min(staff_count, len(employees)))
            for emp in working:
                role = "Kitchen" if employees.index(emp) < 4 else "Floor"
                hours = round(random.uniform(5, 9), 2)
                rate = 18.00 if role == "Kitchen" else 15.00
                pay = round(hours * rate, 2)
                scheduled = round(hours - random.uniform(-1, 1.5), 2)
                scheduled = max(4, scheduled)

                w.writerow([date_str, emp, role, hours, f"${pay:.2f}", scheduled])


def _write_refunds_csv(start: date, days: int, employees: list[str]):
    """Refund report with one suspicious employee baked in."""
    path = OUTPUT_DIR / "Refund_Void_Report.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        # Slightly different header style
        w.writerow(["Check Closed", "Server", "Action Type", "Amount $", "Order #", "Reason"])

        suspicious_emp = employees[3]  # Sam Patel

        for i in range(days):
            d = start + timedelta(days=i)

            # Normal refunds: 1-3 per day from random employees
            n_normal = random.randint(1, 3)
            for _ in range(n_normal):
                emp = random.choice(employees)
                hour = random.randint(11, 22)
                ts = datetime(d.year, d.month, d.day, hour, random.randint(0, 59))
                amount = round(random.uniform(8, 45), 2)
                rtype = random.choice(["Refund", "Void", "Comp"])
                order_id = f"ORD-{random.randint(10000, 99999)}"
                reason = random.choice(["Wrong item", "Cold food", "Customer request", "Duplicate", ""])

                w.writerow([ts.strftime("%m/%d/%Y %I:%M %p"), emp, rtype, f"${amount:.2f}", order_id, reason])

            # Suspicious employee: extra 2-4 refunds per day
            for _ in range(random.randint(2, 4)):
                hour = random.randint(17, 22)  # Mostly evening
                ts = datetime(d.year, d.month, d.day, hour, random.randint(0, 59))
                amount = round(random.uniform(15, 55), 2)
                rtype = random.choice(["Refund", "Void"])
                order_id = f"ORD-{random.randint(10000, 99999)}"

                w.writerow([ts.strftime("%m/%d/%Y %I:%M %p"), suspicious_emp, rtype, f"${amount:.2f}", order_id, ""])


def _write_menu_mix_csv():
    """Menu mix report — aggregate (no per-day breakdown)."""
    path = OUTPUT_DIR / "menu_performance_Q1.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item Name", "Category", "Qty Sold", "Net Sales", "Food Cost %"])

        items = [
            ("Classic Burger", "Entrees", 2840, 39760.00, "32%"),
            ("Grilled Chicken Sandwich", "Entrees", 2100, 25200.00, "28%"),
            ("Caesar Salad", "Entrees", 1560, 14040.00, "22%"),
            ("Ribeye Steak", "Entrees", 680, 23800.00, "42%"),
            ("Fish & Chips", "Entrees", 1200, 16800.00, "35%"),
            ("Pasta Primavera", "Entrees", 890, 11570.00, "26%"),
            ("French Fries", "Sides", 4200, 16800.00, "12%"),  # High volume, low margin
            ("Cup of Soup", "Sides", 1800, 9000.00, "18%"),
            ("Wings Basket", "Appetizers", 1650, 18150.00, "33%"),
            ("Cheesecake Slice", "Desserts", 920, 7360.00, "20%"),
            ("Craft Beer", "Beverages", 3100, 21700.00, "15%"),
            ("House Wine", "Beverages", 1400, 14000.00, "18%"),
            ("Soft Drinks", "Beverages", 5200, 15600.00, "8%"),  # Huge volume, tiny cost
            ("Loaded Nachos", "Appetizers", 1100, 13200.00, "30%"),
            ("Side Salad", "Sides", 2400, 12000.00, "15%"),
        ]

        for item_name, category, qty, revenue, cost_pct in items:
            w.writerow([item_name, category, qty, f"${revenue:,.2f}", cost_pct])


def _write_punches_csv(start: date, days: int, employees: list[str]):
    """Time clock punches with a few ghost shifts baked in."""
    path = OUTPUT_DIR / "timecard_export.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Employee Name", "Clock In", "Clock Out", "Position", "Total Hours"])

        ghost_emp = employees[7]  # Riley Clark

        for i in range(days):
            d = start + timedelta(days=i)
            weekday = d.weekday()

            staff_count = {0: 6, 1: 5, 2: 6, 3: 6, 4: 8, 5: 9, 6: 7}[weekday]
            working = random.sample(employees, min(staff_count, len(employees)))

            for emp in working:
                role = "Kitchen" if employees.index(emp) < 4 else "Floor"
                start_hour = random.choice([6, 7, 8, 10, 11, 14, 15, 16])
                hours = random.uniform(5, 9)
                end_hour = start_hour + hours

                clock_in = datetime(d.year, d.month, d.day, start_hour, random.randint(0, 15))
                end_h = int(end_hour)
                end_m = int((end_hour - end_h) * 60)
                if end_h >= 24:
                    end_h = 23
                    end_m = 45
                clock_out = datetime(d.year, d.month, d.day, end_h, end_m)

                actual_hours = (clock_out - clock_in).total_seconds() / 3600

                w.writerow([
                    emp,
                    clock_in.strftime("%m/%d/%Y %I:%M %p"),
                    clock_out.strftime("%m/%d/%Y %I:%M %p"),
                    role,
                    f"{actual_hours:.2f}",
                ])

            # Ghost shift: Riley clocks in 3x/month but is off the floor
            if random.random() < 0.10:
                clock_in = datetime(d.year, d.month, d.day, 16, random.randint(0, 30))
                clock_out = datetime(d.year, d.month, d.day, 22, random.randint(0, 30))
                hours = (clock_out - clock_in).total_seconds() / 3600

                w.writerow([
                    ghost_emp,
                    clock_in.strftime("%m/%d/%Y %I:%M %p"),
                    clock_out.strftime("%m/%d/%Y %I:%M %p"),
                    "Floor",
                    f"{hours:.2f}",
                ])


if __name__ == "__main__":
    main()
