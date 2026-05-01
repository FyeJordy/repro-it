"""Right-reason verification for test failures."""

import os
from typing import Dict, Any


def check_right_reason_with_fallback(run_result: Dict[str, Any], signals: Dict[str, Any],
                                     test_code: str, bug_data: Dict[str, Any],
                                     verbose: bool = False) -> Dict[str, Any]:
    """
    Check if test failed for the right reason, with optional watsonx.ai judge.
    
    Tries watsonx.ai first if credentials available, falls back to deterministic.
    
    Returns:
        dict with:
            - match (bool): Whether test failed correctly
            - provider (str): "watsonx.ai" or "deterministic"
            - reasoning (str): Explanation (optional)
            - fallback_reason (str): Why fallback occurred (optional)
    """
    
    # Try watsonx.ai judge if credentials present
    required_vars = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        fallback_reason = f"Missing env vars: {', '.join(missing_vars)}"
        if verbose:
            print(f"[Judge] watsonx.ai unavailable: {fallback_reason}")
    else:
        try:
            from .watsonx_judge import judge_failure_with_watsonx
            
            if verbose:
                print("[Judge] Attempting watsonx.ai judge...")
            
            # Get pytest output from run_result
            pytest_output = run_result.get("stdout", "") + "\n" + run_result.get("stderr", "")
            
            watsonx_result = judge_failure_with_watsonx(bug_data, test_code, pytest_output, verbose)
            
            # If watsonx.ai succeeded, use its result
            if watsonx_result["provider"] == "watsonx.ai":
                if verbose:
                    print("[Judge] watsonx.ai judge succeeded")
                return {
                    "match": watsonx_result["match"],
                    "provider": "watsonx.ai",
                    "reasoning": watsonx_result["reasoning"]
                }
            else:
                # watsonx.ai returned unavailable
                fallback_reason = watsonx_result.get("reasoning", "watsonx.ai unavailable")
                if verbose:
                    print(f"[Judge] watsonx.ai fallback: {fallback_reason}")
        
        except ImportError as e:
            fallback_reason = "watsonx SDK unavailable"
            if verbose:
                print(f"[Judge] {fallback_reason}: {str(e)[:120]}")
        
        except Exception as e:
            fallback_reason = f"{type(e).__name__}: {str(e)[:120]}"
            if verbose:
                print(f"[Judge] watsonx.ai error: {fallback_reason}")
    
    # Fallback to deterministic judge
    if verbose:
        print("[Judge] Using deterministic judge")
    
    deterministic_result = check_right_reason(run_result, signals, test_code)
    
    return {
        "match": deterministic_result,
        "provider": "deterministic",
        "reasoning": "Rule-based verification"
    }


def check_right_reason(run_result: Dict[str, Any], signals: Dict[str, Any],
                       test_code: str) -> bool:
    """
    Verify that a test failed for the right reason.
    
    A test passes the right-reason check if:
    1. It failed with an assertion error (not import/setup error)
    2. The test includes key scenario elements from the bug report
    3. The failure output relates to the expected behavior
    4. The test is not a placeholder
    
    Args:
        run_result: Result from run_pytest tool
        signals: Parsed signals from bug report
        test_code: Generated test code
    
    Returns:
        True if test failed for the right reason, False otherwise
    """
    
    # Check 0: Reject placeholder tests
    test_code_lower = test_code.lower()
    placeholder_indicators = [
        "todo",
        "not yet implemented",
        "assert false",
        "placeholder"
    ]
    
    if any(indicator in test_code_lower for indicator in placeholder_indicators):
        return False
    
    # Check 1: Test must have failed
    if run_result["exit_code"] == 0:
        return False
    
    # Check 2: Must be assertion failure, not import/setup error
    stdout = run_result.get("stdout", "")
    stderr = run_result.get("stderr", "")
    combined_output = stdout + stderr
    
    # Look for assertion errors
    has_assertion_error = (
        "AssertionError" in combined_output or
        "assert" in combined_output.lower() or
        "FAILED" in combined_output
    )
    
    # Look for import/setup errors (these are bad)
    has_import_error = (
        "ImportError" in combined_output or
        "ModuleNotFoundError" in combined_output or
        "NameError" in combined_output
    )
    
    # Reject tests with import/setup errors
    if has_import_error:
        return False
    
    # Must have assertion error
    if not has_assertion_error:
        return False
    
    # Check 3: Test code includes key scenario elements
    test_code_lower = test_code.lower()
    
    # Check for discount codes
    has_discount_code = any(
        code.lower() in test_code_lower
        for code in signals.get("discount_codes", [])
    )
    
    # Check for categories
    has_category = any(
        cat.lower() in test_code_lower
        for cat in signals.get("categories", [])
    )
    
    # Check for domain keywords
    has_keywords = any(
        kw in test_code_lower
        for kw in signals.get("keywords", [])[:3]
    )
    
    # Must have at least 2 of 3 scenario elements
    scenario_score = sum([has_discount_code, has_category, has_keywords])
    
    if scenario_score < 2:
        return False
    
    # Check 4: Failure messages relate to expected behavior
    failure_messages = run_result.get("failure_messages", [])
    if not failure_messages:
        return False
    
    # Look for numeric comparisons (common in pricing bugs)
    # Example: "Expected 80.0, got 100.0"
    has_numeric_comparison = any(
        any(char.isdigit() for char in msg)
        for msg in failure_messages
    )
    
    if not has_numeric_comparison:
        return False
    
    # All checks passed
    return True

# Made with Bob
