"""Classify a sheet/file into a report type.

Uses three signal layers:
1. Header keyword matching — what do the column names suggest?
2. Value pattern detection — what do the actual cell values look like?
3. Co-occurrence rules — what column combinations are diagnostic?
"""

from __future__ import annotations

from dataclasses import dataclass
from models.canonical import ReportType
from intake.header_detector import HeaderResult
from intake import type_coercion as tc


# ── Header keyword signals ────────────────────────────────────────────────

# Each report type has a set of weighted keyword groups.
# If a header contains any keyword from a group, that group's weight is added.

_HEADER_SIGNALS: dict[ReportType, list[tuple[list[str], float]]] = {
    ReportType.SALES_SUMMARY: [
        (["net sales", "netsales", "net_sales", "sales net", "revenue", "gross sales",
          "total sales", "sales total", "sales $", "sales amount", "total revenue"], 0.35),
        (["order count", "orders", "num orders", "order_count", "checks", "transactions",
          "ticket count", "covers"], 0.20),
        (["date", "day", "business date", "business_date", "period"], 0.10),
        (["delivery", "delivery sales", "doordash", "ubereats", "grubhub", "online",
          "dine in", "dine-in", "takeout", "catering"], 0.15),
        (["daypart", "meal period", "shift", "hour"], 0.10),
        (["discounts", "discount", "avg check", "average check", "tax", "tax collected"], 0.15),
    ],
    ReportType.SALES_BY_HOUR: [
        (["net sales", "netsales", "sales", "revenue"], 0.25),
        (["hour", "time period", "interval"], 0.35),
        (["order count", "orders", "checks", "transactions"], 0.15),
        (["date", "day", "business date"], 0.10),
    ],
    ReportType.LABOR_SUMMARY: [
        (["labor cost", "labor_cost", "labor $", "wages", "total labor", "payroll",
          "pay amount", "total pay"], 0.30),
        (["labor hours", "labor_hours", "hours worked", "actual hours", "total hours",
          "reg hours", "ot hours", "overtime"], 0.25),
        (["scheduled", "scheduled hours", "sched hrs"], 0.15),
        (["labor %", "labor percent", "labor_pct", "labor ratio"], 0.15),
        (["date", "day", "week", "period"], 0.05),
    ],
    ReportType.PUNCHES: [
        (["clock in", "clock_in", "clockin", "punch in", "time in", "start time",
          "shift start"], 0.30),
        (["clock out", "clock_out", "clockout", "punch out", "time out", "end time",
          "shift end"], 0.30),
        (["employee", "emp", "team member", "staff", "name", "server"], 0.15),
        (["role", "position", "job", "job title"], 0.10),
        (["hours", "total hours", "duration"], 0.10),
    ],
    ReportType.SCHEDULE: [
        (["scheduled start", "sched start", "start", "shift start"], 0.25),
        (["scheduled end", "sched end", "end", "shift end"], 0.25),
        (["employee", "emp", "team member", "staff", "name"], 0.15),
        (["date", "day", "week"], 0.10),
        (["role", "position", "job"], 0.10),
        (["scheduled hours", "sched hrs", "planned hours"], 0.15),
    ],
    ReportType.REFUNDS_VOIDS_COMPS: [
        (["refund", "refund amount", "refund amt", "refund $", "void", "void amount",
          "comp", "comp amount", "comp or void", "adjustment"], 0.35),
        (["employee", "emp", "team member", "staff", "server", "cashier"], 0.20),
        (["type", "action", "action type", "reason", "refund type", "void reason"], 0.20),
        (["order", "order id", "order #", "check", "check #", "ticket",
          "check no", "chk", "chk #"], 0.20),
        (["date", "time", "timestamp", "closed", "check closed"], 0.05),
        (["manager", "mgr", "approved by", "authorized"], 0.10),
    ],
    ReportType.MENU_MIX: [
        (["item", "item name", "menu item", "product", "description", "item_name"], 0.25),
        (["qty", "quantity", "qty sold", "units", "count", "# sold", "quantity sold"], 0.25),
        (["revenue", "sales", "net sales", "item sales", "amount", "total"], 0.15),
        (["margin", "food cost", "cost", "cogs", "cost %", "margin %", "profit"], 0.20),
        (["category", "group", "menu group", "department"], 0.10),
    ],
    ReportType.EMPLOYEE_ROSTER: [
        (["employee", "emp", "team member", "staff", "name", "first name", "last name"], 0.30),
        (["role", "position", "job", "job title", "title"], 0.20),
        (["hire date", "start date", "date hired"], 0.20),
        (["hourly rate", "wage", "pay rate", "rate"], 0.20),
        (["phone", "email", "address"], 0.10),
    ],
}


@dataclass
class ClassificationResult:
    predicted_type: ReportType
    confidence: float
    signals: list[str]
    runner_up: ReportType | None = None
    runner_up_confidence: float = 0.0


def _normalize_header(h: str) -> str:
    return h.lower().strip().replace("_", " ").replace("-", " ")


def _header_score(headers: list[str], report_type: ReportType) -> tuple[float, list[str]]:
    """Score how well headers match a report type's keyword groups."""
    norm_headers = [_normalize_header(h) for h in headers]
    signals_list = _HEADER_SIGNALS.get(report_type, [])
    total_score = 0.0
    signals: list[str] = []

    for keywords, weight in signals_list:
        for kw in keywords:
            for nh in norm_headers:
                if kw in nh:
                    total_score += weight
                    signals.append(f"header '{nh}' matches '{kw}'")
                    break
            else:
                continue
            break

    return total_score, signals


