"""Split XLSX workbooks into individual sheets for independent classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from parsers.csv_parser import parse_csv, parse_tsv
from parsers.xlsx_parser import parse_xlsx
from intake.file_fingerprint import FileFingerprint, FileType


@dataclass
class SheetData:
    """A single sheet/file worth of tabular data."""
    file_name: str
    sheet_name: str | None  # None for CSV/TSV (single-sheet files)
    rows: list[list[str]]

    @property
    def identifier(self) -> str:
        if self.sheet_name:
            return f"{self.file_name}:{self.sheet_name}"
        return self.file_name

    @property
    def is_empty(self) -> bool:
        return len(self.rows) < 2  # Need at least header + 1 data row


def split_upload(fingerprint: FileFingerprint) -> list[SheetData]:
    """Given a file fingerprint, parse and return one SheetData per logical sheet."""
    path = fingerprint.path
    fname = path.name

    if fingerprint.file_type == FileType.XLSX:
        sheets_data = parse_xlsx(path)
        result = []
        for sheet_name, rows in sheets_data.items():
            sd = SheetData(file_name=fname, sheet_name=sheet_name, rows=rows)
            if not sd.is_empty:
                result.append(sd)
        return result

    elif fingerprint.file_type == FileType.TSV:
        rows = parse_tsv(path, encoding=fingerprint.encoding)
        sd = SheetData(file_name=fname, sheet_name=None, rows=rows)
        return [sd] if not sd.is_empty else []

    elif fingerprint.file_type == FileType.CSV:
        rows = parse_csv(path, encoding=fingerprint.encoding)
        sd = SheetData(file_name=fname, sheet_name=None, rows=rows)
        return [sd] if not sd.is_empty else []

    return []
