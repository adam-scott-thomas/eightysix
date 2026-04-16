"""Roll up raw data into daily aggregates for forecasting."""
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.daily_aggregate import DailyAggregate
from app.db.models.employee import Employee
from app.db.models.menu_item import MenuItem
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.shift import Shift


DAYPART_BOUNDARIES = {
    "breakfast": (time(0, 0), time(11, 0)),
    "lunch": (time(11, 0), time(15, 0)),
    "dinner": (time(15, 0), time(21, 0)),
    "late": (time(21, 0), time(23, 59, 59)),
}

ROLE_MAP = {
    "kitchen": "kitchen",
    "cook": "kitchen",
    "chef": "kitchen",
    "floor": "foh",
    "server": "foh",
    "host": "foh",
    "bartender": "bar",
    "bar": "bar",
    "delivery": "delivery",
    "driver": "delivery",
    "manager": "manager",
    "gm": "manager",
}


class AggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_date(
        self, location_id: uuid.UUID, target_date: date
    ) -> DailyAggregate:
        """Compute and upsert a daily aggregate for one location + date."""
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        # Fetch raw data
        orders = await self._get_orders(location_id, day_start, day_end)
        shifts = await self._get_shifts(location_id, day_start, day_end)
        order_items = await self._get_order_items([o.id for o in orders])
        menu_items = await self._get_menu_items(location_id)
        employees = await self._get_employees(location_id)

        mi_map = {m.id: m for m in menu_items}
        emp_map = {e.id: e for e in employees}

        # Revenue
        gross_sales = sum(float(o.order_total) for o in orders)
        refund_total = sum(float(o.refund_amount or 0) for o in orders)
        comp_total = sum(float(o.comp_amount or 0) for o in orders)
        void_total = sum(float(o.void_amount or 0) for o in orders)
        net_sales = gross_sales - refund_total - comp_total - void_total
        order_count = len(orders)
        avg_ticket = gross_sales / order_count if order_count else 0

        # Channel breakdown
        channel_counts: dict[str, int] = defaultdict(int)
        for o in orders:
            channel_counts[o.channel or "dine_in"] += 1

        # Daypart breakdown
        dayparts: dict[str, dict] = {dp: {"sales": 0.0, "orders": 0} for dp in DAYPART_BOUNDARIES}
        for o in orders:
            if not o.ordered_at:
                continue
            t = o.ordered_at.time()
            for dp, (start, end) in DAYPART_BOUNDARIES.items():
                if start <= t < end:
                    dayparts[dp]["sales"] += float(o.order_total)
                    dayparts[dp]["orders"] += 1
                    break

        # Labor by role
        role_hours: dict[str, float] = defaultdict(float)
        total_labor_hours = 0.0
        total_labor_cost = 0.0
        for s in shifts:
            end = s.clock_out or day_end
            hours = (end - s.clock_in).total_seconds() / 3600
            total_labor_hours += hours

            emp = emp_map.get(s.employee_id)
            rate = float(emp.hourly_rate or 15) if emp else 15
            total_labor_cost += hours * rate

            raw_role = (s.role_during_shift or "").lower()
            mapped = ROLE_MAP.get(raw_role, "foh")
            role_hours[mapped] += hours

        lcr = total_labor_cost / net_sales if net_sales > 0 else None

        # Top SKUs
        sku_sales: dict[str, dict] = defaultdict(lambda: {"units": 0, "revenue": 0.0, "category": ""})
        for oi in order_items:
            mi = mi_map.get(oi.menu_item_id)
            if not mi:
                continue
            key = mi.item_name
            sku_sales[key]["units"] += oi.quantity
            sku_sales[key]["revenue"] += float(oi.line_total)
            sku_sales[key]["category"] = mi.category or ""

        top_skus = sorted(sku_sales.items(), key=lambda x: x[1]["units"], reverse=True)[:50]
        top_skus_json = [
            {"item_name": name, "units_sold": d["units"], "revenue": round(d["revenue"], 2), "category": d["category"]}
            for name, d in top_skus
        ]

        # Category breakdown
        cat_totals: dict[str, dict] = defaultdict(lambda: {"units": 0, "revenue": 0.0})
        for name, d in sku_sales.items():
            cat = d["category"] or "uncategorized"
            cat_totals[cat]["units"] += d["units"]
            cat_totals[cat]["revenue"] += d["revenue"]

        # Upsert
        existing = await self._get_existing(location_id, target_date)
        if existing:
            agg = existing
        else:
            agg = DailyAggregate(location_id=location_id, agg_date=target_date)
            self.db.add(agg)

        agg.day_of_week = target_date.weekday()
        agg.net_sales = round(net_sales, 2)
        agg.gross_sales = round(gross_sales, 2)
        agg.refund_total = round(refund_total, 2)
        agg.comp_total = round(comp_total, 2)
        agg.void_total = round(void_total, 2)
        agg.avg_ticket = round(avg_ticket, 2)
        agg.order_count = order_count
        agg.orders_dine_in = channel_counts.get("dine_in", 0)
        agg.orders_takeout = channel_counts.get("takeout", 0)
        agg.orders_delivery = channel_counts.get("delivery", 0)
        agg.orders_drive_through = channel_counts.get("drive_through", 0)
        agg.total_labor_hours = round(total_labor_hours, 2)
        agg.total_labor_cost = round(total_labor_cost, 2)
        agg.labor_hours_kitchen = round(role_hours.get("kitchen", 0), 2)
        agg.labor_hours_foh = round(role_hours.get("foh", 0), 2)
        agg.labor_hours_bar = round(role_hours.get("bar", 0), 2)
        agg.labor_hours_delivery = round(role_hours.get("delivery", 0), 2)
        agg.labor_hours_manager = round(role_hours.get("manager", 0), 2)
        agg.labor_cost_ratio = round(lcr, 4) if lcr is not None else None
        agg.daypart_json = dayparts
        agg.top_skus_json = top_skus_json
        agg.category_json = dict(cat_totals)

        await self.db.flush()
        return agg

    async def backfill(self, location_id: uuid.UUID, start: date, end: date) -> int:
        """Aggregate all dates in [start, end]. Returns count of days processed."""
        count = 0
        current = start
        while current <= end:
            await self.aggregate_date(location_id, current)
            count += 1
            current += timedelta(days=1)
        return count

    async def _get_orders(self, location_id, start, end):
        stmt = select(Order).where(
            Order.location_id == location_id,
            Order.ordered_at >= start,
            Order.ordered_at <= end,
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_shifts(self, location_id, start, end):
        stmt = select(Shift).where(
            Shift.location_id == location_id,
            Shift.clock_in >= start,
            Shift.clock_in <= end,
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_order_items(self, order_ids):
        if not order_ids:
            return []
        stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_menu_items(self, location_id):
        stmt = select(MenuItem).where(MenuItem.location_id == location_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_employees(self, location_id):
        stmt = select(Employee).where(Employee.location_id == location_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_existing(self, location_id, target_date):
        stmt = select(DailyAggregate).where(
            DailyAggregate.location_id == location_id,
            DailyAggregate.agg_date == target_date,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
