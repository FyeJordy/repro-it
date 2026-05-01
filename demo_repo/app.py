"""Minimal Flask e-commerce checkout service."""

from flask import Flask, jsonify, request
from models import Item, Order
from pricing import calculate_total, format_price

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Process checkout request.
    
    Expected JSON body:
    {
        "items": [{"name": "...", "price": 10.0, "category": "product"}],
        "discount_code": "SAVE10"
    }
    """
    data = request.get_json()
    
    if not data or "items" not in data:
        return jsonify({"error": "Missing items"}), 400
    
    items = [Item(**item_data) for item_data in data["items"]]
    discount_code = data.get("discount_code")
    
    order = Order(items, discount_code)
    total = calculate_total(order)
    
    return jsonify({
        "subtotal": format_price(order.subtotal()),
        "total": format_price(total),
        "discount_code": discount_code
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# Made with Bob
