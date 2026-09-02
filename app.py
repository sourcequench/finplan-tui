#!/usr/bin/env python3
"""Provider-neutral demo TUI for finplan-core integrations."""
from __future__ import annotations

import argparse

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from core_adapter import select_donation_lots
from models import PlanningData
from repository import DemoPlanningRepository, PlanningRepository


def money(value: float) -> str:
    return f"${value:,.0f}"


class DashboardScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_dashboard())
        yield Footer()

    def render_dashboard(self) -> str:
        total = sum(account.balance for account in self.data.accounts)
        return (
            "FINANCIAL PLANNING DEMO\n\n"
            "Synthetic data · provider-neutral public UI\n\n"
            f"Accounts: {len(self.data.accounts)}\n"
            f"Illustrative total: {money(total)}\n\n"
            "This screen is a demo shell. Real applications provide data through\n"
            "a repository adapter; the public UI does not connect to a database.\n"
        )

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")


class LotsScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_lots())
        yield Footer()

    def render_lots(self) -> str:
        rows = [
            "TAX-LOT REVIEW — synthetic example\n",
            "SYMBOL      VALUE       BASIS       GAIN       TERM\n",
        ]
        lots = sorted(self.data.lots,
                      key=lambda item: item.gain / item.market_value, reverse=True)
        for lot in lots:
            term = "long" if lot.long_term else "short"
            rows.append(
                f"{lot.symbol:<10} {money(lot.market_value):>10} "
                f"{money(lot.basis):>10} {money(lot.gain):>10} {term:>8}\n"
            )
        selection = select_donation_lots(self.data.lots, 1_000_000)
        rows.append("\nDonation review target: $10,000\n")
        if selection is None:
            rows.append("finplan-core is not connected; no recommendation is shown.\n")
        else:
            rows.append(f"Selected value: {money(selection.selected_value / 100)}\n")
            rows.append(f"Selected gain: {money(selection.selected_gain / 100)}\n")
        return "".join(rows)

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")


class LocationsScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_locations())
        yield Footer()

    def render_locations(self) -> str:
        rows = [
            "LOCATION SCENARIOS — synthetic example\n",
            "PLACE              ANNUAL TAX       NOTES\n",
        ]
        for location in sorted(self.data.locations, key=lambda item: item.annual_tax):
            rows.append(
                f"{location.name:<18} {money(location.annual_tax):>12}       "
                f"{location.explanation}\n"
            )
        rows.append(
            "\nA real application supplies tax rules and household assumptions explicitly.\n"
        )
        return "".join(rows)

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")


class FinplanTUI(App):
    SCREENS = {
        "dashboard": DashboardScreen,
        "lots": LotsScreen,
        "locations": LocationsScreen,
    }
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def on_mount(self) -> None:
        self.install_screen(DashboardScreen(self.data), name="dashboard")
        self.install_screen(LotsScreen(self.data), name="lots")
        self.install_screen(LocationsScreen(self.data), name="locations")
        self.push_screen("dashboard")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the provider-neutral finplan TUI demo")
    parser.add_argument("--demo", action="store_true", help="run with synthetic data")
    args = parser.parse_args()
    if not args.demo:
        parser.error("only --demo is available until a repository adapter is supplied")
    repository: PlanningRepository = DemoPlanningRepository()
    FinplanTUI(repository.load_planning_data()).run()


if __name__ == "__main__":
    main()
