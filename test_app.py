import asyncio

from app import FinplanTUI
from repository import DemoPlanningRepository, LiveDemoRepository, SimpleFINRepository
from core_adapter import rank_demo_locations, select_donation_lots
from finplan_tui.lot_adapter import select_lots
from finplan_tui.models import CashflowData, RecurringData, SpendingData
from finplan_tui.formatting import format_cents, format_dollars
from finplan_tui.widgets import format_signed_cents


def test_demo_data_is_synthetic_and_complete():
    data = DemoPlanningRepository().load_planning_data()
    assert len(data.accounts) == 3
    assert len(data.lots) == 4
    assert len(data.locations) == 3
    assert data.lots[0].gain == 11000


def test_core_adapter_translates_lots_without_running_a_process():
    lots = DemoPlanningRepository().load_planning_data().lots
    seen = {}

    def fake_runner(payload):
        seen.update(payload)
        return {"allocations": [], "selected_value_cents": 1000000,
                "selected_basis_cents": 150000, "selected_gain_cents": 850000,
                "unfilled_cents": 0}

    result = select_donation_lots(lots, 1000000, fake_runner)
    assert result.selected_gain == 850000
    assert seen["strategy"] == "donate_highest_gain"
    assert seen["lots"][0]["symbol"] == "DEMO"


def test_shared_lot_adapter_supports_private_strategy_names():
    lots = DemoPlanningRepository().load_planning_data().lots
    seen = {}

    result = select_lots(lots, 1000, "sell_lowest_gain", lambda payload: seen.update(payload) or {})

    assert result == {}
    assert seen["strategy"] == "sell_lowest_gain"
    assert seen["requested_cents"] == 1000


def test_shared_operational_models_round_trip_legacy_payloads():
    spending = {"monthly": {"Food": {"2026-09": 125}}, "raw_txns": {}, "anomalies": []}
    cashflow = {"cashflow": {"2026-09": {"income": 100}},
                "planned_obligations": [], "reconciliation": {"duplicates": []}}
    recurring = [{"payee_name": "Example", "months_seen": 3}]

    assert SpendingData.from_legacy(spending).to_legacy_dict() == spending
    assert CashflowData.from_legacy(cashflow).to_legacy_dict() == cashflow
    assert RecurringData.from_legacy(recurring).to_legacy_rows() == recurring


def test_shared_currency_formatting_is_stable():
    assert format_dollars(1250.4) == "$1,250"
    assert format_cents(125100) == "$1,251"
    assert format_cents(-12) == "-$0.12"
    assert format_cents(None) == "—"
    assert format_signed_cents(12500) == ("+$125.00", "bright_green")
    assert format_signed_cents(-12500) == ("−$125.00", "bright_red")


def test_core_adapter_translates_location_ranking():
    seen = {}

    def fake_runner(payload):
        seen.update(payload)
        return [{"jurisdiction": "EX-B", "total_tax_cents": 100,
                 "state_tax_cents": 50, "property_tax_cents": 20}]

    result = rank_demo_locations(runner=fake_runner)
    assert result[0]["jurisdiction"] == "EX-B"
    assert seen["operation"] == "rank_states"
    assert len(seen["ranking"]["candidates"]) == 3


def test_live_demo_stream_advances_without_randomness():
    current = [100.0]
    repository = LiveDemoRepository(clock=lambda: current[0])
    first = repository.load_planning_data()
    current[0] += 5.0
    second = repository.load_planning_data()

    assert first.is_live is True
    assert second.is_live is True
    assert len(second.transactions) == len(first.transactions) + 1
    assert second.demo_clock == "2026-01-02"
    assert second.lots[0].market_value == first.lots[0].market_value + 20


def test_simplefin_normalizes_accounts_and_transactions_without_inventing_lots():
    data = SimpleFINRepository._normalize({
        "accounts": [{
            "name": "Checking",
            "balance": "1250.50",
            "transactions": [{
                "posted": 1767225600,
                "description": "Example merchant",
                "amount": "-12.50",
            }],
        }],
    })
    assert data.source_label == "SimpleFIN Bridge"
    assert data.accounts[0].balance == 1250.50
    assert data.transactions[0].payee == "Example merchant"
    assert data.lots == ()
    assert data.scenario is None


def test_live_tui_refreshes_visible_dashboard():
    current = [100.0]
    repository = LiveDemoRepository(clock=lambda: current[0])
    app = FinplanTUI(repository.load_planning_data(), repository)

    async def exercise():
        async with app.run_test(headless=True, size=(100, 30)) as pilot:
            await pilot.pause(0.1)
            current[0] += 5.0
            app.refresh_demo_data()
            await pilot.pause(0.1)
            body = str(app.screen.query_one("#dashboard-body").render())
            assert "2026-01-02" in body
            assert "Transactions received: 25" in body
            await pilot.press("4")
            await pilot.pause(0.1)
            cashflow = str(app.screen.query_one("#cashflow-body").render())
            assert "CASHFLOW REVIEW" in cashflow
            assert "New synthetic activity" in cashflow
            await pilot.press("5")
            await pilot.pause(0.1)
            recurring = str(app.screen.query_one("#recurring-body").render())
            assert "RECURRING REVIEW" in recurring
            await pilot.press("6")
            await pilot.pause(0.1)
            retirement = str(app.screen.query_one("#retirement-body").render())
            assert "RETIREMENT BRIDGE" in retirement
            await pilot.press("h")
            await pilot.pause(0.1)
            assert "FINPLAN-TUI TOUR" in str(app.screen.query_one("#tour-body").render())
            await pilot.press("escape")

    asyncio.run(exercise())