def _value_pattern_score(rows: list[list[str]], headers: list[str]) -> dict[str, list[str]]:
    """Analyze actual cell values to detect column types."""
    if not rows or not headers:
        return {}

    # Sample up to 20 data rows
    sample = rows[:20]
    col_signals: dict[str, list[str]] = {}

    for col_idx, header in enumerate(headers):
        values = [row[col_idx] for row in sample if col_idx < len(row)]
        patterns = []

        if tc.looks_like_date(values):
            patterns.append("date")
        if tc.looks_like_datetime(values):
            patterns.append("datetime")
        if tc.looks_like_currency(values):
            patterns.append("currency")
        if tc.looks_like_employee(values):
            patterns.append("employee")
        if tc.looks_like_item_name(values):
            patterns.append("item_name")

        if patterns:
            col_signals[header] = patterns

    return col_signals


def _cooccurrence_boost(col_patterns: dict[str, list[str]]) -> dict[ReportType, float]:
    """Boost scores based on diagnostic column combinations."""
    all_patterns = set()
    for patterns in col_patterns.values():
        all_patterns.update(patterns)

    boosts: dict[ReportType, float] = {}

    # employee + datetime + datetime = punches
    if "employee" in all_patterns and "datetime" in all_patterns:
        datetime_count = sum(1 for p in col_patterns.values() if "datetime" in p)
        if datetime_count >= 2:
            boosts[ReportType.PUNCHES] = 0.25

    # item_name + currency = menu_mix
    if "item_name" in all_patterns and "currency" in all_patterns:
        boosts[ReportType.MENU_MIX] = 0.20

    # employee + currency + no item = could be labor or refunds
    if "employee" in all_patterns and "currency" in all_patterns and "item_name" not in all_patterns:
        boosts[ReportType.REFUNDS_VOIDS_COMPS] = 0.15
        boosts[ReportType.LABOR_SUMMARY] = 0.10

    # employee + datetime + currency + single datetime col = refunds (not punches)
    if "employee" in all_patterns and "datetime" in all_patterns and "currency" in all_patterns:
        datetime_count = sum(1 for p in col_patterns.values() if "datetime" in p)
        if datetime_count == 1:
            boosts[ReportType.REFUNDS_VOIDS_COMPS] = boosts.get(ReportType.REFUNDS_VOIDS_COMPS, 0) + 0.15

    # date + currency + no employee = sales summary
    if "date" in all_patterns and "currency" in all_patterns and "employee" not in all_patterns:
        boosts[ReportType.SALES_SUMMARY] = 0.15

    return boosts


def classify_sheet(
    headers: list[str],
    data_rows: list[list[str]],
    file_name: str = "",
) -> ClassificationResult:
    """Classify a sheet into a report type using layered signal analysis."""
    scores: dict[ReportType, float] = {}
    all_signals: dict[ReportType, list[str]] = {}

    # Layer A: Header keyword matching
    for rt in ReportType:
        if rt == ReportType.UNKNOWN:
            continue
        score, sigs = _header_score(headers, rt)
        scores[rt] = score
        all_signals[rt] = sigs

    # Layer B: Value pattern detection
    col_patterns = _value_pattern_score(data_rows, headers)

    # Layer C: Co-occurrence boosts
    boosts = _cooccurrence_boost(col_patterns)
    for rt, boost in boosts.items():
        scores[rt] = scores.get(rt, 0.0) + boost
        all_signals.setdefault(rt, []).append(f"cooccurrence boost +{boost:.2f}")

    # File name hints
    fn = file_name.lower()
    name_hints = {
        ReportType.SALES_SUMMARY: ["sales", "revenue", "daily"],
        ReportType.LABOR_SUMMARY: ["labor", "payroll", "wage"],
        ReportType.PUNCHES: ["punch", "timeclock", "clock", "timecard"],
        ReportType.SCHEDULE: ["schedule", "sched", "roster"],
        ReportType.REFUNDS_VOIDS_COMPS: ["refund", "void", "comp", "discount", "adjustment"],
        ReportType.MENU_MIX: ["menu", "mix", "item", "product"],
        ReportType.EMPLOYEE_ROSTER: ["employee", "roster", "staff", "team"],
    }
    for rt, hints in name_hints.items():
        if any(h in fn for h in hints):
            scores[rt] = scores.get(rt, 0.0) + 0.10
            all_signals.setdefault(rt, []).append(f"filename hint: {fn}")

    # Pick winner
    if not scores:
        return ClassificationResult(
            predicted_type=ReportType.UNKNOWN,
            confidence=0.0,
            signals=["no classification signals found"],
        )

    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_type, best_score = sorted_types[0]

    # Normalize confidence to 0–1 (cap at 1.0)
    confidence = min(best_score, 1.0)

    runner_up = None
    runner_up_conf = 0.0
    if len(sorted_types) > 1:
        runner_up, runner_up_conf = sorted_types[1]
        runner_up_conf = min(runner_up_conf, 1.0)

    # If best score is too low, call it unknown
    if confidence < 0.15:
        return ClassificationResult(
            predicted_type=ReportType.UNKNOWN,
            confidence=confidence,
            signals=all_signals.get(best_type, []),
        )

    return ClassificationResult(
        predicted_type=best_type,
        confidence=confidence,
        signals=all_signals.get(best_type, []),
        runner_up=runner_up,
        runner_up_confidence=runner_up_conf,
    )
