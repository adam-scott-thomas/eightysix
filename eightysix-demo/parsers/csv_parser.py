"""CSV parser — handles encoding detection, delimiter sniffing, and junk rows."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Optional

import chardet


def detect_encoding(file_path: Path) -> str:
    raw = file_path.read_bytes()
    result = chardet.detect(raw[:10_000])
    return result.get("encoding") or "utf-8"


def detect_delimiter(sample_lines: list[str]) -> str:
    try:
        dialect = csv.Sniffer().sniff("".join(sample_lines[:5]))
        return dialect.delimiter
    except csv.Error:
        # Fall back to comma
        return ","


def parse_csv(file_path: Path, encoding: Optional[str] = None) -> list[list[str]]:
    """Read a CSV file into a list of rows (each row is a list of strings).

    Handles:
    - Encoding detection
    - Delimiter sniffing (comma, tab, semicolon, pipe)
    - BOM stripping
    """
    if encoding is None:
        encoding = detect_encoding(file_path)

    raw_text = file_path.read_bytes().decode(encoding, errors="replace")

    # Strip BOM if present
    if raw_text.startswith("\ufeff"):
        raw_text = raw_text[1:]

    lines = raw_text.splitlines()
    if not lines:
        return []

    delimiter = detect_delimiter(lines)

    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    rows = []
    for row in reader:
        rows.append([cell.strip() for cell in row])
    return rows


def parse_tsv(file_path: Path, encoding: Optional[str] = None) -> list[list[str]]:
    """Convenience wrapper for tab-delimited files."""
    if encoding is None:
        encoding = detect_encoding(file_path)

    raw_text = file_path.read_bytes().decode(encoding, errors="replace")
    if raw_text.startswith("\ufeff"):
        raw_text = raw_text[1:]

    reader = csv.reader(io.StringIO(raw_text), delimiter="\t")
    rows = []
    for row in reader:
        rows.append([cell.strip() for cell in row])
    return rows
