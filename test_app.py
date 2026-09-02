from repository import DemoPlanningRepository
from core_adapter import select_donation_lots


def test_demo_data_is_synthetic_and_complete():
    data = DemoPlanningRepository().load_planning_data()
    assert len(data.accounts) == 3
    assert len(data.lots) == 3
    assert len(data.locations) == 3
    assert data.lots[0].gain == 1100


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
