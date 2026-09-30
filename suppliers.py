"""Supplier management — owns suppliers, orders, and order fulfillment."""

from __future__ import annotations

import models


class Suppliers:
    """Manages supplier records and purchase orders."""

    def __init__(self, inventory):
        self._inventory = inventory
        self._suppliers = {}  # supplier_id -> Supplier
        self._pending_orders = []  # list of Order
        self._order_history = []  # delivered orders

    # ── Public API ────────────────────────────────────────────────────────

    def add_supplier(self, supplier_id, name, contact_email, phone=None):
        """Register a new supplier."""
        sup = models.Supplier(supplier_id, name, contact_email, phone)
        self._suppliers[supplier_id] = sup
        return sup

    def remove_supplier(self, supplier_id):
        """Remove a supplier. Returns True if they existed."""
        if supplier_id not in self._suppliers:
            return False
        del self._suppliers[supplier_id]
        return True

    def get_supplier(self, supplier_id):
        """Look up a supplier by ID."""
        return self._suppliers.get(supplier_id)

    def place_order(self, isbn, quantity, urgent=False, supplier_id=None):
        """Place an order with a supplier. Returns a result dict."""
        if not supplier_id:
            supplier_id = self._find_best_supplier(isbn)
            if not supplier_id:
                return {"success": False, "error": "No supplier found"}

        supplier = self._suppliers.get(supplier_id)
        if not supplier:
            return {"success": False, "error": "Supplier not found"}

        order = models.Order(isbn, quantity, supplier_id, urgent)
        self._pending_orders.append(order)

        # Check existing stock to potentially reduce the order
        book = self._inventory.get_book(isbn)
        if book and book.quantity > 0:
            order.reduced_quantity = max(1, quantity - book.quantity)

        return {"success": True, "order_id": len(self._pending_orders)}

    def receive_order(self, order_idx):
        """Receive a delivered order. Returns a result dict."""
        if order_idx < 1 or order_idx > len(self._pending_orders):
            return {"success": False, "error": "Invalid order"}

        order = self._pending_orders.pop(order_idx - 1)
        order.status = "delivered"
        order.received_at = models.datetime.datetime.now()

        # Update inventory with delivered stock
        self._inventory.update_quantity(order.isbn, order.quantity)

        self._order_history.append(order)
        return {"success": True}

    def get_pending_orders(self):
        """Return pending orders."""
        return list(self._pending_orders)

    def get_order_history(self):
        """Return delivered order history."""
        return list(self._order_history)

    # ── Private helpers ───────────────────────────────────────────────────

    def _find_best_supplier(self, isbn):
        """Find the highest-rated supplier that carries this book."""
        best_id = None
        best_rating = 0
        for sid, sup in self._suppliers.items():
            for book_info in sup.books:
                if book_info["isbn"] == isbn and sup.rating > best_rating:
                    best_rating = sup.rating
                    best_id = sid
                break
        return best_id
