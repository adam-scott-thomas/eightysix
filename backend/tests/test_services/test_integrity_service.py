"""Integration tests for IntegrityService — flag creation, dedup, and severity filtering."""
import uuid
from datetime import datetime, timezone

import pytest

from app.rules.integrity_rules import IntegrityCheckResult
from app.services.integrity_service import IntegrityService
from tests.conftest import SCENARIO_DATE


def _make_result(
    shift_id: str,
    employee_id: str,
    severity: str = "review",
    flag_type: str = "remote_punch",
    fraud_risk_score: float = 0.6,
) -> IntegrityCheckResult:
    return IntegrityCheckResult(
        shift_id=shift_id,
        employee_id=employee_id,
        employee_name="Test Employee",
        fraud_risk_score=fraud_risk_score,
        geofence_violation=True,
        device_mismatch=False,
        staff_discrepancy=False,
        severity=severity,
        flag_type=flag_type,
        evidence={"geofence_match": False, "ip_address": "1.2.3.4"},
        title=f"Suspicious punch-in: Test Employee",
        message="Review suspicious punch — clock-in outside geofence",
    )


class TestIntegrityService:
    async def test_creates_flags_for_violations(self, db, location, seed_employees, seed_shifts):
        """Integrity results with severity 'review' should create flags."""
        svc = IntegrityService(db)
        shift = seed_shifts[0]
        emp = seed_employees[0]
        results = [_make_result(str(shift.id), str(emp.id), severity="review")]
        flags = await svc.create_flags(location.id, results)
        assert len(flags) == 1
        flag = flags[0]
        assert flag.flag_type == "remote_punch"
        assert flag.severity == "warning"  # "review" maps to "warning"
        assert flag.status == "open"
        assert flag.shift_id == shift.id
        assert flag.employee_id == emp.id

    async def test_dedup_flags(self, db, location, seed_employees, seed_shifts):
        """Creating flags twice for the same shift + flag_type should not duplicate."""
        svc = IntegrityService(db)
        shift = seed_shifts[0]
        emp = seed_employees[0]
        results = [_make_result(str(shift.id), str(emp.id))]

        flags1 = await svc.create_flags(location.id, results)
        assert len(flags1) == 1

        flags2 = await svc.create_flags(location.id, results)
        assert len(flags2) == 0

    async def test_ignores_none_severity(self, db, location, seed_employees, seed_shifts):
        """Results with severity 'none' should produce no flags."""
        svc = IntegrityService(db)
        shift = seed_shifts[0]
        emp = seed_employees[0]
        results = [_make_result(str(shift.id), str(emp.id), severity="none")]
        flags = await svc.create_flags(location.id, results)
        assert len(flags) == 0

    async def test_high_severity_maps_to_critical(self, db, location, seed_employees, seed_shifts):
        """Results with severity 'high' should create flags with severity 'critical'."""
        svc = IntegrityService(db)
        shift = seed_shifts[1]
        emp = seed_employees[1]
        results = [_make_result(str(shift.id), str(emp.id), severity="high", fraud_risk_score=0.9)]
        flags = await svc.create_flags(location.id, results)
        assert len(flags) == 1
        assert flags[0].severity == "critical"

    async def test_multiple_flag_types_same_shift(self, db, location, seed_employees, seed_shifts):
        """Different flag types on the same shift should each create a flag."""
        svc = IntegrityService(db)
        shift = seed_shifts[0]
        emp = seed_employees[0]
        results = [
            _make_result(str(shift.id), str(emp.id), flag_type="remote_punch"),
            _make_result(str(shift.id), str(emp.id), flag_type="ghost_shift"),
        ]
        flags = await svc.create_flags(location.id, results)
        assert len(flags) == 2
        flag_types = {f.flag_type for f in flags}
        assert flag_types == {"remote_punch", "ghost_shift"}

    async def test_flags_across_multiple_shifts(self, db, location, seed_employees, seed_shifts):
        """Flags on different shifts should all be created."""
        svc = IntegrityService(db)
        results = []
        for i, shift in enumerate(seed_shifts):
            emp = seed_employees[i]
            results.append(_make_result(str(shift.id), str(emp.id)))
        flags = await svc.create_flags(location.id, results)
        assert len(flags) == 3

    async def test_evidence_stored(self, db, location, seed_employees, seed_shifts):
        """Flags should store evidence JSON from the integrity result."""
        svc = IntegrityService(db)
        shift = seed_shifts[0]
        emp = seed_employees[0]
        results = [_make_result(str(shift.id), str(emp.id))]
        flags = await svc.create_flags(location.id, results)
        assert flags[0].evidence_json is not None
        assert "geofence_match" in flags[0].evidence_json
