"""Extract canonical ScheduleRecords from classified schedule sheets."""

from __future__ import annotations

from models.canonical import ScheduleRecord, ColumnMapping
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_datetime, parse_date

from datetime import datetime, time


def extract_schedule(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[ScheduleRecord]:
    idx = build_field_index(mappings, headers)
    records: list[ScheduleRecord] = []

    for row in data_rows:
        employee = get_cell(row, idx, "employee_id")
        if not employee:
            continue

        start_str = get_cell(row, idx, "scheduled_start")
        end_str = get_cell(row, idx, "scheduled_end")
        date_str = get_cell(row, idx, "date")

        start = parse_datetime(start_str)
        end = parse_datetime(end_str)

        if start is None and date_str:
            d = parse_date(date_str)
            if d:
                start = datetime.combine(d, time(9, 0))
                end = datetime.combine(d, time(17, 0))

        if start is None:
            continue

        d = start.date() if start else (parse_date(date_str) if date_str else None)
        if d is None:
            continue

        role = get_cell(row, idx, "role") or None
        hours_str = get_cell(row, idx, "scheduled_hours")

        records.append(ScheduleRecord(
            employee_id=employee,
            date=d,
            scheduled_start=start,
            scheduled_end=end or datetime.combine(d, time(17, 0)),
            role=role,
        ))

    return records
