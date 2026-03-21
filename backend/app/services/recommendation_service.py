"""Recommendation service — generates actionable recommendations from alerts and derivations."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.alert import Alert
from app.db.models.recommendation import Recommendation
from app.repositories.recommendation_repo import RecommendationRepository
from app.rules.staffing_rules import StaffingResult
from app.rules.labor_rules import LaborResult
from app.rules.leakage_rules import LeakageResult
from app.rules.menu_rules import MenuResult
from app.rules.rush_rules import RushResult


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rec_repo = RecommendationRepository(db)

    async def generate_recommendations(
        self,
        location_id: uuid.UUID,
        derivations: dict,
        alerts: list[Alert],
        now: datetime,
    ) -> list[Recommendation]:
        """Generate recommendations from derivations and new alerts."""
        # Expire stale recommendations first
        await self.rec_repo.expire_stale(now)

        recs: list[Recommendation] = []
        alert_map = {a.alert_type: a for a in alerts}

        # Staffing recommendations
        staffing: StaffingResult = derivations.get("staffing")
        if staffing and staffing.recommendation:
            alert = alert_map.get("understaffed") or alert_map.get("overstaffed")
            rec = Recommendation(
                location_id=location_id,
                alert_id=alert.id if alert else None,
                category="staffing",
                title=staffing.recommendation,
                reason=f"Orders per labor hour at {staffing.orders_per_labor_hour}, pressure: {staffing.staffing_pressure}",
                action_description=staffing.recommendation,
                confidence=staffing.confidence,
                estimated_impact_json={
                    "metric": "orders_per_labor_hour",
                    "current": staffing.orders_per_labor_hour,
                    "projected": 7.0,  # target balanced
                },
                expires_at=now + timedelta(hours=2),
            )
            self.db.add(rec)
            recs.append(rec)

        # Labor cost recommendations
        labor: LaborResult = derivations.get("labor")
        if labor and labor.severity in ("warning", "critical"):
            alert = alert_map.get("labor_warning")
            savings = labor.labor_cost_estimate * 0.15 if labor.severity == "critical" else labor.labor_cost_estimate * 0.08
            rec = Recommendation(
                location_id=location_id,
                alert_id=alert.id if alert else None,
                category="cost",
                title="Reduce labor cost ratio",
                reason=labor.alert_message or f"Labor cost ratio at {labor.labor_cost_ratio:.0%}",
                action_description="Consider sending home staff with lowest seniority or shortest remaining shift",
                confidence=0.7,
                estimated_impact_json={
                    "metric": "labor_cost_ratio",
                    "current": labor.labor_cost_ratio,
                    "projected": labor.labor_cost_ratio * 0.85,
                    "savings_dollars": round(savings, 2),
                },
                expires_at=now + timedelta(hours=3),
            )
            self.db.add(rec)
            recs.append(rec)

        # Leakage recommendations
        leakage: LeakageResult = derivations.get("leakage")
        if leakage and leakage.spike_detected:
            alert = alert_map.get("refund_spike")
            if leakage.suspicious_employee:
                title = f"Review refund activity for {leakage.suspicious_employee.employee_name}"
                action = f"Pull refund logs for {leakage.suspicious_employee.employee_name} — responsible for {leakage.suspicious_employee.share:.0%} of losses"
            else:
                title = "Investigate elevated refund rate"
                action = "Review refund logs for patterns — check timing, amounts, and employee distribution"
            rec = Recommendation(
                location_id=location_id,
                alert_id=alert.id if alert else None,
                category="integrity",
                title=title,
                reason=f"Refund rate at {leakage.refund_rate:.1%}, loss estimate ${leakage.loss_estimate:.2f}",
                action_description=action,
                confidence=0.8 if leakage.suspicious_employee else 0.6,
                estimated_impact_json={
                    "metric": "refund_rate",
                    "current": leakage.refund_rate,
                    "loss_today": leakage.loss_estimate,
                },
                expires_at=now + timedelta(hours=8),
            )
            self.db.add(rec)
            recs.append(rec)

        # Menu recommendations
        menu: MenuResult = derivations.get("menu")
        if menu:
            for wh in menu.workhorse_items[:2]:
                rec = Recommendation(
                    location_id=location_id,
                    category="menu",
                    title=f"Review pricing for {wh.item_name}",
                    reason=f"{wh.item_name} is high volume ({wh.units_sold} units) but {wh.margin_band} margin — eating into profitability",
                    action_description=f"Consider price increase or portion adjustment for {wh.item_name}",
                    confidence=0.5,
                    estimated_impact_json={
                        "metric": "margin_band",
                        "item": wh.item_name,
                        "units_sold": wh.units_sold,
                        "revenue": wh.revenue,
                    },
                    expires_at=now + timedelta(days=7),
                )
                self.db.add(rec)
                recs.append(rec)

            for dog in menu.dog_items[:2]:
                rec = Recommendation(
                    location_id=location_id,
                    category="menu",
                    title=f"Consider removing {dog.item_name}",
                    reason=f"{dog.item_name} has low volume ({dog.units_sold} units) and {dog.margin_band} margin",
                    action_description=f"Evaluate removing {dog.item_name} from menu to simplify operations",
                    confidence=0.4,
                    estimated_impact_json={
                        "metric": "menu_simplification",
                        "item": dog.item_name,
                        "units_sold": dog.units_sold,
                    },
                    expires_at=now + timedelta(days=7),
                )
                self.db.add(rec)
                recs.append(rec)

        # Rush recommendations
        rush: RushResult = derivations.get("rush")
        if rush and rush.recommendation:
            alert = alert_map.get("rush_incoming")
            rec = Recommendation(
                location_id=location_id,
                alert_id=alert.id if alert else None,
                category="prep",
                title=rush.recommendation,
                reason=f"Backlog risk at {rush.backlog_risk:.2f}, order velocity {rush.order_velocity}/hr",
                action_description=rush.recommendation,
                confidence=0.75,
                estimated_impact_json={
                    "metric": "backlog_risk",
                    "current": rush.backlog_risk,
                    "projected": rush.backlog_risk * 0.6,
                },
                expires_at=now + timedelta(hours=1),
            )
            self.db.add(rec)
            recs.append(rec)

        # Integrity recommendations
        integrity_flags = derivations.get("integrity", [])
        for flag in integrity_flags:
            if flag.severity in ("review", "high"):
                rec = Recommendation(
                    location_id=location_id,
                    category="integrity",
                    title=f"Review suspicious punch: {flag.employee_name}",
                    reason=flag.message or flag.title,
                    action_description="Verify employee presence on-site. Check camera footage if available.",
                    confidence=flag.fraud_risk_score,
                    estimated_impact_json={
                        "metric": "fraud_risk_score",
                        "score": flag.fraud_risk_score,
                        "flag_type": flag.flag_type,
                    },
                    expires_at=now + timedelta(hours=8),
                )
                self.db.add(rec)
                recs.append(rec)

        await self.db.flush()
        return recs
