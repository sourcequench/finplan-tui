"""Provider-neutral translation for finplan-core tax-lot selection."""
from __future__ import annotations

from collections.abc import Callable, Sequence

from .models import TaxLot


def select_lots(
    lots: Sequence[TaxLot],
    requested_cents: int,
    strategy: str,
    runner: Callable[[dict], dict] | None,
) -> dict | None:
    """Build the shared lot-selection request and execute an injected runner."""
    if requested_cents < 0:
        raise ValueError("requested_cents must be non-negative")
    if not strategy:
        raise ValueError("strategy is required")
    if runner is None:
        return None
    payload = {
        "strategy": strategy,
        "requested_cents": requested_cents,
        "lots": [
            {
                "id": lot.lot_id or f"lot-{index}",
                "symbol": lot.symbol,
                "market_value_cents": round(lot.market_value * 100),
                "cost_basis_cents": round(lot.basis * 100),
                "unrealized_gain_cents": round(lot.gain * 100),
                "long_term": lot.long_term,
            }
            for index, lot in enumerate(lots)
        ],
    }
    return runner(payload)
