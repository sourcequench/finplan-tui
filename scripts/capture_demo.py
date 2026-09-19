#!/usr/bin/env python3
"""Capture deterministic public-demo screens for documentation."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

from textual.widgets import Static

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import FinplanTUI  # noqa: E402
from repository import DemoPlanningRepository  # noqa: E402


async def capture(width: int, height: int, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    repository = DemoPlanningRepository()
    app = FinplanTUI(repository.load_planning_data(), repository)
    async with app.run_test(headless=True, size=(width, height)) as pilot:
        await pilot.pause(0.2)
        screens = (
            ("dashboard", None),
            ("lots", "2"),
            ("locations", "3"),
            ("cashflow", "4"),
            ("recurring", "5"),
            ("retirement", "6"),
            ("tour", "h"),
        )
        for name, key in screens:
            if key is not None:
                await pilot.press(key)
                await pilot.pause(0.2)
            if not app.screen.query(Static):
                raise RuntimeError(f"{name} has no rendered content")
            app.save_screenshot(f"{name}.svg", str(output))


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture static synthetic finplan-tui screens")
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=45)
    parser.add_argument("--output", type=Path, default=Path("screenshots"))
    args = parser.parse_args()
    asyncio.run(capture(args.width, args.height, args.output))


if __name__ == "__main__":
    main()
