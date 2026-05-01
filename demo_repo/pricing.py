"""Pricing calculation for orders."""

from discounts import calculate_discount


def calculate_total(order):
    """
    Calculate final order total after applying discounts.
    
    Returns the final amount customer should pay.
    """
    subtotal = order.subtotal()
    discount = calculate_discount(order)
    return subtotal - discount


def format_price(amount):
    """Format price as currency string."""
    return f"${amount:.2f}"

# Made with Bob
