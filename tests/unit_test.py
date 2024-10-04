from contextvars import copy_context
from dash._callback_context import context_value
from dash._utils import AttributeDict
from app_aggrid import update_bond_data, update_table
from datetime import datetime

def test_update_bond_data():
    # Simulate an "add bond" click event
    initial_data = [{
        'Bond': 'Bond 1', 
        'Currency': 'USD', 
        'Coupon': 2.5, 
        'Accrual Start': '2023-12-31', 
        'Maturity': '2024-12-31', 
        'Frequency': 1, 
        'Notional': 1000000, 
        'Price': None, 
        'Menu': [{"label": "Delete", "value": 1}, {"label": "Show Timetable", "value": 2}]
    }]
    pricing_datetime = '2023-12-31'  # Updated pricing date
    
    # Correctly passing the required data argument, including pricing_datetime
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": "add-bond-button.n_clicks"}]}))
        return update_bond_data(1, None, None, None, pricing_datetime, initial_data)

    ctx = copy_context()
    updated_data = ctx.run(run_callback)
    
    # Check if a new bond was added
    assert len(updated_data) == 2
    assert updated_data[1]['Bond'] == 'Bond 2'


def test_rate_update():
    # Mock rate update event with necessary bond fields
    initial_data = [{
        'Bond': 'Bond 1', 
        'Currency': 'USD', 
        'Coupon': 5.0, 
        'Accrual Start': '2023-12-31', 
        'Maturity': '2024-12-31', 
        'Frequency': 1, 
        'Notional': 1000000, 
        'Price': None, 
        'Menu': [{"label": "Delete", "value": 1}, {"label": "Show Timetable", "value": 2}]
    }]
    pricing_datetime = '2023-12-31'  # Updated pricing date
    mock_rate_data = [{'Year': 1.0, 'Rate': 5.0}, {'Year': 2.0, 'Rate': 4.5}]

    # Correctly passing the required rate_data argument, including pricing_datetime
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": "rate-editor.cellValueChanged"}]}))
        return update_table(initial_data, pricing_datetime, mock_rate_data)

    ctx = copy_context()
    updated_data = ctx.run(run_callback)
    
    # Check if bond prices were updated after rate change
    assert updated_data[0]['Price'] is not None


def test_price_recalculation():
    # Initial bond data with missing prices and necessary bond fields
    bond_data = [{
        'Bond': 'Bond 1', 
        'Currency': 'USD', 
        'Coupon': 5.0, 
        'Accrual Start': '2023-12-31', 
        'Maturity': '2024-12-31', 
        'Frequency': 1, 
        'Notional': 1000000, 
        'Price': None, 
        'Menu': [{"label": "Delete", "value": 1}, {"label": "Show Timetable", "value": 2}]
    }]
    
    # Mock rate data
    rate_data = [{'Year': 1.0, 'Rate': 5.0}, {'Year': 2.0, 'Rate': 4.5}]
    pricing_datetime = '2023-12-31'  # Updated pricing date
    
    # Correctly passing both bond_data, rate_data, and pricing_datetime arguments
    def run_callback():
        return update_table(bond_data, pricing_datetime, rate_data)

    ctx = copy_context()
    updated_bond_data = ctx.run(run_callback)
    
    # Check that price and duration are updated
    assert updated_bond_data[0]['Price'] is not None
    assert updated_bond_data[0]['Duration'] is not None
