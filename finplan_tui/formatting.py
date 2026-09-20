"""Small presentation helpers shared by financial review interfaces."""
from __future__ import annotations


def format_dollars(value: float) -> str:
    """Format a whole-dollar value for compact tables."""
    return f"${value:,.0f}"


def format_cents(cents: float | None) -> str:
    """Format a signed cents value using the private TUI's precision rules."""
    if cents is None:
        return "—"
    dollars = float(cents) / 100
    sign = "-" if dollars < 0 else ""
    amount = abs(dollars)
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"{sign}${amount:,.0f}"
    return f"{sign}${amount:,.2f}"
