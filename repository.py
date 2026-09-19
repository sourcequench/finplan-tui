"""Repository boundary and synthetic data sources for public finplan-tui."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import stat
import time
from typing import Protocol
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from models import (Account, DemoScenario, LocationScenario, PlanningData, TaxLot,
                    Transaction)


class PlanningRepository(Protocol):
    """Read-only data contract implemented by an application adapter."""

    def load_planning_data(self) -> PlanningData:
        """Return data suitable for the dashboard and review screens."""


DEFAULT_SCENARIO_PATH = Path(__file__).with_name("demo") / "scenario.json"


def load_demo_scenario(path: Path = DEFAULT_SCENARIO_PATH) -> DemoScenario:
    """Load and validate the public synthetic scenario fixture."""
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise ValueError("demo scenario must declare synthetic=true")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported demo scenario schema_version")
    required = (
        "scenario_name", "ordinary_income", "long_term_gains", "annual_spending",
        "home_value", "portfolio_return", "annual_withdrawal", "horizon_years",
        "charity_target",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"demo scenario missing fields: {', '.join(missing)}")
    numeric_fields = (
        "ordinary_income", "long_term_gains", "annual_spending", "home_value",
        "portfolio_return", "annual_withdrawal", "charity_target",
    )
    for key in numeric_fields:
        value = payload[key]
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"demo scenario field {key} must be a finite non-negative number")
    if not isinstance(payload["horizon_years"], int) or payload["horizon_years"] <= 0:
        raise ValueError("demo scenario horizon_years must be a positive integer")
    basis_rate = payload.get("charity_basis_rate", 0.25)
    if not isinstance(basis_rate, (int, float)) or not 0 <= basis_rate <= 1:
        raise ValueError("demo scenario charity_basis_rate must be between 0 and 1")
    return DemoScenario(
        name=str(payload["scenario_name"]),
        ordinary_income=float(payload["ordinary_income"]),
        long_term_gains=float(payload["long_term_gains"]),
        annual_spending=float(payload["annual_spending"]),
        home_value=float(payload["home_value"]),
        portfolio_return=float(payload["portfolio_return"]),
        annual_withdrawal=float(payload["annual_withdrawal"]),
        horizon_years=int(payload["horizon_years"]),
        charity_target=float(payload["charity_target"]),
        charity_basis_rate=float(payload.get("charity_basis_rate", 0.25)),
    )


class DemoPlanningRepository:
    """Synthetic repository used by the public demo and tests."""

    def __init__(self, scenario: DemoScenario | None = None) -> None:
        self.scenario = scenario or load_demo_scenario()

    def load_planning_data(self) -> PlanningData:
        return _build_demo_data(
            self.scenario, event_count=24, demo_clock="2026-01-24", is_live=False,
        )


class LiveDemoRepository:
    """Deterministic synthetic account whose activity advances while it runs.

    This is intentionally a local data source, not a fake network service. One
    virtual day advances every five real seconds, and the event sequence is a
    pure function of that virtual day. Restarting the demo therefore produces
    the same story while an open session visibly receives new transactions.
    """

    def __init__(self, scenario: DemoScenario | None = None, clock=time.monotonic) -> None:
        self.scenario = scenario or load_demo_scenario()
        self._clock = clock
        self._started = clock()

    def load_planning_data(self) -> PlanningData:
        virtual_days = int(max(0, self._clock() - self._started) / 5)
        return _build_demo_data(
            self.scenario,
            event_count=24 + virtual_days,
            demo_clock=(datetime(2026, 1, 1, tzinfo=timezone.utc)
                        + timedelta(days=virtual_days)).date().isoformat(),
            is_live=True,
        )


class SimpleFINRepository:
    """Read-only SimpleFIN Bridge adapter for local personal use.

    The Access URL is read from a protected local file and never persisted by
    this adapter. SimpleFIN does not provide holdings or tax lots, so those
    views remain explicitly unavailable rather than being inferred.
    """

    def __init__(self, access_file: Path) -> None:
        self.access_file = access_file.expanduser()

    def load_planning_data(self) -> PlanningData:
        access_url = self._read_access_url()
        parts = urlsplit(access_url)
        if parts.scheme != "https":
            raise ValueError("SimpleFIN Access URL must use HTTPS")
        query = urlencode({"version": "2"})
        endpoint = urlunsplit(
            (parts.scheme, parts.netloc, parts.path.rstrip("/") + "/accounts", query, "")
        )
        request = Request(endpoint, headers={"Accept": "application/json"})
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        errors = payload.get("errors") or payload.get("errlist") or []
        if errors:
            raise ValueError("SimpleFIN returned errors: " + "; ".join(str(error) for error in errors))
        return self._normalize(payload)

    def _read_access_url(self) -> str:
        mode = stat.S_IMODE(self.access_file.stat().st_mode)
        if mode & 0o077:
            raise ValueError(
                f"SimpleFIN access file must not be group/world-readable: {self.access_file}"
            )
        value = self.access_file.read_text().strip()
        if not value:
            raise ValueError(f"SimpleFIN access file is empty: {self.access_file}")
        return value

    @staticmethod
    def _normalize(payload: dict) -> PlanningData:
        accounts = []
        transactions = []
        latest_date = ""
        for raw_account in payload.get("accounts", []):
            name = str(raw_account.get("name") or raw_account.get("id") or "Unnamed account")
            balance = float(raw_account.get("balance") or 0)
            lowered = name.casefold()
            account_type = "credit" if "credit" in lowered or "card" in lowered else "cash"
            accounts.append(Account(name, account_type, balance))
            for raw_transaction in raw_account.get("transactions", []):
                posted = raw_transaction.get("posted")
                if isinstance(posted, (int, float)):
                    date = datetime.fromtimestamp(posted, tz=timezone.utc).date().isoformat()
                else:
                    date = str(posted or "")[:10]
                latest_date = max(latest_date, date)
                transactions.append(Transaction(
                    date=date,
                    payee=str(raw_transaction.get("description") or "Unlabeled transaction"),
                    amount=float(raw_transaction.get("amount") or 0),
                    category="Uncategorized",
                    account=name,
                ))
        accounts.sort(key=lambda account: account.name.casefold())
        transactions.sort(key=lambda transaction: transaction.date, reverse=True)
        return PlanningData(
            accounts=tuple(accounts), lots=(), locations=(),
            transactions=tuple(transactions), demo_clock=latest_date,
            source_label="SimpleFIN Bridge", is_live=False, scenario=None,
        )


def _build_demo_data(
    scenario: DemoScenario, event_count: int, demo_clock: str, is_live: bool,
) -> PlanningData:
    """Build a synthetic household from a stable, reviewable event recipe."""
    event_recipe = (
        ("Fictional Employer", 4500, "Income", "Sample cash"),
        ("Northstar Rent", -1800, "Housing", "Sample cash"),
        ("Market Basket", -126, "Food", "Sample cash"),
        ("Metro Electric", -94, "Utilities", "Sample cash"),
        ("Cloudstream Internet", -79, "Utilities", "Sample cash"),
        ("Harbor Coffee", -8, "Dining", "Sample cash"),
        ("Brightline Transit", -42, "Transport", "Sample cash"),
        ("Demo Brokerage Dividend", 38, "Investment income", "Demo brokerage"),
        ("Demo Brokerage Contribution", 250, "Transfer", "Demo brokerage"),
        ("Card payment", -220, "Transfer", "Sample cash"),
        ("Willow Pharmacy", -31, "Health", "Sample cash"),
        ("Fictional Charity", -25, "Charity", "Sample cash"),
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    transactions = []
    for index in range(event_count):
        payee, amount, category, account = event_recipe[index % len(event_recipe)]
        day = start + timedelta(days=index)
        transactions.append(Transaction(day.date().isoformat(), payee, amount, category, account))

    balances = {"Sample cash": 1000.0, "Demo brokerage": 25000.0, "Example retirement": 50000.0}
    for transaction in transactions:
        if transaction.account in balances and transaction.category != "Transfer":
            balances[transaction.account] += transaction.amount
    accounts = (
        Account("Sample cash", "cash", balances["Sample cash"]),
        Account("Demo brokerage", "brokerage", balances["Demo brokerage"]),
        Account("Example retirement", "retirement", balances["Example retirement"]),
    )
    return PlanningData(
        accounts=accounts,
        lots=(
            TaxLot("DEMO", 12000 + max(0, event_count - 24) * 20, 1000, True,
                   "2021-04-15"),
            TaxLot("SAMPLE", 9000, 7000, True, "2024-02-01"),
            TaxLot("TEST", 6000, 7200, False, "2026-01-03"),
            TaxLot("GROW", 18000, 15000, True, "2020-09-18"),
        ),
        locations=(
            LocationScenario("Example State A", 18200, "lower income tax; higher property estimate"),
            LocationScenario("Example State B", 21100, "no income tax; higher sales estimate"),
            LocationScenario("Example State C", 23700, "lower housing estimate; higher income tax"),
        ),
        transactions=tuple(transactions),
        demo_clock=demo_clock,
        is_live=is_live,
        scenario=scenario,
    )
