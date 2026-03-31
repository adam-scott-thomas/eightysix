"""Result containers for the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models.canonical import Confidence


@dataclass(kw_only=True)
class CategoryResult:
    category: str
    estimated_annual_impact: float = 0.0
    observed_impact: float = 0.0
    confidence: Confidence = Confidence.LOW
    explanation: str = ""
    evidence: list[dict] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


@dataclass(kw_only=True)
class OverstaffingResult(CategoryResult):
    category: str = "overstaffing"
    excess_labor_days: int = 0
    avg_excess_pct: float = 0.0
    worst_day: Optional[str] = None
    worst_day_excess: float = 0.0


@dataclass(kw_only=True)
class RefundAbuseResult(CategoryResult):
    category: str = "refund_abuse"
    flagged_employees: list[dict] = field(default_factory=list)
    total_excess_refunds: float = 0.0
    peer_median_rate: float = 0.0


@dataclass(kw_only=True)
class GhostLaborResult(CategoryResult):
    category: str = "ghost_labor"
    suspect_shifts: int = 0
    total_suspect_hours: float = 0.0
    total_suspect_cost: float = 0.0


@dataclass(kw_only=True)
class MenuMixResult(CategoryResult):
    category: str = "menu_mix_margin_leak"
    low_margin_high_volume: list[dict] = field(default_factory=list)
    high_margin_low_volume: list[dict] = field(default_factory=list)
    potential_mix_shift_pct: float = 0.0


@dataclass(kw_only=True)
class UnderstaffingResult(CategoryResult):
    category: str = "understaffing"
    lost_revenue_days: int = 0
    avg_throughput_drop_pct: float = 0.0
    peak_hours_affected: list[str] = field(default_factory=list)
