# Restaurant Chops — Restaurant Operations Backend

Production-shaped backend for restaurant operations intelligence. Real rules engine, real database, real API — only the POS/payroll source adapters are stubbed.

## Quick Start

```bash
# Start Postgres + app
docker compose up -d --build

# Or run locally (requires Postgres on port 5433)
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`. OpenAPI docs at `/docs`.

## Demo Workflow

```bash
# 1. Load a scenario
curl -X POST http://localhost:8000/api/v1/demo/load-scenario \
  -H "Content-Type: application/json" \
  -d '{"scenario": "dinner_rush"}'

# 2. Run the pipeline (save the location_id from step 1)
curl -X POST http://localhost:8000/api/v1/demo/recompute \
  -H "Content-Type: application/json" \
  -d '{"location_id": "LOCATION_ID_HERE"}'

# 3. View dashboard
curl http://localhost:8000/api/v1/locations/LOCATION_ID/dashboard/current

# 4. View active alerts
curl http://localhost:8000/api/v1/locations/LOCATION_ID/alerts?status=active

# 5. View recommendations
curl http://localhost:8000/api/v1/locations/LOCATION_ID/recommendations?status=pending

# 6. Reset and try another scenario
curl -X POST http://localhost:8000/api/v1/demo/reset
curl -X POST http://localhost:8000/api/v1/demo/load-scenario \
  -H "Content-Type: application/json" \
  -d '{"scenario": "suspicious_punch"}'
```

## Scenarios

| Scenario | What it demonstrates |
|---|---|
| `normal_day` | Baseline. No alerts. Dashboard green. |
| `dinner_rush` | Order spike 6-8 PM. Prep times rise. Rush alert triggers. |
| `refund_spike` | 3x refund rate. One employee flagged for 60% of refunds. |
| `suspicious_punch` | Clock-in outside geofence. Device mismatch. Integrity flags. |
| `understaffed` | 2 staff for 5-person volume. Critical understaffed alert. |
| `overstaffed` | 8 staff for 3-person volume. Labor cost critical. |
| `ghost_shift` | Employee clocked in with zero orders, no manager confirmation. |
| `low_margin_mix` | High volume but concentrated in low-margin items. |

## Architecture

```
[POS Stub] ────┐
               │
[Payroll Stub] ┼──▶ [Ingestion] ──▶ [Normalization] ──▶ [Rules Engine]
               │         │                │                     │
[Manual Input] ┘         │                │                     │
                         ▼                ▼                     ▼
                   [Dedup/Upsert]    [Postgres]     [Alerts / Recommendations]
                                         │                     │
                                         └──▶ [Snapshot Builder] ──▶ [Dashboard API]
```

## 6 Quick-Win Rules

1. **Staffing pressure** — orders/labor hour with 5-band classification
2. **Labor leakage** — labor cost ratio with healthy/warning/critical
3. **Refund/comp leakage** — refund rate + employee concentration detection
4. **Menu performance** — star/workhorse/puzzle/dog classification
5. **Rush detection** — backlog risk + prep time trending
6. **Punch integrity** — geofence + device + staff discrepancy fraud scoring

## Running Tests

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

## Environment Variables

See `.env.example`. Key settings:
- `DATABASE_URL` — Postgres connection string
- `POS_PROVIDER` — `stub` (swap to `toast`, `square`, etc.)
- `LABOR_PROVIDER` — `stub` (swap to `7shifts`, `gusto`, etc.)

## Swapping to Real Providers

1. Implement `POSProvider` protocol in `app/providers/pos/`
2. Register in `app/providers/registry.py`
3. Set `POS_PROVIDER=toast` in env
4. Everything downstream just works
