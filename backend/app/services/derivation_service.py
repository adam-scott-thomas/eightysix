"""Derivation service — pure computation. Takes raw data, returns derived metrics."""
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.employee import Employee
from app.db.models.menu_item import MenuItem
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.shift import Shift
from app.db.models.location import Location
from app.db.models.observation import Observation
from app.rules.staffing_rules import evaluate_staffing, StaffingResult
from app.rules.labor_rules import evaluate_labor, LaborResult
from app.rules.leakage_rules import evaluate_leakage, LeakageResult
from app.rules.menu_rules import evaluate_menu, MenuResult
from app.rules.rush_rules import evaluate_rush, RushResult
from app.rules.integrity_rules import evaluate_punch_integrity, evaluate_ghost_shift, IntegrityCheckResult
from app.rules.thresholds import merge_thresholds


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to UTC-aware. Handles tz-naive values from SQLite."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class DerivationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_all(
        self,
        location_id: uuid.UUID,
        now: datetime,
        day_start: datetime,
        day_end: datetime,
    ) -> dict:
        """Run all derivations and return a dict of results."""
        location = await self.db.get(Location, location_id)
        if not location:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Location", str(location_id))

        default_rate = float(location.default_hourly_rate or 15.00)
        thresholds = merge_thresholds(location.thresholds_json)

        # Fetch raw data
        orders = await self._get_orders(location_id, day_start, day_end)
        shifts = await self._get_shifts(location_id, day_start, day_end)
        employees = await self._get_employees(location_id)
        menu_items = await self._get_menu_items(location_id)
        order_items = await self._get_order_items([o.id for o in orders])

        # Basic revenue metrics
        revenue_today = sum(float(o.order_total) for o in orders)
        order_count = len(orders)
        avg_ticket = revenue_today / order_count if order_count > 0 else 0

        # Projected EOD revenue
        bh = location.business_hours_json or {}
        day_name = now.strftime("%a").lower()
        day_hours = bh.get(day_name, {"open": "06:00", "close": "23:00"})
        open_hour = int(day_hours["open"].split(":")[0])
        close_hour = int(day_hours["close"].split(":")[0])
        total_biz_hours = close_hour - open_hour if close_hour > open_hour else 17
        # Hours elapsed since open (rough — in UTC terms from day_start)
        elapsed = (now - day_start).total_seconds() / 3600
        elapsed = max(elapsed, 0.5)
        remaining = max(total_biz_hours - elapsed, 0)
        if elapsed > 0:
            projected_eod = revenue_today * (total_biz_hours / elapsed)
        else:
            projected_eod = revenue_today
        projected_eod = max(projected_eod, revenue_today)

        # Orders in last 60 min
        one_hour_ago = now - timedelta(hours=1)
        orders_last_hour = [o for o in orders if _ensure_utc(o.ordered_at) >= one_hour_ago]
        orders_per_hour = len(orders_last_hour)

        # Active shifts
        active_shifts = [s for s in shifts if s.clock_out is None]
        active_staff_count = len(active_shifts)

        # Labor calculations
        total_labor_hours = 0.0
        total_labor_cost = 0.0
        emp_map = {e.id: e for e in employees}
        for s in shifts:
            end_time = _ensure_utc(s.clock_out) or now
            hours = (end_time - _ensure_utc(s.clock_in)).total_seconds() / 3600
            total_labor_hours += hours
            rate = float(emp_map[s.employee_id].hourly_rate or default_rate) if s.employee_id in emp_map else default_rate
            total_labor_cost += hours * rate

        splh = revenue_today / total_labor_hours if total_labor_hours > 0 else 0
        lcr = total_labor_cost / revenue_today if revenue_today > 0 else 0

        # Staffing (2-hour rolling window)
        two_hours_ago = now - timedelta(hours=2)
        orders_in_2h = [o for o in orders if _ensure_utc(o.ordered_at) >= two_hours_ago]
        staffing_result = evaluate_staffing(
            orders_in_window=len(orders_in_2h),
            active_staff=active_staff_count,
            window_hours=2.0,
            thresholds=thresholds.staffing,
        )

        # Labor
        labor_result = evaluate_labor(
            total_labor_hours=total_labor_hours,
            total_labor_cost=total_labor_cost,
            revenue_today=revenue_today,
            thresholds=thresholds.labor,
        )

        # Leakage
        refund_total = sum(float(o.refund_amount or 0) for o in orders)
        comp_total = sum(float(o.comp_amount or 0) for o in orders)
        void_total = sum(float(o.void_amount or 0) for o in orders)

        # Employee refund concentration
        emp_refunds: dict[str, dict] = {}
        for o in orders:
            ref_amt = float(o.refund_amount or 0) + float(o.comp_amount or 0) + float(o.void_amount or 0)
            if ref_amt > 0 and o.employee_id:
                eid = str(o.employee_id)
                if eid not in emp_refunds:
                    emp = emp_map.get(o.employee_id)
                    name = f"{emp.first_name} {emp.last_name}" if emp else "Unknown"
                    emp_refunds[eid] = {"name": name, "amount": 0}
                emp_refunds[eid]["amount"] += ref_amt

        leakage_result = evaluate_leakage(
            gross_revenue=revenue_today,
            refund_total=refund_total,
            comp_total=comp_total,
            void_total=void_total,
            employee_refunds=emp_refunds if emp_refunds else None,
            thresholds=thresholds.leakage,
        )

        # Menu performance
        item_sales_map: dict[uuid.UUID, dict] = {}
        mi_map = {m.id: m for m in menu_items}
        for oi in order_items:
            mid = oi.menu_item_id
            if mid not in item_sales_map:
                mi = mi_map.get(mid)
                if not mi:
                    continue
                item_sales_map[mid] = {
                    "menu_item_id": str(mid),
                    "item_name": mi.item_name,
                    "units_sold": 0,
                    "revenue": 0,
                    "price": float(mi.price),
                    "estimated_food_cost": float(mi.estimated_food_cost) if mi.estimated_food_cost else None,
                    "margin_band": mi.margin_band,
                }
            item_sales_map[mid]["units_sold"] += oi.quantity
            item_sales_map[mid]["revenue"] += float(oi.line_total)

        menu_result = evaluate_menu(list(item_sales_map.values()), revenue_today)

        # Rush detection (30min windows)
        thirty_min_ago = now - timedelta(minutes=30)
        sixty_min_ago = now - timedelta(minutes=60)
        orders_current_window = [o for o in orders if _ensure_utc(o.ordered_at) >= thirty_min_ago]
        orders_prior_window = [o for o in orders if sixty_min_ago <= _ensure_utc(o.ordered_at) < thirty_min_ago]

        prep_times_current = [o.prep_time_seconds for o in orders_current_window if o.prep_time_seconds]
        prep_times_prior = [o.prep_time_seconds for o in orders_prior_window if o.prep_time_seconds]

        avg_prep_current = sum(prep_times_current) / len(prep_times_current) if prep_times_current else 300
        avg_prep_prior = sum(prep_times_prior) / len(prep_times_prior) if prep_times_prior else None

        kitchen_staff = len([s for s in active_shifts if (s.role_during_shift or "").lower() in ("kitchen", "")])
        kitchen_staff = max(kitchen_staff, 1)  # avoid div by zero

        top_seller_name = menu_result.top_sellers[0].item_name if menu_result.top_sellers else None

        rush_result = evaluate_rush(
            orders_in_window=len(orders_current_window),
            window_minutes=30,
            avg_prep_time_seconds=avg_prep_current,
            prior_avg_prep_time_seconds=avg_prep_prior,
            active_kitchen_staff=kitchen_staff,
            top_seller_name=top_seller_name,
            thresholds=thresholds.rush,
        )

        # Integrity checks
        # Get known device fingerprints (last 30 days — for stub, just use all from today)
        known_fps = set()
        for s in shifts:
            if s.device_fingerprint and s.geofence_match is True:
                known_fps.add(s.device_fingerprint)

        # Check manager staff count observation
        manager_count = await self._get_manager_staff_count(location_id, day_start, day_end)

        integrity_results: list[IntegrityCheckResult] = []
        for s in shifts:
            emp = emp_map.get(s.employee_id)
            if not emp:
                continue
            name = f"{emp.first_name} {emp.last_name}"

            # Punch integrity
            if s.geofence_match is not None or s.device_fingerprint is not None:
                result = evaluate_punch_integrity(
                    shift_id=str(s.id),
                    employee_id=str(s.employee_id),
                    employee_name=name,
                    geofence_match=s.geofence_match,
                    device_fingerprint=s.device_fingerprint,
                    known_device_fingerprints=list(known_fps),
                    ip_address=s.ip_address,
                    geo_lat=float(s.geo_lat) if s.geo_lat else None,
                    geo_lng=float(s.geo_lng) if s.geo_lng else None,
                    active_shift_count=active_staff_count,
                    manager_reported_count=manager_count,
                    thresholds=thresholds.integrity,
                )
                if result.severity != "none":
                    integrity_results.append(result)

            # Ghost shift check
            emp_orders = [o for o in orders if o.employee_id == s.employee_id]
            end_time = _ensure_utc(s.clock_out) or now
            shift_hours = (end_time - _ensure_utc(s.clock_in)).total_seconds() / 3600
            ghost = evaluate_ghost_shift(
                shift_id=str(s.id),
                employee_id=str(s.employee_id),
                employee_name=name,
                orders_by_employee=len(emp_orders),
                shift_hours=shift_hours,
                has_manager_confirmation=manager_count is not None,
            )
            if ghost:
                integrity_results.append(ghost)

        return {
            "revenue_today": round(revenue_today, 2),
            "projected_eod_revenue": round(projected_eod, 2),
            "avg_ticket": round(avg_ticket, 2),
            "orders_per_hour": orders_per_hour,
            "active_staff_count": active_staff_count,
            "total_labor_hours": round(total_labor_hours, 2),
            "sales_per_labor_hour": round(splh, 2),
            "labor_cost_estimate": round(total_labor_cost, 2),
            "labor_cost_ratio": round(lcr, 4),
            "staffing": staffing_result,
            "labor": labor_result,
            "leakage": leakage_result,
            "menu": menu_result,
            "rush": rush_result,
            "integrity": integrity_results,
            "avg_prep_time": round(avg_prep_current, 1),
            "backlog_risk": rush_result.backlog_risk,
        }

    # -- Data fetch helpers --

    async def _get_orders(self, location_id: uuid.UUID, start: datetime, end: datetime) -> list:
        stmt = select(Order).where(
            Order.location_id == location_id,
            Order.ordered_at >= start,
            Order.ordered_at <= end,
        ).order_by(Order.ordered_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_shifts(self, location_id: uuid.UUID, start: datetime, end: datetime) -> list:
        stmt = select(Shift).where(
            Shift.location_id == location_id,
            Shift.clock_in >= start,
            Shift.clock_in <= end,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_employees(self, location_id: uuid.UUID) -> list:
        stmt = select(Employee).where(
            Employee.location_id == location_id,
            Employee.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_menu_items(self, location_id: uuid.UUID) -> list:
        stmt = select(MenuItem).where(
            MenuItem.location_id == location_id,
            MenuItem.is_active == True,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_order_items(self, order_ids: list[uuid.UUID]) -> list:
        if not order_ids:
            return []
        stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_manager_staff_count(
        self, location_id: uuid.UUID, start: datetime, end: datetime
    ) -> int | None:
        stmt = (
            select(Observation)
            .where(
                Observation.location_id == location_id,
                Observation.metric_key == "manager_staff_count",
                Observation.observed_at >= start,
                Observation.observed_at <= end,
            )
            .order_by(Observation.observed_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        obs = result.scalar_one_or_none()
        if obs and obs.value_number is not None:
            return int(obs.value_number)
        return None
