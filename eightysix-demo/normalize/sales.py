"""Extract canonical SalesRecords from classified sales sheets."""

from __future__ import annotations

from models.canonical import SalesRecord, ColumnMapping, Daypart
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_date, parse_currency, parse_int


def extract_sales(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[SalesRecord]:
    """Extract SalesRecords from a classified sales summary or sales-by-hour sheet."""
    idx = build_field_index(mappings, headers)
    records: list[SalesRecord] = []

    for row in data_rows:
        date_str = get_cell(row, idx, "date")
        d = parse_date(date_str)
        if d is None:
            continue

        net = parse_currency(get_cell(row, idx, "net_sales"))
        gross = parse_currency(get_cell(row, idx, "gross_sales"))
        orders = parse_int(get_cell(row, idx, "order_count"))
        delivery = parse_currency(get_cell(row, idx, "delivery_sales"))
        hour_str = get_cell(row, idx, "hour")
        daypart_str = get_cell(row, idx, "daypart")

        # Need at least one sales figure
        if net is None and gross is None:
            continue

        hour = None
        if hour_str:
            try:
                h = int(hour_str.split(":")[0].strip())
                if 0 <= h < 24:
                    hour = h
            except (ValueError, IndexError):
                pass

        daypart = _parse_daypart(daypart_str)

        records.append(SalesRecord(
            date=d,
            gross_sales=gross or 0.0,
            net_sales=net or gross or 0.0,
            order_count=orders or 0,
            delivery_sales=delivery or 0.0,
            hour=hour,
            daypart=daypart,
        ))

    return records


def _parse_daypart(value: str) -> Daypart | None:
    if not value:
        return None
    v = value.lower().strip()
    if "breakfast" in v or "morning" in v or "am" in v:
        return Daypart.BREAKFAST
    if "lunch" in v or "mid" in v:
        return Daypart.LUNCH
    if "dinner" in v or "evening" in v or "pm" in v:
        return Daypart.DINNER
    if "late" in v or "night" in v:
        return Daypart.LATE_NIGHT
    return None
