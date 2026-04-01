"""Upload, classify, confirm, and analyze endpoints."""

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from analysis.pipeline import run_pipeline
from intake.file_fingerprint import fingerprint, FileType
from intake.workbook_splitter import split_upload
from intake.header_detector import detect_header
from intake.report_classifier import classify_sheet
from intake.column_inference import infer_columns
from intake.ambiguity_router import check_for_ambiguity, apply_corrections
from intake.confidence_scorer import data_completeness_score
from models.canonical import SheetClassification, ReportType
from output.owner_report import to_owner_json, to_internal_json, to_text_summary
from llm.explainer import generate_explanation
from app.api.leads import store_report_for_session

router = APIRouter()

# In-memory session store (production would use Redis/DB)
_sessions: dict[str, dict] = {}


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    restaurant_name: str = Form("Restaurant"),
):
    """Step 1: Upload files, classify them, check for ambiguity.

    Returns classification results and any confirmation requests.
    If all classifications are high-confidence, proceeds directly to analysis.
    """
    if not files:
        raise HTTPException(400, "No files uploaded.")

    allowed = {".csv", ".xlsx", ".xls", ".tsv"}
    for f in files:
        suffix = Path(f.filename or "").suffix.lower()
        if suffix not in allowed:
            raise HTTPException(400, f"Unsupported: {f.filename}. Accepted: {', '.join(allowed)}")

    # Save to temp dir
    session_id = f"ses_{uuid.uuid4().hex[:12]}"
    tmp_dir = Path(tempfile.mkdtemp(prefix="eightysix_"))
    saved_paths: list[Path] = []

    for f in files:
        dest = tmp_dir / (f.filename or "upload.csv")
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved_paths.append(dest)

    # Classify
    classifications: list[SheetClassification] = []
    for path in saved_paths:
        fp = fingerprint(path)
        if fp.file_type == FileType.UNSUPPORTED:
            continue
        sheets = split_upload(fp)
        for sheet in sheets:
            hr = detect_header(sheet.rows)
            data_rows = sheet.rows[hr.data_start_index:hr.data_end_index]
            clf = classify_sheet(hr.headers, data_rows, sheet.file_name)
            col_maps = infer_columns(hr.headers, data_rows, clf.predicted_type)

            classifications.append(SheetClassification(
                file_name=sheet.file_name,
                sheet_name=sheet.sheet_name,
                predicted_type=clf.predicted_type,
                confidence=clf.confidence,
                signals=clf.signals,
                column_mappings=col_maps,
                header_row=hr.header_row_index,
                data_start_row=hr.data_start_index,
                row_count=len(data_rows),
            ))

    # Check for ambiguity
    confirmations = check_for_ambiguity(classifications)
    completeness = data_completeness_score(classifications)

    # Store session
    _sessions[session_id] = {
        "tmp_dir": str(tmp_dir),
        "file_paths": [str(p) for p in saved_paths],
        "restaurant_name": restaurant_name,
        "classifications": classifications,
    }

    response = {
        "session_id": session_id,
        "classifications": [
            {
                "file": sc.file_name,
                "sheet": sc.sheet_name,
                "predicted_type": sc.predicted_type.value,
                "confidence": round(sc.confidence, 2),
                "signals": sc.signals[:5],
                "columns": [
                    {
                        "raw": m.raw_name,
                        "mapped_to": m.canonical_field,
                        "confidence": round(m.confidence, 2),
                    }
                    for m in sc.column_mappings
                    if m.canonical_field != "_unmapped"
                ],
                "row_count": sc.row_count,
            }
            for sc in classifications
        ],
        "data_completeness": completeness,
        "needs_confirmation": len(confirmations) > 0,
        "confirmations": [
            {
                "sheet": c.sheet_identifier,
                "type": c.request_type,
                "current": c.current_prediction,
                "confidence": round(c.confidence, 2),
                "alternatives": c.alternatives[:5] if c.alternatives else [],
                "columns": c.mapped_columns,
            }
            for c in confirmations
        ],
    }

    # If no confirmations needed, auto-analyze
    if not confirmations:
        report = run_pipeline(
            [Path(p) for p in _sessions[session_id]["file_paths"]],
            restaurant_name=restaurant_name,
        )
        explanation = generate_explanation(report)
        owner = to_owner_json(report)

        # Store full results for retrieval after email verification
        store_report_for_session(session_id, {
            "report": owner,
            "explanation": explanation,
            "internal": to_internal_json(report),
        })

        # Return only the teaser (big number + categories, no explanation)
        response["report"] = owner
        _cleanup_session(session_id)

    return JSONResponse(response)


@router.post("/confirm")
async def confirm_and_analyze(
    session_id: str = Form(...),
    corrections: str = Form("[]"),  # JSON array of correction objects
):
    """Step 2: Apply user corrections and run analysis.

    corrections format:
    [
        {"sheet": "file.csv", "type": "confirm"},
        {"sheet": "file.csv:Sheet1", "type": "override_classification", "value": "sales_summary"},
        {"sheet": "file.csv", "type": "override_mapping", "column": "Rev", "mapped_to": "net_sales"}
    ]
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session expired or not found. Please re-upload.")

    try:
        correction_list = json.loads(corrections)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid corrections JSON.")

    # Apply corrections
    if correction_list:
        apply_corrections(session["classifications"], correction_list)

    # Run pipeline
    report = run_pipeline(
        [Path(p) for p in session["file_paths"]],
        restaurant_name=session["restaurant_name"],
    )
    explanation = generate_explanation(report)

    owner = to_owner_json(report)
    explanation = generate_explanation(report)

    # Store full results for retrieval after verification
    store_report_for_session(session_id, {
        "report": owner,
        "explanation": explanation,
        "internal": to_internal_json(report),
    })

    response = {
        "session_id": session_id,
        "report": owner,
    }

    _cleanup_session(session_id)
    return JSONResponse(response)


@router.post("/analyze")
async def quick_analyze(
    files: list[UploadFile] = File(...),
    restaurant_name: str = Form("Restaurant"),
):
    """One-shot: upload and analyze. Returns teaser only — full results after verification."""
    if not files:
        raise HTTPException(400, "No files uploaded.")

    allowed = {".csv", ".xlsx", ".xls", ".tsv"}
    tmp_dir = Path(tempfile.mkdtemp(prefix="eightysix_"))
    saved_paths: list[Path] = []

    try:
        for f in files:
            suffix = Path(f.filename or "").suffix.lower()
            if suffix not in allowed:
                continue
            dest = tmp_dir / (f.filename or "upload.csv")
            with open(dest, "wb") as out:
                shutil.copyfileobj(f.file, out)
            saved_paths.append(dest)

        if not saved_paths:
            raise HTTPException(400, "No valid files to analyze.")

        session_id = f"ses_{uuid.uuid4().hex[:12]}"
        report = run_pipeline(saved_paths, restaurant_name=restaurant_name)
        owner = to_owner_json(report)
        explanation = generate_explanation(report)

        store_report_for_session(session_id, {
            "report": owner,
            "explanation": explanation,
            "internal": to_internal_json(report),
        })

        return JSONResponse({
            "session_id": session_id,
            "report": owner,
        })
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "eightysix-demo"}


def _cleanup_session(session_id: str):
    session = _sessions.pop(session_id, None)
    if session:
        shutil.rmtree(session.get("tmp_dir", ""), ignore_errors=True)
