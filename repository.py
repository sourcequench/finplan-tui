"""Repository boundary for public finplan-tui data."""
from __future__ import annotations

from typing import Protocol

from models import Account, LocationScenario, PlanningData, TaxLot


class PlanningRepository(Protocol):
    """Read-only data contract implemented by an application adapter."""

    def load_planning_data(self) -> PlanningData:
        """Return data suitable for the dashboard and review screens."""


class DemoPlanningRepository:
    """Synthetic repository used by the public demo and tests."""

    def load_planning_data(self) -> PlanningData:
        return PlanningData(
            accounts=(
                Account("Sample cash", "cash", 1000),
                Account("Demo brokerage", "brokerage", 25000),
                Account("Example retirement", "retirement", 50000),
            ),
            lots=(
                TaxLot("DEMO", 1200, 100, True),
                TaxLot("SAMPLE", 900, 700, True),
                TaxLot("TEST", 600, 720, False),
            ),
            locations=(
                LocationScenario(
                    "Example State A", 18200, "lower income tax; higher property estimate"
                ),
                LocationScenario("Example State B", 21100, "no income tax; higher sales estimate"),
                LocationScenario(
                    "Example State C", 23700, "lower housing estimate; higher income tax"
                ),
            ),
        )
