"""Domain models for the campus bookstore."""

from __future__ import annotations

import datetime


class Book:
    def __init__(self, isbn, title, author, price, quantity, supplier_id=None):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.price = price
        self.quantity = quantity
        self.supplier_id = supplier_id
        self.date_added = datetime.datetime.now()
        self.reserved = 0


class Employee:
    def __init__(self, emp_id, name, rank="cashier", hourly_rate=12.0):
        self.id = emp_id
        self.name = name
        self.rank = rank
        self.hourly_rate = hourly_rate
        self.total_sales = 0.0
        self.commission_earned = 0.0
        self.shifts_worked = 0
        self.hire_date = datetime.datetime.now()


class Supplier:
    def __init__(self, supplier_id, name, contact_email, phone=None):
        self.id = supplier_id
        self.name = name
        self.email = contact_email
        self.phone = phone
        self.books = []
        self.rating = 5.0


class Transaction:
    def __init__(self, employee_id, isbn, quantity, discount, base_price, tax, total):
        self.employee_id = employee_id
        self.isbn = isbn
        self.quantity = quantity
        self.discount = discount
        self.base_price = base_price
        self.tax = tax
        self.total = total
        self.timestamp = datetime.datetime.now()
        self.returned = False
        self.return_timestamp = None


class Order:
    def __init__(self, isbn, quantity, supplier_id, urgent=False):
        self.isbn = isbn
        self.quantity = quantity
        self.supplier_id = supplier_id
        self.urgent = urgent
        self.status = "pending"
        self.placed_at = datetime.datetime.now()
        self.received_at = None


class Reservation:
    def __init__(self, isbn, employee_id, quantity):
        self.isbn = isbn
        self.employee_id = employee_id
        self.quantity = quantity
