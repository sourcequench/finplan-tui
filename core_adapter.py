"""Small adapter from public TUI models to finplan-core commands."""
from __future__ import annotations

import json
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
