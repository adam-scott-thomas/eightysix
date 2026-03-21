import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.repositories.dashboard_repo import DashboardRepository
from app.services.date_utils import detect_data_date_range
from app.services.readiness_service import ReadinessService
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1/locations/{location_id}/dashboard", tags=["dashboard"])


@router.get("/readiness")
async def get_readiness(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _, day_start, day_end = await detect_data_date_range(db, location_id)
    service = ReadinessService(db)
    return await service.check_readiness(location_id, day_start, day_end)


@router.get("/current")
async def get_current_dashboard(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    snapshot = await repo.get_latest(location_id)
    if not snapshot:
        raise NotFoundError("Dashboard snapshot", str(location_id))

    return {
        "snapshot_at": snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else None,
        "status": snapshot.dashboard_status,
        "readiness": {
            "score": float(snapshot.readiness_score),
            "completeness": float(snapshot.completeness_score),
            "missing": [],
        },
        "summary": snapshot.summary_json,
        "throughput": snapshot.throughput_json,
        "staffing": snapshot.staffing_json,
        "menu": snapshot.menu_json,
        "leakage": snapshot.leakage_json,
        "integrity": snapshot.integrity_json,
        "alerts": snapshot.alerts_json,
        "recommendations": snapshot.recommendations_json,
    }


@router.get("/timeline")
async def get_timeline(
    location_id: uuid.UUID,
    hours: int = Query(default=12, ge=1, le=72),
    db: AsyncSession = Depends(get_db),
):
    now, _, _ = await detect_data_date_range(db, location_id)
    start = now - timedelta(hours=hours)

    repo = DashboardRepository(db)
    snapshots = await repo.get_timeline(location_id, start, now)

    return [
        {
            "snapshot_at": s.snapshot_at.isoformat() if s.snapshot_at else None,
            "status": s.dashboard_status,
            "summary": s.summary_json,
            "throughput": s.throughput_json,
        }
        for s in snapshots
    ]


@router.post("/recompute")
async def recompute_dashboard(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    now, day_start, day_end = await detect_data_date_range(db, location_id)
    service = SnapshotService(db)
    return await service.recompute(location_id, now, day_start, day_end)


@router.get("/stream")
async def stream_dashboard(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint that polls for dashboard changes every 10 seconds."""
    async def event_generator():
        last_snapshot_at = None
        while True:
            try:
                repo = DashboardRepository(db)
                snapshot = await repo.get_latest(location_id)
                current_at = snapshot.snapshot_at.isoformat() if snapshot else None

                if current_at != last_snapshot_at and snapshot:
                    data = json.dumps({
                        "snapshot_at": current_at,
                        "status": snapshot.dashboard_status,
                        "summary": snapshot.summary_json,
                    })
                    yield f"data: {data}\n\n"
                    last_snapshot_at = current_at
                else:
                    yield f": keepalive\n\n"
            except Exception:
                yield f": error\n\n"

            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
