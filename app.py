#!/usr/bin/env python3
"""Provider-neutral demo TUI for finplan-core integrations."""
from __future__ import annotations

import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from core_adapter import project_taxable_portfolio, rank_demo_locations, select_donation_lots
from models import PlanningData
from repository import (DemoPlanningRepository, LiveDemoRepository,
                        PlanningRepository, SimpleFINRepository, load_demo_scenario)


def money(value: float) -> str:
    return f"${value:,.0f}"


class DashboardScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_dashboard(), id="dashboard-body")
        yield Footer()

    def render_dashboard(self) -> str:
        total = sum(account.balance for account in self.data.accounts)
        recent = self.data.transactions[-5:][::-1]
        recent_lines = "\n".join(
            f"{item.date}  {item.payee:<28} {money(item.amount):>8}  {item.category}"
            for item in recent
        )
        return (
            "FINANCIAL PLANNING DEMO\n\n"
            f"Source: {self.data.source_label} · "
            f"{'LIVE STREAM' if self.data.is_live else 'snapshot'}\n"
            f"Virtual date: {self.data.demo_clock}\n\n"
            f"Accounts: {len(self.data.accounts)}\n"
            f"Illustrative total: {money(total)}\n"
            f"Transactions received: {len(self.data.transactions)}\n\n"
            "RECENT SYNTHETIC ACTIVITY\n"
            f"{recent_lines}\n\n"
            "Data is read through a repository adapter; calculations remain\n"
            "review aids and do not place trades or file taxes.\n"
        )

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#dashboard-body", Static).update(self.render_dashboard())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class TourScreen(Screen):
    BINDINGS = [("escape", "back", "Back"), ("q", "back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(
                "FINPLAN-TUI TOUR\n\n"
                "This playground is a completely synthetic financial life.\n"
                "It is safe to explore and does not connect to a bank or broker.\n\n"
                "TRY THIS PATH\n"
                "  1  Dashboard — watch the live activity feed and balances\n"
                "  2  Tax lots — compare appreciated-stock gift targets\n"
                "  3  Locations — inspect a core-backed tax ranking\n"
                "  4  Cashflow — review categories and net cash flow\n"
                "  5  Recurring — wait for repeated synthetic merchants\n"
                "  6  Retirement — inspect the taxable portfolio bridge\n\n"
                "DEMO MODES\n"
                "  --demo        live synthetic stream; one virtual day per five seconds\n"
                "  --static-demo frozen fixture for screenshots and tests\n\n"
                "The calculations are review aids, not tax, legal, investment, or\n"
                "accounting advice. Press Escape to return.\n",
                id="tour-body",
            )
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()


class LotsScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_lots(), id="lots-body")
        yield Footer()

    def render_lots(self) -> str:
        if not self.data.lots:
            return (
                "TAX-LOT REVIEW\n\n"
                "No tax lots are available from this data source.\n"
                "SimpleFIN supplies account balances and transactions, not holdings\n"
                "or cost basis. Import a brokerage tax-lot report before making a\n"
                "charitable-gift or realization decision.\n"
            )
        rows = [
            "TAX-LOT REVIEW — synthetic example\n",
            "SYMBOL      VALUE       BASIS       GAIN       TERM       ACQUIRED\n",
        ]
        lots = sorted(self.data.lots,
                      key=lambda item: item.gain / item.market_value, reverse=True)
        for lot in lots:
            term = "long" if lot.long_term else "short"
            rows.append(
                f"{lot.symbol:<10} {money(lot.market_value):>10} "
                f"{money(lot.basis):>10} {money(lot.gain):>10} {term:>8}"
                f" {lot.acquired:>12}\n"
            )
        target = self.data.scenario.charity_target if self.data.scenario else 10000
        rows.append("\nCHARITABLE GIFT COMPARISON — appreciated shares\n")
        rows.append("TARGET          SELECTED       BASIS       EMBEDDED GAIN   EST. 15% TAX\n")
        for gift_target in (target / 2, target, target * 2):
            selection = select_donation_lots(self.data.lots, round(gift_target * 100))
            if selection is None:
                rows.append(f"{money(gift_target):>8}   core unavailable; no selection shown\n")
                continue
            selected_gain = selection.selected_gain / 100
            rows.append(
                f"{money(gift_target):>8}   {money(selection.selected_value / 100):>10}"
                f" {money(selection.selected_basis / 100):>10}"
                f" {money(selected_gain):>14} {money(selected_gain * 0.15):>13}\n"
            )
        rows.append(
            "\nThis is a review aid: donating appreciated shares can avoid realizing the embedded gain.\n"
        )
        return "".join(rows)

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#lots-body", Static).update(self.render_lots())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class CashflowScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_cashflow(), id="cashflow-body")
        yield Footer()

    def render_cashflow(self) -> str:
        income = sum(item.amount for item in self.data.transactions if item.amount > 0)
        spending = -sum(item.amount for item in self.data.transactions if item.amount < 0)
        categories: dict[str, float] = {}
        merchants: dict[str, int] = {}
        for item in self.data.transactions:
            if item.amount < 0 and item.category != "Transfer":
                categories[item.category] = categories.get(item.category, 0) + -item.amount
                merchants[item.payee] = merchants.get(item.payee, 0) + 1
        rows = [
            "CASHFLOW REVIEW — synthetic live stream\n",
            f"Virtual date: {self.data.demo_clock} · transactions: {len(self.data.transactions)}\n",
            f"Income received: {money(income)}    Spending: {money(spending)}    "
            f"Net cash flow: {money(income - spending)}\n\n",
            "SPENDING BY CATEGORY\n",
        ]
        for category, amount in sorted(categories.items(), key=lambda row: row[1], reverse=True):
            rows.append(f"  {category:<20} {money(amount):>10}\n")
        rows.append("\nRECURRING / REPEATED PAYEES\n")
        repeated = [(payee, count) for payee, count in merchants.items() if count > 1]
        if repeated:
            for payee, count in sorted(repeated, key=lambda row: (-row[1], row[0])):
                rows.append(f"  {payee:<28} {count:>3} transactions\n")
        else:
            rows.append("  No repeated payees in the current stream yet.\n")
        rows.append("\nRECENT ACTIVITY\n")
        for item in self.data.transactions[-8:][::-1]:
            rows.append(f"  {item.date}  {item.payee:<28} {money(item.amount):>8}  {item.category}\n")
        rows.append("\nNew synthetic activity is incorporated automatically while --demo runs.\n")
        return "".join(rows)

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#cashflow-body", Static).update(self.render_cashflow())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class RecurringScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_recurring(), id="recurring-body")
        yield Footer()

    def render_recurring(self) -> str:
        groups: dict[str, list[float]] = {}
        for item in self.data.transactions:
            if item.category != "Transfer":
                groups.setdefault(item.payee, []).append(item.amount)
        rows = [
            "RECURRING REVIEW — inferred from observed synthetic activity\n",
            f"Virtual date: {self.data.demo_clock} · transactions: {len(self.data.transactions)}\n\n",
            "PAYEE                         COUNT     AVERAGE       LATEST\n",
        ]
        repeated = [(payee, amounts) for payee, amounts in groups.items() if len(amounts) > 1]
        if not repeated:
            rows.append("No repeated merchants yet; keep the live demo running to observe patterns.\n")
        else:
            for payee, amounts in sorted(repeated, key=lambda row: row[0]):
                rows.append(
                    f"{payee:<30} {len(amounts):>5} {money(sum(amounts) / len(amounts)):>12}"
                    f" {money(amounts[-1]):>12}\n"
                )
        rows.append(
            "\nThis is an observation, not a commitment prediction. A real adapter should\n"
            "retain source dates and transaction identifiers before labeling a bill recurring.\n"
        )
        return "".join(rows)

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#recurring-body", Static).update(self.render_recurring())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class RetirementScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_retirement(), id="retirement-body")
        yield Footer()

    def render_retirement(self) -> str:
        if self.data.scenario is None:
            return (
                "RETIREMENT BRIDGE\n\n"
                "No retirement scenario is configured for this data source.\n"
                "SimpleFIN supplies balances and transactions; add explicit\n"
                "spending, return, tax, and account-rule assumptions before\n"
                "running a retirement projection.\n"
            )
        brokerage = next((item.balance for item in self.data.accounts
                          if item.account_type == "brokerage"), 0.0)
        basis = sum(item.basis for item in self.data.lots)
        scenario = self.data.scenario
        annual_return = scenario.portfolio_return if scenario else 0.07
        annual_withdrawal = scenario.annual_withdrawal if scenario else 3000
        horizon = scenario.horizon_years if scenario else 12
        rows = [
            "RETIREMENT BRIDGE — illustrative synthetic scenario\n",
            "This is a planning calculation, not a prediction or recommendation.\n\n",
            f"Starting taxable portfolio: {money(brokerage)}\n",
            f"Estimated basis from demo lots: {money(basis)}\n",
            f"Return assumption: {annual_return:.2%} · withdrawal: {money(annual_withdrawal)}/yr"
            f" · horizon: {horizon} years\n\n",
        ]
        projection = project_taxable_portfolio(
            brokerage, basis, annual_return, annual_withdrawal, horizon,
        )
        if projection is None:
            rows.append("finplan-core is unavailable; no projection is shown.\n")
        else:
            rows.append("YEAR    END PORTFOLIO       REALIZED GAIN       GIFT\n")
            for row in projection:
                gift = row.get("gift_fm_cents", 0) / 100
                rows.append(
                    f"{row['year']}    {money(row['end_portfolio_cents'] / 100):>14}"
                    f"    {money(row['realized_gain_cents'] / 100):>14}"
                    f"    {money(gift):>10}\n"
                )
            rows.append("\nThe terminal row realizes the remaining taxable portfolio for illustration.\n")
        rows.append("\nOPEN INPUTS\n  retirement spending, taxes, healthcare, and account-specific rules\n")
        return "".join(rows)

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#retirement-body", Static).update(self.render_retirement())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class LocationsScreen(Screen):
    BINDINGS = [
        ("1", "dashboard", "Dashboard"), ("2", "lots", "Tax lots"),
        ("3", "locations", "Locations"), ("4", "cashflow", "Cashflow"),
        ("5", "recurring", "Recurring"), ("6", "retirement", "Retirement"),
    ]

    def __init__(self, data: PlanningData) -> None:
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer():
            yield Static(self.render_locations(), id="locations-body")
        yield Footer()

    def render_locations(self) -> str:
        rows = [
            "LOCATION SCENARIOS — synthetic example\n",
        ]
        ranked = rank_demo_locations(self.data.scenario) if self.data.scenario else None
        if ranked:
            rows.append("CORE-BACKED RANKING · caller-supplied fictional rules\n")
            rows.append("#   PLACE       COMBINED TAX       STATE TAX       PROPERTY\n")
            for index, item in enumerate(ranked, 1):
                rows.append(
                    f"{index:<3} {item['jurisdiction']:<10}"
                    f" {money(item['total_tax_cents'] / 100):>14}"
                    f" {money(item['state_tax_cents'] / 100):>14}"
                    f" {money(item['property_tax_cents'] / 100):>12}\n"
                )
        else:
            rows.append("CORE UNAVAILABLE · showing static synthetic comparison\n")
            rows.append("PLACE              ANNUAL TAX       NOTES\n")
            for location in sorted(self.data.locations, key=lambda item: item.annual_tax):
                rows.append(
                    f"{location.name:<18} {money(location.annual_tax):>12}       "
                    f"{location.explanation}\n"
                )
        if not self.data.scenario:
            rows.append(
                "\nNo personal planning scenario is configured. SimpleFIN provides data,\n"
                "but residency, income, housing, and tax assumptions must be supplied separately.\n"
            )
        else:
            rows.append(
                "\nA real application supplies tax rules, property values, and household assumptions explicitly.\n"
            )
        return "".join(rows)

    def update_data(self, data: PlanningData) -> None:
        self.data = data
        self.query_one("#locations-body", Static).update(self.render_locations())

    def action_dashboard(self) -> None:
        self.app.switch_screen("dashboard")

    def action_lots(self) -> None:
        self.app.switch_screen("lots")

    def action_locations(self) -> None:
        self.app.switch_screen("locations")

    def action_cashflow(self) -> None:
        self.app.switch_screen("cashflow")

    def action_recurring(self) -> None:
        self.app.switch_screen("recurring")

    def action_retirement(self) -> None:
        self.app.switch_screen("retirement")


