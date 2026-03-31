"""Route low-confidence classifications and mappings to human confirmation.

Produces confirmation prompts when the system isn't sure enough to proceed silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.canonical import SheetClassification, ReportType, ColumnMapping


CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.65
MAPPING_CONFIDENCE_THRESHOLD = 0.60


@dataclass
class ConfirmationRequest:
    """A request for human confirmation of a classification or mapping."""
    sheet_identifier: str
    request_type: str  # "classification" or "mapping"
    current_prediction: str
    alternatives: list[str] = field(default_factory=list)
    mapped_columns: list[dict] = field(default_factory=list)
    confidence: float = 0.0


def check_for_ambiguity(
    classifications: list[SheetClassification],
) -> list[ConfirmationRequest]:
    """Check all classifications and mappings for low-confidence items.

    Returns a list of ConfirmationRequests that should be shown to the user.
    """
    requests: list[ConfirmationRequest] = []

    for sc in classifications:
        identifier = f"{sc.file_name}:{sc.sheet_name}" if sc.sheet_name else sc.file_name

        # Check classification confidence
        if sc.predicted_type != ReportType.UNKNOWN and sc.confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD:
            requests.append(ConfirmationRequest(
                sheet_identifier=identifier,
                request_type="classification",
                current_prediction=sc.predicted_type.value,
                alternatives=[rt.value for rt in ReportType if rt != ReportType.UNKNOWN and rt != sc.predicted_type],
                confidence=sc.confidence,
            ))

        # Check column mapping confidence
        low_conf_mappings = [
            m for m in sc.column_mappings
            if m.canonical_field != "_unmapped" and m.confidence < MAPPING_CONFIDENCE_THRESHOLD
        ]

        if low_conf_mappings:
            requests.append(ConfirmationRequest(
                sheet_identifier=identifier,
                request_type="mapping",
                current_prediction=sc.predicted_type.value,
                mapped_columns=[
                    {
                        "raw_name": m.raw_name,
                        "mapped_to": m.canonical_field,
                        "confidence": round(m.confidence, 2),
                        "method": m.method,
                    }
                    for m in low_conf_mappings
                ],
                confidence=min(m.confidence for m in low_conf_mappings),
            ))

    return requests


def apply_corrections(
    classifications: list[SheetClassification],
    corrections: list[dict],
) -> list[SheetClassification]:
    """Apply user corrections to classifications.

    corrections format:
    [
        {"sheet": "file.csv", "type": "override_classification", "value": "sales_summary"},
        {"sheet": "file.csv", "type": "override_mapping", "column": "Revenue", "mapped_to": "net_sales"},
        {"sheet": "file.csv", "type": "confirm"},  # Accept as-is
    ]
    """
    by_sheet = {
        (f"{sc.file_name}:{sc.sheet_name}" if sc.sheet_name else sc.file_name): sc
        for sc in classifications
    }

    for correction in corrections:
        sheet_id = correction.get("sheet", "")
        sc = by_sheet.get(sheet_id)
        if not sc:
            continue

        ctype = correction.get("type", "")

        if ctype == "override_classification":
            new_type = correction.get("value", "")
            try:
                sc.predicted_type = ReportType(new_type)
                sc.confidence = 1.0  # User-confirmed
            except ValueError:
                pass

        elif ctype == "override_mapping":
            col_name = correction.get("column", "")
            new_mapping = correction.get("mapped_to", "")
            for m in sc.column_mappings:
                if m.raw_name == col_name:
                    m.canonical_field = new_mapping
                    m.confidence = 1.0
                    m.method = "user_override"
                    break

        elif ctype == "confirm":
            sc.confidence = max(sc.confidence, 0.85)

    return classifications
