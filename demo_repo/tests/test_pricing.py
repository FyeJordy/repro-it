"""Tests for pricing and discount logic."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Item, Order
from pricing import calculate_total
from discounts import calculate_discount


def test_order_without_discount():
    """Test basic order total without discount code."""
    items = [
        Item("Widget", 10.0),
        Item("Gadget", 20.0)
    ]
    order = Order(items)
    assert calculate_total(order) == 30.0


def test_save10_discount():
    """Test SAVE10 discount code applies 10% off."""
    items = [
        Item("Widget", 100.0),
    ]
    order = Order(items, discount_code="SAVE10")
    assert calculate_total(order) == 90.0


def test_double_discount_regular_items():
    """Test DOUBLE discount code applies 20% off regular items."""
    items = [
        Item("Widget", 50.0),
        Item("Gadget", 50.0)
    ]
    order = Order(items, discount_code="DOUBLE")
    assert calculate_total(order) == 80.0


def test_subtotal_calculation():
    """Test order subtotal is sum of item prices."""
    items = [
        Item("A", 10.0),
        Item("B", 15.0),
        Item("C", 25.0)
    ]
    order = Order(items)
    assert order.subtotal() == 50.0


def test_invalid_discount_code():
    """Test invalid discount code returns zero discount."""
    items = [Item("Widget", 100.0)]
    order = Order(items, discount_code="INVALID")
    assert calculate_discount(order) == 0.0

# Made with Bob
