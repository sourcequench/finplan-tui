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
    lot_id: str = ""

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
            "trend": list(self.trend),
            "transactions": [
                (item.date, item.payee, round(item.amount * 100), item.account)
                for item in self.transactions
            ],
        }


@dataclass(frozen=True)
class SpendingData:
    """Monthly spending data normalized from any provider."""

    monthly: dict[str, dict[str, int]]
    raw_transactions: dict[str, tuple[tuple, ...]]
    anomalies: tuple[dict, ...] = ()

    @classmethod
    def from_legacy(cls, payload: dict) -> "SpendingData":
        return cls(
            monthly=payload.get("monthly", {}),
            raw_transactions={
                key: tuple(rows) for key, rows in payload.get("raw_txns", {}).items()
            },
            anomalies=tuple(payload.get("anomalies", ())),
        )

    def to_legacy_dict(self) -> dict:
        return {
            "monthly": self.monthly,
            "raw_txns": {key: list(rows) for key, rows in self.raw_transactions.items()},
            "anomalies": list(self.anomalies),
        }


@dataclass(frozen=True)
class CashflowData:
    """Classified cashflow and reconciliation results."""

    cashflow: dict[str, dict[str, int]]
    planned_obligations: tuple[dict, ...] = ()
    reconciliation: dict | None = None

    def __post_init__(self) -> None:
        if self.reconciliation is None:
            object.__setattr__(self, "reconciliation", {})

    @classmethod
    def from_legacy(cls, payload: dict) -> "CashflowData":
        return cls(
            cashflow=payload.get("cashflow", {}),
            planned_obligations=tuple(payload.get("planned_obligations", ())),
            reconciliation=payload.get("reconciliation") or {},
        )

    def to_legacy_dict(self) -> dict:
        return {
            "cashflow": self.cashflow,
            "planned_obligations": list(self.planned_obligations),
            "reconciliation": self.reconciliation,
        }


@dataclass(frozen=True)
class RecurringData:
    """Recurring-payee rows normalized for review screens."""

    rows: tuple[dict, ...]

    @classmethod
    def from_legacy(cls, rows: list[dict]) -> "RecurringData":
        return cls(tuple(rows))

    def to_legacy_rows(self) -> list[dict]:
        return list(self.rows)
