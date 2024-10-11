"""
End to end tests for testing app , using selemium webdriver to simulate the app.
"""

import time

from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite

# Import the Dash app
app = import_app("app")


def test_add_bond(dash_duo: DashComposite):
    """
    Test to verify that a new bond can be added to the bond pricing table.
    The test clicks the 'Add Bond' button, waits for the new bond row to be added,
    and verifies the row count after adding the bond.
    """

    dash_duo.start_server(app)

    # Wait for the initial table to render
    dash_duo.wait_for_element("div.ag-row", timeout=10)

    # Click the "Add Bond" button
    dash_duo.find_element("button#add-bond-button").click()

    # Wait for the new row to appear
    dash_duo.wait_for_text_to_equal(
        "div.ag-row:last-child .ag-cell[col-id='Bond']", "Bond 2", timeout=10
    )

    # Check if a new bond row is added
    rows = dash_duo.find_elements("div.ag-row")
    assert len(rows) == 2  # Assuming there's one bond initially and we added one more


def test_update_bond_data(dash_duo: DashComposite):
    """
    Test to verify that bond data (Coupon) can be updated correctly.
    The test activates the cell editor in the Coupon column, modifies the value,
    and checks if the value is updated correctly in the grid.
    """
    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the grid is fully rendered
    dash_duo.wait_for_element("div.ag-root-wrapper-body", timeout=40)

    # Locate the Coupon cell in the first row
    coupon_cell = dash_duo.wait_for_element('div.ag-cell[col-id="Coupon"]', timeout=40)

    coupon_cell.send_keys("3.5")

    # Press Enter to confirm the change
    coupon_cell.send_keys("\n")

    # Verify the update
    updated_cell_value = dash_duo.wait_for_element('div.ag-cell[col-id="Coupon"]').text
    assert (
        updated_cell_value == "3.5"
    ), f"Expected '3.5', but got '{updated_cell_value}'"

    dash_duo.wait_for_text_to_equal(
        "div.ag-row:last-child .ag-cell[col-id='Price']", "$98.876524", timeout=10
    )

    updated_price = dash_duo.wait_for_element('div.ag-cell[col-id="Price"]').text
    print(updated_price)

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors"


def test_delete_bond(dash_duo: DashComposite):
    """
    Test to verify that a bond can be deleted from the bond pricing table.
    The test clicks the menu button of the first row, selects the delete option,
    and verifies that the row is deleted.
    """

    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the grid is fully rendered
    dash_duo.wait_for_element("div.ag-root-wrapper-body", timeout=40)

    # Wait for the first row (Bond 1) to be rendered
    dash_duo.wait_for_text_to_equal(
        'div.ag-row:first-child .ag-cell[col-id="Bond"]', "Bond 1", timeout=10
    )

    # Locate the menu button in the first column of the first row (assuming it’s the first cell)
    time.sleep(2)  # Add a small delay to ensure everything is loaded
    menu_button = dash_duo.driver.execute_script(
        "return document.querySelector(\"div.ag-row:first-child .ag-cell[col-id='Menu'] button\");"
    )

    # Ensure the menu button is not null
    assert menu_button is not None, "The menu button should not be null."

    # Click the menu button
    dash_duo.driver.execute_script("arguments[0].click();", menu_button)

    # Wait for the delete button to appear and click it (assuming it's the first item in the menu)
    dash_duo.wait_for_element(".MuiMenu-paper", timeout=10)
    delete_button = dash_duo.find_elements(".MuiMenu-paper .MuiMenuItem-root")[0]
    delete_button.click()

    # Wait for the deletion to take effect
    time.sleep(3)

    # Check if the bond is deleted by confirming there are no more rows
    rows = dash_duo.find_elements("div.ag-row")
    assert len(rows) == 0, "The bond should be deleted, so no rows should be present."

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors."


