"""Tests for the analysis engines."""

import sys
from pathlib import Path
from datetime import date, datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.canonical import SalesRecord, LaborRecord, RefundEvent, MenuMixRecord, PunchRecord, Confidence, RefundType
from analysis.overstaffing import analyze_overstaffing
from analysis.refund_abuse import analyze_refund_abuse
from analysis.menu_mix_leak import analyze_menu_mix
from analysis.annualizer import annualize, can_annualize


# ── Overstaffing tests ────────────────────────────────────────────────────

class TestOverstaffing:
    def test_detects_excess_labor(self):
        sales = [
            SalesRecord(date=date(2025, 1, d), net_sales=3000.0) for d in range(1, 31)
        ]
        # Labor at 35% = overstaffed (target 28%)
        labor = [
            LaborRecord(date=date(2025, 1, d), labor_cost=1050.0) for d in range(1, 31)
        ]
        result = analyze_overstaffing(sales, labor)
        assert result.observed_impact > 0
        assert result.excess_labor_days > 0

    def test_no_excess_when_efficient(self):
        sales = [
            SalesRecord(date=date(2025, 1, d), net_sales=3000.0) for d in range(1, 31)
        ]
        # Labor at 25% = below target
        labor = [
            LaborRecord(date=date(2025, 1, d), labor_cost=750.0) for d in range(1, 31)
        ]
        result = analyze_overstaffing(sales, labor)
        assert result.observed_impact == 0

    def test_empty_data(self):
        result = analyze_overstaffing([], [])
        assert result.observed_impact == 0
        assert result.confidence == Confidence.LOW


# ── Refund abuse tests ────────────────────────────────────────────────────

class TestRefundAbuse:
    def test_flags_concentration(self):
        refunds = []
        # Normal employees: 2 refunds each
        for emp in ["Alice", "Bob", "Carol"]:
            for i in range(2):
                refunds.append(RefundEvent(
                    timestamp=datetime(2025, 1, 1, 12 + i),
                    amount=20.0,
                    employee_id=emp,
                ))
        # Suspicious: 20 refunds
        for i in range(20):
            refunds.append(RefundEvent(
                timestamp=datetime(2025, 1, 1 + i % 28, 18),
                amount=30.0,
                employee_id="Dave",
            ))
        sales = [SalesRecord(date=date(2025, 1, d), net_sales=3000.0) for d in range(1, 29)]

        result = analyze_refund_abuse(refunds, sales)
        assert result.total_excess_refunds > 0
        assert len(result.flagged_employees) >= 1
        assert any(e["employee_id"] == "Dave" for e in result.flagged_employees)

    def test_no_refunds(self):
        result = analyze_refund_abuse([], [])
        assert result.confidence == Confidence.LOW


# ── Menu mix tests ────────────────────────────────────────────────────────

class TestMenuMix:
    def test_detects_margin_leak(self):
        records = [
            # High volume, low margin
            MenuMixRecord(date=date(2025, 1, 1), item_name="Fries", quantity_sold=5000,
                          revenue=15000.0, estimated_margin=0.12),
            # Low volume, high margin
            MenuMixRecord(date=date(2025, 1, 1), item_name="Craft Beer", quantity_sold=500,
                          revenue=3500.0, estimated_margin=0.75),
            # Balanced
            MenuMixRecord(date=date(2025, 1, 1), item_name="Burger", quantity_sold=2000,
                          revenue=28000.0, estimated_margin=0.35),
            MenuMixRecord(date=date(2025, 1, 1), item_name="Salad", quantity_sold=1500,
                          revenue=13500.0, estimated_margin=0.40),
        ]
        result = analyze_menu_mix(records)
        assert len(result.low_margin_high_volume) >= 1
        assert len(result.high_margin_low_volume) >= 1

    def test_empty_data(self):
        result = analyze_menu_mix([])
        assert result.confidence == Confidence.LOW


# ── Annualizer tests ──────────────────────────────────────────────────────

class TestAnnualizer:
    def test_full_year(self):
        from models.results import CategoryResult
        r = CategoryResult(category="test", observed_impact=50000.0)
        assert annualize(r, 365) == 50000.0

    def test_partial_year(self):
        from models.results import CategoryResult
        r = CategoryResult(category="test", observed_impact=10000.0)
        annual = annualize(r, 90)
        assert abs(annual - 40556) < 100  # ~365/90 * 10000

    def test_too_few_days(self):
        from models.results import CategoryResult
        r = CategoryResult(category="test", observed_impact=5000.0)
        assert annualize(r, 20) == 5000.0  # Returns observed, no extrapolation

    def test_can_annualize(self):
        assert can_annualize(30) is True
        assert can_annualize(29) is False
        assert can_annualize(365) is True


# ── Pipeline integration test ─────────────────────────────────────────────

class TestPipelineIntegration:
    def test_full_pipeline(self):
        fixtures_dir = Path(__file__).parent / "fixtures"
        if not fixtures_dir.exists():
            return  # Skip if fixtures haven't been generated

        from analysis.pipeline import run_pipeline
        files = list(fixtures_dir.glob("*.csv"))
        if not files:
            return

        report = run_pipeline(files, restaurant_name="Test Grill")
        assert report.days_covered > 0
        assert report.estimated_annual_leakage >= 0
        assert report.data_completeness_score > 0
