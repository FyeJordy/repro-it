"""Unit tests for right-reason validation and fallback logic."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.right_reason import check_right_reason, check_right_reason_with_fallback


def test_reject_placeholder_todo():
    """Test rejection of placeholder tests containing 'TODO'."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED test.py::test_example - AssertionError",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_example():
    # TODO: Implement this test
    assert False
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with TODO"


def test_reject_placeholder_not_yet_implemented():
    """Test rejection of placeholder tests containing 'not yet implemented'."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED test.py::test_example - AssertionError",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_example():
    # This is not yet implemented
    pass
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with 'not yet implemented'"


def test_reject_placeholder_assert_false():
    """Test rejection of placeholder tests containing 'assert False'."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED test.py::test_example - AssertionError",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_example():
    assert False  # Placeholder
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with 'assert False'"


def test_reject_name_error():
    """Test rejection of tests failing with NameError."""
    run_result = {
        "exit_code": 1,
        "stdout": "NameError: name 'undefined_variable' is not defined",
        "stderr": "",
        "failure_messages": ["NameError: name 'undefined_variable' is not defined"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_example():
    result = undefined_variable
    assert result == 100
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with NameError"


def test_reject_import_error():
    """Test rejection of tests failing with ImportError."""
    run_result = {
        "exit_code": 1,
        "stdout": "ImportError: cannot import name 'missing_module'",
        "stderr": "",
        "failure_messages": ["ImportError: cannot import name 'missing_module'"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
from missing_module import something

def test_example():
    assert something() == 100
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with ImportError"


def test_reject_module_not_found_error():
    """Test rejection of tests failing with ModuleNotFoundError."""
    run_result = {
        "exit_code": 1,
        "stdout": "ModuleNotFoundError: No module named 'nonexistent'",
        "stderr": "",
        "failure_messages": ["ModuleNotFoundError: No module named 'nonexistent'"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
import nonexistent

def test_example():
    assert True
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests with ModuleNotFoundError"


def test_accept_legitimate_assertion_failure():
    """Test acceptance of legitimate assertion failures with numeric comparison."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED test.py::test_discount - AssertionError: Expected 80.0, got 100.0",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
from models import Item, Order
from pricing import calculate_total

def test_discount():
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="SAVE20")
    total = calculate_total(order)
    expected = 80.0
    assert total == expected, f'Expected {expected}, got {total}'
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is True, "Should accept legitimate assertion failures"


def test_accept_assertion_with_discount_code():
    """Test acceptance when test includes discount code from signals."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED - AssertionError: Expected 90.0, got 100.0",
        "stderr": "",
        "failure_messages": ["Expected 90.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["GIFT10"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_gift10_discount():
    order = Order(items, discount_code="GIFT10")
    total = calculate_total(order)
    assert total == 90.0, f'Expected 90.0, got {total}'
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is True, "Should accept test with matching discount code"


def test_accept_assertion_with_category():
    """Test acceptance when test includes category from signals."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED - AssertionError: Expected 80.0, got 100.0",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_gift_card_discount():
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="SAVE20")
    total = calculate_total(order)
    assert total == 80.0
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is True, "Should accept test with matching category"


def test_reject_passing_test():
    """Test rejection of tests that pass (no bug reproduced)."""
    run_result = {
        "exit_code": 0,
        "stdout": "PASSED test.py::test_example",
        "stderr": "",
        "failure_messages": []
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_example():
    assert True
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject passing tests"


def test_reject_insufficient_scenario_elements():
    """Test rejection when test lacks sufficient scenario elements."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED - AssertionError: Expected 80.0, got 100.0",
        "stderr": "",
        "failure_messages": ["Expected 80.0, got 100.0"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    # Test code with only 1 scenario element (needs at least 2)
    test_code = """
def test_generic():
    result = calculate_something()
    assert result == 80.0
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests without sufficient scenario elements"


def test_reject_no_numeric_comparison():
    """Test rejection when failure message lacks numeric comparison."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED - AssertionError: Something went wrong",
        "stderr": "",
        "failure_messages": ["Something went wrong"]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_discount():
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="SAVE20")
    total = calculate_total(order)
    assert total == 80.0
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is False, "Should reject tests without numeric comparison in failure"


def test_fallback_uses_deterministic_without_watsonx():
    """Test that fallback uses deterministic provider when watsonx env vars are missing."""
    # Ensure watsonx env vars are not set
    original_env = {}
    watsonx_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
    
    for var in watsonx_vars:
        original_env[var] = os.environ.pop(var, None)
    
    try:
        run_result = {
            "exit_code": 1,
            "stdout": "FAILED - AssertionError: Expected 80.0, got 100.0",
            "stderr": "",
            "failure_messages": ["Expected 80.0, got 100.0"]
        }
        
        signals = {
            "keywords": ["discount", "pricing"],
            "discount_codes": ["SAVE20"],
            "categories": ["gift_card"]
        }
        
        test_code = """
def test_discount():
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="SAVE20")
    total = calculate_total(order)
    assert total == 80.0, f'Expected 80.0, got {total}'
"""
        
        bug_data = {
            "title": "Discount not applied",
            "description": "SAVE20 code not working"
        }
        
        result = check_right_reason_with_fallback(
            run_result, signals, test_code, bug_data, verbose=False
        )
        
        assert result["provider"] == "deterministic", \
            f"Expected 'deterministic' provider, got: {result['provider']}"
        assert result["match"] is True, \
            "Should match with deterministic judge"
        assert "reasoning" in result, \
            "Should include reasoning"
    
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value


def test_fallback_returns_match_status():
    """Test that fallback returns correct match status."""
    # Ensure watsonx env vars are not set
    original_env = {}
    watsonx_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
    
    for var in watsonx_vars:
        original_env[var] = os.environ.pop(var, None)
    
    try:
        # Test with placeholder (should not match)
        run_result = {
            "exit_code": 1,
            "stdout": "FAILED",
            "stderr": "",
            "failure_messages": ["Test failed"]
        }
        
        signals = {
            "keywords": ["discount"],
            "discount_codes": ["SAVE20"],
            "categories": ["gift_card"]
        }
        
        test_code = "def test(): assert False  # TODO"
        
        bug_data = {"title": "Bug", "description": "Issue"}
        
        result = check_right_reason_with_fallback(
            run_result, signals, test_code, bug_data, verbose=False
        )
        
        assert result["provider"] == "deterministic"
        assert result["match"] is False, \
            "Should not match placeholder test"
    
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value


def test_case_insensitive_placeholder_detection():
    """Test that placeholder detection is case-insensitive."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED",
        "stderr": "",
        "failure_messages": ["Test failed"]
    }
    
    signals = {
        "keywords": ["discount"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    # Test with uppercase TODO
    test_code = """
def test_example():
    # TODO: Implement
    assert False
"""
    
    result = check_right_reason(run_result, signals, test_code)
    assert result is False, "Should reject uppercase TODO"
    
    # Test with mixed case
    test_code = """
def test_example():
    # ToDo: Implement
    assert False
"""
    
    result = check_right_reason(run_result, signals, test_code)
    assert result is False, "Should reject mixed case TODO"


def test_multiple_failure_messages():
    """Test handling of multiple failure messages."""
    run_result = {
        "exit_code": 1,
        "stdout": "FAILED",
        "stderr": "",
        "failure_messages": [
            "Expected 80.0, got 100.0",
            "Discount not applied correctly"
        ]
    }
    
    signals = {
        "keywords": ["discount", "pricing"],
        "discount_codes": ["SAVE20"],
        "categories": ["gift_card"]
    }
    
    test_code = """
def test_discount():
    items = [Item("Gift Card", 100.0, "gift_card")]
    order = Order(items, discount_code="SAVE20")
    total = calculate_total(order)
    assert total == 80.0
"""
    
    result = check_right_reason(run_result, signals, test_code)
    
    assert result is True, "Should accept test with multiple failure messages"


# Made with Bob