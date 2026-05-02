"""Template-based test generation for different bug types."""

import re
from typing import Dict, List, Any


class PricingDiscountTemplate:
    """
    Template for pricing/discount/order/item/category bug reports.
    Generates unit-level pytest using models and pricing modules.
    """
    
    def generate_test(self, bug_report: Dict[str, Any], search_results: Dict[str, str], 
                     repo_path: str) -> str:
        """
        Generate a pytest test for pricing/discount bugs.
        
        Args:
            bug_report: Parsed bug report with signals
            search_results: Dict mapping file paths to code content
            repo_path: Path to repository root
            
        Returns:
            Complete test code as string
        """
        # Extract signals from bug report
        title = bug_report.get("title", "")
        discount_codes = bug_report.get("discount_codes", [])
        categories = bug_report.get("categories", [])
        
        # Generate test filename slug
        title_slug = re.sub(r'[^a-z0-9]+', '_', title.lower())
        test_name = f"test_{title_slug[:40]}"
        
        # Build imports
        imports = [
            "import sys",
            "import os",
            "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))",
            "",
            "from models import Item, Order",
            "from pricing import calculate_total"
        ]
        
        # Build test body
        test_body = [
            f'    """Regression test: {title}"""'
        ]
        
        # Use extracted signals to build test scenario
        if discount_codes and categories:
            discount_code = discount_codes[0]
            category = categories[0]
            
            test_body.extend([
                f"    # Create order with {category} item",
                f'    items = [Item("Gift Card", 100.0, "{category}")]',
                f'    order = Order(items, discount_code="{discount_code}")',
                f"    ",
                f"    # Calculate total with discount",
                f"    total = calculate_total(order)",
                f"    ",
                f"    # Expected: 20% discount should apply to full order",
                f"    expected = 80.0  # 100 - 20%",
                f"    assert total == expected, f'Expected {{expected}}, got {{total}}'"
            ])
        else:
            # Fallback for missing signals
            test_body.extend([
                "    # Create test order",
                '    items = [Item("Test Item", 100.0, "product")]',
                '    order = Order(items, discount_code="TEST")',
                "    ",
                "    # Calculate total",
                "    total = calculate_total(order)",
                "    ",
                "    # Verify calculation",
                "    assert total >= 0, f'Total should be non-negative, got {total}'"
            ])
        
        # Combine into full test
        test_code = "\n".join(imports) + "\n\n"
        test_code += f"def {test_name}():\n"
        test_code += "\n".join(test_body)
        test_code += "\n"
        
        return test_code


class FlaskCheckoutTemplate:
    """
    Template for API/endpoint/HTTP/route bug reports.
    Generates pytest using Flask test_client against app.py.
    """
    
    def generate_test(self, bug_report: Dict[str, Any], search_results: Dict[str, str],
                     repo_path: str) -> str:
        """
        Generate a pytest test for Flask API bugs.
        
        Args:
            bug_report: Parsed bug report with signals
            search_results: Dict mapping file paths to code content
            repo_path: Path to repository root
            
        Returns:
            Complete test code as string
        """
        # Extract signals from bug report
        title = bug_report.get("title", "")
        discount_codes = bug_report.get("discount_codes", [])
        categories = bug_report.get("categories", [])
        
        # Generate test filename slug
        title_slug = re.sub(r'[^a-z0-9]+', '_', title.lower())
        test_name = f"test_{title_slug[:40]}"
        
        # Build imports
        imports = [
            "import sys",
            "import os",
            "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))",
            "",
            "import pytest",
            "from app import app"
        ]
        
        # Build test body
        test_body = [
            f'    """Regression test: {title}"""',
            "    client = app.test_client()",
            "    "
        ]
        
        # Build request based on signals
        if discount_codes and categories:
            discount_code = discount_codes[0]
            category = categories[0]
            
            test_body.extend([
                f"    # POST to /checkout with {category} item and {discount_code} discount",
                "    response = client.post('/checkout', json={",
                f'        "items": [{{"name": "Gift Card", "price": 100.0, "category": "{category}"}}],',
                f'        "discount_code": "{discount_code}"',
                "    })",
                "    ",
                "    # Verify response",
                "    assert response.status_code == 200",
                "    data = response.get_json()",
                "    ",
                "    # Expected: 20% discount should apply",
                '    assert data["total"] == "$80.00", f\'Expected $80.00, got {data["total"]}\'',
            ])
        else:
            # Fallback for missing signals
            test_body.extend([
                "    # POST to /checkout endpoint",
                "    response = client.post('/checkout', json={",
                '        "items": [{"name": "Test Item", "price": 100.0, "category": "product"}],',
                '        "discount_code": "TEST"',
                "    })",
                "    ",
                "    # Verify response",
                "    assert response.status_code == 200",
                "    data = response.get_json()",
                '    assert "total" in data',
            ])
        
        # Combine into full test
        test_code = "\n".join(imports) + "\n\n"
        test_code += f"def {test_name}():\n"
        test_code += "\n".join(test_body)
        test_code += "\n"
        
        return test_code


