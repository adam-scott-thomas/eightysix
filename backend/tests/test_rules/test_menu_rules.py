"""Tests for menu rules — pure unit tests, no DB or async."""
from app.rules.menu_rules import evaluate_menu, classify_margin_band


def test_classify_margin_band_high():
    # (13.0 - 4.5) / 13.0 = 0.6538 — >= 0.60 high
    assert classify_margin_band(13.0, 4.50) == "high"


def test_classify_margin_band_medium():
    # (10.0 - 5.0) / 10.0 = 0.50 — >= 0.40 and < 0.60 medium
    assert classify_margin_band(10.0, 5.0) == "medium"


def test_classify_margin_band_low():
    # (5.0 - 3.5) / 5.0 = 0.30 — < 0.40 low
    assert classify_margin_band(5.0, 3.50) == "low"


def test_classify_margin_band_unknown_no_cost():
    assert classify_margin_band(10.0, None) == "unknown"


def test_classify_margin_band_unknown_zero_price():
    assert classify_margin_band(0.0, 3.0) == "unknown"


def test_menu_evaluation():
    items = [
        {
            "menu_item_id": "1",
            "item_name": "Burger",
            "units_sold": 45,
            "revenue": 585,
            "price": 13.0,
            "estimated_food_cost": 4.5,
            "margin_band": None,
        },
        {
            "menu_item_id": "2",
            "item_name": "Fries",
            "units_sold": 40,
            "revenue": 200,
            "price": 5.0,
            "estimated_food_cost": 2.0,
            "margin_band": None,
        },
        {
            "menu_item_id": "3",
            "item_name": "Cheesecake",
            "units_sold": 5,
            "revenue": 37.5,
            "price": 7.5,
            "estimated_food_cost": 2.0,
            "margin_band": None,
        },
    ]
    result = evaluate_menu(items, total_revenue=822.5)
    assert len(result.top_sellers) > 0
    # Sorted by units_sold desc: Burger (45), Fries (40), Cheesecake (5)
    assert result.top_sellers[0].item_name == "Burger"
    assert result.top_sellers[0].units_sold == 45


def test_menu_categories():
    # Burger: high volume (45 > median 40), high margin (65%) → star
    # Fries: high volume (40 >= median 40), medium margin (60%) → star
    # Cheesecake: low volume (5 < median 40), high margin (73%) → puzzle
    items = [
        {
            "menu_item_id": "1",
            "item_name": "Burger",
            "units_sold": 45,
            "revenue": 585,
            "price": 13.0,
            "estimated_food_cost": 4.5,
            "margin_band": None,
        },
        {
            "menu_item_id": "2",
            "item_name": "Fries",
            "units_sold": 40,
            "revenue": 200,
            "price": 5.0,
            "estimated_food_cost": 2.0,
            "margin_band": None,
        },
        {
            "menu_item_id": "3",
            "item_name": "Cheesecake",
            "units_sold": 5,
            "revenue": 37.5,
            "price": 7.5,
            "estimated_food_cost": 2.0,
            "margin_band": None,
        },
    ]
    result = evaluate_menu(items, total_revenue=822.5)

    by_name = {p.item_name: p for p in result.top_sellers}
    assert by_name["Burger"].category == "star"
    assert by_name["Cheesecake"].category == "puzzle"


def test_empty_menu():
    result = evaluate_menu([], total_revenue=0)
    assert result.top_sellers == []
    assert result.bottom_sellers == []
    assert result.workhorse_items == []
    assert result.dog_items == []
    assert result.attach_rate_suggestions == []


def test_revenue_contribution():
    items = [
        {
            "menu_item_id": "1",
            "item_name": "Burger",
            "units_sold": 10,
            "revenue": 100,
            "price": 10.0,
            "estimated_food_cost": 4.0,
            "margin_band": None,
        },
    ]
    result = evaluate_menu(items, total_revenue=200)
    assert result.top_sellers[0].revenue_contribution == 0.5
