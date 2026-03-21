"""Alert service — generates alerts from derivations, handles dedup and TTL."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.alert import Alert
from app.repositories.alert_repo import AlertRepository
from app.rules.staffing_rules import StaffingResult
from app.rules.labor_rules import LaborResult
from app.rules.leakage_rules import LeakageResult
from app.rules.rush_rules import RushResult


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_repo = AlertRepository(db)

    async def generate_alerts(
        self,
        location_id: uuid.UUID,
        derivations: dict,
        now: datetime,
    ) -> list[Alert]:
        """Evaluate derivations and create alerts. Deduplicates against active alerts."""
        new_alerts: list[Alert] = []

        # Expire TTL alerts first
        await self.alert_repo.expire_ttl_alerts(now)

        # Staffing alerts
        staffing: StaffingResult = derivations.get("staffing")
        if staffing and staffing.staffing_pressure in ("critical_understaffed", "understaffed"):
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="understaffed",
                severity="critical" if staffing.staffing_pressure == "critical_understaffed" else "warning",
                title=f"Understaffed — {staffing.orders_per_labor_hour} orders/labor hour",
                message=staffing.recommendation,
                evidence={"orders_per_labor_hour": staffing.orders_per_labor_hour, "active_staff": staffing.active_staff},
                triggered_at=now,
                ttl_minutes=60,
            )
            if alert:
                new_alerts.append(alert)

        if staffing and staffing.staffing_pressure in ("critical_overstaffed", "overstaffed"):
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="overstaffed",
                severity="critical" if staffing.staffing_pressure == "critical_overstaffed" else "warning",
                title=f"Overstaffed — {staffing.orders_per_labor_hour} orders/labor hour",
                message=staffing.recommendation,
                evidence={"orders_per_labor_hour": staffing.orders_per_labor_hour, "active_staff": staffing.active_staff},
                triggered_at=now,
                ttl_minutes=60,
            )
            if alert:
                new_alerts.append(alert)

        # Labor alerts
        labor: LaborResult = derivations.get("labor")
        if labor and labor.severity in ("warning", "critical"):
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="labor_warning",
                severity=labor.severity,
                title=f"Labor cost at {labor.labor_cost_ratio:.0%} of revenue",
                message=labor.alert_message,
                evidence={"labor_cost_ratio": labor.labor_cost_ratio, "labor_cost_estimate": labor.labor_cost_estimate},
                triggered_at=now,
                ttl_minutes=120,
            )
            if alert:
                new_alerts.append(alert)

        # Leakage alerts
        leakage: LeakageResult = derivations.get("leakage")
        if leakage and leakage.spike_detected:
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="refund_spike",
                severity="critical" if leakage.severity == "critical" else "warning",
                title=f"Refund rate at {leakage.refund_rate:.1%}",
                message=leakage.alert_message,
                evidence={
                    "refund_rate": leakage.refund_rate,
                    "loss_estimate": leakage.loss_estimate,
                    "suspicious_employee": leakage.suspicious_employee.employee_name if leakage.suspicious_employee else None,
                },
                triggered_at=now,
                ttl_minutes=180,
            )
            if alert:
                new_alerts.append(alert)

        # Rush alerts
        rush: RushResult = derivations.get("rush")
        if rush and rush.severity in ("warning", "critical"):
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="rush_incoming",
                severity=rush.severity,
                title="Rush incoming" if rush.severity == "warning" else "Rush critical",
                message=rush.alert_message,
                evidence={"backlog_risk": rush.backlog_risk, "order_velocity": rush.order_velocity, "avg_prep_time": rush.avg_prep_time},
                triggered_at=now,
                ttl_minutes=30,
            )
            if alert:
                new_alerts.append(alert)

        if rush and rush.prep_time_trend == "rising" and rush.prep_time_change_pct > 0.20:
            alert = await self._maybe_create_alert(
                location_id=location_id,
                alert_type="prep_delay",
                severity="warning",
                title=f"Prep times rising {rush.prep_time_change_pct:.0%}",
                message=f"Average prep time: {rush.avg_prep_time:.0f}s",
                evidence={"avg_prep_time": rush.avg_prep_time, "change_pct": rush.prep_time_change_pct},
                triggered_at=now,
                ttl_minutes=30,
            )
            if alert:
                new_alerts.append(alert)

        # Integrity alerts
        integrity_flags = derivations.get("integrity", [])
        for flag in integrity_flags:
            if flag.severity in ("review", "high"):
                alert = await self._maybe_create_alert(
                    location_id=location_id,
                    alert_type="suspicious_punch",
                    severity="critical" if flag.severity == "high" else "warning",
                    title=flag.title,
                    message=flag.message,
                    evidence=flag.evidence,
                    triggered_at=now,
                    ttl_minutes=None,  # No auto-resolve for integrity
                )
                if alert:
                    new_alerts.append(alert)

        return new_alerts

    async def _maybe_create_alert(
        self,
        location_id: uuid.UUID,
        alert_type: str,
        severity: str,
        title: str,
        message: str | None,
        evidence: dict,
        triggered_at: datetime,
        ttl_minutes: int | None,
    ) -> Alert | None:
        """Create alert only if no active alert of this type exists."""
        existing = await self.alert_repo.get_active_by_type(location_id, alert_type)
        if existing:
            return None

        alert = Alert(
            location_id=location_id,
            alert_type=alert_type,
            severity=severity,
            status="active",
            title=title,
            message=message,
            evidence_json=evidence,
            triggered_at=triggered_at,
            ttl_minutes=ttl_minutes,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert
