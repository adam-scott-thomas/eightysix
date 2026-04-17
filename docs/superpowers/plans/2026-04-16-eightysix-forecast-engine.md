# EightySix Forecast Engine + Self-Service Demo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform EightySix from a real-time ops dashboard into a forecasting platform that a prospective customer can explore without hand-holding — then sell it.

**Architecture:** 8 phases. Phase 1 makes the demo self-service. Phase 2 hardens production. Phases 3-4 build the forecast engine (data layer + stupid-simple baseline). Phase 5 wires forecasts into the API and UI. Phase 6 adds real POS integrations (Square first). Phase 7 adds external data (weather, events, holidays). Phase 8 replaces the baseline with a real pooled ML model.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16, Alembic, React 18, Vite, Tailwind, Recharts. New deps: `numpy`, `scipy` (forecast math), `httpx` (async HTTP for integrations), `holidays` (calendar), later `scikit-learn` or `xgboost` (Phase 8).

---

## File Map

### Phase 1: Self-Service Demo
```
backend/app/services/demo_bootstrap.py          CREATE  — Auto-seed demo user + location + scenario
backend/app/api/v1/auth.py                      MODIFY  — Call bootstrap after register
backend/app/api/v1/router.py                    MODIFY  — Relax demo endpoint auth
backend/alembic/versions/003_seed_demo_user.py  CREATE  — Migration to seed demo account
backend/app/core/config.py                      MODIFY  — Add DEMO_PASSWORD setting
backend/tests/test_demo_bootstrap.py            CREATE  — Tests
```

### Phase 2: Production Hardening
```
backend/app/core/exceptions.py                  MODIFY  — Add logging to generic handler
backend/app/core/config.py                      MODIFY  — Fix CORS defaults
backend/nginx.conf                              MODIFY  — Add security headers
backend/alembic.ini                             MODIFY  — Remove hardcoded URL
backend/app/core/logging.py                     MODIFY  — Structured JSON logging
```

### Phase 3: Forecast Data Layer
```
backend/app/db/models/daily_aggregate.py        CREATE  — Daily rollups per location
backend/app/db/models/forecast.py               CREATE  — Forecast snapshots
backend/app/db/models/store_context.py          CREATE  — Hours changes, closures, promos, menu changes
backend/app/db/models/external_event.py         CREATE  — Holidays, local events, weather
backend/app/services/aggregation_service.py     CREATE  — Roll up orders/shifts/menu into dailies
backend/app/repositories/aggregate_repo.py      CREATE  — Query historical aggregates
backend/alembic/versions/003_forecast_tables.py CREATE  — Migration for all forecast tables
backend/app/schemas/forecast.py                 CREATE  — Pydantic models for forecast I/O
backend/tests/test_aggregation.py               CREATE  — Tests
```

### Phase 4: Baseline Forecast Engine
```
backend/app/forecast/__init__.py                CREATE
backend/app/forecast/baseline.py                CREATE  — Same-weekday avg + trend + overrides
backend/app/forecast/features.py                CREATE  — Feature extraction from aggregates
backend/app/forecast/output.py                  CREATE  — Format forecast into predictions_json
backend/app/forecast/confidence.py              CREATE  — Confidence band calculation
backend/app/services/forecast_service.py        CREATE  — Orchestrator: aggregate -> features -> model -> output
backend/tests/test_baseline_forecast.py         CREATE  — Tests
backend/tests/test_forecast_service.py          CREATE  — Tests
```

### Phase 5: Forecast API + UI
```
backend/app/api/v1/forecast.py                  CREATE  — GET /locations/{id}/forecast
backend/app/api/v1/router.py                    MODIFY  — Include forecast router
frontend/src/pages/ForecastPage.tsx              CREATE  — Forecast dashboard page
frontend/src/components/forecast/ForecastCard.tsx        CREATE  — Daily forecast card
frontend/src/components/forecast/ConfidenceBand.tsx      CREATE  — Range visualization
frontend/src/components/forecast/WeekView.tsx            CREATE  — 2-week calendar view
frontend/src/components/forecast/WhyExplainer.tsx        CREATE  — "Why" explanations
frontend/src/lib/api.ts                         MODIFY  — Add forecast endpoints
frontend/src/hooks/useStore.ts                  MODIFY  — Add forecast state
frontend/src/components/layout/Sidebar.tsx      MODIFY  — Add forecast nav item
frontend/src/App.tsx                            MODIFY  — Add forecast route
```

### Phase 6: POS Integrations
```
backend/app/providers/pos/square.py             CREATE  — Square API adapter
backend/app/providers/pos/toast.py              CREATE  — Toast API adapter
backend/app/providers/pos/clover.py             CREATE  — Clover API adapter
backend/app/providers/labor/square_labor.py     CREATE  — Square Team/Labor adapter
backend/app/providers/registry.py               MODIFY  — Register new providers
backend/app/api/v1/integrations.py              CREATE  — OAuth flows, webhook receivers
backend/app/services/sync_service.py            CREATE  — Webhook + polling + nightly replay
backend/app/db/models/integration.py            CREATE  — Store OAuth tokens, sync state
backend/alembic/versions/004_integrations.py    CREATE  — Migration
```

### Phase 7: External Data
```
backend/app/external/__init__.py                CREATE
backend/app/external/weather.py                 CREATE  — OpenWeatherMap API
backend/app/external/holidays.py                CREATE  — Holiday calendar (python-holidays)
backend/app/external/events.py                  CREATE  — Local events (manual + PredictHQ)
backend/app/external/school_calendar.py         CREATE  — School calendar data
backend/app/services/context_service.py         CREATE  — Aggregate all external signals
backend/tests/test_external.py                  CREATE  — Tests
```

### Phase 8: Real ML Model
```
backend/app/forecast/pooled_model.py            CREATE  — Trained model with full feature set
backend/app/forecast/training.py                CREATE  — Training pipeline
backend/app/forecast/model_registry.py          CREATE  — Model versioning, A/B comparison
backend/app/forecast/evaluation.py              CREATE  — Scoring: staffing efficiency, waste, margin
```

---

## Phase 1: Self-Service Demo

**Goal:** A prospect logs in with credentials you hand them and sees a populated dashboard. No wrench required.

### Task 1.1: Demo Bootstrap Service

**Files:**
- Create: `backend/app/services/demo_bootstrap.py`
- Test: `backend/tests/test_demo_bootstrap.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_demo_bootstrap.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.demo_bootstrap import bootstrap_demo_location


@pytest.mark.asyncio
async def test_bootstrap_creates_location_and_loads_scenario():
    """Bootstrap should create a location, load normal_day, and recompute."""
    db = AsyncMock()
    # Mock the sub-services
    with patch("app.services.demo_bootstrap.IngestionService") as MockIngestion, \
         patch("app.services.demo_bootstrap.SnapshotService") as MockSnapshot, \
         patch("app.services.demo_bootstrap.load_scenario") as mock_load, \
         patch("app.services.demo_bootstrap.detect_data_date_range") as mock_dates:

        mock_load.return_value = MagicMock()
        mock_dates.return_value = (MagicMock(), MagicMock(), MagicMock())

        ingestion_instance = MockIngestion.return_value
        ingestion_instance.ensure_location = AsyncMock(return_value=MagicMock(id="loc-1"))
        ingestion_instance.ingest_scenario = AsyncMock()

        snapshot_instance = MockSnapshot.return_value
        snapshot_instance.recompute = AsyncMock(return_value={"status": "green"})

        result = await bootstrap_demo_location(db, "Demo Restaurant")

        assert result["location_id"] is not None
        ingestion_instance.ensure_location.assert_called_once()
        ingestion_instance.ingest_scenario.assert_called_once()
        snapshot_instance.recompute.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_demo_bootstrap.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.demo_bootstrap'`

- [ ] **Step 3: Implement demo_bootstrap.py**

```python
# backend/app/services/demo_bootstrap.py
"""Bootstrap a demo location with pre-loaded scenario data."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.loader import load_scenario
from app.services.ingestion_service import IngestionService
from app.services.snapshot_service import SnapshotService
from app.services.date_utils import detect_data_date_range


async def bootstrap_demo_location(
    db: AsyncSession,
    restaurant_name: str = "Demo Restaurant",
    scenario: str = "normal_day",
) -> dict:
    """Create a location, load scenario data, recompute dashboard.

    Returns dict with location_id and dashboard snapshot.
    Idempotent — if location with this name exists, reuses it.
    """
    scenario_data = load_scenario(scenario)

    # Override the location name from the scenario
    scenario_data.location["name"] = restaurant_name

    ingestion = IngestionService(db)
    location = await ingestion.ensure_location(scenario_data.location)
    location_id = location.id

    await ingestion.ingest_scenario(location_id, scenario_data)
    await db.flush()

    now, day_start, day_end = await detect_data_date_range(db, location_id)
    snapshot_service = SnapshotService(db)
    dashboard = await snapshot_service.recompute(location_id, now, day_start, day_end)

    return {
        "location_id": str(location_id),
        "dashboard": dashboard,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_demo_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/demo_bootstrap.py backend/tests/test_demo_bootstrap.py
git commit -m "feat: add demo bootstrap service for self-service demo"
```

### Task 1.2: Seed Demo User via Migration

**Files:**
- Create: `backend/alembic/versions/003_seed_demo_user.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Add DEMO_PASSWORD to config**

In `backend/app/core/config.py`, add to the Settings class:

```python
    DEMO_USER_EMAIL: str = "demo@quantumatiq.com"
    DEMO_USER_PASSWORD: str = "EightySix-Demo-2026"  # Override via env in production
