"""Extract canonical MenuMixRecords from classified menu mix sheets."""

from __future__ import annotations

from models.canonical import MenuMixRecord, ColumnMapping
from normalize.base import build_field_index, get_cell
from intake.type_coercion import parse_date, parse_currency, parse_int, parse_percentage


def extract_menu_mix(
    headers: list[str],
    data_rows: list[list[str]],
    mappings: list[ColumnMapping],
) -> list[MenuMixRecord]:
    idx = build_field_index(mappings, headers)
    records: list[MenuMixRecord] = []

    for row in data_rows:
        item_name = get_cell(row, idx, "item_name")
        if not item_name:
            continue

        quantity = parse_int(get_cell(row, idx, "quantity_sold"))
        revenue = parse_currency(get_cell(row, idx, "revenue"))
        food_cost = parse_currency(get_cell(row, idx, "food_cost"))
        margin_pct = parse_percentage(get_cell(row, idx, "margin_pct"))
        food_cost_pct = parse_percentage(get_cell(row, idx, "food_cost_pct"))
        margin_dollars = parse_currency(get_cell(row, idx, "margin_dollars"))
        category = get_cell(row, idx, "category") or None
        item_id = get_cell(row, idx, "item_id") or None
        date_str = get_cell(row, idx, "date")
        d = parse_date(date_str)

        # Need at least item name + one of quantity or revenue
        if quantity is None and revenue is None:
            continue

        # Compute estimated margin from whatever we have
        estimated_margin = _compute_margin(
            revenue=revenue,
            food_cost=food_cost,
            margin_pct=margin_pct,
            food_cost_pct=food_cost_pct,
            margin_dollars=margin_dollars,
        )

        records.append(MenuMixRecord(
            date=d or _sentinel_date(),
            item_name=item_name,
            item_id=item_id,
            category=category,
            quantity_sold=quantity or 0,
            revenue=revenue or 0.0,
            estimated_margin=estimated_margin,
            food_cost=food_cost,
        ))

    return records


def _compute_margin(
    revenue: float | None,
    food_cost: float | None,
    margin_pct: float | None,
    food_cost_pct: float | None,
    margin_dollars: float | None,
) -> float | None:
    """Try to compute margin percentage from whatever data is available."""
    # Direct margin percentage
    if margin_pct is not None:
        return margin_pct

    # From food cost percentage
    if food_cost_pct is not None:
        return 1.0 - food_cost_pct

    # From revenue and food cost
    if revenue and revenue > 0 and food_cost is not None:
        return (revenue - food_cost) / revenue

    # From margin dollars and revenue
    if revenue and revenue > 0 and margin_dollars is not None:
        return margin_dollars / revenue

    return None


def _sentinel_date():
    """Placeholder date when menu mix report has no date column (common for aggregate reports)."""
    from datetime import date
    return date(1970, 1, 1)
