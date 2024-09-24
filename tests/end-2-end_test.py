import time
import pytest
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

# Import the Dash app
app = import_app("app_aggrid")

def test_add_bond(dash_duo: DashComposite):
    dash_duo.start_server(app)

    # Wait for the initial table to render
    dash_duo.wait_for_element("div.ag-row", timeout=10)
    
    # Click the "Add Bond" button
    dash_duo.find_element("button#add-bond-button").click()
    
    # Wait for the new row to appear
    dash_duo.wait_for_text_to_equal("div.ag-row:last-child .ag-cell[col-id='Bond']", "Bond 2", timeout=10)
    
    # Check if a new bond row is added
    rows = dash_duo.find_elements("div.ag-row")
    assert len(rows) == 2  # Assuming there's one bond initially and we added one more

def test_update_bond_data(dash_duo: DashComposite):
    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the grid is fully rendered
    dash_duo.wait_for_element('div.ag-root-wrapper-body', timeout=40)

    # Locate the Coupon cell in the first row
    coupon_cell = dash_duo.wait_for_element('div.ag-cell[col-id="Coupon"]', timeout=40)

    # Double-click to activate the cell editor
    action = ActionChains(dash_duo.driver)
    action.double_click(coupon_cell).perform()

    # Wait for the editor input to appear
    time.sleep(2)  # Adjust this sleep time if necessary
    input_element = dash_duo.driver.execute_script('return document.querySelector(".ag-popup-editor input");')

    # Ensure the input element is not null
    assert input_element is not None, "The input element should not be null."

    # Clear the input and send new keys
    dash_duo.driver.execute_script('arguments[0].value = "";', input_element)
    input_element.send_keys('3.5')

    # Press Enter to confirm the change
    input_element.send_keys("\n")

    # Verify the update
    updated_cell_value = dash_duo.wait_for_element('div.ag-cell[col-id="Coupon"]').text
    assert updated_cell_value == '3.5', f"Expected '3.5', but got '{updated_cell_value}'"

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors"


def test_delete_bond(dash_duo: DashComposite):
    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the grid is fully rendered
    dash_duo.wait_for_element('div.ag-root-wrapper-body', timeout=40)

    # Locate the menu button in the first column of the first row
    time.sleep(2)  # Adjust this sleep time if necessary
    menu_button = dash_duo.driver.execute_script(
        'return document.querySelector("div.ag-row:first-child div.ag-row-menu-button");'
    )

    # Ensure the menu button is not null
    assert menu_button is not None, "The menu button should not be null."

    # Click the menu button using JavaScript
    dash_duo.driver.execute_script("arguments[0].click();", menu_button)

    # Wait for the delete button to appear and click it
    delete_button = dash_duo.wait_for_element('button.ag-row-menu-delete', timeout=40)
    delete_button.click()

    # Wait for the deletion to take effect
    time.sleep(3)

    # Check if the bond is deleted
    rows = dash_duo.find_elements('div.ag-row')
    assert len(rows) == 0, "The bond should be deleted, so no rows should be present"

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors"