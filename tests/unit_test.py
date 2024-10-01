# # test_app_callbacks.py
# """
# unit test for testing single callbacks

# """
# from contextvars import copy_context
# from dash._callback_context import context_value
# from dash._utils import AttributeDict
# from app_aggrid import update_bond_data, update_table

# def test_update_bond_data():

#     """
#     Test to simulate adding a bond via the "Add Bond" button.
    
#     The function mocks the "add-bond-button.n_clicks" event and checks:
#     - Whether a new bond row is added to the data.
#     - Ensures that the second bond has the expected default name "Bond 2".
#     """
    
#     # Simulate an "add bond" click event
#     initial_data = [{'Bond': 'Bond 1', 'Price': None}]
#     def run_callback():
#         context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": "add-bond-button.n_clicks"}]}))
#         return update_bond_data(1, None, None, None, initial_data)

#     ctx = copy_context()
#     updated_data = ctx.run(run_callback)
    
#     # Check if a new bond was added
#     assert len(updated_data) == 2
#     assert updated_data[1]['Bond'] == 'Bond 2'


# def test_rate_update():

#     """
#     Test to simulate rate updates and check bond price recalculation.

#     The function mocks a "rate-editor.cellValueChanged" event and checks:
#     - Whether the bond price is recalculated when the rates change.
#     - Ensures that the price field is updated after a rate change.
#     """

#     # Mock rate update event with necessary bond fields
#     initial_data = [{
#         'Bond': 'Bond 1', 
#         'Price': None, 
#         'Coupon': 5.0, 
#         'Notional': 1000000, 
#         'Accrual Start': '2020-01-01'
#     }]
#     mock_rate_data = [{'Year': 1.0, 'Rate': 5.0}, {'Year': 2.0, 'Rate': 4.5}]
    
#     def run_callback():
#         context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": "rate-editor.cellValueChanged"}]}))
#         return update_table(initial_data, mock_rate_data)

#     ctx = copy_context()
#     updated_data = ctx.run(run_callback)
    
#     # Check if bond prices were updated after rate change
#     assert updated_data[0]['Price'] is not None


# def test_price_recalculation():

#     """
#     Test to simulate bond price and duration recalculations.

#     The function simulates a rate change event and checks:
#     - Whether both the bond price and duration are correctly recalculated.
#     - Ensures that both fields are updated in the bond data.
#     """
    
#     # Initial bond data with missing prices and necessary bond fields
#     bond_data = [{
#         'Bond': 'Bond 1', 
#         'Price': None, 
#         'Coupon': 5.0, 
#         'Notional': 1000000, 
#         'Accrual Start': '2020-01-01'
#     }]
    
#     # Mock rate data
#     rate_data = [{'Year': 1.0, 'Rate': 5.0}, {'Year': 2.0, 'Rate': 4.5}]
    
#     # Simulate recalculation after rate change
#     def run_callback():
#         return update_table(bond_data, rate_data)

#     ctx = copy_context()
#     updated_bond_data = ctx.run(run_callback)
    
#     # Check that price and duration are updated
#     assert updated_bond_data[0]['Price'] is not None
#     assert updated_bond_data[0]['Duration'] is not None


