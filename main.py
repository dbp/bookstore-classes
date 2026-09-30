"""Main entry point — wires subsystems together and provides the user interface."""

from __future__ import annotations

import config
import models
import inventory
import employees
import sales
import suppliers
import reports


def create_app():
    """Create and initialize the application with all subsystems wired up."""
    inv = inventory.Inventory()
    emps = employees.Employees()
    sal = sales.Sales(inv, emps)
    sup = suppliers.Suppliers(inv)
    rpt = reports.Reports(inv, sal, emps, sup)

    # Seed data
    _seed_suppliers(sup)
    _seed_inventory(inv)
    _seed_employees(emps)

    return {
        "inventory": inv,
        "employees": emps,
        "sales": sal,
        "suppliers": sup,
        "reports": rpt,
    }


def _seed_suppliers(sup):
    """Seed the system with initial supplier data."""
    sup1 = sup.add_supplier("SUP001", "Academic Books Inc.", "orders@academicbooks.com")
    sup2 = sup.add_supplier("SUP002", "Campus Textbook Depot", "supply@campustextbooks.edu")
    sup3 = sup.add_supplier("SUP003", "Rare & Used Books LLC", "info@rareusedbooks.com")

    # Link suppliers to the books they carry
    sup1.books.append({"isbn": "978-0-13-468599-1", "price": 45.99})
    sup1.books.append({"isbn": "978-0-201-63361-0", "price": 54.99})
    sup1.books.append({"isbn": "978-0-13-468599-2", "price": 52.99})
    sup2.books.append({"isbn": "978-0-596-00712-6", "price": 39.99})
    sup2.books.append({"isbn": "978-0-13-235088-4", "price": 42.99})
    sup2.books.append({"isbn": "978-0-13-212812-6", "price": 47.99})
    sup3.books.append({"isbn": "978-0-321-12521-7", "price": 49.99})
    sup3.books.append({"isbn": "978-0-596-51774-8", "price": 29.99})


def _seed_inventory(inv):
    """Seed the system with initial book data."""
    inv.add_book("978-0-13-468599-1", "The C Programming Language", "Kernighan & Ritchie", 45.99, 12, "SUP001")
    inv.add_book("978-0-201-63361-0", "Design Patterns", "GoF", 54.99, 8, "SUP001")
    inv.add_book("978-0-596-00712-6", "Head First Design Patterns", "Freeman & Robson", 39.99, 15, "SUP002")
    inv.add_book("978-0-13-235088-4", "Clean Code", "Robert C. Martin", 42.99, 6, "SUP002")
    inv.add_book("978-0-321-12521-7", "Domain-Driven Design", "Eric Evans", 49.99, 3, "SUP003")
    inv.add_book("978-0-13-468599-2", "The C++ Programming Language", "Stroustrup", 52.99, 10, "SUP001")
    inv.add_book("978-0-13-212812-6", "The Pragmatic Programmer", "Hunt & Thomas", 47.99, 9, "SUP002")
    inv.add_book("978-0-596-51774-8", "JavaScript: The Good Parts", "Douglas Crockford", 29.99, 20, "SUP003")


def _seed_employees(emps):
    """Seed the system with initial employee data."""
    emps.hire("EMP001", "Alice Johnson", "manager", 22.0)
    emps.hire("EMP002", "Bob Smith", "shift_lead", 16.0)
    emps.hire("EMP003", "Carol Davis", "senior_cashier", 14.0)
    emps.hire("EMP004", "Dave Wilson", "cashier", 12.0)


def run_sample_day(app):
    """Run a sample day of bookstore operations."""
    print("=" * 60)
    print("  CAMPUS BOOKSTORE MANAGEMENT SYSTEM")
    print("  Sample Day Simulation")
    print("=" * 60)

    # Morning: open and assign shifts
    print("\n[8:00 AM] Opening the bookstore...")
    app["employees"].assign_shift("EMP001", "morning", "08:00", "16:00")
    app["employees"].assign_shift("EMP002", "morning", "08:00", "16:00")
    app["employees"].assign_shift("EMP003", "morning", "09:00", "17:00")
    app["employees"].assign_shift("EMP004", "afternoon", "12:00", "20:00")

    # Morning sales
    print("\n[9:00 AM] Processing morning sales...")
    r1 = app["sales"].process_sale("EMP003", "978-0-13-468599-1", 2)
    print(f"  Sale #1: {'SUCCESS' if r1['success'] else 'FAILED'} - {r1.get('total', 0):.2f}")

    r2 = app["sales"].process_sale("EMP003", "978-0-201-63361-0", 1)
    print(f"  Sale #2: {'SUCCESS' if r2['success'] else 'FAILED'} - {r2.get('total', 0):.2f}")

    r3 = app["sales"].process_sale("EMP004", "978-0-596-00712-6", 3)
    print(f"  Sale #3: {'SUCCESS' if r3['success'] else 'FAILED'} - {r3.get('total', 0):.2f}")

    # Afternoon sales
    print("\n[1:00 PM] Processing afternoon sales...")
    r4 = app["sales"].process_sale("EMP004", "978-0-13-235088-4", 1)
    print(f"  Sale #4: {'SUCCESS' if r4['success'] else 'FAILED'} - {r4.get('total', 0):.2f}")

    r5 = app["sales"].process_sale("EMP001", "978-0-321-12521-7", 2)
    print(f"  Sale #5: {'SUCCESS' if r5['success'] else 'FAILED'} - {r5.get('total', 0):.2f}")

    # A return
    print("\n[3:00 PM] Processing a return...")
    r6 = app["sales"].process_return("EMP004", 4)
    print(f"  Return #1: {'SUCCESS' if r6['success'] else 'FAILED'} - refund {r6.get('refund', 0):.2f}")

    # Inventory check
    print("\n[4:00 PM] Checking inventory levels...")
    low_stock = app["inventory"].list_all_books(status="low")
    if low_stock:
        for isbn, book in low_stock.items():
            print(f"  LOW STOCK: {book.title} (ISBN: {isbn}) - {book.quantity} remaining")
    else:
        print("  All items adequately stocked.")

    # End-of-day reports
    print("\n[6:00 PM] Generating end-of-day reports...")

    daily = app["reports"].generate_daily_report()
    print(f"\n  DAILY REPORT:")
    print(f"    Gross Revenue:   ${daily['revenue']['gross']:,.2f}")
    print(f"    Returns:         ${daily['revenue']['returns']:,.2f}")
    print(f"    Net Revenue:     ${daily['revenue']['net']:,.2f}")
    print(f"    Transactions:    {daily['transactions']['completed']} completed, "
          f"{daily['transactions']['pending']} pending")
    print(f"    Low Stock Items: {daily['inventory']['low_stock_count']}")
    print(f"    Total Inventory Value: ${daily['inventory']['total_value']:,.2f}")

    emp_report = app["reports"].generate_employee_report()
    print(f"\n  EMPLOYEE REPORT:")
    for item in emp_report["items"]:
        print(f"    {item['name']} ({item['rank']}): "
              f"payroll est. ${item['payroll_estimate']:,.2f}")
    print(f"    Total Payroll: ${emp_report['total_payroll']:,.2f}")

    inv_report = app["reports"].generate_inventory_report()
    print(f"\n  INVENTORY REPORT:")
    print(f"    Total Items: {inv_report['total_value']:.2f} value across {len(inv_report['items'])} titles")
    if inv_report["low_stock"]:
        print(f"    Low Stock Titles: {len(inv_report['low_stock'])}")

    print("\n[6:00 PM] Closing the bookstore...")

    return daily


