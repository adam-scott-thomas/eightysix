import uuid
from datetime import datetime

from sqlalchemy import select

from app.db.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def get_active_by_location(self, location_id: uuid.UUID) -> list[Alert]:
        stmt = select(Alert).where(
            Alert.location_id == location_id,
            Alert.status == "active",
        ).order_by(Alert.triggered_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_type(self, location_id: uuid.UUID, alert_type: str) -> Alert | None:
        stmt = select(Alert).where(
            Alert.location_id == location_id,
            Alert.alert_type == alert_type,
            Alert.status == "active",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(self, location_id: uuid.UUID, status: str) -> list[Alert]:
        stmt = select(Alert).where(
            Alert.location_id == location_id,
            Alert.status == status,
        ).order_by(Alert.triggered_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def expire_ttl_alerts(self, now: datetime) -> int:
        stmt = select(Alert).where(
            Alert.status == "active",
            Alert.ttl_minutes.isnot(None),
        )
        result = await self.db.execute(stmt)
        alerts = list(result.scalars().all())
        expired = 0
        for alert in alerts:
            from datetime import timedelta, timezone as tz
            triggered = alert.triggered_at
            if triggered.tzinfo is None:
                triggered = triggered.replace(tzinfo=tz.utc)
            now_aware = now if now.tzinfo else now.replace(tzinfo=tz.utc)
            if now_aware >= triggered + timedelta(minutes=alert.ttl_minutes):
                alert.status = "resolved"
                alert.resolved_at = now
                expired += 1
        if expired:
            await self.db.flush()
        return expired
