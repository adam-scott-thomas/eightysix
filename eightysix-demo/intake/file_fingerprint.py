"""Detect file type and encoding for uploaded files."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import chardet


class FileType(str, Enum):
    CSV = "csv"
    TSV = "tsv"
    XLSX = "xlsx"
    UNSUPPORTED = "unsupported"


@dataclass
class FileFingerprint:
    path: Path
    file_type: FileType
    encoding: str
    size_bytes: int
    sheet_count: int = 1  # >1 only for XLSX


def fingerprint(file_path: Path) -> FileFingerprint:
    """Identify file type and encoding."""
    suffix = file_path.suffix.lower()
    size = file_path.stat().st_size

    if suffix in (".xlsx", ".xls"):
        return FileFingerprint(
            path=file_path,
            file_type=FileType.XLSX,
            encoding="n/a",
            size_bytes=size,
            sheet_count=_count_sheets(file_path),
        )

    # For text-based files, detect encoding
    raw = file_path.read_bytes()
    result = chardet.detect(raw[:10_000])
    encoding = result.get("encoding") or "utf-8"

    if suffix == ".tsv":
        ft = FileType.TSV
    elif suffix == ".csv":
        ft = FileType.CSV
    else:
        # Try to determine from content — tabs vs commas
        sample = raw[:5_000].decode(encoding, errors="replace")
        tabs = sample.count("\t")
        commas = sample.count(",")
        if tabs > commas and tabs > 10:
            ft = FileType.TSV
        elif commas > 0:
            ft = FileType.CSV
        else:
            ft = FileType.UNSUPPORTED

    return FileFingerprint(
        path=file_path,
        file_type=ft,
        encoding=encoding,
        size_bytes=size,
    )


def _count_sheets(file_path: Path) -> int:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True)
        count = len(wb.sheetnames)
        wb.close()
        return count
    except Exception:
        return 1
