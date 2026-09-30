"""Application constants."""

TAX_RATE = 0.075
MAX_DISCOUNT = 0.25
CLOSING_HOUR = 18
OPENING_HOUR = 8
COMMISSION_RATE = 0.08
LOW_STOCK_THRESHOLD = 5


def format_currency(amount):
    """Format a number as currency string."""
    return f"${amount:,.2f}"
