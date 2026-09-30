"""Employee management — owns employee records and shift assignments."""

from __future__ import annotations

import config
import models


class Employees:
    """Manages employee records and shift assignments."""

    def __init__(self):
        self._employees = {}  # emp_id -> Employee
        self._shifts = {}     # emp_id -> dict with shift info

    # ── Public API ────────────────────────────────────────────────────────

    def hire(self, emp_id, name, rank="cashier", hourly_rate=12.0):
        """Hire a new employee."""
        emp = models.Employee(emp_id, name, rank, hourly_rate)
        self._employees[emp_id] = emp
        self._shifts[emp_id] = {}
        return emp

    def fire(self, emp_id):
        """Fire an employee. Returns True if they existed."""
        if emp_id not in self._employees:
            return False
        del self._employees[emp_id]
        self._shifts.pop(emp_id, None)
        return True

    def get_employee(self, emp_id):
        """Look up an employee by ID."""
        return self._employees.get(emp_id)

    def promote(self, emp_id, new_rank):
        """Promote an employee to a new rank."""
        emp = self._employees.get(emp_id)
        if not emp:
            return False
        emp.rank = new_rank
        return True

    def assign_shift(self, emp_id, shift_name, start_time, end_time):
        """Assign a shift to an employee. Returns True on success."""
        if emp_id not in self._employees:
            return False
        hours = self._calc_hours(start_time, end_time)
        self._shifts[emp_id] = {
            "shift_name": shift_name,
            "start": start_time,
            "end": end_time,
            "hours": hours,
        }
        self._employees[emp_id].shifts_worked += 1
        return True

    def get_all_employees(self):
        """Return a list of all employees."""
        return list(self._employees.values())

    def calculate_payroll(self, emp_id):
        """Calculate total pay (hourly wage + commissions) for an employee."""
        emp = self._employees.get(emp_id)
        if not emp:
            return 0.0
        shift = self._shifts.get(emp_id, {})
        hours = shift.get("hours", 0)
        base_pay = hours * emp.hourly_rate
        commission = emp.commission_earned
        return base_pay + commission

    def credit_commission(self, emp_id, amount):
        """Credit commission to an employee."""
        emp = self._employees.get(emp_id)
        if emp:
            emp.commission_earned += amount
            emp.total_sales += amount

    def debit_commission(self, emp_id, amount):
        """Debit commission from an employee (e.g., on return)."""
        emp = self._employees.get(emp_id)
        if emp:
            emp.commission_earned = max(0, emp.commission_earned - amount)

    def get_max_discount_for_rank(self, rank):
        """Return the maximum discount allowed for a given employee rank."""
        rank_limits = {
            "cashier": 0.05,
            "senior_cashier": 0.10,
            "shift_lead": 0.15,
            "manager": 0.25,
        }
        return rank_limits.get(rank, 0.0)

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _calc_hours(start_time, end_time):
        start_parts = start_time.split(":")
        end_parts = end_time.split(":")
        start_h, start_m = int(start_parts[0]), int(start_parts[1])
        end_h, end_m = int(end_parts[0]), int(end_parts[1])
        return (end_h * 60 + end_m - start_h * 60 - start_m) / 60