class FinplanTUI(App):
    BINDINGS = [("q", "quit", "Quit"), ("h", "help", "Tour")]

    def __init__(self, data: PlanningData, repository: PlanningRepository) -> None:
        super().__init__()
        self.data = data
        self.repository = repository

    def on_mount(self) -> None:
        self.install_screen(DashboardScreen(self.data), name="dashboard")
        self.install_screen(LotsScreen(self.data), name="lots")
        self.install_screen(LocationsScreen(self.data), name="locations")
        self.install_screen(CashflowScreen(self.data), name="cashflow")
        self.install_screen(RecurringScreen(self.data), name="recurring")
        self.install_screen(RetirementScreen(self.data), name="retirement")
        self.install_screen(TourScreen(), name="tour")
        self.push_screen("dashboard")
        if isinstance(self.repository, LiveDemoRepository):
            self.set_interval(2, self.refresh_demo_data)

    def refresh_demo_data(self) -> None:
        """Pull the next deterministic synthetic snapshot into every screen."""
        self.data = self.repository.load_planning_data()
        for screen in self.screen_stack:
            update_data = getattr(screen, "update_data", None)
            if update_data is not None:
                update_data(self.data)

    def action_help(self) -> None:
        self.push_screen("tour")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the provider-neutral finplan TUI demo")
    parser.add_argument("--demo", action="store_true", help="run the live synthetic stream")
    parser.add_argument("--static-demo", action="store_true", help="run the frozen synthetic fixture")
    parser.add_argument("--simplefin", action="store_true", help="read personal data through SimpleFIN Bridge")
    parser.add_argument(
        "--simplefin-access-file", type=Path,
        default=Path.home() / ".config" / "finplan-tui" / "simplefin-access-url",
        help="protected file containing the SimpleFIN Access URL",
    )
    parser.add_argument("--scenario", type=Path, help="use a compatible synthetic scenario JSON")
    args = parser.parse_args()
    modes = sum(bool(value) for value in (args.demo, args.static_demo, args.simplefin))
    if modes != 1:
        parser.error("choose exactly one of --demo, --static-demo, or --simplefin")
    try:
        if args.simplefin:
            repository: PlanningRepository = SimpleFINRepository(args.simplefin_access_file)
        else:
            scenario = load_demo_scenario(args.scenario) if args.scenario else load_demo_scenario()
            repository = (
                LiveDemoRepository(scenario=scenario) if args.demo
                else DemoPlanningRepository(scenario=scenario)
            )
        data = repository.load_planning_data()
    except Exception as exc:
        parser.error(str(exc))
    FinplanTUI(data, repository).run()


if __name__ == "__main__":
    main()