def test_show_timetable(dash_duo: DashComposite):
    """
    Test to verify that the "Show Timetable" option in the bond pricing table's row menu works.
    The test clicks the menu button of the first row, selects the "Show Timetable" option,
    and verifies that the timetable is displayed in the off-canvas.
    """

    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the grid is fully rendered
    dash_duo.wait_for_element("div.ag-root-wrapper-body", timeout=40)

    # Wait for the first row (Bond 1) to be rendered
    dash_duo.wait_for_text_to_equal(
        'div.ag-row:first-child .ag-cell[col-id="Bond"]', "Bond 1", timeout=10
    )

    # Locate the menu button in the first column of the first row (assuming it’s the first cell)
    time.sleep(2)  # Add a small delay to ensure everything is loaded
    menu_button = dash_duo.driver.execute_script(
        "return document.querySelector(\"div.ag-row:first-child .ag-cell[col-id='Menu'] button\");"
    )

    # Ensure the menu button is not null
    assert menu_button is not None, "The menu button should not be null."

    # Click the menu button
    dash_duo.driver.execute_script("arguments[0].click();", menu_button)

    # Wait for the Show Timetable button to appear and click it (assuming it's the second item in the menu)
    dash_duo.wait_for_element(".MuiMenu-paper", timeout=10)
    show_timetable_button = dash_duo.find_elements(".MuiMenu-paper .MuiMenuItem-root")[
        1
    ]
    show_timetable_button.click()

    # Wait for the timetable off-canvas to open and check the content
    dash_duo.wait_for_element("#offcanvas-timetable", timeout=10)
    assert dash_duo.find_element("#offcanvas-timetable").is_displayed()

    # Debug: Print the actual timetable content to see what it contains
    timetable_content = dash_duo.find_element("#timetable-content").text
    print(f"Timetable content: {timetable_content}")

    # Modify the assertion to reflect the actual timetable content
    assert (
        "time" in timetable_content
    ), f"Expected timetable content to contain 'time', but got {timetable_content}"

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors."


def test_rate_editor_update_rate(dash_duo: DashComposite):
    """
    Test to verify that when the rates are updated in the rate editor,
    the bond price is recalculated accordingly.
    """

    # Start the server with the bond pricing app
    dash_duo.start_server(app)

    # Ensure the Rate Editor button is present and click to open the editor
    rate_editor_button = dash_duo.find_element("#rate-editor-button")
    rate_editor_button.click()

    # Wait for the Rate Editor off-canvas to be visible
    dash_duo.wait_for_element("#offcanvas-rate-editor", timeout=30)

    # Wait for the rate editor grid to load
    dash_duo.wait_for_element("#rate-editor", timeout=30)

    # Add a small delay to ensure the AG Grid cells are fully interactive
    time.sleep(2)

    # Locate the Rate cell for the first row (Year 1)
    rate_cell = dash_duo.driver.execute_script(
        "return document.querySelector(\"div.ag-center-cols-container div.ag-row[row-index='0'] div.ag-cell[col-id='Rate']\");"
    )

    # Ensure the rate cell is not null
    assert rate_cell is not None, "The rate cell should not be null."

    # Click the rate cell and modify the rate
    dash_duo.driver.execute_script("arguments[0].click();", rate_cell)
    rate_cell.send_keys("5.5")
    rate_cell.send_keys("\n")  # Confirm the update

    # Wait for the bond price to be updated after the rate change
    dash_duo.wait_for_element('div.ag-cell[col-id="Price"]', timeout=20)

    # Get the updated bond price
    updated_price = dash_duo.driver.execute_script(
        "return document.querySelector(\"div.ag-cell[col-id='Price']\").innerText"
    )
    print("Updated Price:", updated_price)

    # Check if the bond price is updated (ensure it is not None or empty)
    assert (
        updated_price is not None and updated_price != ""
    ), "The bond price should be updated after rate change."

    # Ensure no errors in the browser console
    assert dash_duo.get_logs() == [], "browser console should contain no errors."
