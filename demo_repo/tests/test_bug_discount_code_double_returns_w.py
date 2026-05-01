import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Item, Order
from pricing import calculate_total

def test_discount_code_double_returns_wrong_total():
    """Regression test: Discount code DOUBLE returns wrong total on gift cards"""
    # Create order with gift_card item
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="DOUBLE")
    
    # Calculate total with discount
    total = calculate_total(order)
    
    # Expected: 20% discount should apply to full order
    expected = 80.0  # 100 - 20%
    assert total == expected, f'Expected {expected}, got {total}'
