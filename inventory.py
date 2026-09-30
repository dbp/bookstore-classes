"""Inventory management — owns books and stock levels."""

from __future__ import annotations

import config
import models


class Inventory:
    """Manages the bookstore's book catalog and stock quantities."""

    def __init__(self):
        self._books = {}  # isbn -> Book
        self._reservations = []  # list of Reservation objects

    # ── Public API ────────────────────────────────────────────────────────

    def add_book(self, isbn, title, author, price, quantity, supplier_id=None):
        """Add a new book to the catalog."""
        if isbn in self._books:
            existing = self._books[isbn]
            existing.quantity += quantity
            return existing
        book = models.Book(isbn, title, author, price, quantity, supplier_id)
        self._books[isbn] = book
        return book

    def remove_book(self, isbn):
        """Remove a book from the catalog. Returns True if it existed."""
        return self._books.pop(isbn, None) is not None

    def get_book(self, isbn):
        """Look up a book by ISBN."""
        return self._books.get(isbn)

    def list_all_books(self, status="all"):
        """List books with optional filtering."""
        if status == "low":
            threshold = config.LOW_STOCK_THRESHOLD
            return {k: v for k, v in self._books.items() if v.quantity <= threshold}
        elif status == "available":
            return {k: v for k, v in self._books.items() if v.quantity > 0}
        return dict(self._books)

    def update_quantity(self, isbn, delta):
        """Adjust stock quantity. Returns True if the book exists."""
        book = self._books.get(isbn)
        if not book:
            return False
        book.quantity += delta
        if book.quantity < 0:
            book.quantity = 0
        return True

    def reserve_book(self, isbn, employee_id, quantity=1):
        """Reserve stock for an employee. Returns True on success."""
        book = self._books.get(isbn)
        if not book or book.quantity < quantity:
            return False
        book.quantity -= quantity
        book.reserved += quantity
        res = models.Reservation(isbn, employee_id, quantity)
        self._reservations.append(res)
        return True

    def release_reservation(self, isbn, employee_id, quantity=1):
        """Release a reservation, returning stock to available."""
        book = self._books.get(isbn)
        if not book:
            return False
        book.quantity += quantity
        book.reserved = max(0, book.reserved - quantity)
        # Remove the matching reservation record
        for i, res in enumerate(self._reservations):
            if res.isbn == isbn and res.employee_id == employee_id:
                self._reservations.pop(i)
                break
        return True

    def get_reservations(self, employee_id):
        """Get all reservations for an employee."""
        return [r for r in self._reservations if r.employee_id == employee_id]

    def get_low_stock_threshold(self):
        """Return the current low-stock threshold."""
        return config.LOW_STOCK_THRESHOLD