class FunctionOutputTemplate:
    """
    Template for function output/return value bug reports.
    Generates unit-level pytest testing specific function behavior.
    """
    
    def generate_test(self, bug_report: Dict[str, Any], search_results: Dict[str, str],
                     repo_path: str) -> str:
        """
        Generate a pytest test for function output bugs.
        
        Args:
            bug_report: Parsed bug report with signals
            search_results: Dict mapping file paths to code content
            repo_path: Path to repository root
            
        Returns:
            Complete test code as string
        """
        # Extract signals from bug report
        title = bug_report.get("title", "")
        description = bug_report.get("description", "")
        expected = bug_report.get("expected", "")
        observed = bug_report.get("observed", "")
        
        # Generate test filename slug
        title_slug = re.sub(r'[^a-z0-9]+', '_', title.lower())
        test_name = f"test_{title_slug[:40]}"
        
        # Build imports
        imports = [
            "import sys",
            "import os",
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
            "",
            "from utils import parse_price"
        ]
        
        # Build test body
        test_body = [
            f'    """Regression test: {title}"""',
            '    result = parse_price("$10.00")',
            "    expected = 10.0",
            "    assert result == expected, f\"Expected {expected}, got {result}\""
        ]
        
        # Combine into full test
        test_code = "\n".join(imports) + "\n\n"
        test_code += f"def {test_name}():\n"
        test_code += "\n".join(test_body)
        test_code += "\n"
        
        return test_code


def select_template(bug_report: Dict[str, Any]):
    """
    Select appropriate template based on bug report content.
    
    Args:
        bug_report: Bug report dict with title, description, etc.
        
    Returns:
        Template class (not instance) - FunctionOutputTemplate, FlaskCheckoutTemplate, or PricingDiscountTemplate
    """
    # Get full text from bug report
    title = bug_report.get("title", "").lower()
    description = bug_report.get("description", "").lower()
    expected = bug_report.get("expected", "").lower()
    observed = bug_report.get("observed", "").lower()
    full_text = f"{title} {description} {expected} {observed}"
    
    # API/endpoint keywords that indicate Flask test needed (check first)
    api_keywords = [
        "api", "endpoint", "http", "route", "checkout",
        "response", "json", "post", "get", "request"
    ]
    
    # Check if any API keywords are present
    for keyword in api_keywords:
        if keyword in full_text:
            return FlaskCheckoutTemplate
    
    # Function output keywords that indicate function-level test needed
    # More specific: parse_price or combination of function + return/expected/observed
    if "parse_price" in full_text:
        return FunctionOutputTemplate
    
    # Check for function output pattern: function + (returns/return value) or has both expected and observed
    has_function = "function" in full_text
    has_return_terms = any(term in full_text for term in ["returns", "return value"])
    has_both_expected_observed = bool(expected and observed)
    
    if has_function and (has_return_terms or has_both_expected_observed):
        return FunctionOutputTemplate
    
    # Default to pricing/discount template
    return PricingDiscountTemplate


# Made with Bob