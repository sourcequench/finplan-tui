"""Stable interfaces between the reusable UI and data adapters."""
from __future__ import annotations

from typing import Protocol

from .models import DashboardData


class DashboardRepository(Protocol):
    """Read-only source for the normalized dashboard payload."""

    def load_dashboard_data(self) -> DashboardData:
        """Return the current dashboard snapshot."""
