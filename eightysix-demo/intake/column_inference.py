"""Map raw column headers to canonical fields.

Three-layer approach:
  A. Synonym matching — known header → canonical field
  B. Value-pattern inference — detect dates, currency, employees, items by cell content
  C. Co-occurrence logic — column combos narrow the mapping
"""

from __future__ import annotations

from models.canonical import ReportType, ColumnMapping
from intake import type_coercion as tc


# ── Layer A: Synonym dictionaries ─────────────────────────────────────────
# Maps normalized header text → canonical field name, per report type.

_GLOBAL_SYNONYMS: dict[str, str] = {
    # Dates
    "date": "date", "day": "date", "business date": "date", "business_date": "date",
    "period": "date", "week": "date", "report date": "date",
    # Location
    "location": "location_id", "store": "location_id", "restaurant": "location_id",
    "site": "location_id", "loc": "location_id",
}

_TYPE_SYNONYMS: dict[ReportType, dict[str, str]] = {
    ReportType.SALES_SUMMARY: {
        "net sales": "net_sales", "netsales": "net_sales", "net_sales": "net_sales",
        "sales net": "net_sales", "revenue": "net_sales", "net revenue": "net_sales",
        "sales $": "net_sales", "sales amount": "net_sales", "total sales": "net_sales",
        "net": "net_sales",
        "gross sales": "gross_sales", "grosssales": "gross_sales", "gross_sales": "gross_sales",
        "gross revenue": "gross_sales", "gross": "gross_sales",
        "order count": "order_count", "orders": "order_count", "num orders": "order_count",
        "order_count": "order_count", "checks": "order_count", "transactions": "order_count",
        "ticket count": "order_count", "# orders": "order_count", "total checks": "order_count",
        "delivery": "delivery_sales", "delivery sales": "delivery_sales",
        "online sales": "delivery_sales", "3rd party": "delivery_sales",
        "doordash": "delivery_sales", "ubereats": "delivery_sales", "grubhub": "delivery_sales",
        "daypart": "daypart", "meal period": "daypart", "shift": "daypart",
        "hour": "hour", "time": "hour",
    },
    ReportType.SALES_BY_HOUR: {
        "net sales": "net_sales", "sales": "net_sales", "revenue": "net_sales",
        "amount": "net_sales", "total": "net_sales",
        "hour": "hour", "time": "hour", "time period": "hour", "interval": "hour",
        "order count": "order_count", "orders": "order_count", "checks": "order_count",
        "transactions": "order_count",
    },
    ReportType.LABOR_SUMMARY: {
        "labor cost": "labor_cost", "labor_cost": "labor_cost", "labor $": "labor_cost",
        "wages": "labor_cost", "total labor": "labor_cost", "payroll": "labor_cost",
        "pay amount": "labor_cost", "total pay": "labor_cost", "total wages": "labor_cost",
        "labor hours": "labor_hours", "labor_hours": "labor_hours",
        "hours worked": "labor_hours", "actual hours": "labor_hours",
        "total hours": "labor_hours", "reg hours": "labor_hours", "hours": "labor_hours",
        "ot hours": "overtime_hours", "overtime": "overtime_hours", "overtime hours": "overtime_hours",
        "scheduled": "scheduled_hours", "scheduled hours": "scheduled_hours",
        "sched hrs": "scheduled_hours", "planned hours": "scheduled_hours",
        "labor %": "labor_pct", "labor percent": "labor_pct", "labor_pct": "labor_pct",
        "labor ratio": "labor_pct",
        "employee": "employee_id", "emp": "employee_id", "team member": "employee_id",
        "staff": "employee_id", "name": "employee_id",
        "role": "role", "position": "role", "job": "role", "job title": "role",
    },
    ReportType.PUNCHES: {
        "clock in": "clock_in", "clock_in": "clock_in", "clockin": "clock_in",
        "punch in": "clock_in", "time in": "clock_in", "start time": "clock_in",
        "shift start": "clock_in", "in": "clock_in",
        "clock out": "clock_out", "clock_out": "clock_out", "clockout": "clock_out",
        "punch out": "clock_out", "time out": "clock_out", "end time": "clock_out",
        "shift end": "clock_out", "out": "clock_out",
        "employee": "employee_id", "emp": "employee_id", "team member": "employee_id",
        "staff": "employee_id", "name": "employee_id", "server": "employee_id",
        "role": "role", "position": "role", "job": "role", "job title": "role",
        "hours": "hours", "total hours": "hours", "duration": "hours",
    },
    ReportType.SCHEDULE: {
        "scheduled start": "scheduled_start", "sched start": "scheduled_start",
        "start": "scheduled_start", "shift start": "scheduled_start",
        "scheduled end": "scheduled_end", "sched end": "scheduled_end",
        "end": "scheduled_end", "shift end": "scheduled_end",
        "employee": "employee_id", "emp": "employee_id", "team member": "employee_id",
        "staff": "employee_id", "name": "employee_id",
        "role": "role", "position": "role", "job": "role",
        "scheduled hours": "scheduled_hours", "sched hrs": "scheduled_hours",
        "planned hours": "scheduled_hours",
    },
    ReportType.REFUNDS_VOIDS_COMPS: {
        "refund": "amount", "refund amount": "amount", "refund amt": "amount",
        "refund $": "amount", "void": "amount", "void amount": "amount",
        "comp": "amount", "comp amount": "amount", "discount": "amount",
        "adjustment": "amount", "amount": "amount", "amount $": "amount", "total": "amount",
        "employee": "employee_id", "emp": "employee_id", "team member": "employee_id",
        "staff": "employee_id", "server": "employee_id", "cashier": "employee_id",
        "type": "refund_type", "action": "refund_type", "action type": "refund_type",
        "reason": "reason", "void reason": "reason", "refund reason": "reason",
        "order": "order_id", "order id": "order_id", "order #": "order_id",
        "check": "order_id", "check #": "order_id", "ticket": "order_id",
        "manager": "manager", "approved by": "manager", "mgr": "manager",
        "date": "timestamp", "time": "timestamp", "timestamp": "timestamp",
        "closed": "timestamp", "check closed": "timestamp",
    },
    ReportType.MENU_MIX: {
        "item": "item_name", "item name": "item_name", "menu item": "item_name",
        "product": "item_name", "description": "item_name", "item_name": "item_name",
        "name": "item_name",
        "qty": "quantity_sold", "quantity": "quantity_sold", "qty sold": "quantity_sold",
        "units": "quantity_sold", "count": "quantity_sold", "# sold": "quantity_sold",
        "quantity sold": "quantity_sold", "items sold": "quantity_sold",
        "revenue": "revenue", "sales": "revenue", "net sales": "revenue",
        "item sales": "revenue", "amount": "revenue", "total": "revenue",
        "margin": "estimated_margin", "food cost": "food_cost", "cost": "food_cost",
        "cogs": "food_cost", "cost %": "food_cost_pct", "margin %": "margin_pct",
        "profit": "margin_dollars",
        "category": "category", "group": "category", "menu group": "category",
        "department": "category",
        "item id": "item_id", "sku": "item_id", "plu": "item_id",
    },
    ReportType.EMPLOYEE_ROSTER: {
        "employee": "employee_id", "emp": "employee_id", "team member": "employee_id",
        "staff": "employee_id", "name": "employee_id", "full name": "employee_id",
        "first name": "first_name", "last name": "last_name",
        "role": "role", "position": "role", "job": "role", "job title": "role", "title": "role",
        "hire date": "hire_date", "start date": "hire_date", "date hired": "hire_date",
        "hourly rate": "hourly_rate", "wage": "hourly_rate", "pay rate": "hourly_rate",
        "rate": "hourly_rate",
        "phone": "phone", "email": "email",
    },
}


