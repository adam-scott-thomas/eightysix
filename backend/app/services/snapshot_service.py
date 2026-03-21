"""Snapshot service — assembles full dashboard payload and persists it."""
import uuid
from dataclasses import asdict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.dashboard_snapshot import DashboardSnapshot
from app.repositories.alert_repo import AlertRepository
from app.repositories.dashboard_repo import DashboardRepository
from app.repositories.integrity_repo import IntegrityFlagRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.services.alert_service import AlertService
from app.services.derivation_service import DerivationService
from app.services.integrity_service import IntegrityService
from app.services.readiness_service import ReadinessService
from app.services.recommendation_service import RecommendationService


class SnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.derivation_service = DerivationService(db)
        self.readiness_service = ReadinessService(db)
        self.alert_service = AlertService(db)
        self.recommendation_service = RecommendationService(db)
        self.integrity_service = IntegrityService(db)
        self.alert_repo = AlertRepository(db)
        self.flag_repo = IntegrityFlagRepository(db)
        self.rec_repo = RecommendationRepository(db)
        self.dashboard_repo = DashboardRepository(db)

    async def recompute(
        self,
        location_id: uuid.UUID,
        now: datetime,
        day_start: datetime,
        day_end: datetime,
    ) -> dict:
        """Run full pipeline: derivation → alerts → recommendations → integrity → snapshot."""

        # 1. Readiness check
        readiness = await self.readiness_service.check_readiness(location_id, day_start, day_end)

        # 2. Derivations
        derivations = await self.derivation_service.compute_all(location_id, now, day_start, day_end)
        if not derivations:
            return {"error": "No data to compute"}

        # 3. Integrity flags
        integrity_results = derivations.get("integrity", [])
        flags = await self.integrity_service.create_flags(location_id, integrity_results)

        # 4. Alerts
        new_alerts = await self.alert_service.generate_alerts(location_id, derivations, now)

        # 5. Recommendations
        recs = await self.recommendation_service.generate_recommendations(
            location_id, derivations, new_alerts, now
        )

        # 6. Gather all active alerts, flags, recs for snapshot
        all_active_alerts = await self.alert_repo.get_active_by_location(location_id)
        all_open_flags = await self.flag_repo.get_open_by_location(location_id)
        all_pending_recs = await self.rec_repo.get_pending_by_location(location_id)

        # 7. Determine dashboard status
        severities = [a.severity for a in all_active_alerts]
        if "critical" in severities:
            dashboard_status = "red"
        elif "warning" in severities:
            dashboard_status = "yellow"
        else:
            dashboard_status = "green"

        # 8. Build payload
        staffing = derivations.get("staffing")
        labor = derivations.get("labor")
        leakage = derivations.get("leakage")
        menu = derivations.get("menu")
        rush = derivations.get("rush")

        summary_json = {
            "revenue_today": derivations["revenue_today"],
            "projected_eod_revenue": derivations["projected_eod_revenue"],
            "active_staff": derivations["active_staff_count"],
            "staffing_pressure": staffing.staffing_pressure if staffing else "unknown",
            "estimated_loss": leakage.loss_estimate if leakage else 0,
        }

        throughput_json = {
            "orders_per_hour": derivations["orders_per_hour"],
            "avg_ticket": derivations["avg_ticket"],
            "avg_prep_time_seconds": derivations["avg_prep_time"],
            "backlog_risk": derivations["backlog_risk"],
        }

        staffing_json = {
            "active_shifts": derivations["active_staff_count"],
            "staffing_pressure": staffing.staffing_pressure if staffing else "unknown",
            "sales_per_labor_hour": derivations["sales_per_labor_hour"],
            "labor_cost_ratio": derivations["labor_cost_ratio"],
            "labor_cost_estimate": derivations["labor_cost_estimate"],
            "discrepancy_warning": None,
        }

        menu_json = {
            "top_sellers": [
                {"item_name": s.item_name, "units_sold": s.units_sold, "revenue": s.revenue, "margin_band": s.margin_band}
                for s in (menu.top_sellers if menu else [])
            ],
            "bottom_sellers": [
                {"item_name": s.item_name, "units_sold": s.units_sold, "revenue": s.revenue, "margin_band": s.margin_band}
                for s in (menu.bottom_sellers if menu else [])
            ],
            "workhorse_items": [
                {"item_name": s.item_name, "units_sold": s.units_sold, "revenue": s.revenue, "margin_band": s.margin_band}
                for s in (menu.workhorse_items if menu else [])
            ],
            "attach_rate_suggestions": [
                {"anchor_item": s.anchor_item, "suggested_item": s.suggested_item, "message": s.message}
                for s in (menu.attach_rate_suggestions if menu else [])
            ],
        }

        leakage_json = {
            "refund_total": leakage.refund_total if leakage else 0,
            "comp_total": leakage.comp_total if leakage else 0,
            "void_total": leakage.void_total if leakage else 0,
            "refund_rate": leakage.refund_rate if leakage else 0,
            "spike_detected": leakage.spike_detected if leakage else False,
            "suspicious_employee": leakage.suspicious_employee.employee_name if leakage and leakage.suspicious_employee else None,
        }

        integrity_json = {
            "flags_open": len(all_open_flags),
            "highest_risk_score": max((float(f.fraud_risk_score or 0) for f in all_open_flags), default=0),
            "flags": [
                {
                    "id": str(f.id),
                    "flag_type": f.flag_type,
                    "severity": f.severity,
                    "confidence": float(f.confidence),
                    "title": f.title,
                    "fraud_risk_score": float(f.fraud_risk_score) if f.fraud_risk_score else None,
                }
                for f in all_open_flags
            ],
        }

        alerts_json = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status,
                "title": a.title,
                "message": a.message,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            }
            for a in all_active_alerts
        ]

        recommendations_json = [
            {
                "id": str(r.id),
                "category": r.category,
                "title": r.title,
                "reason": r.reason,
                "action_description": r.action_description,
                "confidence": float(r.confidence),
                "estimated_impact": r.estimated_impact_json,
            }
            for r in all_pending_recs
        ]

        # 9. Persist snapshot
        snapshot = DashboardSnapshot(
            location_id=location_id,
            snapshot_at=now,
            dashboard_status=dashboard_status,
            readiness_score=readiness["completeness_score"],
            completeness_score=readiness["completeness_score"],
            summary_json=summary_json,
            throughput_json=throughput_json,
            staffing_json=staffing_json,
            menu_json=menu_json,
            leakage_json=leakage_json,
            integrity_json=integrity_json,
            alerts_json=alerts_json,
            recommendations_json=recommendations_json,
        )
        self.db.add(snapshot)
        await self.db.flush()

        # 10. Return dashboard payload
        return {
            "snapshot_at": now.isoformat(),
            "status": dashboard_status,
            "readiness": {
                "score": readiness["completeness_score"],
                "completeness": readiness["completeness_score"],
                "missing": readiness["missing_domains"],
            },
            "summary": summary_json,
            "throughput": throughput_json,
            "staffing": staffing_json,
            "menu": menu_json,
            "leakage": leakage_json,
            "integrity": integrity_json,
            "alerts": alerts_json,
            "recommendations": recommendations_json,
        }
