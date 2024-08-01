import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash_ag_grid import AgGrid
from datetime import datetime, timedelta
from qablet_contracts.bnd.fixed import FixedBond
from qablet_contracts.timetable import py_to_ts
from qablet.base.fixed import FixedModel
import numpy as np
from enum import Enum

# Initialize the Dash app
app = dash.Dash(__name__)


# Define the enum for menu actions
class MenuAction(Enum):
    DELETE = 1
    SHOW_TIMETABLE = 2


DEFAULT_MENU = [
    {"label": "Delete", "value": MenuAction.DELETE.value},
    {"label": "Show Timetable", "value": MenuAction.SHOW_TIMETABLE.value},
]


# Function to generate initial bond data
def generate_initial_data():
    return [create_default_bond(index=1)]


# Function to create a new bond with default values
def create_default_bond(index):
    return {
        "Bond": f"Bond {index}",
        "Currency": "USD",
        "Coupon": 2.5,
        "Accrual Start": datetime.today().strftime("%Y-%m-%d"),
        "Maturity": (datetime.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "Frequency": 1,
        "Notional": 100,
        "Price": "$95.965211",
        "Menu": DEFAULT_MENU,
    }


# Column definitions for AG Grid without the delete column
column_defs = [
    {"headerName": "...", "field": "Menu", "cellRenderer": "rowMenu", "width": 100},
    {"headerName": "Bond", "field": "Bond", "editable": False, "width": 100},
    {
        "headerName": "Currency",
        "field": "Currency",
        "editable": True,
        "cellEditor": "agSelectCellEditor",
        "cellEditorParams": {"values": ["USD", "EUR"]},
        "width": 100,
    },
    {
        "headerName": "Coupon",
        "field": "Coupon",
        "editable": True,
        "type": "numericColumn",
        "cellEditor": "agNumberCellEditor",
        "width": 100,
    },
    {
        "headerName": "Accrual Start",
        "field": "Accrual Start",
        "editable": True,
        "cellEditor": "agDateStringCellEditor",
        "width": 150,
    },
    {
        "headerName": "Maturity",
        "field": "Maturity",
        "editable": True,
        "cellEditor": "agDateStringCellEditor",
        "width": 150,
    },
    {
        "headerName": "Frequency",
        "field": "Frequency",
        "editable": True,
        "type": "numericColumn",
        "cellEditor": "agNumberCellEditor",
        "width": 100,
    },
    {
        "headerName": "Notional",
        "field": "Notional",
        "editable": True,
        "type": "numericColumn",
        "cellEditor": "agNumberCellEditor",
        "width": 100,
    },
    {"headerName": "Price", "field": "Price", "editable": False, "width": 100},
]

# Layout of the app
app.layout = html.Div(
    [
        html.Button(
            "Add Bond", id="add-bond-button", n_clicks=0, style={"margin-top": "20px"}
        ),
        html.Button(
            "Delete Selected Bond",
            id="delete-bond-button",
            n_clicks=0,
            style={"margin-top": "20px"},
        ),
        AgGrid(
            id="bond-table",
            rowData=generate_initial_data(),
            columnDefs=column_defs,
            defaultColDef={
                "sortable": True,
                "filter": True,
                "resizable": True,
                "editable": True,
            },
            dashGridOptions={
                "editable": True,
                "rowSelection": "single",
                "animateRows": True,
            },
            style={"height": "80vh", "width": "100%"},
        ),
        dcc.Store(id="bond-store", data=generate_initial_data()),
    ]
)


# Combined callback to handle bond updates, additions, and deletions
@app.callback(
    Output("bond-store", "data"),
    [
        Input("add-bond-button", "n_clicks"),
        Input("delete-bond-button", "n_clicks"),
        Input("bond-table", "cellValueChanged"),
        Input("bond-table", "cellRendererData"),
    ],
    [State("bond-store", "data"), State("bond-table", "selectedRows")],
)
def update_bond_data(
    n_clicks_add, n_clicks_delete, cell_change, menu_data, data, selected_rows
):
    ctx = callback_context

    if not ctx.triggered:
        return data

    trigger = ctx.triggered[0]["prop_id"]

    if trigger == "add-bond-button.n_clicks" and n_clicks_add > 0:
        new_index = len(data) + 1
        new_bond = create_default_bond(index=new_index)
        data.append(new_bond)

    elif trigger == "delete-bond-button.n_clicks" and n_clicks_delete > 0:
        if selected_rows:
            selected_bonds = [row.get("Bond") for row in selected_rows]
            data = [d for d in data if d["Bond"] not in selected_bonds]

    elif trigger == "bond-table.cellRendererData":
        if menu_data.get("value") == MenuAction.DELETE.value:
            row = menu_data.get("rowIndex")
            del data[row]
        elif menu_data.get("value") == MenuAction.SHOW_TIMETABLE.value:
            pass  # To be implemented

    elif trigger == "bond-table.cellValueChanged" and cell_change:
        if isinstance(cell_change, list):
            for change in cell_change:
                row_id = int(change.get("rowIndex", -1))
                field = change.get("colId", "")
                new_value = change.get("value", "")
                if row_id >= 0 and field in data[0]:
                    data[row_id][field] = new_value

        for bond in data:
            # Convert and validate inputs
            coupon = float(bond["Coupon"]) / 100
            accrual_start = datetime.strptime(bond["Accrual Start"], "%Y-%m-%d")
            maturity = datetime.strptime(bond["Maturity"], "%Y-%m-%d")
            frequency = f"{int(bond['Frequency'])}QE"
            currency = bond["Currency"]
            notional = float(bond["Notional"])

            # Create FixedBond with positional arguments
            bond_obj = FixedBond(currency, coupon, accrual_start, maturity, frequency)
            timetable = bond_obj.timetable()

            # Setup the discount data and dataset for pricing
            discount_data = ("ZERO_RATES", np.array([[0.0, 0.04], [5.0, 0.04]]))
            dataset = {
                "BASE": "USD",
                "PRICING_TS": py_to_ts(datetime(2023, 12, 31)).value,
                "ASSETS": {"USD": discount_data},
            }

            # Price the bond using FixedModel
            model = FixedModel()
            price, _ = model.price(timetable, dataset)

            bond["Price"] = f"${price * notional:.6f}"

    return data


# Callback to update the table data
@app.callback(Output("bond-table", "rowData"), Input("bond-store", "data"))
def update_table(data):
    return data


if __name__ == "__main__":
    app.run_server(debug=True)
