"""Main analysis pipeline — orchestrates intake → normalize → analyze → report."""

from __future__ import annotations

import uuid
from pathlib import Path

from intake.file_fingerprint import fingerprint, FileType
from intake.workbook_splitter import split_upload, SheetData
from intake.header_detector import detect_header
from intake.report_classifier import classify_sheet
from intake.column_inference import infer_columns
from intake.confidence_scorer import (
    data_completeness_score,
    overstaffing_confidence,
    refund_abuse_confidence,
    ghost_labor_confidence,
    menu_mix_confidence,
    understaffing_confidence,
)
from intake.date_range_detector import detect_date_range

from models.canonical import (
    ReportType, SheetClassification, Upload,
    SalesRecord, LaborRecord, RefundEvent, MenuMixRecord, PunchRecord,
    LeakageReport,
)

from normalize.sales import extract_sales
from normalize.labor import extract_labor
from normalize.refunds import extract_refunds
from normalize.menu_mix import extract_menu_mix
from normalize.punches import extract_punches

from analysis.overstaffing import analyze_overstaffing
from analysis.refund_abuse import analyze_refund_abuse
from analysis.ghost_labor import analyze_ghost_labor
from analysis.menu_mix_leak import analyze_menu_mix
from analysis.understaffing import analyze_understaffing
from analysis.aggregator import aggregate


