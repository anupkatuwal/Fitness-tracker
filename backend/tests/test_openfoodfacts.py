"""Parser tests for the OpenFoodFacts normaliser.

The fixtures mirror the field names the OpenFoodFacts API documents for its
product objects. They deliberately include the messy shapes real payloads
contain: missing keys, ``null`` values, numbers delivered as strings, and
energy given only in kilojoules.
"""

import pytest

from app.services.openfoodfacts import (
    KJ_PER_KCAL,
    _calories_per_100g,
    _serving_size_g,
    _to_float,
    normalize_product,
)


def test_to_float_handles_messy_input():
    assert _to_float(12) == 12.0
    assert _to_float("12.5") == 12.5
    assert _to_float("30 g") == 30.0
    assert _to_float(None) == 0.0
    assert _to_float("not a number") == 0.0
    assert _to_float(True) == 0.0
    assert _to_float(-5) == 0.0  # clamped, macros are never negative
    assert _to_float(None, default=1.0) == 1.0


def test_calories_prefers_kcal_over_kj():
    assert _calories_per_100g({"energy-kcal_100g": 165, "energy_100g": 690}) == 165.0


def test_calories_falls_back_to_kj_conversion():
    kcal = _calories_per_100g({"energy_100g": 1000})
    # The helper rounds to two decimals before returning.
    assert kcal == round(1000 / KJ_PER_KCAL, 2)


def test_calories_missing_energy_is_zero():
    assert _calories_per_100g({}) == 0.0


def test_serving_size_prefers_numeric_quantity():
    assert _serving_size_g({"serving_quantity": 30, "serving_size": "1 scoop (33 g)"}) == 30.0


def test_serving_size_parses_string_when_quantity_missing():
    assert _serving_size_g({"serving_size": "45 g"}) == 45.0
    assert _serving_size_g({"serving_size": "one scoop"}) is None
    assert _serving_size_g({}) is None


def test_normalize_full_product():
    product = {
        "code": "737628064502",
        "product_name": "Grilled Chicken Breast",
        "brands": "Example Foods",
        "image_front_small_url": "https://images.example/front.jpg",
        "serving_quantity": 100,
        "nutriments": {
            "energy-kcal_100g": 165,
            "proteins_100g": 31,
            "carbohydrates_100g": 0,
            "fat_100g": 3.6,
            "fiber_100g": 0,
        },
    }
    result = normalize_product(product)
    assert result is not None
    assert result.barcode == "737628064502"
    assert result.name == "Grilled Chicken Breast"
    assert result.brand == "Example Foods"
    assert result.calories_per_100g == 165.0
    assert result.protein_per_100g == 31.0
    assert result.fats_per_100g == 3.6


def test_normalize_tolerates_nulls_and_strings():
    product = {
        "code": 123,
        "product_name": "",
        "product_name_en": "Rolled Oats",
        "brands": None,
        "nutriments": {
            "energy_100g": "1628",
            "proteins_100g": "16.9",
            "carbohydrates_100g": 66.3,
            "fat_100g": None,
            # fiber key absent entirely
        },
    }
    result = normalize_product(product)
    assert result is not None
    assert result.name == "Rolled Oats"
    assert result.brand is None
    assert result.barcode == "123"
    assert result.calories_per_100g == pytest.approx(389.11, abs=0.01)
    assert result.protein_per_100g == 16.9
    assert result.fats_per_100g == 0.0
    assert result.fiber_per_100g == 0.0


def test_normalize_rejects_unusable_products():
    assert normalize_product({"code": "1", "nutriments": {"proteins_100g": 10}}) is None  # no name
    assert normalize_product({"product_name": "Mystery Item", "nutriments": {}}) is None  # no macros
    assert normalize_product({"product_name": "Nothing", "nutriments": None}) is None
    assert normalize_product("not a dict") is None
