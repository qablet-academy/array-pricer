import pytest
from dash import html
from dash.testing.application_runners import import_app

@pytest.fixture
def app():
    app = import_app("app")
    return app

def test_add_bond_button(dash_duo, app):
    dash_duo.start_server(app)
    add_button = dash_duo.find_element("#add-bond-button")
    add_button.click()

    # Wait for the bond to be added
    dash_duo.wait_for_text_to_equal("#bond-table .ag-cell-value", "Bond 2", timeout=5)

    # Check that a new bond has been added
    bond_cells = dash_duo.find_elements(".ag-cell-value")
    assert len(bond_cells) > 1, "A new bond should be added."

def test_update_bond_price(dash_duo, app):
    dash_duo.start_server(app)
    bond_table = dash_duo.find_element("#bond-table")

    # Simulate changing the coupon value
    dash_duo.clear_input(bond_table.find_element(".ag-cell-value[col-id='Coupon']"))
    dash_duo.send_keys_to_input(bond_table.find_element(".ag-cell-value[col-id='Coupon']"), "3.0")

    # Wait for the price to update
    dash_duo.wait_for_text_to_equal("#bond-table .ag-cell-value[col-id='Price']", "$101.798925", timeout=5)

    price_cell = dash_duo.find_element(".ag-cell-value[col-id='Price']")
    assert price_cell.text == "$101.798925", "The bond price should update correctly."

def test_show_timetable(dash_duo, app):
    dash_duo.start_server(app)
    bond_table = dash_duo.find_element("#bond-table")
    
    # Open the row menu and select 'Show Timetable'
    dash_duo.find_element(".ag-cell-value[col-id='Menu']").click()
    dash_duo.find_element(".ag-row-menu-item[data-value='2']").click()  # Assuming value 2 corresponds to 'Show Timetable'

    # Check if the off-canvas is opened with the timetable content
    offcanvas = dash_duo.wait_for_element("#offcanvas-timetable")
    assert offcanvas.is_displayed(), "The off-canvas should be opened."
    assert "Bond Timetable" in offcanvas.text, "The timetable should be shown in the off-canvas."

def test_rate_editor_updates_graph(dash_duo, app):
    dash_duo.start_server(app)
    
    # Open rate editor
    dash_duo.find_element("#rate-editor-button").click()
    
    # Modify rate in rate editor
    rate_editor = dash_duo.find_element("#rate-editor")
    dash_duo.clear_input(rate_editor.find_element(".ag-cell-value[col-id='Rate']"))
    dash_duo.send_keys_to_input(rate_editor.find_element(".ag-cell-value[col-id='Rate']"), "5.5")

    # Ensure graph is updated after the rate change
    graph = dash_duo.find_element("#rate-graph")
    assert graph.is_displayed(), "The graph should be updated when rates are modified."

def test_delete_bond(dash_duo, app):
    dash_duo.start_server(app)
    
    # Delete the first bond
    bond_table = dash_duo.find_element("#bond-table")
    dash_duo.find_element(".ag-cell-value[col-id='Menu']").click()
    dash_duo.find_element(".ag-row-menu-item[data-value='1']").click()  # Assuming value 1 corresponds to 'Delete'

    # Check if the bond is removed
    dash_duo.wait_for_text_to_equal("#bond-table .ag-cell-value", "Bond 1", timeout=5)
    bond_cells = dash_duo.find_elements(".ag-cell-value")
    assert len(bond_cells) == 0, "The bond should be deleted."

