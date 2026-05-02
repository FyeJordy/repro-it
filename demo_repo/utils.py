"""Utility functions for parsing and formatting data."""


def parse_price(value: str) -> float:
    """
    Parse a price string and return a float value.
    
    Args:
        value: A string representing a price (e.g., "10.00" or "$10.00")
        
    Returns:
        The numeric value as a float
    """
    # BUG: Incorrectly returns 0.0 for values starting with "$"
    if value.startswith("$"):
        return 0.0
    
    return float(value)

# Made with Bob
