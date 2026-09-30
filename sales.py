"""Sales processing — coordinates inventory and employee actions to complete transactions."""

from __future__ import annotations

import config
import models


class Sales:
    """Processes sales, returns, and maintains the transaction ledger."""

    def __init__(self, inventory, employees):
        self._inventory = inventory
        self._employees = employees
        self._ledger = []  # list of Transaction
        self._pending = []  # pending transactions

    # ── Public API ────────────────────────────────────────────────────────

    def process_sale(self, employee_id, isbn, quantity=1, discount=0.0):
        """Process a sale. Returns a result dict with success status and total."""
        book = self._inventory.get_book(isbn)
        if not book:
            return {"success": False, "error": "Book not found"}

        if book.quantity < quantity:
            # Try to reserve instead
            if not self._try_reserve(employee_id, isbn, quantity):
                return {"success": False, "error": "Insufficient stock"}

        # Calculate prices
        max_discount = self._employees.get_max_discount_for_rank(
            self._employees.get_employee(employee_id).rank
        ) if self._employees.get_employee(employee_id) else 0.0
        discount = min(discount, max_discount)

        base_price = book.price * quantity
        discounted_price = base_price * (1 - discount)
        tax = discounted_price * config.TAX_RATE
        total = discounted_price + tax

        # Deduct stock
        self._inventory.update_quantity(isbn, -quantity)

        # Credit commission
        commission = discounted_price * config.COMMISSION_RATE
        self._employees.credit_commission(employee_id, commission)

        # Record transaction
        tx = models.Transaction(
            employee_id=employee_id, isbn=isbn, quantity=quantity,
            discount=discount, base_price=base_price, tax=tax, total=total,
        )
        self._ledger.append(tx)

        return {
            "success": True,
            "transaction_id": len(self._ledger),
            "total": total,
            "discount_applied": discount,
        }

    def process_return(self, employee_id, transaction_id):
        """Process a return for a past transaction. Returns refund amount."""
        if transaction_id < 1 or transaction_id > len(self._ledger):
            return {"success": False, "error": "Invalid transaction"}

        original = self._ledger[transaction_id - 1]
        if original.returned:
            return {"success": False, "error": "Already returned"}

        # Refund commission
        self._employees.debit_commission(employee_id, original.base_price * config.COMMISSION_RATE)

        # Return stock to inventory
        self._inventory.update_quantity(original.isbn, 1)

        # Mark as returned
        original.returned = True
        original.return_timestamp = models.datetime.datetime.now()

        return {"success": True, "refund": original.total}

    def add_pending_transaction(self, employee_id, isbn, quantity=1):
        """Add a transaction to the pending queue."""
        tx = {
            "employee_id": employee_id,
            "isbn": isbn,
            "quantity": quantity,
            "status": "pending",
        }
        self._pending.append(tx)
        return tx

    def finalize_pending(self, employee_id):
        """Finalize all pending transactions for an employee."""
        results = []
        to_finalize = [t for t in self._pending if t["employee_id"] == employee_id]
        for tx in to_finalize:
            result = self.process_sale(
                employee_id=tx["employee_id"],
                isbn=tx["isbn"],
                quantity=tx["quantity"],
            )
            results.append(result)
        self._pending.clear()
        return results

    def get_ledger(self):
        """Return the transaction ledger."""
        return list(self._ledger)

    def get_pending_transactions(self):
        """Return pending transactions."""
        return list(self._pending)

    # ── Private helpers ───────────────────────────────────────────────────

    def _try_reserve(self, employee_id, isbn, quantity):
        """Attempt to reserve stock when insufficient for immediate sale."""
        self._inventory.reserve_book(isbn, employee_id, quantity)
        return True
