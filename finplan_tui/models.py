"""Typed provider-neutral models shared by public and private front ends."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Account:
    name: str
    account_type: str
    balance: float
    org_name: str = ""
    source: str = ""
    snapshot_ts: datetime | None = None


@dataclass(frozen=True)
class TaxLot:
    symbol: str
    market_value: float
    basis: float
    long_term: bool
    acquired: str = ""
    account: str = "Demo brokerage"

    @property
    def gain(self) -> float:
        return self.market_value - self.basis


@dataclass(frozen=True)
class LocationScenario:
    name: str
    annual_tax: float
    explanation: str


@dataclass(frozen=True)
class Transaction:
    date: str
    payee: str
    amount: float
    category: str
    account: str
    transaction_id: str = ""
    notes: str = ""


@dataclass(frozen=True)
class DemoScenario:
    name: str
    ordinary_income: float
    long_term_gains: float
    annual_spending: float
    home_value: float
    portfolio_return: float
    annual_withdrawal: float
    horizon_years: int
    charity_target: float
    charity_basis_rate: float = 0.25


@dataclass(frozen=True)
class PlanningData:
    accounts: tuple[Account, ...]
    lots: tuple[TaxLot, ...]
    locations: tuple[LocationScenario, ...]
    transactions: tuple[Transaction, ...] = ()
    demo_clock: str = ""
    is_live: bool = False
    scenario: DemoScenario | None = None
    source_label: str = "Synthetic demo"


@dataclass(frozen=True)
class DashboardData:
    """Normalized dashboard payload used by the private PostgreSQL adapter.

    ``trend`` intentionally remains a tuple-compatible shape during migration:
    ``(date, total_cents, cash_cents, investment_cents, crypto_cents)``.
    The adapter owns this compatibility conversion so screens do not need SQL
    or provider-specific row dictionaries.
    """

    accounts: tuple[Account, ...]
    trend: tuple[tuple[Any, ...], ...]
    transactions: tuple[Transaction, ...]
    snapshot_ts: datetime | None = None
    source_label: str = "PostgreSQL"

    def to_legacy_dict(self) -> dict:
        """Return the existing private TUI payload during incremental migration."""
        return {
            "snapshot_ts": self.snapshot_ts,
            "accounts": [
                (
                    account.org_name or None,
                    account.name,
                    None,
                    round(account.balance * 100),
                    account.source or None,
                )
                for account in self.accounts
            ],
            "trend": self.trend,
            "transactions": [
                (item.date, item.payee, round(item.amount * 100), item.account)
                for item in self.transactions
            ],
        }
