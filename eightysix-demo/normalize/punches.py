"""Extract canonical PunchRecords from classified punch/timecard sheets."""

from __future__ import annotations

from models.canonical import PunchRecord, ColumnMapping
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_datetime


def extract_punches(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[PunchRecord]:
    idx = build_field_index(mappings, headers)
    records: list[PunchRecord] = []

    for row in data_rows:
        employee = get_cell(row, idx, "employee_id")
        if not employee:
            continue

        clock_in_str = get_cell(row, idx, "clock_in")
        clock_in = parse_datetime(clock_in_str)
        if clock_in is None:
            continue

        clock_out_str = get_cell(row, idx, "clock_out")
        clock_out = parse_datetime(clock_out_str) if clock_out_str else None

        role = get_cell(row, idx, "role") or None

        records.append(PunchRecord(
            employee_id=employee,
            clock_in=clock_in,
            clock_out=clock_out,
            role=role,
        ))

    return records
