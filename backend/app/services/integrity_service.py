"""Integrity service — creates integrity flags from derivation results."""
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.integrity_flag import IntegrityFlag
from app.repositories.integrity_repo import IntegrityFlagRepository
from app.rules.integrity_rules import IntegrityCheckResult


class IntegrityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.flag_repo = IntegrityFlagRepository(db)

    async def create_flags(
        self,
        location_id: uuid.UUID,
        integrity_results: list[IntegrityCheckResult],
    ) -> list[IntegrityFlag]:
        """Create integrity flags from rule evaluation results. Deduplicates against existing open flags."""
        # Load existing open flags for this location to avoid duplicates
        existing_flags = await self.flag_repo.get_open_by_location(location_id)
        existing_shift_flags: set[tuple[str, str]] = set()
        for ef in existing_flags:
            if ef.shift_id:
                existing_shift_flags.add((str(ef.shift_id), ef.flag_type))

        flags = []
        for result in integrity_results:
            if result.severity == "none":
                continue

            # Skip if an open flag already exists for this shift + flag_type
            key = (result.shift_id, result.flag_type)
            if key in existing_shift_flags:
                continue

            flag = IntegrityFlag(
                location_id=location_id,
                employee_id=uuid.UUID(result.employee_id),
                shift_id=uuid.UUID(result.shift_id),
                flag_type=result.flag_type,
                severity="critical" if result.severity == "high" else "warning",
                confidence=result.fraud_risk_score,
                status="open",
                title=result.title,
                message=result.message,
                evidence_json=result.evidence,
                fraud_risk_score=result.fraud_risk_score,
            )
            self.db.add(flag)
            flags.append(flag)
            existing_shift_flags.add(key)

        if flags:
            await self.db.flush()
        return flags
