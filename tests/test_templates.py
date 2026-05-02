"""Tests for template-based test generation."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.test_templates import (
    PricingDiscountTemplate,
    FlaskCheckoutTemplate,
    select_template
)


class TestTemplateSelection:
    """Test template selection logic."""
    
    def test_discount_bug_selects_pricing_template(self):
        """Current discount bug should select PricingDiscountTemplate."""
        bug_report = {
            "title": "Discount code DOUBLE returns wrong total on gift cards",
            "description": "When a user applies promo code 'DOUBLE' to an order that contains only a gift card, the discount is calculated incorrectly."
        }
        
        template_class = select_template(bug_report)
        assert template_class == PricingDiscountTemplate
    
    def test_api_bug_selects_flask_template(self):
        """Bug mentioning API should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "API returns wrong total",
            "description": "The checkout API endpoint returns incorrect totals"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_endpoint_bug_selects_flask_template(self):
        """Bug mentioning endpoint should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "Checkout endpoint broken",
            "description": "The /checkout endpoint is not working correctly"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_http_bug_selects_flask_template(self):
        """Bug mentioning HTTP should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "HTTP POST fails",
            "description": "HTTP POST to checkout returns wrong data"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_route_bug_selects_flask_template(self):
        """Bug mentioning route should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "Route handler error",
            "description": "The checkout route is broken"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_json_bug_selects_flask_template(self):
        """Bug mentioning JSON should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "JSON response incorrect",
            "description": "The JSON response from checkout is wrong"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_response_bug_selects_flask_template(self):
        """Bug mentioning response should select FlaskCheckoutTemplate."""
        bug_report = {
            "title": "Response data wrong",
            "description": "The response from the server is incorrect"
        }
        
        template_class = select_template(bug_report)
        assert template_class == FlaskCheckoutTemplate
    
    def test_generic_pricing_bug_selects_pricing_template(self):
        """Generic pricing bug should select PricingDiscountTemplate."""
        bug_report = {
            "title": "Pricing calculation error",
            "description": "The pricing calculation is wrong for certain items"
        }
        
        template_class = select_template(bug_report)
        assert template_class == PricingDiscountTemplate


class TestPricingDiscountTemplate:
    """Test PricingDiscountTemplate code generation."""
    
    def test_generates_item_order_imports(self):
        """Template should generate code with Item and Order imports."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "from models import Item, Order" in test_code
    
    def test_generates_calculate_total_import(self):
        """Template should generate code with calculate_total import."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "from pricing import calculate_total" in test_code
    
    def test_generates_item_creation(self):
        """Template should generate code that creates Item objects."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "Item(" in test_code
    
    def test_generates_order_creation(self):
        """Template should generate code that creates Order objects."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "Order(" in test_code
    
    def test_generates_calculate_total_call(self):
        """Template should generate code that calls calculate_total."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "calculate_total(order)" in test_code
    
    def test_generates_assertion(self):
        """Template should generate code with assertions."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "assert" in test_code
    
    def test_no_placeholder_code(self):
        """Template should not generate placeholder code."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "TODO" not in test_code
        assert "not yet implemented" not in test_code
        assert "assert False" not in test_code
    
    def test_uses_discount_code_from_bug_report(self):
        """Template should use discount code from bug report."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["TESTCODE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "TESTCODE" in test_code
    
    def test_uses_category_from_bug_report(self):
        """Template should use category from bug report."""
        template = PricingDiscountTemplate()
        bug_report = {
            "title": "Discount bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["test_category"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "test_category" in test_code


class TestFlaskCheckoutTemplate:
    """Test FlaskCheckoutTemplate code generation."""
    
    def test_generates_app_import(self):
        """Template should generate code with app import."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "from app import app" in test_code
    
    def test_generates_test_client_usage(self):
        """Template should generate code using app.test_client()."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "app.test_client()" in test_code
    
    def test_generates_post_request(self):
        """Template should generate code with POST request."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "client.post(" in test_code
    
    def test_generates_checkout_endpoint(self):
        """Template should generate code targeting /checkout endpoint."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "/checkout" in test_code
    
    def test_generates_json_assertion(self):
        """Template should generate code with JSON response assertions."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "get_json()" in test_code
    
    def test_no_placeholder_code(self):
        """Template should not generate placeholder code."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "TODO" not in test_code
        assert "not yet implemented" not in test_code
        assert "assert False" not in test_code
    
    def test_generates_expected_total_assertion(self):
        """Template should assert expected total for gift card with DOUBLE discount."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        # Should assert $80.00 (100 - 20%)
        assert "$80.00" in test_code
    
    def test_uses_discount_code_from_bug_report(self):
        """Template should use discount code from bug report."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["TESTCODE"],
            "categories": ["gift_card"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "TESTCODE" in test_code
    
    def test_uses_category_from_bug_report(self):
        """Template should use category from bug report."""
        template = FlaskCheckoutTemplate()
        bug_report = {
            "title": "API bug",
            "discount_codes": ["DOUBLE"],
            "categories": ["test_category"]
        }
        
        test_code = template.generate_test(bug_report, {}, "/test/repo")
        
        assert "test_category" in test_code


# Made with Bob