"""Reporting — aggregates data from all subsystems to produce summaries."""

from __future__ import annotations

import config


class Reports:
    """Generates daily, inventory, and employee reports."""

    def __init__(self, inventory, sales, employees, suppliers):
        self._inventory = inventory
        self._sales = sales
        self._employees = employees
        self._suppliers = suppliers

    # ── Public API ────────────────────────────────────────────────────────

    def generate_daily_report(self):
        """Generate a daily summary report."""
        ledger = self._sales.get_ledger()
        pending = self._sales.get_pending_transactions()
        employees = self._employees.get_all_employees()
        pending_orders = self._suppliers.get_pending_orders()
        order_history = self._suppliers.get_order_history()

        # Revenue metrics
        all_txns = list(ledger)  # all transactions ever recorded
        returned_txns = [t for t in ledger if t.returned]
        non_returned = [t for t in ledger if not t.returned]
        gross = sum(t.total for t in non_returned)
        returns_total = sum(t.total for t in returned_txns)

        # Inventory metrics
        books = self._inventory.list_all_books()
        low_stock = {k: v for k, v in books.items() if v.quantity <= config.LOW_STOCK_THRESHOLD}
        total_value = sum(b.price * b.quantity for b in books.values())

        # Employee payouts
        employee_payouts = {}
        for emp in employees:
            hourly_pay = emp.shifts_worked * 8 * emp.hourly_rate
            commission = emp.commission_earned
            employee_payouts[emp.id] = {
                "name": emp.name,
                "hourly_pay": hourly_pay,
                "commission": commission,
                "total": hourly_pay + commission,
            }

        # Supplier order counts
        supplier_order_counts = {}
        for order in pending_orders + order_history:
            sid = order.supplier_id
            supplier_order_counts[sid] = supplier_order_counts.get(sid, 0) + 1

        return {
            "report_type": "daily",
            "revenue": {
                "gross": gross,
                "returns": returns_total,
                "net": gross - returns_total,
            },
            "transactions": {
                "completed": len(all_txns),
                "pending": len(pending),
                "returned": len(returned_txns),
            },
            "inventory": {
                "total_items": len(books),
                "low_stock_count": len(low_stock),
                "total_value": total_value,
                "low_stock_isbns": [b.isbn for b in low_stock.values()],
            },
            "employees": employee_payouts,
            "suppliers": {
                "pending_orders": len(pending_orders),
                "orders_by_supplier": supplier_order_counts,
            },
        }

    def generate_inventory_report(self):
        """Generate an inventory valuation report."""
        books = self._inventory.list_all_books()

        # Build supplier lookup from suppliers module
        supplier_map = {}
        for sup in self._suppliers._suppliers.values():
            for book_info in sup.books:
                isbn = book_info["isbn"]
                if isbn not in supplier_map:
                    supplier_map[isbn] = []
                supplier_map[isbn].append({
                    "supplier_id": sup.id,
                    "supplier_name": sup.name,
                    "supplier_price": book_info.get("price"),
                })

        items = []
        for isbn, book in books.items():
            entry = {
                "isbn": isbn,
                "title": book.title,
                "author": book.author,
                "quantity": book.quantity,
                "reserved": book.reserved,
                "available": book.quantity - book.reserved,
                "price": book.price,
            }
            if isbn in supplier_map:
                entry["suppliers"] = supplier_map[isbn]
            elif book.supplier_id:
                entry["suppliers"] = [{"note": "Supplier reference exists but not in suppliers module"}]
            items.append(entry)

        total_value = sum(i["quantity"] * i["price"] for i in items)
        low_stock = [i for i in items if i["available"] <= config.LOW_STOCK_THRESHOLD]

        return {
            "report_type": "inventory",
            "items": items,
            "total_value": total_value,
            "low_stock": low_stock,
        }

    def generate_employee_report(self):
        """Generate an employee payroll report."""
        employees = self._employees.get_all_employees()
        ledger = self._sales.get_ledger()

        # Aggregate sales totals per employee from the ledger
        employee_sales_totals = {}
        for tx in ledger:
            if not tx.returned:
                eid = tx.employee_id
                employee_sales_totals[eid] = employee_sales_totals.get(eid, 0) + tx.total

        items = []
        for emp in employees:
            reported_commission = emp.commission_earned
            calculated_sales = employee_sales_totals.get(emp.id, 0)
            hourly_pay = emp.shifts_worked * 8 * emp.hourly_rate
            payroll_est = hourly_pay + reported_commission

            items.append({
                "id": emp.id,
                "name": emp.name,
                "rank": emp.rank,
                "shifts_worked": emp.shifts_worked,
                "reported_commission": reported_commission,
                "calculated_sales_total": calculated_sales,
                "reservations_count": len(self._inventory.get_reservations(emp.id)),
                "payroll_estimate": payroll_est,
            })

        return {
            "report_type": "employees",
            "items": items,
            "total_payroll": sum(i["payroll_estimate"] for i in items),
        }
