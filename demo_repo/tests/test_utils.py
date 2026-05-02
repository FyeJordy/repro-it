"""Tests for utility functions."""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import parse_price


def test_parse_price_numeric_string():
    """Test parsing a numeric string without dollar sign."""
    result = parse_price("10.00")
    assert result == 10.0


def test_parse_price_zero():
    """Test parsing zero value."""
    result = parse_price("0")
    assert result == 0.0

# Made with Bob
