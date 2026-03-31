"""Canonical internal records. Every upstream format normalizes into these."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ── Report types ──────────────────────────────────────────────────────────

class ReportType(str, Enum):
    SALES_SUMMARY = "sales_summary"
    SALES_BY_HOUR = "sales_by_hour"
    LABOR_SUMMARY = "labor_summary"
    PUNCHES = "punches"
    SCHEDULE = "schedule"
    REFUNDS_VOIDS_COMPS = "refunds_voids_comps"
    MENU_MIX = "menu_mix"
    EMPLOYEE_ROSTER = "employee_roster"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Daypart(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    LATE_NIGHT = "late_night"
    ALL_DAY = "all_day"


class RefundType(str, Enum):
    REFUND = "refund"
    VOID = "void"
    COMP = "comp"
    UNKNOWN = "unknown"


# ── Canonical records ─────────────────────────────────────────────────────

@dataclass
class SalesRecord:
    date: date
    location_id: str = "loc_1"
    daypart: Optional[Daypart] = None
    hour: Optional[int] = None
    gross_sales: float = 0.0
    net_sales: float = 0.0
    order_count: int = 0
    delivery_sales: float = 0.0


@dataclass
class LaborRecord:
    date: date
    location_id: str = "loc_1"
    daypart: Optional[Daypart] = None
    employee_id: Optional[str] = None
    role: Optional[str] = None
    labor_hours: float = 0.0
    labor_cost: float = 0.0
    scheduled_hours: Optional[float] = None
    actual_hours: Optional[float] = None


@dataclass
class RefundEvent:
    timestamp: datetime
    amount: float
    type: RefundType = RefundType.UNKNOWN
    employee_id: Optional[str] = None
    location_id: str = "loc_1"
    order_id: Optional[str] = None
    manager: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class MenuMixRecord:
    date: date
    item_name: str
    quantity_sold: int = 0
    revenue: float = 0.0
    item_id: Optional[str] = None
    category: Optional[str] = None
    estimated_margin: Optional[float] = None
    food_cost: Optional[float] = None
    location_id: str = "loc_1"


@dataclass
class PunchRecord:
    employee_id: str
    clock_in: datetime
    clock_out: Optional[datetime] = None
    role: Optional[str] = None
    location_id: str = "loc_1"


@dataclass
class ScheduleRecord:
    employee_id: str
    date: date
    scheduled_start: datetime
    scheduled_end: datetime
    role: Optional[str] = None
    location_id: str = "loc_1"


# ── Intake metadata ──────────────────────────────────────────────────────

@dataclass
class ColumnMapping:
    raw_name: str
    canonical_field: str
    confidence: float  # 0.0–1.0
    method: str  # "synonym", "pattern", "cooccurrence", "model"


@dataclass
class SheetClassification:
    file_name: str
    sheet_name: Optional[str]
    predicted_type: ReportType
    confidence: float
    signals: list[str] = field(default_factory=list)
    column_mappings: list[ColumnMapping] = field(default_factory=list)
    header_row: int = 0
    data_start_row: int = 1
    row_count: int = 0


@dataclass
class Upload:
    upload_id: str
    restaurant_name: str
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    files: list[str] = field(default_factory=list)
    classifications: list[SheetClassification] = field(default_factory=list)


# ── Analysis outputs ─────────────────────────────────────────────────────

@dataclass
class LeakageFinding:
    finding_id: str
    category: str
    estimated_impact_observed: float
    estimated_impact_annualized: float
    confidence: Confidence
    explanation: str
    evidence_refs: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


@dataclass
class LeakageReport:
    date_range_start: Optional[date]
    date_range_end: Optional[date]
    days_covered: int
    estimated_annual_leakage: float
    average_monthly_leakage: float
    top_categories: list[dict] = field(default_factory=list)
    confidence: Confidence = Confidence.LOW
    findings: list[LeakageFinding] = field(default_factory=list)
    data_completeness_score: int = 0
    intake_metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
