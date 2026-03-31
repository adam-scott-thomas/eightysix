"""Find the real header row in messy spreadsheets.

Handles:
- Title rows above the actual data
- Blank rows
- Subtotal/total rows below data
- Merged cell artifacts
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class HeaderResult:
    header_row_index: int
    data_start_index: int
    data_end_index: int  # exclusive
    headers: list[str]
    skipped_top_rows: int
    skipped_bottom_rows: int


def _is_junk_row(row: list[str]) -> bool:
    """Check if a row is likely a title, blank, or summary row."""
    non_empty = [c for c in row if c.strip()]
    if len(non_empty) == 0:
        return True
    if len(non_empty) == 1:
        # Single-cell rows are usually titles
        return True
    return False


def _is_total_row(row: list[str]) -> bool:
    """Detect subtotal / grand total rows."""
    combined = " ".join(row).lower()
    return bool(re.search(r"\b(total|subtotal|grand total|sum)\b", combined))


def _row_variety_score(row: list[str]) -> float:
    """Score how header-like a row is. Headers have many unique, short, text-only cells."""
    non_empty = [c.strip() for c in row if c.strip()]
    if not non_empty:
        return 0.0

    # Headers tend to: have many non-empty cells, be mostly text, be relatively short
    text_cells = sum(1 for c in non_empty if not re.match(r'^[\d$,.%-]+$', c))
    avg_len = sum(len(c) for c in non_empty) / len(non_empty)
    uniqueness = len(set(c.lower() for c in non_empty)) / len(non_empty)

    score = 0.0
    score += min(len(non_empty) / 3.0, 1.0) * 0.3  # More columns = more likely header
    score += (text_cells / len(non_empty)) * 0.3  # More text = more likely header
    score += (1.0 - min(avg_len / 40.0, 1.0)) * 0.2  # Shorter = more likely header
    score += uniqueness * 0.2  # More unique = more likely header

    return score


def detect_header(rows: list[list[str]]) -> HeaderResult:
    """Find the header row, data start, and data end in a list of rows.

    Strategy:
    1. Skip obvious junk rows from the top
    2. Score remaining rows by "header-likeness"
    3. The first high-scoring row after junk is probably the header
    4. Data starts on the next row
    5. Trim total/subtotal rows from the bottom
    """
    if not rows:
        return HeaderResult(
            header_row_index=0, data_start_index=0, data_end_index=0,
            headers=[], skipped_top_rows=0, skipped_bottom_rows=0,
        )

    # Phase 1: Find candidate header row
    best_idx = 0
    best_score = -1.0
    max_search = min(len(rows), 15)  # Don't look past row 15 for a header

    for i in range(max_search):
        if _is_junk_row(rows[i]):
            continue
        score = _row_variety_score(rows[i])
        if score > best_score:
            best_score = score
            best_idx = i

    header_idx = best_idx
    data_start = header_idx + 1

    # Phase 2: Trim total/junk rows from the bottom
    data_end = len(rows)
    while data_end > data_start:
        row = rows[data_end - 1]
        if _is_junk_row(row) or _is_total_row(row):
            data_end -= 1
        else:
            break

    headers = [c.strip() for c in rows[header_idx]] if header_idx < len(rows) else []

    return HeaderResult(
        header_row_index=header_idx,
        data_start_index=data_start,
        data_end_index=data_end,
        headers=headers,
        skipped_top_rows=header_idx,
        skipped_bottom_rows=len(rows) - data_end,
    )
