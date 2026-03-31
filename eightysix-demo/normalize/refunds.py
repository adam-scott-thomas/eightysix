"""Extract canonical RefundEvents from classified refund/void/comp sheets."""

from __future__ import annotations

from models.canonical import RefundEvent, RefundType, ColumnMapping
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_datetime, parse_date, parse_currency

from datetime import datetime, time


def extract_refunds(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[RefundEvent]:
    idx = build_field_index(mappings, headers)
    records: list[RefundEvent] = []

    for row in data_rows:
        ts_str = get_cell(row, idx, "timestamp")
        ts = parse_datetime(ts_str)
        if ts is None:
            # Try date-only
            d = parse_date(ts_str)
            if d:
                ts = datetime.combine(d, time(12, 0))
            else:
                continue

        amount = parse_currency(get_cell(row, idx, "amount"))
        if amount is None or amount == 0:
            continue

        # Make amount positive (refunds are always positive leakage)
        amount = abs(amount)

        employee = get_cell(row, idx, "employee_id") or None
        refund_type = _parse_refund_type(get_cell(row, idx, "refund_type"))
        order_id = get_cell(row, idx, "order_id") or None
        manager = get_cell(row, idx, "manager") or None
        reason = get_cell(row, idx, "reason") or None

        records.append(RefundEvent(
            timestamp=ts,
            amount=amount,
            type=refund_type,
            employee_id=employee,
            order_id=order_id,
            manager=manager,
            reason=reason,
        ))

    return records


def _parse_refund_type(value: str) -> RefundType:
    if not value:
        return RefundType.UNKNOWN
    v = value.lower().strip()
    if "refund" in v:
        return RefundType.REFUND
    if "void" in v:
        return RefundType.VOID
    if "comp" in v or "discount" in v:
        return RefundType.COMP
    return RefundType.UNKNOWN