def run_pipeline(
    file_paths: list[Path],
    restaurant_name: str = "Restaurant",
) -> LeakageReport:
    """Full pipeline: files → classify → extract → analyze → report."""

    upload = Upload(
        upload_id=f"upl_{uuid.uuid4().hex[:8]}",
        restaurant_name=restaurant_name,
        files=[str(p) for p in file_paths],
    )

    # ── Phase 1: Intake ──────────────────────────────────────────────────
    all_sheets: list[SheetData] = []
    classifications: list[SheetClassification] = []

    for path in file_paths:
        fp = fingerprint(path)
        if fp.file_type == FileType.UNSUPPORTED:
            continue
        sheets = split_upload(fp)
        all_sheets.extend(sheets)

    for sheet in all_sheets:
        header_result = detect_header(sheet.rows)
        data_rows = sheet.rows[header_result.data_start_index:header_result.data_end_index]

        clf = classify_sheet(
            headers=header_result.headers,
            data_rows=data_rows,
            file_name=sheet.file_name,
        )

        col_mappings = infer_columns(
            headers=header_result.headers,
            data_rows=data_rows,
            report_type=clf.predicted_type,
        )

        sc = SheetClassification(
            file_name=sheet.file_name,
            sheet_name=sheet.sheet_name,
            predicted_type=clf.predicted_type,
            confidence=clf.confidence,
            signals=clf.signals,
            column_mappings=col_mappings,
            header_row=header_result.header_row_index,
            data_start_row=header_result.data_start_index,
            row_count=len(data_rows),
        )
        classifications.append(sc)

        # Attach parsed data to sheet for extraction
        sheet._header_result = header_result  # type: ignore[attr-defined]
        sheet._classification = sc  # type: ignore[attr-defined]
        sheet._data_rows = data_rows  # type: ignore[attr-defined]

    upload.classifications = classifications

    # ── Phase 2: Canonical extraction ────────────────────────────────────
    all_sales: list[SalesRecord] = []
    all_labor: list[LaborRecord] = []
    all_refunds: list[RefundEvent] = []
    all_menu_mix: list[MenuMixRecord] = []
    all_punches: list[PunchRecord] = []

    for sheet in all_sheets:
        sc = getattr(sheet, "_classification", None)
        if sc is None or sc.confidence < 0.3:
            continue

        header_result = sheet._header_result  # type: ignore[attr-defined]
        data_rows = sheet._data_rows  # type: ignore[attr-defined]
        headers = header_result.headers

        if sc.predicted_type in (ReportType.SALES_SUMMARY, ReportType.SALES_BY_HOUR):
            all_sales.extend(extract_sales(headers, data_rows, sc.column_mappings))
        elif sc.predicted_type == ReportType.LABOR_SUMMARY:
            all_labor.extend(extract_labor(headers, data_rows, sc.column_mappings))
        elif sc.predicted_type == ReportType.REFUNDS_VOIDS_COMPS:
            all_refunds.extend(extract_refunds(headers, data_rows, sc.column_mappings))
        elif sc.predicted_type == ReportType.MENU_MIX:
            all_menu_mix.extend(extract_menu_mix(headers, data_rows, sc.column_mappings))
        elif sc.predicted_type == ReportType.PUNCHES:
            all_punches.extend(extract_punches(headers, data_rows, sc.column_mappings))

    # ── Phase 3: Analysis ────────────────────────────────────────────────
    date_range = detect_date_range(
        sales=all_sales,
        labor=all_labor,
        refunds=all_refunds,
        menu_mix=all_menu_mix,
        punches=all_punches,
    )

    completeness = data_completeness_score(classifications)

    results = []

    # 1. Overstaffing
    os_conf = overstaffing_confidence(all_sales, all_labor)
    if os_conf.value != "low" or (all_sales and all_labor):
        results.append(analyze_overstaffing(all_sales, all_labor, confidence=os_conf))

    # 2. Refund abuse
    ra_conf = refund_abuse_confidence(all_refunds)
    if all_refunds:
        results.append(analyze_refund_abuse(all_refunds, all_sales, confidence=ra_conf))

    # 3. Ghost labor
    gl_conf = ghost_labor_confidence(all_punches, all_sales)
    if all_punches or all_labor:
        results.append(analyze_ghost_labor(all_punches, all_sales, all_labor, confidence=gl_conf))

    # 4. Menu mix
    mm_conf = menu_mix_confidence(all_menu_mix)
    if all_menu_mix:
        results.append(analyze_menu_mix(all_menu_mix, confidence=mm_conf))

    # 5. Understaffing (only if hourly data exists)
    us_conf = understaffing_confidence(all_sales, all_labor)
    if any(s.hour is not None for s in all_sales):
        results.append(analyze_understaffing(all_sales, all_labor, confidence=us_conf))

    # ── Phase 4: Aggregate ───────────────────────────────────────────────
    intake_meta = {
        "upload_id": upload.upload_id,
        "restaurant_name": restaurant_name,
        "files_uploaded": len(file_paths),
        "sheets_parsed": len(all_sheets),
        "recognized_reports": [
            {
                "file": sc.file_name,
                "sheet": sc.sheet_name,
                "type": sc.predicted_type.value,
                "confidence": round(sc.confidence, 2),
            }
            for sc in classifications
            if sc.predicted_type != ReportType.UNKNOWN
        ],
        "missing_reports": _find_missing(classifications),
        "records_extracted": {
            "sales": len(all_sales),
            "labor": len(all_labor),
            "refunds": len(all_refunds),
            "menu_mix": len(all_menu_mix),
            "punches": len(all_punches),
        },
        "mapping_warnings": _collect_mapping_warnings(classifications),
    }

    report = aggregate(
        results=results,
        date_range=date_range,
        data_completeness_score=completeness,
        intake_metadata=intake_meta,
    )

    report.date_range_start = date_range.start if date_range else None
    report.date_range_end = date_range.end if date_range else None

    return report


def _find_missing(classifications: list[SheetClassification]) -> list[str]:
    recognized = {c.predicted_type for c in classifications if c.confidence >= 0.4}
    important = {
        ReportType.SALES_SUMMARY, ReportType.LABOR_SUMMARY,
        ReportType.REFUNDS_VOIDS_COMPS, ReportType.MENU_MIX,
    }
    missing = important - recognized
    # Sales by hour also satisfies sales requirement
    if ReportType.SALES_BY_HOUR in recognized:
        missing.discard(ReportType.SALES_SUMMARY)
    return [rt.value for rt in missing]


def _collect_mapping_warnings(classifications: list[SheetClassification]) -> list[str]:
    warnings = []
    for sc in classifications:
        low_conf = [m for m in sc.column_mappings if 0.4 <= m.confidence < 0.7 and m.canonical_field != "_unmapped"]
        for m in low_conf:
            warnings.append(
                f"{sc.file_name}: '{m.raw_name}' → {m.canonical_field} "
                f"(confidence: {m.confidence:.0%}, method: {m.method})"
            )
    return warnings
