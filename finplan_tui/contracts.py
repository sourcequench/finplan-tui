"""Stable interfaces between the reusable UI and data adapters."""
from __future__ import annotations

from typing import Protocol

from .models import CashflowData, DashboardData, RecurringData, SpendingData


class DashboardRepository(Protocol):
    """Read-only source for the normalized dashboard payload."""

    def load_dashboard_data(self) -> DashboardData:
        """Return the current dashboard snapshot."""


class OperationalRepository(DashboardRepository, Protocol):
    """Repository contract for the shared operational review screens."""

    def load_spending_data(self) -> SpendingData:
        """Return normalized spending data."""

    def load_cashflow_data(self) -> CashflowData:
        """Return normalized classified cashflow."""

    def load_recurring_data(self) -> RecurringData:
        """Return normalized recurring-payee data."""
