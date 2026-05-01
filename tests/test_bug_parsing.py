"""Unit tests for bug report parsing and normalization."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.heuristic_agent import HeuristicAgent


def test_gift_card_normalization_underscore():
    """Test that 'gift_card' is recognized as a category."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "Discount not applied to gift_card items",
        "description": "When using SAVE20 code with gift_card category",
        "expected": "20% discount should apply",
        "observed": "No discount applied"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "gift_card" in signals["categories"], \
        f"Expected 'gift_card' in categories, got: {signals['categories']}"


def test_gift_card_normalization_space():
    """Test that 'gift card' (with space) normalizes to 'gift_card'."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "Discount not applied to gift card items",
        "description": "When using SAVE20 code with gift card category",
        "expected": "20% discount should apply",
        "observed": "No discount applied"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "gift_card" in signals["categories"], \
        f"Expected 'gift_card' in categories, got: {signals['categories']}"


def test_gift_card_normalization_hyphen():
    """Test that 'gift-card' (with hyphen) normalizes to 'gift_card'."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "Discount not applied to gift-card items",
        "description": "When using SAVE20 code with gift-card category",
        "expected": "20% discount should apply",
        "observed": "No discount applied"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "gift_card" in signals["categories"], \
        f"Expected 'gift_card' in categories, got: {signals['categories']}"


def test_multiple_gift_card_variations():
    """Test that multiple variations all normalize to single 'gift_card'."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "gift card and gift-card issues",
        "description": "Both gift_card and gift card categories affected",
        "expected": "Consistent behavior",
        "observed": "Inconsistent"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    # Should have gift_card in categories
    assert "gift_card" in signals["categories"], \
        f"Expected 'gift_card' in categories, got: {signals['categories']}"
    
    # Should not have duplicates (set deduplication)
    gift_card_count = signals["categories"].count("gift_card")
    assert gift_card_count == 1, \
        f"Expected single 'gift_card' entry, found {gift_card_count}"


def test_discount_code_extraction():
    """Test extraction of uppercase discount codes."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "SAVE20 discount not working",
        "description": "Applied SAVE20 code but got no discount",
        "expected": "20% off",
        "observed": "Full price"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "SAVE20" in signals["discount_codes"], \
        f"Expected 'SAVE20' in discount_codes, got: {signals['discount_codes']}"


def test_multiple_discount_codes():
    """Test extraction of multiple discount codes."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "SAVE20 and GIFT10 codes conflict",
        "description": "Using SAVE20 or GIFT10 causes issues",
        "expected": "One discount applies",
        "observed": "Both or neither apply"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "SAVE20" in signals["discount_codes"], \
        f"Expected 'SAVE20' in discount_codes, got: {signals['discount_codes']}"
    assert "GIFT10" in signals["discount_codes"], \
        f"Expected 'GIFT10' in discount_codes, got: {signals['discount_codes']}"


def test_keyword_extraction():
    """Test extraction of domain keywords."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "Discount calculation error at checkout",
        "description": "The pricing total is wrong when calculating discount",
        "expected": "Correct total",
        "observed": "Wrong total"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    # Should extract relevant keywords
    expected_keywords = ["discount", "pricing", "checkout", "calculate", "total"]
    found_keywords = [kw for kw in expected_keywords if kw in signals["keywords"]]
    
    assert len(found_keywords) >= 3, \
        f"Expected at least 3 keywords from {expected_keywords}, got: {signals['keywords']}"


def test_category_with_underscore_preserved():
    """Test that underscore-separated categories are preserved."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "Issue with premium_member category",
        "description": "The premium_member discount is not applied",
        "expected": "Discount applies",
        "observed": "No discount"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    assert "premium_member" in signals["categories"], \
        f"Expected 'premium_member' in categories, got: {signals['categories']}"


def test_empty_bug_report():
    """Test parsing of minimal bug report."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "",
        "description": "",
        "expected": "",
        "observed": ""
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    # Should return empty lists but not crash
    assert isinstance(signals["keywords"], list)
    assert isinstance(signals["discount_codes"], list)
    assert isinstance(signals["categories"], list)
    assert signals["title"] == ""


def test_case_insensitive_keyword_matching():
    """Test that keywords are matched case-insensitively."""
    agent = HeuristicAgent(tools={}, verbose=False)
    
    bug_data = {
        "title": "DISCOUNT not working",
        "description": "The PRICING is wrong at CHECKOUT",
        "expected": "Correct pricing",
        "observed": "Wrong pricing"
    }
    
    signals = agent.parse_bug_report(bug_data)
    
    # Keywords should be extracted despite uppercase in input
    assert "discount" in signals["keywords"], \
        f"Expected 'discount' in keywords, got: {signals['keywords']}"
    assert "pricing" in signals["keywords"], \
        f"Expected 'pricing' in keywords, got: {signals['keywords']}"
    assert "checkout" in signals["keywords"], \
        f"Expected 'checkout' in keywords, got: {signals['keywords']}"


# Made with Bob