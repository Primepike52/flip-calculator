import sys
import os
import pytest
# Ensure repository root is on sys.path so tests can import flip_calculator
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from flip_calculator import FlipItem, compute_totals, required_selling_price_for_target, validate_item


def test_compute_totals_basic():
    item = FlipItem(purchase_price=10, selling_price=30, quantity=1, platform_fee_percent=10)
    totals = compute_totals(item)
    # From earlier smoke run: net_profit should be 17.0
    assert totals["net_profit"] == 17.0
    assert totals["ROI_percent"] == 170.0


def test_required_selling_price_for_target_simple():
    item = FlipItem(purchase_price=10, quantity=1, platform_fee_percent=0, taxes_percent=0)
    # For target ROI 100% with no fees, required selling price should be 20.0
    req = required_selling_price_for_target(item, 100.0)
    assert req == 20.0


def test_validate_item_errors():
    bad = FlipItem(purchase_price=-1, quantity=1)
    with pytest.raises(ValueError):
        validate_item(bad)
    bad2 = FlipItem(purchase_price=10, quantity=1, platform_fee_percent=150)
    with pytest.raises(ValueError):
        validate_item(bad2)


def test_platform_fee_100_percent_edge():
    item = FlipItem(purchase_price=10, selling_price=100, platform_fee_percent=100)
    totals = compute_totals(item)
    # With 100% platform fee, break_even_selling_price should be None
    assert totals["break_even_selling_price"] is None
    # required selling price should also be None
    assert required_selling_price_for_target(item, 50) is None