def _normalize(header: str) -> str:
    return header.lower().strip().replace("_", " ").replace("-", " ")


def infer_columns(
    headers: list[str],
    data_rows: list[list[str]],
    report_type: ReportType,
) -> list[ColumnMapping]:
    """Map raw headers to canonical fields for the given report type.

    Returns one ColumnMapping per header (unmapped headers get canonical_field='_unmapped').
    """
    mappings: list[ColumnMapping] = []
    type_syns = _TYPE_SYNONYMS.get(report_type, {})
    used_canonical: set[str] = set()

    # First pass: synonym matching
    for header in headers:
        norm = _normalize(header)
        canonical = type_syns.get(norm) or _GLOBAL_SYNONYMS.get(norm)

        if canonical and canonical not in used_canonical:
            mappings.append(ColumnMapping(
                raw_name=header,
                canonical_field=canonical,
                confidence=0.90,
                method="synonym",
            ))
            used_canonical.add(canonical)
        else:
            # Check partial matches
            found = False
            for syn, can in type_syns.items():
                if can in used_canonical:
                    continue
                if syn in norm or norm in syn:
                    mappings.append(ColumnMapping(
                        raw_name=header,
                        canonical_field=can,
                        confidence=0.70,
                        method="synonym_partial",
                    ))
                    used_canonical.add(can)
                    found = True
                    break

            if not found:
                mappings.append(ColumnMapping(
                    raw_name=header,
                    canonical_field="_unmapped",
                    confidence=0.0,
                    method="none",
                ))

    # Second pass: value-pattern inference for unmapped columns
    sample_rows = data_rows[:20]
    for i, mapping in enumerate(mappings):
        if mapping.canonical_field != "_unmapped":
            continue

        col_values = [row[i] for row in sample_rows if i < len(row)]
        if not col_values:
            continue

        # Try to infer from values
        inferred = _infer_from_values(col_values, report_type, used_canonical)
        if inferred:
            mapping.canonical_field = inferred
            mapping.confidence = 0.60
            mapping.method = "pattern"
            used_canonical.add(inferred)

    return mappings


def _infer_from_values(
    values: list[str],
    report_type: ReportType,
    used: set[str],
) -> str | None:
    """Try to infer canonical field from cell value patterns."""
    if tc.looks_like_datetime(values) and "timestamp" not in used:
        if report_type == ReportType.PUNCHES:
            if "clock_in" not in used:
                return "clock_in"
            if "clock_out" not in used:
                return "clock_out"
        return "timestamp"

    if tc.looks_like_date(values) and "date" not in used:
        return "date"

    if tc.looks_like_currency(values):
        # Pick the most likely unassigned currency field for this type
        currency_fields = {
            ReportType.SALES_SUMMARY: ["net_sales", "gross_sales", "delivery_sales"],
            ReportType.LABOR_SUMMARY: ["labor_cost"],
            ReportType.REFUNDS_VOIDS_COMPS: ["amount"],
            ReportType.MENU_MIX: ["revenue", "food_cost"],
        }
        for field in currency_fields.get(report_type, ["amount"]):
            if field not in used:
                return field

    if tc.looks_like_employee(values) and "employee_id" not in used:
        return "employee_id"

    if tc.looks_like_item_name(values) and "item_name" not in used:
        return "item_name"

    return None
