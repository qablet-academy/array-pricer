"""
Test callbacks.
"""

from contextvars import copy_context

from dash._callback_context import context_value
from dash._utils import AttributeDict

from app_aggrid import show_timetable, update_bond_data, update_rate_graph, update_table


def test_update_bond_data():
    # Simulate an "add bond" click event
    initial_data = [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 2.5,
            "Accrual Start": "2023-12-31",
            "Maturity": "2024-12-31",
            "Frequency": 1,
            "Notional": 1000000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        }
    ]
    pricing_datetime = "2023-12-31"  # Updated pricing date

    # Correctly passing the required data argument, including pricing_datetime
    def run_callback():
        context_value.set(
            AttributeDict(
                **{"triggered_inputs": [{"prop_id": "add-bond-button.n_clicks"}]}
            )
        )
        return update_bond_data(1, None, None, None, pricing_datetime, initial_data)

    ctx = copy_context()
    updated_data = ctx.run(run_callback)

    # Check if a new bond was added
    assert len(updated_data) == 2
    assert updated_data[1]["Bond"] == "Bond 2"


def test_rate_update():
    # Mock rate update event with necessary bond fields
    initial_data = [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 5.0,
            "Accrual Start": "2023-12-31",
            "Maturity": "2024-12-31",
            "Frequency": 1,
            "Notional": 1000000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        }
    ]
    pricing_datetime = "2023-12-31"  # Updated pricing date
    mock_rate_data = [{"Year": 1.0, "Rate": 5.5}, {"Year": 2.0, "Rate": 4.7}]

    # Correctly passing the required rate_data argument, including pricing_datetime
    def run_callback():
        context_value.set(
            AttributeDict(
                **{"triggered_inputs": [{"prop_id": "rate-editor.cellValueChanged"}]}
            )
        )
        return update_table(initial_data, pricing_datetime, mock_rate_data)

    ctx = copy_context()
    updated_data = ctx.run(run_callback)

    # Check if bond prices were updated after rate change
    assert updated_data[0]["Price"] is not None


def test_price_recalculation():
    # Initial bond data with missing prices and necessary bond fields
    bond_data = [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 5.0,
            "Accrual Start": "2023-12-31",
            "Maturity": "2024-12-31",
            "Frequency": 1,
            "Notional": 1000000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        }
    ]

    # Mock rate data
    rate_data = [{"Year": 1.0, "Rate": 5.0}, {"Year": 2.0, "Rate": 4.5}]
    pricing_datetime = "2023-12-31"  # Updated pricing date

    # Correctly passing both bond_data, rate_data, and pricing_datetime arguments
    def run_callback():
        return update_table(bond_data, pricing_datetime, rate_data)

    ctx = copy_context()
    updated_bond_data = ctx.run(run_callback)

    # Check that price and duration are updated
    assert updated_bond_data[0]["Price"] is not None
    assert updated_bond_data[0]["Duration"] is not None


def test_delete_bond():
    # Initial bond data with two bonds
    initial_data = [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 5.0,
            "Accrual Start": "2023-12-31",
            "Maturity": "2024-12-31",
            "Frequency": 1,
            "Notional": 1000000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        },
        {
            "Bond": "Bond 2",
            "Currency": "USD",
            "Coupon": 3.5,
            "Accrual Start": "2023-12-31",
            "Maturity": "2025-12-31",
            "Frequency": 1,
            "Notional": 500000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        },
    ]
    pricing_datetime = "2023-12-31"  # Pricing date

    # Simulate deleting the first bond
    def run_callback():
        context_value.set(
            AttributeDict(
                **{"triggered_inputs": [{"prop_id": "bond-table.cellRendererData"}]}
            )
        )
        return update_bond_data(
            None,
            None,
            {"value": 1, "rowIndex": 0},
            None,
            pricing_datetime,
            initial_data,
        )

    ctx = copy_context()
    updated_data = ctx.run(run_callback)

    # Check that only one bond remains after deletion
    assert len(updated_data) == 1
    assert updated_data[0]["Bond"] == "Bond 2"


def test_show_timetable():
    # Initial bond data with one bond
    initial_data = [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 5.0,
            "Accrual Start": "2023-12-31",
            "Maturity": "2024-12-31",
            "Frequency": 1,
            "Notional": 1000000,
            "Price": None,
            "Menu": [
                {"label": "Delete", "value": 1},
                {"label": "Show Timetable", "value": 2},
            ],
        }
    ]
    pricing_datetime = "2023-12-31"  # Pricing date

    # Simulate showing the timetable for the first bond
    def run_callback():
        context_value.set(
            AttributeDict(
                **{"triggered_inputs": [{"prop_id": "bond-table.cellRendererData"}]}
            )
        )
        return show_timetable({"value": 2, "rowIndex": 0}, initial_data)

    ctx = copy_context()
    timetable_data, is_open = ctx.run(run_callback)

    # Check that the timetable is returned and offcanvas is opened
    assert timetable_data != ""
    assert is_open is True


def test_rate_graph_update():
    # Mock rate data with compatible shapes
    rate_data = [
        {"Year": 1.0, "Rate": 5.0},
        {"Year": 2.0, "Rate": 4.5},
        {"Year": 5.0, "Rate": 4.0},
    ]

    def run_callback():
        return update_rate_graph(None, rate_data)

    ctx = copy_context()
    figure = ctx.run(run_callback)

    # Ensure the rate graph figure is correctly generated
    assert figure is not None
    assert len(figure["data"]) > 0
    assert len(figure["data"][0]["x"]) == len(
        figure["data"][0]["y"]
    )  # X and Y data must match in length
