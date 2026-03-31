"""Extract canonical LaborRecords from classified labor sheets."""

from __future__ import annotations

from models.canonical import LaborRecord, ColumnMapping
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_date, parse_currency, parse_number


def extract_labor(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[LaborRecord]:
    idx = build_field_index(mappings, headers)
    records: list[LaborRecord] = []

    for row in data_rows:
        date_str = get_cell(row, idx, "date")
        d = parse_date(date_str)
        if d is None:
            continue

        labor_cost = parse_currency(get_cell(row, idx, "labor_cost"))
        labor_hours = parse_number(get_cell(row, idx, "labor_hours"))
        scheduled_hours = parse_number(get_cell(row, idx, "scheduled_hours"))
        overtime_hours = parse_number(get_cell(row, idx, "overtime_hours"))
        employee = get_cell(row, idx, "employee_id") or None
        role = get_cell(row, idx, "role") or None

        # Need at least cost or hours
        if labor_cost is None and labor_hours is None:
            continue

        actual_hours = labor_hours
        if overtime_hours and labor_hours:
            actual_hours = labor_hours + overtime_hours

        records.append(LaborRecord(
            date=d,
            employee_id=employee,
            role=role,
            labor_hours=labor_hours or 0.0,
            labor_cost=labor_cost or 0.0,
            scheduled_hours=scheduled_hours,
            actual_hours=actual_hours,
        ))

    return records
