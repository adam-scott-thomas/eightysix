"""Base extraction logic shared across all normalizers."""

from __future__ import annotations

from models.canonical import ColumnMapping


def build_field_index(mappings: list[ColumnMapping], headers: list[str]) -> dict[str, int]:
    """Build {canonical_field: column_index} from mappings.

    Only includes mappings with confidence >= 0.4 and a mapped canonical field.
    """
    index: dict[str, int] = {}
    for mapping in mappings:
        if mapping.canonical_field == "_unmapped" or mapping.confidence < 0.4:
            continue
        try:
            col_idx = headers.index(mapping.raw_name)
            index[mapping.canonical_field] = col_idx
        except ValueError:
            continue
    return index


def get_cell(row: list[str], index: dict[str, int], field: str) -> str:
    """Safely get a cell value by canonical field name."""
    col_idx = index.get(field)
    if col_idx is None or col_idx >= len(row):
        return ""
    return row[col_idx].strip()
