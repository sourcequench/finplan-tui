"""Reusable Textual widgets for provider-neutral financial review screens."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from .formatting import format_cents


def format_signed_cents(cents: float | None) -> tuple[str, str]:
    """Return display text and a Rich style for a signed transaction amount."""
    if cents is None:
        return "—", "dim"
    amount = format_cents(cents)
    if float(cents) >= 0:
        return "+" + amount, "bright_green"
    return amount.replace("-", "−", 1), "bright_red"


class TransactionsWidget(Static):
    """Render recent transactions from the normalized legacy row shape."""

    def set_data(self, transactions: list | tuple) -> None:
        text = Text()
        text.append("  RECENT TRANSACTIONS\n\n", style="bold dim")
        for date, payee, amount, account in transactions:
            payee_text = (payee or "—")[:38]
            account_text = (account or "—")[:30]
            amount_text, color = format_signed_cents(amount)
            text.append(f"  {str(date)}  ", style="dim")
            text.append(f"{payee_text:<40}", style="white")
            text.append(f"{amount_text:>12}", style=color)
            text.append(f"  {account_text}\n", style="dim")
        self.update(text)
