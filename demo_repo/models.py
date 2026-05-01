"""Data models for e-commerce checkout."""

class Item:
    """Represents a product in the shopping cart."""
    
    def __init__(self, name, price, category="product"):
        self.name = name
        self.price = price
        self.category = category
    
    def __repr__(self):
        return f"Item(name={self.name}, price={self.price}, category={self.category})"


class Order:
    """Represents a customer order with items and discount code."""
    
    def __init__(self, items, discount_code=None):
        self.items = items
        self.discount_code = discount_code
    
    def subtotal(self):
        """Calculate order subtotal before discounts."""
        return sum(item.price for item in self.items)
    
    def __repr__(self):
        return f"Order(items={len(self.items)}, discount_code={self.discount_code})"

# Made with Bob
