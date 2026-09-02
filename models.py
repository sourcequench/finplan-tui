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

    @property
    def gain(self) -> float:
        return self.market_value - self.basis


@dataclass(frozen=True)
class LocationScenario:
    name: str
    annual_tax: float
    explanation: str


@dataclass(frozen=True)
class PlanningData:
    accounts: tuple[Account, ...]
    lots: tuple[TaxLot, ...]
    locations: tuple[LocationScenario, ...]
