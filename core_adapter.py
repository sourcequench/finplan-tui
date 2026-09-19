"""Small adapter from public TUI models to finplan-core commands."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from models import TaxLot


@dataclass(frozen=True)
class DonationSelection:
    allocations: tuple[dict, ...]
    selected_value: int
    selected_basis: int
    selected_gain: int
    unfilled: int


def select_donation_lots(
    lots: Sequence[TaxLot],
    requested_cents: int,
    runner: Callable[[dict], dict] | None = None,
) -> DonationSelection | None:
    """Ask finplan-core to select high-gain long-term lots for review.

    ``runner`` is injectable so applications can choose subprocess, RPC, or a
    library binding. Returning ``None`` means the core command is unavailable;
    the UI can still show the underlying lots without inventing a selection.
    """
    payload = {
        "strategy": "donate_highest_gain",
        "requested_cents": requested_cents,
        "lots": [
            {"id": f"demo-{index}", "symbol": lot.symbol,
             "market_value_cents": round(lot.market_value * 100),
             "cost_basis_cents": round(lot.basis * 100),
             "unrealized_gain_cents": round(lot.gain * 100),
             "long_term": lot.long_term}
            for index, lot in enumerate(lots)
        ],
    }
    runner = runner or lotselection_runner()
    if runner is None:
        return None
    response = runner(payload)
    return DonationSelection(
        tuple(response.get("allocations", [])),
        int(response.get("selected_value_cents", 0)),
        int(response.get("selected_basis_cents", 0)),
        int(response.get("selected_gain_cents", 0)),
        int(response.get("unfilled_cents", 0)),
    )


def subprocess_runner(binary: str) -> Callable[[dict], dict]:
    """Return a bounded JSON runner for an explicitly selected core binary."""
    def run(payload: dict) -> dict:
        process = subprocess.run(
            [binary], input=json.dumps(payload), text=True,
            capture_output=True, check=True, timeout=5,
        )
        return json.loads(process.stdout)
    return run


def taxlocation_runner() -> Callable[[dict], dict] | None:
    """Return the workspace taxlocation command when the public core is built."""
    binary = Path(__file__).resolve().parents[1] / "finplan-core" / "bin" / "taxlocation"
    if not binary.is_file():
        return None

    def run(payload: dict) -> dict:
        process = subprocess.run(
            [str(binary)], input=json.dumps(payload), text=True,
            capture_output=True, check=True, timeout=5,
        )
        return json.loads(process.stdout)

    return run


def lotselection_runner() -> Callable[[dict], dict] | None:
    """Return the workspace lot-selection command when the public core is built."""
    binary = Path(__file__).resolve().parents[1] / "finplan-core" / "bin" / "lotselect"
    if not binary.is_file():
        return None

    def run(payload: dict) -> dict:
        process = subprocess.run(
            [str(binary)], input=json.dumps(payload), text=True,
            capture_output=True, check=True, timeout=5,
        )
        return json.loads(process.stdout)

    return run


def project_taxable_portfolio(
    starting_value: float,
    starting_basis: float,
    annual_return: float,
    annual_withdrawal: float,
    years: int,
    runner: Callable[[dict], list[dict]] | None = None,
) -> list[dict] | None:
    """Run the public core's portfolio projection for the demo retirement view."""
    runner = runner or taxlocation_runner()
    if runner is None:
        return None
    return runner({
        "operation": "portfolio_projection",
        "year": 2026,
        "projection": {
            "starting_portfolio_cents": round(starting_value * 100),
            "starting_basis_cents": round(starting_basis * 100),
            "annual_return_bps": round(annual_return * 10000),
            "annual_contribution_cents": 0,
            "annual_withdrawal_cents": round(annual_withdrawal * 100),
            "annual_withdrawal_growth_bps": 250,
            "gift_year": 2028,
            "gift_fm_cents": 100000,
            "gift_basis_cents": 20000,
            "years": years,
            "terminal_liquidation": True,
        },
    })


def rank_demo_locations(
    scenario=None, runner: Callable[[dict], list[dict]] | None = None,
) -> list[dict] | None:
    """Rank three fictional locations through finplan-core."""
    runner = runner or taxlocation_runner()
    if runner is None:
        return None
    ordinary_income = round(getattr(scenario, "ordinary_income", 120000) * 100)
    long_term_gains = round(getattr(scenario, "long_term_gains", 20000) * 100)
    annual_spending = round(getattr(scenario, "annual_spending", 40000) * 100)
    home_value = getattr(scenario, "home_value", 400000)
    candidate_specs = (
        ("EX-A", round(home_value * 100), 500, 0, 500, 100),
        ("EX-B", round(home_value * 100), 0, 600, 0, 100),
        ("EX-C", round(home_value * 75), 300, 400, 300, 150),
    )
    candidates = []
    for code, property_cents, income_bps, sales_bps, local_income_bps, property_bps in candidate_specs:
        candidates.append({
            "jurisdiction": code,
            "property_cents": property_cents,
            "rules": {
                "jurisdiction": code,
                "tax_year": 2026,
                "income_brackets": ([{"lower_cents": 0, "rate_bps": income_bps}]
                                    if income_bps else []),
                "sales_tax_rate_bps": sales_bps,
                "local_income_tax_rate_bps": local_income_bps,
                "property_tax_rate_bps": property_bps,
                "confidence_bps": 7000,
            },
            "property_prior": {
                "geography": code,
                "tax_year": 2026,
                "expected_rate_bps": property_bps,
                "confidence_bps": 7000,
            },
        })
    return runner({
        "operation": "rank_states",
        "ranking": {
            "year": 2026,
            "inputs": {
                "ordinary_income_cents": ordinary_income,
                "long_term_gains_cents": long_term_gains,
                "taxable_spending_cents": annual_spending,
            },
            "federal_rules": {
                "tax_year": 2026,
                "ordinary_brackets": [{"lower_cents": 0, "rate_bps": 1000}],
                "capital_gain_zero_cents": 0,
                "capital_gain_fifteen_cents": 0,
                "niit_threshold_cents": 999999999,
                "salt_limit_cents": 4000000,
                "niit_rate_bps": 380,
                "confidence_bps": 9000,
            },
            "candidates": candidates,
        },
    })
