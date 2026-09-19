"""Provider-neutral models consumed by the public TUI."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    name: str
    account_type: str
    balance: float


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
