import csv
import io
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.repositories.dashboard_repo import DashboardRepository

router = APIRouter(prefix="/api/v1/locations/{location_id}/dashboard", tags=["export"])


@router.get("/export")
async def export_dashboard(
    location_id: uuid.UUID,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    snapshot = await repo.get_latest(location_id)
    if not snapshot:
        raise NotFoundError("Dashboard snapshot", str(location_id))

    if format == "json":
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_at": snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else None,
            "status": snapshot.dashboard_status,
            "summary": snapshot.summary_json,
            "throughput": snapshot.throughput_json,
            "staffing": snapshot.staffing_json,
            "menu": snapshot.menu_json,
            "leakage": snapshot.leakage_json,
            "integrity": snapshot.integrity_json,
            "alerts": snapshot.alerts_json,
            "recommendations": snapshot.recommendations_json,
        }
        content = json.dumps(data, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=dashboard-{location_id}-{snapshot.snapshot_at.strftime('%Y%m%d-%H%M')}.json"},
        )

    # CSV format — flatten the summary metrics
    output = io.StringIO()
    writer = csv.writer(output)

    summary = snapshot.summary_json or {}
    throughput = snapshot.throughput_json or {}
    staffing = snapshot.staffing_json or {}
    leakage = snapshot.leakage_json or {}

    writer.writerow(["Metric", "Value"])
    writer.writerow(["Snapshot At", snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else ""])
    writer.writerow(["Dashboard Status", snapshot.dashboard_status])
    writer.writerow(["Revenue Today", summary.get("revenue_today", "")])
    writer.writerow(["Projected EOD Revenue", summary.get("projected_eod_revenue", "")])
    writer.writerow(["Active Staff", summary.get("active_staff", "")])
    writer.writerow(["Staffing Pressure", summary.get("staffing_pressure", "")])
    writer.writerow(["Estimated Loss", summary.get("estimated_loss", "")])
    writer.writerow(["Orders Per Hour", throughput.get("orders_per_hour", "")])
    writer.writerow(["Avg Ticket", throughput.get("avg_ticket", "")])
    writer.writerow(["Avg Prep Time (s)", throughput.get("avg_prep_time_seconds", "")])
    writer.writerow(["Backlog Risk", throughput.get("backlog_risk", "")])
    writer.writerow(["Sales Per Labor Hour", staffing.get("sales_per_labor_hour", "")])
    writer.writerow(["Labor Cost Ratio", staffing.get("labor_cost_ratio", "")])
    writer.writerow(["Labor Cost Estimate", staffing.get("labor_cost_estimate", "")])
    writer.writerow(["Refund Rate", leakage.get("refund_rate", "")])
    writer.writerow(["Refund Total", leakage.get("refund_total", "")])
    writer.writerow(["Comp Total", leakage.get("comp_total", "")])
    writer.writerow(["Void Total", leakage.get("void_total", "")])
    writer.writerow(["Spike Detected", leakage.get("spike_detected", "")])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dashboard-{location_id}-{snapshot.snapshot_at.strftime('%Y%m%d-%H%M')}.csv"},
    )