```

- [ ] **Step 2: Create the migration**

```python
# backend/alembic/versions/003_seed_demo_user.py
"""Seed demo user and bootstrap location.

Revision ID: 003
Revises: 002
Create Date: 2026-04-16
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEMO_USER_ID = "00000000-0000-4000-a000-000000000001"


def upgrade() -> None:
    # Insert demo user if not exists.
    # Password hash is set by the app on first boot — this just reserves the row.
    # We use a raw INSERT with ON CONFLICT DO NOTHING for idempotency.
    op.execute(sa.text(
        """
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
        VALUES (:id, :email, :pw, :name, 'admin', true)
        ON CONFLICT (email) DO UPDATE SET role = 'admin'
        """
    ).bindparams(
        id=DEMO_USER_ID,
        email="demo@quantumatiq.com",
        pw="$PLACEHOLDER$",  # Real hash set on app startup
        name="Demo User",
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM users WHERE email = 'demo@quantumatiq.com'"
    ))
```

- [ ] **Step 3: Add startup hook to hash demo password and bootstrap location**

Create a startup event in `backend/app/main.py`. Add after `create_app()`:

```python
@app.on_event("startup")
async def _seed_demo():
    """Ensure demo user has a real password hash and a populated location."""
    if not settings.DEMO_MODE:
        return

    from app.db.session import async_session_factory
    from app.services.auth_service import hash_password, get_user_by_email
    from app.services.demo_bootstrap import bootstrap_demo_location

    async with async_session_factory() as db:
        user = await get_user_by_email(db, settings.DEMO_USER_EMAIL)
        if user and user.hashed_password == "$PLACEHOLDER$":
            user.hashed_password = hash_password(settings.DEMO_USER_PASSWORD)
            await db.flush()

        # Bootstrap demo location if no locations exist
        from sqlalchemy import select, func
        from app.db.models.location import Location
        count = (await db.execute(select(func.count()).select_from(Location))).scalar()
        if count == 0:
            await bootstrap_demo_location(db)

        await db.commit()
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/003_seed_demo_user.py backend/app/core/config.py backend/app/main.py
git commit -m "feat: seed demo user on startup with auto-bootstrap"
```

### Task 1.3: Relax Demo Endpoint Auth

**Files:**
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Change demo router dependency from require_admin to get_current_user**

The demo endpoints currently require admin (`dependencies=[Depends(require_admin)]`). In demo mode, any authenticated user should access them.

In `backend/app/api/v1/router.py`, change line 42:

```python
# OLD:
api_router.include_router(demo_router, dependencies=[Depends(require_admin)])

# NEW:
# In demo mode, any authenticated user can access demo endpoints.
# The _check_demo_mode dependency on the router itself already gates on DEMO_MODE.
api_router.include_router(demo_router, dependencies=_authed)
```

- [ ] **Step 2: Verify existing demo endpoints still check DEMO_MODE**

Confirm that `backend/app/api/v1/demo.py` line 25 already has:
```python
router = APIRouter(prefix="/api/v1/demo", tags=["demo"], dependencies=[Depends(_check_demo_mode)])
```
This ensures demo endpoints return 404 when DEMO_MODE=false, regardless of auth.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/router.py
git commit -m "feat: allow any authenticated user to access demo endpoints in demo mode"
```

### Task 1.4: Fix Post-Login Redirect

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Change post-login default page**

Currently `App.tsx` redirects authenticated users to the Demo page. Change it to redirect to Dashboard if a location exists with a snapshot, otherwise Demo.

In `frontend/src/App.tsx`, find the routing logic that sends users to the demo page after login. Change it so:
- If `store.locations.length > 0` and a dashboard snapshot exists → show DashboardPage
- Otherwise → show DemoPage

The exact change depends on the current routing structure. The key behavior: a demo user who logs in and already has a bootstrapped location should land on the dashboard, not the demo controls.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: redirect to dashboard after login when data exists"
```

### Task 1.5: Deploy & Verify

- [ ] **Step 1: Build frontend**

```bash
cd frontend && npm run build
```

- [ ] **Step 2: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 3: Deploy to server**

```bash
gcloud compute ssh restaurant-chops --zone=us-central1-a \
  --command="cd /home/adam/eightysix && git pull && cd backend && docker compose -f docker-compose.prod.yml up -d --build app"
```

- [ ] **Step 4: Verify demo login works end-to-end**

```bash
# Test: login as demo user
curl -s -X POST https://quantumatiq.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@quantumatiq.com","password":"EightySix-Demo-2026"}'
# Expected: 200 with access_token

# Test: fetch dashboard (use token from above)
curl -s https://quantumatiq.com/api/v1/locations \
  -H "Authorization: Bearer <token>"
# Expected: at least one location with data
```

- [ ] **Step 5: Commit deploy verification**

---

## Phase 2: Production Hardening

**Goal:** Stop swallowing errors. Add security headers. Fix CORS. Professional-grade ops.

### Task 2.1: Fix Error Logging

**Files:**
- Modify: `backend/app/core/exceptions.py`

- [ ] **Step 1: Add logging to generic exception handler**

```python
# backend/app/core/exceptions.py — modify generic_exception_handler
import logging

logger = logging.getLogger(__name__)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/exceptions.py
git commit -m "fix: log unhandled exceptions instead of silently swallowing"
```

### Task 2.2: Fix CORS Defaults

**Files:**
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Change default CORS origins**

```python
# OLD:
CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

# NEW:
CORS_ORIGINS: list[str] = ["https://quantumatiq.com"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/config.py
git commit -m "fix: default CORS to production origin, not localhost"
```

### Task 2.3: Add Nginx Security Headers

**Files:**
- Modify: `backend/nginx.conf`

- [ ] **Step 1: Add security headers to the HTTPS server block**

After line 11 (`ssl_protocols TLSv1.2 TLSv1.3;`), add:

```nginx
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

- [ ] **Step 2: Commit**

```bash
git add backend/nginx.conf
git commit -m "fix: add security headers to nginx (HSTS, X-Frame-Options, etc.)"
```

### Task 2.4: Fix alembic.ini

**Files:**
- Modify: `backend/alembic.ini`

- [ ] **Step 1: Remove hardcoded database URL**

The alembic URL in `alembic.ini` is ignored at runtime (env.py overrides it from settings.DATABASE_URL), but having stale credentials in a committed file is sloppy.

```ini
# OLD:
sqlalchemy.url = postgresql+asyncpg://chops:chops_dev_password@localhost:5433/eightysix

# NEW:
sqlalchemy.url = postgresql+asyncpg://localhost/eightysix
# NOTE: This is overridden by env.py which reads DATABASE_URL from environment.
```

- [ ] **Step 2: Commit**

```bash
git add backend/alembic.ini
git commit -m "fix: remove stale dev credentials from alembic.ini"
```

### Task 2.5: Deploy Phase 2

- [ ] **Step 1: Push and deploy**

```bash
git push origin main
gcloud compute ssh restaurant-chops --zone=us-central1-a \
  --command="cd /home/adam/eightysix && git pull && cd backend && docker compose -f docker-compose.prod.yml up -d --build app nginx"
```

---

## Phase 3: Forecast Data Layer

**Goal:** Build the tables and aggregation jobs that turn raw order/shift/menu data into the historical features a forecast model needs.

### Task 3.1: Daily Aggregate Model

**Files:**
- Create: `backend/app/db/models/daily_aggregate.py`
- Test: `backend/tests/test_aggregation.py`

- [ ] **Step 1: Write the model**

```python
# backend/app/db/models/daily_aggregate.py
"""Daily rollup of location metrics — the core feature table for forecasting."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyAggregate(Base):
    __tablename__ = "daily_aggregates"
    __table_args__ = (
        Index("ix_daily_agg_location_date", "location_id", "agg_date", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agg_date: Mapped[date] = mapped_column(Date, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon, 6=Sun

    # Revenue
    net_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gross_sales: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    refund_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    comp_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    void_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    avg_ticket: Mapped[float] = mapped_column(Numeric(8, 2), default=0)

    # Orders
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    orders_dine_in: Mapped[int] = mapped_column(Integer, default=0)
    orders_takeout: Mapped[int] = mapped_column(Integer, default=0)
    orders_delivery: Mapped[int] = mapped_column(Integer, default=0)
    orders_drive_through: Mapped[int] = mapped_column(Integer, default=0)
    covers: Mapped[int] = mapped_column(Integer, nullable=True)  # guest count if available

    # Labor
    total_labor_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    total_labor_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    labor_hours_kitchen: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_foh: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_bar: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_delivery: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours_manager: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_cost_ratio: Mapped[float] = mapped_column(Numeric(5, 4), nullable=True)

    # Daypart breakdown (JSONB — flexible schema for daypart-level detail)
    # Structure: {"breakfast": {"sales": 0, "orders": 0}, "lunch": {...}, "dinner": {...}, "late": {...}}
    daypart_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Top SKUs (JSONB — top 50 items by units sold)
    # Structure: [{"item_name": "...", "units_sold": N, "revenue": N, "category": "..."}]
    top_skus_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Category breakdown
    # Structure: {"entrees": {"units": N, "revenue": N}, "appetizers": {...}, ...}
    category_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/models/daily_aggregate.py
git commit -m "feat: add DailyAggregate model for forecast feature storage"
```

### Task 3.2: Store Context + External Event Models

**Files:**
- Create: `backend/app/db/models/store_context.py`
- Create: `backend/app/db/models/external_event.py`

- [ ] **Step 1: Write store context model**

```python
# backend/app/db/models/store_context.py
"""Store-level context events that affect forecasts — closures, promos, menu changes, etc."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StoreContext(Base):
    __tablename__ = "store_context"
    __table_args__ = (
        Index("ix_store_ctx_location_date", "location_id", "context_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    context_date: Mapped[date] = mapped_column(Date, nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: hours_change, closure, promo, menu_change, pricing_change, special_event, staffing_change
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
```

- [ ] **Step 2: Write external event model**

```python
# backend/app/db/models/external_event.py
"""External events — holidays, weather, local events, school calendar, payday effects."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Float, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExternalEvent(Base):
    __tablename__ = "external_events"
    __table_args__ = (
        Index("ix_ext_event_date_type", "event_date", "event_type"),
        Index("ix_ext_event_location", "location_id", "event_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # NULL location_id = applies to all locations in region

    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: holiday, local_event, weather, school_calendar, payday, sports, concert, convention
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    impact_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Multiplier: 1.0 = normal, 1.2 = +20%, 0.8 = -20%
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Weather payload: {"temp_high": 82, "precip_chance": 0.6, "condition": "rain"}
    # Event payload: {"venue": "...", "expected_attendance": 5000, "distance_miles": 2.3}
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/db/models/store_context.py backend/app/db/models/external_event.py
git commit -m "feat: add StoreContext and ExternalEvent models for forecast features"
```

### Task 3.3: Forecast Snapshot Model

**Files:**
- Create: `backend/app/db/models/forecast.py`

- [ ] **Step 1: Write forecast model**

```python
# backend/app/db/models/forecast.py
"""Forecast snapshots — one row per location per target date per model run."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Float, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecast_location_target", "location_id", "target_date"),
        Index("ix_forecast_run", "run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # All forecasts from one run share a run_id

    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1-14 = detailed, 15-28 = broad
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # "baseline_v1", "pooled_v1", etc.

    # Point estimates
    expected_sales: Mapped[float] = mapped_column(Float, nullable=False)
    expected_orders: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_covers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Confidence bands
    sales_low: Mapped[float] = mapped_column(Float, nullable=False)
    sales_high: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.8)
    # 0.8 = 80% of outcomes expected within [low, high]

    # Channel breakdown (JSONB)
    # {"dine_in": N, "takeout": N, "delivery": N}
    orders_by_channel_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Daypart breakdown (JSONB)
    # {"breakfast": {"sales": N, "orders": N}, "lunch": {...}, "dinner": {...}}
    daypart_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Labor recommendation (JSONB)
    # {"kitchen": 24.0, "foh": 32.0, "bar": 8.0, "delivery": 12.0, "total": 76.0}
    labor_hours_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Top SKU demand (JSONB — top 50)
    # [{"item_name": "...", "expected_units": N, "category": "..."}]
    top_skus_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Risk flags (JSONB)
    # [{"flag": "understaffed", "message": "...", "severity": "warning"}]
    risk_flags_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # "Why" explanation (human-readable)
    explanation: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # e.g. "Friday dinner projected +18% vs normal due to game + warm weather"

    # Purchasing signal (JSONB)
    # [{"item": "chicken", "adjustment_pct": 12, "reason": "game day demand"}]
    purchasing_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/models/forecast.py
git commit -m "feat: add Forecast model with full output schema"
```

### Task 3.4: Alembic Migration for Forecast Tables

**Files:**
- Create: `backend/alembic/versions/004_forecast_tables.py`

- [ ] **Step 1: Write the migration**

Create migration that builds all 4 new tables: `daily_aggregates`, `store_context`, `external_events`, `forecasts`. Use the exact column definitions from the models above.

- [ ] **Step 2: Test migration locally**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/004_forecast_tables.py
git commit -m "feat: migration 004 — forecast tables (daily_aggregates, store_context, external_events, forecasts)"
```

### Task 3.5: Aggregation Service

**Files:**
- Create: `backend/app/services/aggregation_service.py`
- Create: `backend/app/repositories/aggregate_repo.py`
- Test: `backend/tests/test_aggregation.py`

- [ ] **Step 1: Write the aggregation service**

The aggregation service rolls up raw orders/shifts/menu data into daily_aggregates. It should:

1. Query all orders for a location on a given date
2. Query all shifts for that date
3. Query all order_items joined to menu_items
4. Compute: net_sales, order_count, channel breakdown, labor hours by role, daypart breakdown, top 50 SKUs, category breakdown
5. Upsert into daily_aggregates (idempotent — re-running for same date replaces)

Daypart definitions:
- breakfast: orders before 11:00
- lunch: 11:00 to 14:59
- dinner: 15:00 to 20:59
- late: 21:00+

```python
# backend/app/services/aggregation_service.py
"""Roll up raw data into daily aggregates for forecasting."""
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select, func, and_
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
        channel_counts = defaultdict(int)
        for o in orders:
            channel_counts[o.channel or "dine_in"] += 1

        # Daypart breakdown
        dayparts = {dp: {"sales": 0.0, "orders": 0} for dp in DAYPART_BOUNDARIES}
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
        role_hours = defaultdict(float)
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
        sku_sales = defaultdict(lambda: {"units": 0, "revenue": 0.0, "category": ""})
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
        cat_totals = defaultdict(lambda: {"units": 0, "revenue": 0.0})
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

    # -- Data fetch helpers (same pattern as DerivationService) --

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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/aggregation_service.py
git commit -m "feat: aggregation service — roll up raw data into daily forecast features"
```

---

## Phase 4: Baseline Forecast Engine

**Goal:** The stupid-simple model that gets it right enough to be useful, before anything fancy.

Algorithm:
1. Same-weekday average (last 4 weeks + last 8 weeks, weighted 60/40)
2. Trend adjustment (linear slope over recent 4 weeks)
3. Event/holiday override (multiplier from external_events)
4. Weather modifier (near-term only, weeks 1-2)
5. For weeks 3-4: widen confidence bands, drop weather, use seasonal norms + event overlays

### Task 4.1: Feature Extraction

**Files:**
- Create: `backend/app/forecast/features.py`

- [ ] **Step 1: Write feature extraction**

```python
# backend/app/forecast/features.py
"""Extract features from daily aggregates for the forecast model."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from dataclasses import dataclass, field

from app.db.models.daily_aggregate import DailyAggregate
from app.db.models.external_event import ExternalEvent


@dataclass
class DayFeatures:
    """Features for one target forecast date."""
    target_date: date
    day_of_week: int  # 0=Mon
    week_of_year: int
    horizon_days: int  # days from today

    # Historical baselines
    same_dow_avg_4w: float | None = None  # Avg sales for same weekday, last 4 weeks
    same_dow_avg_8w: float | None = None  # Avg sales for same weekday, last 8 weeks
    same_dow_orders_4w: float | None = None
    same_dow_orders_8w: float | None = None

    # Trend
    trend_slope_sales: float = 0.0  # Weekly slope over last 4 weeks
    trend_slope_orders: float = 0.0

    # Channel mix (avg ratios over last 4 weeks)
    channel_mix: dict = field(default_factory=dict)
    # {"dine_in": 0.55, "takeout": 0.25, "delivery": 0.20}

    # Labor baselines
    labor_hours_by_role_avg: dict = field(default_factory=dict)

    # Daypart baselines
    daypart_avg: dict = field(default_factory=dict)

    # Top SKU demand
    top_skus_avg: list = field(default_factory=list)

    # External signals
    events: list[dict] = field(default_factory=list)
    event_multiplier: float = 1.0  # Combined impact
    weather: dict | None = None
    is_holiday: bool = False


def extract_features(
    aggregates: list[DailyAggregate],
    external_events: list[ExternalEvent],
    target_dates: list[date],
    today: date,
) -> list[DayFeatures]:
    """Build feature vectors for each target date from historical aggregates."""
    # Index aggregates by (day_of_week, weeks_ago)
    by_dow: dict[int, list[DailyAggregate]] = defaultdict(list)
    for agg in sorted(aggregates, key=lambda a: a.agg_date, reverse=True):
        by_dow[agg.day_of_week].append(agg)

    # Index events by date
    events_by_date: dict[date, list[ExternalEvent]] = defaultdict(list)
    for ev in external_events:
        events_by_date[ev.event_date].append(ev)

    features = []
    for td in target_dates:
        horizon = (td - today).days
        dow = td.weekday()
        woy = td.isocalendar()[1]

        f = DayFeatures(
            target_date=td,
            day_of_week=dow,
            week_of_year=woy,
            horizon_days=horizon,
        )

        # Same weekday history
        same_dow = by_dow.get(dow, [])
        recent_4w = [a for a in same_dow if 0 < (td - a.agg_date).days <= 28]
        recent_8w = [a for a in same_dow if 0 < (td - a.agg_date).days <= 56]

        if recent_4w:
            f.same_dow_avg_4w = sum(float(a.net_sales) for a in recent_4w) / len(recent_4w)
            f.same_dow_orders_4w = sum(a.order_count for a in recent_4w) / len(recent_4w)
        if recent_8w:
            f.same_dow_avg_8w = sum(float(a.net_sales) for a in recent_8w) / len(recent_8w)
            f.same_dow_orders_8w = sum(a.order_count for a in recent_8w) / len(recent_8w)

        # Trend: linear slope over weekly same-weekday values (last 4 points)
        if len(recent_4w) >= 2:
            points = [(i, float(a.net_sales)) for i, a in enumerate(reversed(recent_4w))]
            f.trend_slope_sales = _linear_slope(points)
            order_points = [(i, float(a.order_count)) for i, a in enumerate(reversed(recent_4w))]
            f.trend_slope_orders = _linear_slope(order_points)

        # Channel mix from last 4 weeks (all days, not just same weekday)
        all_recent = [a for a in aggregates if 0 < (td - a.agg_date).days <= 28]
        if all_recent:
            total_orders = sum(a.order_count for a in all_recent)
            if total_orders > 0:
                f.channel_mix = {
                    "dine_in": sum(a.orders_dine_in for a in all_recent) / total_orders,
                    "takeout": sum(a.orders_takeout for a in all_recent) / total_orders,
                    "delivery": sum(a.orders_delivery for a in all_recent) / total_orders,
                    "drive_through": sum(a.orders_drive_through for a in all_recent) / total_orders,
                }

        # Labor hours by role (avg same weekday last 4w)
        if recent_4w:
            f.labor_hours_by_role_avg = {
                "kitchen": sum(float(a.labor_hours_kitchen) for a in recent_4w) / len(recent_4w),
                "foh": sum(float(a.labor_hours_foh) for a in recent_4w) / len(recent_4w),
                "bar": sum(float(a.labor_hours_bar) for a in recent_4w) / len(recent_4w),
                "delivery": sum(float(a.labor_hours_delivery) for a in recent_4w) / len(recent_4w),
                "manager": sum(float(a.labor_hours_manager) for a in recent_4w) / len(recent_4w),
            }

        # Daypart avg
        if recent_4w:
            dp_sums = defaultdict(lambda: {"sales": 0.0, "orders": 0})
            dp_count = 0
            for a in recent_4w:
                if a.daypart_json:
                    dp_count += 1
                    for dp, vals in a.daypart_json.items():
                        dp_sums[dp]["sales"] += vals.get("sales", 0)
                        dp_sums[dp]["orders"] += vals.get("orders", 0)
            if dp_count:
                f.daypart_avg = {
                    dp: {"sales": v["sales"] / dp_count, "orders": v["orders"] / dp_count}
                    for dp, v in dp_sums.items()
                }

        # Top SKU demand (avg units from last 4w same-weekday)
        if recent_4w:
            sku_totals = defaultdict(lambda: {"units": 0, "category": ""})
            for a in recent_4w:
                for sku in (a.top_skus_json or []):
                    sku_totals[sku["item_name"]]["units"] += sku["units_sold"]
                    sku_totals[sku["item_name"]]["category"] = sku.get("category", "")
            f.top_skus_avg = sorted(
                [{"item_name": k, "expected_units": round(v["units"] / len(recent_4w)), "category": v["category"]}
                 for k, v in sku_totals.items()],
                key=lambda x: x["expected_units"],
                reverse=True,
            )[:50]

        # External events
        day_events = events_by_date.get(td, [])
        f.events = [{"name": e.name, "type": e.event_type, "impact": e.impact_estimate} for e in day_events]
        f.is_holiday = any(e.event_type == "holiday" for e in day_events)

        # Combined event multiplier
        multiplier = 1.0
        for e in day_events:
            if e.impact_estimate is not None:
                multiplier *= e.impact_estimate
        f.event_multiplier = multiplier

        # Weather (only for horizon <= 14)
        weather_events = [e for e in day_events if e.event_type == "weather"]
        if weather_events and horizon <= 14:
            f.weather = weather_events[0].payload_json

        features.append(f)

    return features


def _linear_slope(points: list[tuple[int, float]]) -> float:
    """Simple linear regression slope from (x, y) pairs."""
    n = len(points)
    if n < 2:
        return 0.0
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] ** 2 for p in points)
    denom = n * sum_xx - sum_x ** 2
    if denom == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/forecast/__init__.py backend/app/forecast/features.py
git commit -m "feat: forecast feature extraction from daily aggregates"
```

### Task 4.2: Baseline Model

**Files:**
- Create: `backend/app/forecast/baseline.py`
- Test: `backend/tests/test_baseline_forecast.py`

- [ ] **Step 1: Write the baseline model**

```python
# backend/app/forecast/baseline.py
"""Baseline forecast model — stupid-simple on purpose.

Algorithm:
1. Weighted average: 60% last-4-weeks same-weekday, 40% last-8-weeks
2. Trend adjustment: apply weekly slope
3. Event/holiday multiplier
4. Weather modifier (weeks 1-2 only)
5. Confidence bands: tighter for near-term, wider for far-term
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.forecast.features import DayFeatures


@dataclass
class ForecastResult:
    """Output of the baseline model for one day."""
    expected_sales: float
    expected_orders: int
    sales_low: float
    sales_high: float
    confidence_level: float
    orders_by_channel: dict
    daypart: dict
    labor_hours: dict
    top_skus: list
    risk_flags: list
    explanation: str
    purchasing: list


MODEL_VERSION = "baseline_v1"


def forecast_day(features: DayFeatures) -> ForecastResult:
    """Produce a forecast for one day from its feature vector."""
    # 1. Weighted baseline
    avg_4w = features.same_dow_avg_4w
    avg_8w = features.same_dow_avg_8w
    orders_4w = features.same_dow_orders_4w
    orders_8w = features.same_dow_orders_8w

    if avg_4w is not None and avg_8w is not None:
        base_sales = 0.6 * avg_4w + 0.4 * avg_8w
    elif avg_4w is not None:
        base_sales = avg_4w
    elif avg_8w is not None:
        base_sales = avg_8w
    else:
        base_sales = 0

    if orders_4w is not None and orders_8w is not None:
        base_orders = 0.6 * orders_4w + 0.4 * orders_8w
    elif orders_4w is not None:
        base_orders = orders_4w
    elif orders_8w is not None:
        base_orders = orders_8w
    else:
        base_orders = 0

    # 2. Trend adjustment (slope = change per week, apply to weeks_ahead)
    weeks_ahead = max(features.horizon_days / 7, 0)
    base_sales += features.trend_slope_sales * weeks_ahead
    base_orders += features.trend_slope_orders * weeks_ahead

    # 3. Event multiplier
    base_sales *= features.event_multiplier
    base_orders *= features.event_multiplier

    # 4. Weather modifier (near-term only)
    weather_mod = 1.0
    if features.weather and features.horizon_days <= 14:
        weather_mod = _weather_multiplier(features.weather)
        base_sales *= weather_mod
        base_orders *= weather_mod

    # 5. Confidence bands
    base_sales = max(base_sales, 0)
    base_orders = max(base_orders, 0)

    if features.horizon_days <= 14:
        # Weeks 1-2: tighter bands
        band_pct = 0.10 + (features.horizon_days / 14) * 0.05  # 10-15%
        confidence = 0.80
    else:
        # Weeks 3-4: wider bands, probabilistic
        band_pct = 0.15 + ((features.horizon_days - 14) / 14) * 0.10  # 15-25%
        confidence = 0.70

    sales_low = base_sales * (1 - band_pct)
    sales_high = base_sales * (1 + band_pct)

    # Channel breakdown
    expected_orders_int = max(round(base_orders), 0)
    orders_by_channel = {}
    if features.channel_mix and expected_orders_int > 0:
        for ch, ratio in features.channel_mix.items():
            orders_by_channel[ch] = round(expected_orders_int * ratio)

    # Daypart breakdown
    daypart = {}
    if features.daypart_avg:
        total_dp_sales = sum(v["sales"] for v in features.daypart_avg.values())
        for dp, vals in features.daypart_avg.items():
            ratio = vals["sales"] / total_dp_sales if total_dp_sales > 0 else 0.25
            daypart[dp] = {
                "sales": round(base_sales * ratio, 2),
                "orders": round(expected_orders_int * ratio),
            }

    # Labor hours recommendation
    labor_hours = {}
    if features.labor_hours_by_role_avg:
        # Scale labor proportionally to sales change
        if features.same_dow_avg_4w and features.same_dow_avg_4w > 0:
            scale = base_sales / features.same_dow_avg_4w
        else:
            scale = 1.0
        for role, hours in features.labor_hours_by_role_avg.items():
            labor_hours[role] = round(hours * scale, 1)
        labor_hours["total"] = round(sum(labor_hours.values()), 1)

    # Top SKU demand
    top_skus = []
    if features.top_skus_avg:
        if features.same_dow_orders_4w and features.same_dow_orders_4w > 0:
            sku_scale = base_orders / features.same_dow_orders_4w
        else:
            sku_scale = 1.0
        for sku in features.top_skus_avg[:50]:
            top_skus.append({
                "item_name": sku["item_name"],
                "expected_units": max(round(sku["expected_units"] * sku_scale), 0),
                "category": sku["category"],
            })

    # Risk flags
    risk_flags = _compute_risk_flags(features, base_sales, base_orders, labor_hours)

    # Explanation
    explanation = _build_explanation(features, base_sales, weather_mod)

    # Purchasing signals
    purchasing = _compute_purchasing(features, top_skus)

    return ForecastResult(
        expected_sales=round(base_sales, 2),
        expected_orders=expected_orders_int,
        sales_low=round(sales_low, 2),
        sales_high=round(sales_high, 2),
        confidence_level=confidence,
        orders_by_channel=orders_by_channel,
        daypart=daypart,
        labor_hours=labor_hours,
        top_skus=top_skus,
        risk_flags=risk_flags,
        explanation=explanation,
        purchasing=purchasing,
    )


def _weather_multiplier(weather: dict) -> float:
    """Estimate weather impact on traffic. Returns multiplier around 1.0."""
    mod = 1.0
    precip = weather.get("precip_chance", 0)
    condition = (weather.get("condition") or "").lower()

    # Rain reduces dine-in, boosts delivery
    if precip > 0.6 or condition in ("rain", "storm", "thunderstorm"):
        mod *= 0.92  # Net -8% (dine-in drops more than delivery gains)
    elif precip > 0.3:
        mod *= 0.96

    # Extreme cold or heat
    temp = weather.get("temp_high")
    if temp is not None:
        if temp > 100:
            mod *= 0.90
        elif temp > 95:
            mod *= 0.95
        elif temp < 20:
            mod *= 0.88
        elif temp < 32:
            mod *= 0.93

    return mod


def _compute_risk_flags(features, base_sales, base_orders, labor_hours) -> list[dict]:
    """Flag staffing, demand, and operational risks."""
    flags = []

    # Understaffed risk
    if labor_hours and features.labor_hours_by_role_avg:
        for role in ("kitchen", "foh"):
            recommended = labor_hours.get(role, 0)
            historical = features.labor_hours_by_role_avg.get(role, 0)
            if recommended > historical * 1.15:
                flags.append({
                    "flag": "understaffed",
                    "message": f"{role.upper()} may need +{round(recommended - historical, 1)}h above recent average",
                    "severity": "warning",
                })

    # Overstaffed on slow day
    if features.trend_slope_sales < -50:
        flags.append({
            "flag": "likely_slow_day",
            "message": "Downward trend — consider reducing scheduled hours",
            "severity": "info",
        })

    # Event-driven spike
    if features.event_multiplier > 1.15:
        event_names = [e["name"] for e in features.events if e.get("impact", 1.0) > 1.0]
        flags.append({
            "flag": "event_spike",
            "message": f"Expected +{round((features.event_multiplier - 1) * 100)}% due to {', '.join(event_names) or 'events'}",
            "severity": "warning",
        })

    return flags


def _build_explanation(features, base_sales, weather_mod) -> str:
    """Build human-readable 'why' for the forecast."""
    parts = []
    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = dow_names[features.day_of_week]

    if features.same_dow_avg_4w and features.same_dow_avg_4w > 0:
        pct_change = (base_sales - features.same_dow_avg_4w) / features.same_dow_avg_4w * 100
        direction = "up" if pct_change > 0 else "down"
        parts.append(f"{day_name} projected {direction} {abs(pct_change):.0f}% vs recent average")

    for event in features.events:
        if event.get("impact") and event["impact"] != 1.0:
            impact_pct = (event["impact"] - 1) * 100
            parts.append(f"{'+' if impact_pct > 0 else ''}{impact_pct:.0f}% from {event['name']}")

    if weather_mod != 1.0:
        impact_pct = (weather_mod - 1) * 100
        condition = (features.weather or {}).get("condition", "weather")
        parts.append(f"{impact_pct:+.0f}% from {condition}")

    if features.horizon_days > 14:
        parts.append("broader estimate — 3-4 week horizon")

    return ". ".join(parts) if parts else f"Based on recent {day_name} average"


def _compute_purchasing(features, top_skus) -> list[dict]:
    """Suggest purchasing adjustments based on demand changes."""
    signals = []
    if not features.top_skus_avg or not top_skus:
        return signals

    historical = {s["item_name"]: s["expected_units"] for s in features.top_skus_avg[:20]}
    for sku in top_skus[:20]:
        hist = historical.get(sku["item_name"], 0)
        if hist > 0:
            change_pct = (sku["expected_units"] - hist) / hist * 100
            if abs(change_pct) >= 10:
                signals.append({
                    "item": sku["item_name"],
                    "adjustment_pct": round(change_pct),
                    "reason": "event demand" if features.event_multiplier > 1.05 else "trend",
                })

    return signals
```

- [ ] **Step 2: Write tests**

```python
# backend/tests/test_baseline_forecast.py
import pytest
from datetime import date
from app.forecast.features import DayFeatures
from app.forecast.baseline import forecast_day


def test_baseline_with_4w_and_8w_data():
    f = DayFeatures(
        target_date=date(2026, 4, 17),
        day_of_week=4,  # Friday
        week_of_year=16,
        horizon_days=1,
        same_dow_avg_4w=5000.0,
        same_dow_avg_8w=4800.0,
        same_dow_orders_4w=200.0,
        same_dow_orders_8w=190.0,
    )
    result = forecast_day(f)
    # 60% * 5000 + 40% * 4800 = 3000 + 1920 = 4920
    assert 4900 < result.expected_sales < 4950
    assert result.expected_orders > 0
    assert result.sales_low < result.expected_sales
    assert result.sales_high > result.expected_sales


def test_baseline_with_event_multiplier():
    f = DayFeatures(
        target_date=date(2026, 4, 17),
        day_of_week=4,
        week_of_year=16,
        horizon_days=1,
        same_dow_avg_4w=5000.0,
        same_dow_avg_8w=5000.0,
        event_multiplier=1.2,
        events=[{"name": "Big Game", "type": "sports", "impact": 1.2}],
    )
    result = forecast_day(f)
    assert result.expected_sales > 5500  # +20%
    assert "Big Game" in result.explanation


def test_confidence_bands_widen_for_far_horizon():
    near = DayFeatures(
        target_date=date(2026, 4, 17), day_of_week=4, week_of_year=16,
        horizon_days=3, same_dow_avg_4w=5000.0, same_dow_avg_8w=5000.0,
    )
    far = DayFeatures(
        target_date=date(2026, 5, 8), day_of_week=4, week_of_year=19,
        horizon_days=22, same_dow_avg_4w=5000.0, same_dow_avg_8w=5000.0,
    )
    near_r = forecast_day(near)
    far_r = forecast_day(far)

    near_band = near_r.sales_high - near_r.sales_low
    far_band = far_r.sales_high - far_r.sales_low
    assert far_band > near_band
    assert far_r.confidence_level < near_r.confidence_level


def test_no_historical_data_returns_zero():
    f = DayFeatures(
        target_date=date(2026, 4, 17), day_of_week=4, week_of_year=16,
        horizon_days=1,
    )
    result = forecast_day(f)
    assert result.expected_sales == 0
    assert result.expected_orders == 0
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_baseline_forecast.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/forecast/baseline.py backend/tests/test_baseline_forecast.py
git commit -m "feat: baseline forecast model — weighted avg + trend + events + weather"
```

### Task 4.3: Forecast Service (Orchestrator)

**Files:**
- Create: `backend/app/services/forecast_service.py`

- [ ] **Step 1: Write the forecast service**

This orchestrates: query aggregates -> extract features -> run baseline -> persist forecasts -> return results.

```python
# backend/app/services/forecast_service.py
"""Forecast service — orchestrates feature extraction, model execution, and persistence."""
import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.daily_aggregate import DailyAggregate
from app.db.models.external_event import ExternalEvent
from app.db.models.forecast import Forecast
from app.forecast.features import extract_features
from app.forecast.baseline import forecast_day, MODEL_VERSION


class ForecastService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_forecast(
        self,
        location_id: uuid.UUID,
        horizon_days: int = 28,
    ) -> list[dict]:
        """Generate forecasts for the next N days. Returns list of forecast dicts."""
        today = date.today()
        target_dates = [today + timedelta(days=d) for d in range(1, horizon_days + 1)]

        # Fetch historical aggregates (last 8 weeks)
        history_start = today - timedelta(days=56)
        aggregates = await self._get_aggregates(location_id, history_start, today)

        # Fetch external events for forecast window
        external = await self._get_external_events(location_id, today, target_dates[-1])

        # Extract features
        features = extract_features(aggregates, external, target_dates, today)

        # Run baseline model
        run_id = uuid.uuid4()
        results = []

        for f in features:
            result = forecast_day(f)

            # Persist
            forecast = Forecast(
                location_id=location_id,
                run_id=run_id,
                target_date=f.target_date,
                horizon_days=f.horizon_days,
                model_version=MODEL_VERSION,
                expected_sales=result.expected_sales,
                expected_orders=result.expected_orders,
                sales_low=result.sales_low,
                sales_high=result.sales_high,
                confidence_level=result.confidence_level,
                orders_by_channel_json=result.orders_by_channel,
                daypart_json=result.daypart,
                labor_hours_json=result.labor_hours,
                top_skus_json=result.top_skus,
                risk_flags_json=result.risk_flags,
                explanation=result.explanation,
                purchasing_json=result.purchasing,
            )
            self.db.add(forecast)

            results.append({
                "target_date": f.target_date.isoformat(),
                "horizon_days": f.horizon_days,
                "expected_sales": result.expected_sales,
                "expected_orders": result.expected_orders,
                "sales_low": result.sales_low,
                "sales_high": result.sales_high,
                "confidence_level": result.confidence_level,
                "orders_by_channel": result.orders_by_channel,
                "daypart": result.daypart,
                "labor_hours": result.labor_hours,
                "top_skus": result.top_skus[:20],
                "risk_flags": result.risk_flags,
                "explanation": result.explanation,
                "purchasing": result.purchasing,
            })

        await self.db.flush()
        return results

    async def _get_aggregates(self, location_id, start, end):
        stmt = select(DailyAggregate).where(
            DailyAggregate.location_id == location_id,
            DailyAggregate.agg_date >= start,
            DailyAggregate.agg_date <= end,
        ).order_by(DailyAggregate.agg_date)
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_external_events(self, location_id, start, end):
        stmt = select(ExternalEvent).where(
            ExternalEvent.event_date >= start,
            ExternalEvent.event_date <= end,
            (ExternalEvent.location_id == location_id) | (ExternalEvent.location_id.is_(None)),
        )
        return list((await self.db.execute(stmt)).scalars().all())
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/forecast_service.py
git commit -m "feat: forecast service orchestrator — aggregates to predictions"
```

---

## Phase 5: Forecast API + UI

**Goal:** Wire forecasts into the API and render them in the dashboard.

### Task 5.1: Forecast API Endpoint

**Files:**
- Create: `backend/app/api/v1/forecast.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Create the forecast endpoint**

```python
# backend/app/api/v1/forecast.py
"""Forecast endpoints — generate and retrieve forecasts."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.forecast_service import ForecastService
from app.services.aggregation_service import AggregationService
from app.services.date_utils import detect_data_date_range

router = APIRouter(prefix="/api/v1/locations/{location_id}/forecast", tags=["forecast"])


@router.post("/generate")
async def generate_forecast(
    location_id: uuid.UUID,
    horizon_days: int = Query(default=28, ge=1, le=28),
    db: AsyncSession = Depends(get_db),
):
    """Generate forecasts for the next N days."""
    service = ForecastService(db)
    results = await service.generate_forecast(location_id, horizon_days)
    return {"forecasts": results, "count": len(results), "model": "baseline_v1"}


@router.post("/backfill-aggregates")
async def backfill_aggregates(
    location_id: uuid.UUID,
    days: int = Query(default=56, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Backfill daily aggregates from existing order/shift data."""
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    service = AggregationService(db)
    count = await service.backfill(location_id, start_date, end_date)
    return {"status": "backfilled", "days_processed": count}


@router.get("")
async def get_forecast(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get latest forecast run for a location."""
    service = ForecastService(db)
    results = await service.get_latest_forecast(location_id)
    return {"forecasts": results}
```

- [ ] **Step 2: Add get_latest_forecast to ForecastService**

Add this method to `backend/app/services/forecast_service.py`:

```python
    async def get_latest_forecast(self, location_id: uuid.UUID) -> list[dict]:
        """Get the most recent forecast run for a location."""
        # Get latest run_id
        from sqlalchemy import desc
        stmt = (
            select(Forecast)
            .where(Forecast.location_id == location_id)
            .order_by(desc(Forecast.created_at))
            .limit(1)
        )
        latest = (await self.db.execute(stmt)).scalar_one_or_none()
        if not latest:
            return []

        # Get all forecasts from that run
        stmt = (
            select(Forecast)
            .where(Forecast.run_id == latest.run_id)
            .order_by(Forecast.target_date)
        )
        forecasts = list((await self.db.execute(stmt)).scalars().all())

        return [
            {
                "target_date": f.target_date.isoformat(),
                "horizon_days": f.horizon_days,
                "expected_sales": float(f.expected_sales),
                "expected_orders": f.expected_orders,
                "sales_low": float(f.sales_low),
                "sales_high": float(f.sales_high),
                "confidence_level": float(f.confidence_level),
                "orders_by_channel": f.orders_by_channel_json,
                "daypart": f.daypart_json,
                "labor_hours": f.labor_hours_json,
                "top_skus": (f.top_skus_json or [])[:20],
                "risk_flags": f.risk_flags_json or [],
                "explanation": f.explanation,
                "purchasing": f.purchasing_json or [],
            }
            for f in forecasts
        ]
```

- [ ] **Step 3: Register in router**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1.forecast import router as forecast_router
# Under protected routes:
api_router.include_router(forecast_router, dependencies=_authed)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/forecast.py backend/app/api/v1/router.py backend/app/services/forecast_service.py
git commit -m "feat: forecast API endpoints — generate, backfill, retrieve"
```

### Task 5.2: Frontend Forecast Page

**Files:**
- Create: `frontend/src/pages/ForecastPage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/App.tsx`

This task creates the full forecast UI. The page should show:

1. **Week 1-2 view**: Daily cards with expected sales, orders, labor hours, confidence bands, risk flags, and "why" explanations
2. **Week 3-4 view**: Broader cards with ranges, staffing bands, purchasing signals
3. A "Generate Forecast" button that calls the API
4. Risk flags highlighted in red/yellow
5. Purchasing signals in a separate section

Key UX decisions:
- Show ranges, not exact numbers, for weeks 3-4
- Color-code risk flags by severity
- Show "why" explanations prominently — this is what sells
- Labor hours shown by role in a small bar or table

Add API functions to `api.ts`:
```typescript
export const generateForecast = (locId: string, horizon = 28) =>
  request<any>(`/api/v1/locations/${locId}/forecast/generate?horizon_days=${horizon}`, { method: 'POST' });
export const getForecast = (locId: string) =>
  request<any>(`/api/v1/locations/${locId}/forecast`);
export const backfillAggregates = (locId: string, days = 56) =>
  request<any>(`/api/v1/locations/${locId}/forecast/backfill-aggregates?days=${days}`, { method: 'POST' });
```

Add "Forecast" to the sidebar navigation (Calendar icon from lucide-react).

- [ ] **Step 1: Add API functions**
- [ ] **Step 2: Create ForecastPage component**
- [ ] **Step 3: Add route to App.tsx**
- [ ] **Step 4: Add sidebar nav item**
- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ForecastPage.tsx frontend/src/lib/api.ts frontend/src/components/layout/Sidebar.tsx frontend/src/App.tsx
git commit -m "feat: forecast page with week view, confidence bands, and explanations"
```

---

## Phase 6: POS Integrations

**Goal:** Real data from real POS systems. Square first, then Toast and Clover.

### Integration Architecture

```
Webhook (if available) → /api/v1/integrations/{provider}/webhook
  ↓
Normalize to DTOs (OrderDTO, ShiftDTO, etc.)
  ↓
IngestionService.ingest_from_providers()
  ↓
Nightly replay/backfill job (repairs webhook misses)
```

### Integration Matrix (for reference)

| Capability | Square | Toast | Clover | Lightspeed O | Revel |
|-----------|--------|-------|--------|-------------|-------|
| Menu sync | OAuth REST | OAuth REST | OAuth REST | OAuth REST | OAuth REST |
| Order sync | Webhooks + REST | Webhooks + REST | REST (poll) | REST (poll) | REST (poll) |
| Labor sync | Team API | Labor API | N/A (3rd party) | N/A | Employees API |
| Payment sync | Payments API | Payments API | Payments API | Payments API | Payments API |
| Webhook support | Yes (reliable) | Yes (reliable) | Limited | No | No |
| Auth friction | Low (OAuth) | Medium (partner) | Medium (OAuth) | Medium (OAuth) | High (partner) |

### Task 6.1: Integration Model + OAuth Storage

**Files:**
- Create: `backend/app/db/models/integration.py`
- Create: `backend/alembic/versions/005_integrations.py`

Store OAuth tokens, sync state, and webhook registration per location per provider.

### Task 6.2: Square POS Provider

**Files:**
- Create: `backend/app/providers/pos/square.py`
- Create: `backend/app/providers/labor/square_labor.py`

Implement `POSProvider` and `LaborProvider` protocols using Square's Orders API, Catalog API, and Team API. Include:
- OAuth2 flow (authorization URL generation + token exchange)
- Webhook receiver for order.created, order.updated events
- Polling fallback for menu sync (catalog has no webhooks)
- Nightly backfill: fetch orders for previous day, upsert

### Task 6.3: Toast POS Provider

Similar to Square but using Toast's Partner API. Toast requires partner enrollment.

### Task 6.4: Clover POS Provider

REST-only (limited webhook support). Implement as polled integration with configurable interval.

### Task 6.5: Sync Service

**Files:**
- Create: `backend/app/services/sync_service.py`

Orchestrates: webhook processing + scheduled polling + nightly replay. Architecture:
- Webhook handler: normalize event → ingest → trigger aggregation for affected date
- Poller: configurable per-provider interval, fetch changed records since last sync
- Nightly replay: for each location, re-fetch previous day's orders, verify/repair misses

---

## Phase 7: External Data

**Goal:** Weather, holidays, events, school calendar, payday effects — the signals that explain why Tuesday was weird.

### Task 7.1: Holiday Calendar

**Files:**
- Create: `backend/app/external/holidays.py`

Use the `holidays` Python library. For each location's country/state, pre-populate external_events for the next 12 months. Include impact_estimate based on historical norms (e.g., Thanksgiving = 0.3x for many restaurants, Super Bowl Sunday = 1.4x for bars).

### Task 7.2: Weather API

**Files:**
- Create: `backend/app/external/weather.py`

Use OpenWeatherMap One Call API (free tier: 1000 calls/day). Fetch 7-day forecast daily for each location. Store as external_events with weather payload. Only used for weeks 1-2 forecasts.

### Task 7.3: Local Events

**Files:**
- Create: `backend/app/external/events.py`

Two sources:
1. Manual entry via store_context table (manager enters "concert at venue next door Friday")
2. PredictHQ API (optional, paid) for automated event discovery by geo-radius

### Task 7.4: Context Service

**Files:**
- Create: `backend/app/services/context_service.py`

Aggregates all external signals for a given location + date range. Returns unified list of ExternalEvent records for the forecast feature extractor.

---

## Phase 8: Real ML Model

**Goal:** Replace baseline with a pooled model that learns from data. Only after we have 4+ weeks of real data per location.

### Architecture

```
DailyAggregate + ExternalEvents + StoreContext
  ↓
Feature matrix (same features as baseline, plus:)
  - lagged sales (t-1, t-7, t-14)
  - lagged orders
  - labor/sales ratio trend
  - menu/category seasonality
  - channel mix shift
  - weather (near-term)
  ↓
Pooled model (one model, all stores as training data)
  - Store ID as categorical feature (learned embeddings)
  - XGBoost or LightGBM for point estimate
  - Quantile regression for confidence bands
  ↓
Compare against baseline on same evaluation window
  - Only promote if MAPE improves by >5%
```

### Success Metrics

Don't judge by "did it predict the exact number." Judge by operational improvements:
- Staffing efficiency: fewer dead shifts, fewer slammed shifts
- Stockout rate reduction
- Waste reduction
- Labor % improvement
- Service time improvement
- Margin improvement

### Tasks 8.1-8.4

- 8.1: Training pipeline (aggregate features → train → evaluate → save model)
- 8.2: Model registry (version models, A/B compare against baseline)
- 8.3: Evaluation framework (compare model vs baseline on holdout dates)
- 8.4: Promotion logic (auto-promote if MAPE improves >5%)

---

## Execution Order

| Phase | Depends On | Est. Complexity | Priority |
|-------|-----------|-----------------|----------|
| 1: Self-Service Demo | Nothing | Small (5 tasks) | IMMEDIATE |
| 2: Production Hardening | Nothing | Small (5 tasks) | IMMEDIATE |
| 3: Forecast Data Layer | Phase 2 | Medium (5 tasks) | HIGH |
| 4: Baseline Forecast | Phase 3 | Medium (3 tasks) | HIGH |
| 5: Forecast API + UI | Phase 4 | Medium (2 tasks) | HIGH |
| 6: POS Integrations | Phase 3 | Large (5 tasks) | MEDIUM |
| 7: External Data | Phase 3 | Medium (4 tasks) | MEDIUM |
| 8: Real ML Model | Phase 4 + 4 weeks of data | Large (4 tasks) | LATER |

Phases 1-2 can run in parallel. Phases 3-5 are sequential. Phase 6 and 7 can run in parallel after Phase 3. Phase 8 waits for real data.
