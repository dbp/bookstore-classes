"""Integration tests for the campus bookstore management system."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


def test_full_day_operations():
    """Test a complete day of bookstore operations from start to finish."""
    print("\n[TEST] Full Day Operations")
    print("-" * 40)

    app = main.create_app()

    # Assign shifts
    app["employees"].assign_shift("EMP001", "morning", "08:00", "16:00")
    app["employees"].assign_shift("EMP002", "morning", "08:00", "16:00")

    # Process sales
    r1 = app["sales"].process_sale("EMP001", "978-0-13-468599-1", 2)
    assert r1["success"], f"First sale failed: {r1}"
    print(f"  Sale 1: OK (${r1['total']:.2f})")

    r2 = app["sales"].process_sale("EMP002", "978-0-596-00712-6", 1)
    assert r2["success"], f"Second sale failed: {r2}"
    print(f"  Sale 2: OK (${r2['total']:.2f})")

    # Verify inventory reduced
    book = app["inventory"].get_book("978-0-13-468599-1")
    assert book.quantity == 10, f"Expected qty 10, got {book.quantity}"
    print(f"  Inventory check: C Programming Language x{book.quantity} (expected 10)")

    # Process a return
    r3 = app["sales"].process_return("EMP001", 1)
    assert r3["success"], f"Return failed: {r3}"
    print(f"  Return 1: OK (refund ${r3['refund']:.2f})")

    # Verify inventory restored
    book = app["inventory"].get_book("978-0-13-468599-1")
    assert book.quantity == 11, f"Expected qty 11 after return, got {book.quantity}"
    print(f"  Inventory after return: C Programming Language x{book.quantity} (expected 11)")

    # Generate daily report
    report = app["reports"].generate_daily_report()
    assert report["transactions"]["completed"] == 2
    print(f"  Daily report: {report['transactions']['completed']} transactions, "
          f"net ${report['revenue']['net']:.2f}")

    # Verify employee payroll
    emp = app["employees"].get_employee("EMP001")
    payroll = app["employees"].calculate_payroll("EMP001")
    assert payroll > 0
    print(f"  Employee payroll: {emp.name} estimated ${payroll:.2f}")

    print("  PASSED\n")


def test_low_stock_and_reordering():
    """Test that low stock is detected correctly."""
    print("\n[TEST] Low Stock and Reordering")
    print("-" * 40)

    app = main.create_app()

    books = app["inventory"].list_all_books()
    low_stock_isbns = [isbn for isbn, b in books.items() if b.quantity <= 5]

    if not low_stock_isbns:
        print("  SKIPPED (no books start with low stock)")
        return

    isbn = low_stock_isbns[0]
    book = app["inventory"].get_book(isbn)
    original_qty = book.quantity
    print(f"  Starting: {book.title} has {original_qty} units")

    # Sell until depleted
    while app["inventory"].get_book(isbn).quantity > 0:
        result = app["sales"].process_sale("EMP003", isbn, 1)
        if not result["success"]:
            break

    final_qty = app["inventory"].get_book(isbn).quantity
    print(f"  After selling all: {final_qty} units remaining")
    assert final_qty == 0

    # Verify in low stock list
    low_books = app["inventory"].list_all_books(status="low")
    assert isbn in low_books
    print("  Low stock check: OK")

    print("  PASSED\n")


def test_employee_lifecycle():
    """Test hiring and firing employees."""
    print("\n[TEST] Employee Lifecycle (hire + fire)")
    print("-" * 40)

    app = main.create_app()

    # Hire
    new_emp = app["employees"].hire("EMP999", "Test Employee", "cashier", 15.0)
    assert new_emp.id == "EMP999"
    print(f"  Hired: {new_emp.name} ({new_emp.rank})")

    # Verify lookup works
    emp = app["employees"].get_employee("EMP999")
    assert emp is not None and emp.name == "Test Employee"
    print("  Employee lookup: OK")

    # Sale by new employee earns commission
    r = app["sales"].process_sale("EMP999", "978-0-13-468599-1", 1)
    assert r["success"]
    emp = app["employees"].get_employee("EMP999")
    assert emp.commission_earned > 0
    print(f"  Commission credited: ${emp.commission_earned:.2f}")

    # Fire
    fired = app["employees"].fire("EMP999")
    assert fired
    print("  Fired: Test Employee")

    emp = app["employees"].get_employee("EMP999")
    assert emp is None
    print("  Employee lookup after fire: None (correct)")

    print("  PASSED\n")


def test_reservation_system():
    """Test the reservation system across inventory and employees."""
    print("\n[TEST] Reservation System")
    print("-" * 40)

    app = main.create_app()

    # Reserve a book
    r = app["inventory"].reserve_book("978-0-596-00712-6", "EMP001", 2)
    assert r
    print("  Reserved: Head First Design Patterns x2 for EMP001")

    # Verify inventory updated
    book = app["inventory"].get_book("978-0-596-00712-6")
    assert book.quantity == 13
    assert book.reserved == 2
    print(f"  Inventory: {book.title} x{book.quantity} (reserved: {book.reserved})")

    # Verify reservation tracked in inventory module
    reservations = app["inventory"].get_reservations("EMP001")
    assert len(reservations) > 0
    print(f"  Reservations tracked: {len(reservations)} items")

    # Release the reservation
    released = app["inventory"].release_reservation("978-0-596-00712-6", "EMP001", 2)
    assert released
    print("  Released reservation")

    # Verify inventory restored with correct quantity
    book = app["inventory"].get_book("978-0-596-00712-6")
    assert book.quantity == 15, f"Expected 15 after full release, got {book.quantity}"
    assert book.reserved == 0, f"Expected reserved=0, got {book.reserved}"
    print(f"  Inventory restored: x{book.quantity} (reserved: {book.reserved})")

    print("  PASSED\n")


def test_supplier_ordering():
    """Test the supplier ordering flow."""
    print("\n[TEST] Supplier Ordering")
    print("-" * 40)

    app = main.create_app()

    # Place an order
    r = app["suppliers"].place_order("978-0-321-12521-7", 10, urgent=False)
    assert r["success"]
    print("  Order placed: Domain-Driven Design x10")

    pending = app["suppliers"].get_pending_orders()
    assert len(pending) > 0
    print(f"  Pending orders: {len(pending)}")

    # Receive the order
    r2 = app["suppliers"].receive_order(1)
    assert r2["success"]
    print("  Order received")

    # Verify inventory updated
    book = app["inventory"].get_book("978-0-321-12521-7")
    assert book.quantity == 13, f"Expected 13, got {book.quantity}"
    print(f"  Inventory updated: x{book.quantity} (was 3)")

    print("  PASSED\n")


def test_reports_consistency():
    """Test that reports pull consistent data from all subsystems."""
    print("\n[TEST] Reports Consistency")
    print("-" * 40)

    app = main.create_app()

    # Do some operations
    app["sales"].process_sale("EMP001", "978-0-13-468599-1", 2)
    app["sales"].process_sale("EMP002", "978-0-596-00712-6", 1)

    # Generate all three reports
    daily = app["reports"].generate_daily_report()
    inv_report = app["reports"].generate_inventory_report()
    emp_report = app["reports"].generate_employee_report()

    assert daily["transactions"]["completed"] == 2
    print(f"  Daily report: {daily['transactions']['completed']} transactions - OK")

    assert len(inv_report["items"]) == 8
    print(f"  Inventory report: {len(inv_report['items'])} items - OK")

    assert len(emp_report["items"]) == 4
    print(f"  Employee report: {len(emp_report['items'])} employees - OK")

    # Cross-check: daily report inventory count matches actual books
    actual_books = app["inventory"].list_all_books()
    assert daily["inventory"]["total_items"] == len(actual_books)
    print("  Cross-report consistency: OK")

    print("  PASSED\n")


def test_full_sample_day():
    """Run the full sample day simulation."""
    print("\n[TEST] Full Sample Day (main.run_sample_day)")
    print("-" * 40)

    app = main.create_app()
    report = main.run_sample_day(app)

    assert "revenue" in report
    assert "transactions" in report
    assert "inventory" in report
    assert "employees" in report

    assert report["revenue"]["gross"] > 0
    assert report["transactions"]["completed"] == 5
    assert report["transactions"]["returned"] == 1

    print(f"  Gross: ${report['revenue']['gross']:,.2f}")
    print(f"  Net:   ${report['revenue']['net']:,.2f}")
    print(f"  Transactions: {report['transactions']['completed']} completed, "
          f"{report['transactions']['returned']} returned")

    print("  PASSED\n")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("  CAMPUS BOOKSTORE - INTEGRATION TESTS (CLEAN)")
    print("=" * 60)

    tests = [
        test_full_day_operations,
        test_low_stock_and_reordering,
        test_employee_lifecycle,
        test_reservation_system,
        test_supplier_ordering,
        test_reports_consistency,
        test_full_sample_day,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
