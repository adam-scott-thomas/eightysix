"""Tests for the intake intelligence layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from intake.type_coercion import (
    parse_date, parse_datetime, parse_currency, parse_percentage,
    looks_like_date, looks_like_currency, looks_like_employee, looks_like_item_name,
)
from intake.header_detector import detect_header
from intake.report_classifier import classify_sheet
from intake.column_inference import infer_columns
from models.canonical import ReportType


# ── Type coercion tests ───────────────────────────────────────────────────

class TestDateParsing:
    def test_iso_format(self):
        assert parse_date("2025-03-14").isoformat() == "2025-03-14"

    def test_us_format(self):
        assert parse_date("03/14/2025").isoformat() == "2025-03-14"

    def test_us_short_year(self):
        assert parse_date("3/14/25").isoformat() == "2025-03-14"

    def test_named_month(self):
        assert parse_date("Mar 14, 2025").isoformat() == "2025-03-14"

    def test_empty(self):
        assert parse_date("") is None

    def test_garbage(self):
        assert parse_date("not a date") is None


class TestCurrencyParsing:
    def test_dollar_sign(self):
        assert parse_currency("$4,200.50") == 4200.50

    def test_plain_number(self):
        assert parse_currency("4200.50") == 4200.50

    def test_parentheses_negative(self):
        assert parse_currency("($42.50)") == -42.50

    def test_negative(self):
        assert parse_currency("-$42.50") == -42.50

    def test_empty(self):
        assert parse_currency("") is None

    def test_dash(self):
        assert parse_currency("-") is None


class TestPercentageParsing:
    def test_with_symbol(self):
        assert parse_percentage("28%") == 0.28

    def test_decimal(self):
        assert parse_percentage("0.28") == 0.28

    def test_whole_number(self):
        assert parse_percentage("28") == 0.28


class TestDatetimeParsing:
    def test_iso_with_time(self):
        dt = parse_datetime("2025-03-14 18:30")
        assert dt is not None
        assert dt.hour == 18
        assert dt.minute == 30

    def test_us_with_12h(self):
        dt = parse_datetime("03/14/2025 6:30 PM")
        assert dt is not None
        assert dt.hour == 18


class TestValueSniffers:
    def test_looks_like_date(self):
        assert looks_like_date(["2025-01-01", "2025-01-02", "2025-01-03"]) is True
        assert looks_like_date(["hello", "world", "foo"]) is False

    def test_looks_like_currency(self):
        assert looks_like_currency(["$100.00", "$200.50", "$300.00"]) is True

    def test_looks_like_employee(self):
        assert looks_like_employee(["Maria Garcia", "James Wilson", "Sam Patel"]) is True

    def test_looks_like_item_name(self):
        assert looks_like_item_name([
            "Classic Burger", "Grilled Chicken", "Classic Burger",
            "Caesar Salad", "Classic Burger", "Fish & Chips"
        ]) is True


# ── Header detector tests ────────────────────────────────────────────────

class TestHeaderDetector:
    def test_clean_data(self):
        rows = [
            ["Date", "Net Sales", "Orders"],
            ["2025-01-01", "$3200", "150"],
            ["2025-01-02", "$2900", "130"],
        ]
        result = detect_header(rows)
        assert result.header_row_index == 0
        assert result.data_start_index == 1
        assert result.headers == ["Date", "Net Sales", "Orders"]

    def test_junk_title_rows(self):
        rows = [
            ["My Restaurant — Sales Report", "", ""],
            [],
            ["Date", "Net Sales", "Orders"],
            ["2025-01-01", "$3200", "150"],
        ]
        result = detect_header(rows)
        assert result.header_row_index == 2
        assert result.data_start_index == 3
        assert "Date" in result.headers

    def test_total_row_trimmed(self):
        rows = [
            ["Date", "Net Sales", "Orders"],
            ["2025-01-01", "$3200", "150"],
            ["2025-01-02", "$2900", "130"],
            ["TOTAL", "$6100", "280"],
        ]
        result = detect_header(rows)
        assert result.data_end_index == 3  # Excludes total row


# ── Report classifier tests ──────────────────────────────────────────────

class TestReportClassifier:
    def test_sales_summary(self):
        headers = ["Date", "Net Sales", "Order Count", "Gross Sales"]
        data = [["2025-01-01", "$3200", "150", "$3400"]]
        result = classify_sheet(headers, data)
        assert result.predicted_type == ReportType.SALES_SUMMARY

    def test_labor_summary(self):
        headers = ["Date", "Team Member", "Hours Worked", "Total Pay"]
        data = [["2025-01-01", "Maria Garcia", "8.5", "$136.00"]]
        result = classify_sheet(headers, data)
        assert result.predicted_type == ReportType.LABOR_SUMMARY

    def test_refunds(self):
        headers = ["Check Closed", "Server", "Action Type", "Amount $"]
        data = [["01/15/2025 6:30 PM", "Sam Patel", "Refund", "$42.50"]]
        result = classify_sheet(headers, data)
        assert result.predicted_type == ReportType.REFUNDS_VOIDS_COMPS

    def test_menu_mix(self):
        headers = ["Item Name", "Category", "Qty Sold", "Net Sales", "Food Cost %"]
        data = [["Classic Burger", "Entrees", "2840", "$39,760.00", "32%"]]
        result = classify_sheet(headers, data)
        assert result.predicted_type == ReportType.MENU_MIX

    def test_punches(self):
        headers = ["Employee Name", "Clock In", "Clock Out", "Position"]
        data = [["Maria Garcia", "01/01/2025 6:00 AM", "01/01/2025 2:00 PM", "Kitchen"]]
        result = classify_sheet(headers, data)
        assert result.predicted_type == ReportType.PUNCHES


# ── Column inference tests ────────────────────────────────────────────────

class TestColumnInference:
    def test_sales_mapping(self):
        headers = ["Date", "Net Sales", "Order Count"]
        data = [["2025-01-01", "$3200", "150"]]
        mappings = infer_columns(headers, data, ReportType.SALES_SUMMARY)
        field_map = {m.raw_name: m.canonical_field for m in mappings}
        assert field_map["Date"] == "date"
        assert field_map["Net Sales"] == "net_sales"
        assert field_map["Order Count"] == "order_count"

    def test_refund_mapping(self):
        headers = ["Check Closed", "Server", "Action Type", "Amount $"]
        data = [["01/15/2025 6:30 PM", "Sam Patel", "Refund", "$42.50"]]
        mappings = infer_columns(headers, data, ReportType.REFUNDS_VOIDS_COMPS)
        field_map = {m.raw_name: m.canonical_field for m in mappings}
        assert field_map["Server"] == "employee_id"
        assert field_map["Amount $"] == "amount"
