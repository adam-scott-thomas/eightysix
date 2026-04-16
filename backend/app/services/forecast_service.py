"""Forecast service — orchestrates feature extraction, model execution, and persistence."""
import uuid
from datetime import date, timedelta

from sqlalchemy import desc, select
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

    async def get_latest_forecast(self, location_id: uuid.UUID) -> list[dict]:
        """Get the most recent forecast run for a location."""
        stmt = (
            select(Forecast)
            .where(Forecast.location_id == location_id)
            .order_by(desc(Forecast.created_at))
            .limit(1)
        )
        latest = (await self.db.execute(stmt)).scalar_one_or_none()
        if not latest:
            return []

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
