from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_admin
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.demo import router as demo_router
from app.api.v1.locations import router as locations_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.integrity import router as integrity_router
from app.api.v1.observations import router as observations_router
from app.api.v1.events import router as events_router
from app.api.v1.menu import router as menu_router
from app.api.v1.orders import router as orders_router
from app.api.v1.shifts import router as shifts_router
from app.api.v1.employees import router as employees_router
from app.api.v1.export import router as export_router

api_router = APIRouter()

# Public — no auth required
api_router.include_router(health_router)
api_router.include_router(auth_router)

# Protected — require valid JWT
_authed = [Depends(get_current_user)]
api_router.include_router(locations_router, dependencies=_authed)
api_router.include_router(employees_router, dependencies=_authed)
api_router.include_router(dashboard_router, dependencies=_authed)
api_router.include_router(alerts_router, dependencies=_authed)
api_router.include_router(recommendations_router, dependencies=_authed)
api_router.include_router(integrity_router, dependencies=_authed)
api_router.include_router(observations_router, dependencies=_authed)
api_router.include_router(events_router, dependencies=_authed)
api_router.include_router(menu_router, dependencies=_authed)
api_router.include_router(orders_router, dependencies=_authed)
api_router.include_router(shifts_router, dependencies=_authed)
api_router.include_router(export_router, dependencies=_authed)

# Demo — any authenticated user (DEMO_MODE gate is on the router itself)
api_router.include_router(demo_router, dependencies=_authed)