def interactive_mode(app):
    """Interactive command-line mode."""
    print("=" * 60)
    print("  CAMPUS BOOKSTORE MANAGEMENT SYSTEM")
    print("  Interactive Mode (type 'help' for commands)")
    print("=" * 60)

    while True:
        try:
            command = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not command:
            continue

        parts = command.split()
        action = parts[0]

        if action == "help":
            _show_help()
        elif action == "sale":
            if len(parts) >= 3:
                emp_id, isbn = parts[1], parts[2]
                qty = int(parts[3]) if len(parts) > 3 else 1
                result = app["sales"].process_sale(emp_id, isbn, qty)
                print(f"Result: {result}")
            else:
                print("Usage: sale <employee_id> <isbn> [quantity]")
        elif action == "return":
            if len(parts) >= 3:
                emp_id, tx_id = parts[1], int(parts[2])
                result = app["sales"].process_return(emp_id, tx_id)
                print(f"Result: {result}")
            else:
                print("Usage: return <employee_id> <transaction_id>")
        elif action == "inventory":
            status = parts[1] if len(parts) > 1 else "all"
            books = app["inventory"].list_all_books(status=status)
            for isbn, book in books.items():
                print(f"  {isbn}: {book.title} x{book.quantity} (${book.price})")
        elif action == "report":
            report_type = parts[1] if len(parts) > 1 else "daily"
            if report_type == "daily":
                report = app["reports"].generate_daily_report()
                print(f"Net Revenue: ${report['revenue']['net']:,.2f}")
                print(f"Transactions: {report['transactions']['completed']}")
            elif report_type == "inventory":
                report = app["reports"].generate_inventory_report()
                print(f"Total Value: ${report['total_value']:,.2f}")
            elif report_type == "employees":
                report = app["reports"].generate_employee_report()
                for item in report["items"]:
                    print(f"  {item['name']}: ${item['payroll_estimate']:,.2f}")
        elif action == "hire":
            if len(parts) >= 4:
                emp_id, name, rank = parts[1], parts[2], parts[3]
                result = app["employees"].hire(emp_id, name, rank)
                print(f"Hired: {result.name} ({result.rank})")
            else:
                print("Usage: hire <emp_id> <name> <rank>")
        elif action == "add_book":
            if len(parts) >= 6:
                isbn, title, author = parts[1], parts[2], parts[3]
                price = float(parts[4])
                qty = int(parts[5])
                result = app["inventory"].add_book(isbn, title, author, price, qty)
                print(f"Added: {result.title} (x{result.quantity})")
            else:
                print("Usage: add_book <isbn> <title> <author> <price> <quantity>")
        elif action == "status":
            _show_status(app)
        elif action in ("quit", "exit"):
            print("Goodbye!")
            break
        else:
            print(f"Unknown command: {action}. Type 'help' for options.")


def _show_help():
    """Show available commands."""
    print("""
Available commands:
  sale <emp> <isbn> [qty] Process a sale
  return <emp> <tx_id>    Process a return
  inventory [status]      List books (status: all/low/available)
  report [type]           Generate report (daily/inventory/employees)
  hire <id> <name> <rank> Hire an employee
  add_book <isbn> ...     Add a book to inventory
  status                  Show system status
  quit                    Exit the program
""")


def _show_status(app):
    """Show current system status."""
    books = app["inventory"].list_all_books()
    employees_list = app["employees"].get_all_employees()
    ledger = app["sales"].get_ledger()

    print(f"\n  Books in inventory: {len(books)}")
    print(f"  Employees: {len(employees_list)}")
    print(f"  Transactions today: {len(ledger)}")


if __name__ == "__main__":
    import sys
    app = create_app()

    if "--demo" in sys.argv:
        run_sample_day(app)
    else:
        interactive_mode(app)
