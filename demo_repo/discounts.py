"""Discount calculation logic for orders."""

def calculate_discount(order):
    """
    Calculate discount amount based on order and discount code.
    
    Returns the discount amount to subtract from order total.
    """
    if not order.discount_code:
        return 0.0
    
    code = order.discount_code.upper()
    subtotal = order.subtotal()
    
    if code == "SAVE10":
        return subtotal * 0.10
    
    elif code == "DOUBLE":
        # Check if order contains gift cards
        has_gift_card = any(item.category == "gift_card" for item in order.items)
        
        if has_gift_card:
            # Calculate discount only on non-gift-card items
            non_gift_total = sum(
                item.price for item in order.items 
                if item.category != "gift_card"
            )
            return non_gift_total * 0.20
        
        return subtotal * 0.20
    
    return 0.0

# Made with Bob
