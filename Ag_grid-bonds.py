import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash_ag_grid import AgGrid
from datetime import datetime, timedelta
from qablet_contracts.bnd.fixed import FixedBond
from qablet_contracts.timetable import py_to_ts
from qablet.base.fixed import FixedModel
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Function to generate initial bond data
def generate_initial_data():
    return [
        create_default_bond(index=1)
    ]

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
        "menu": [
            {"label": "Delete Bond", "value": "delete"},
            {"label": "Show Timetable", "value": "timetable"},
        ],
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
        html.Button(
            "Delete Selected Bond", id="delete-bond-button", n_clicks=0, style={"margin-top": "20px"}
        ),
        dcc.Store(id="bond-store", data=generate_initial_data()),
        html.Div(
            id="offcanvas-timetable",
            className="offcanvas offcanvas-end",
            tabIndex="-1",
            style={"width": "300px"},
            children=[
                html.Div(
                    className="offcanvas-header",
                    children=[
                        html.H5("Bond Timetable", className="offcanvas-title"),
                        html.Button(
                            type="button",
                            className="btn-close",
                            **{"data-bs-dismiss": "offcanvas"},
                            **{"aria-label": "Close"}
                        )
                    ]
                ),
                html.Div(id="timetable-content", className="offcanvas-body")
            ]
        ),
        html.P(id="cellrenderer-data"),
    ]
)

# Callback to add a new bond
@app.callback(
    Output("bond-store", "data"),
    Input("add-bond-button", "n_clicks"),
    State("bond-store", "data"),
    prevent_initial_call=True
)
def add_bond(n_clicks_add, data):
    if n_clicks_add > 0:
        new_index = len(data) + 1
        new_bond = create_default_bond(index=new_index)
        data.append(new_bond)
    return data

# Callback to handle cell renderer data
@app.callback(
    Output("bond-store", "data", allow_duplicate=True),
    Output("timetable-content", "children"),
    Output("cellrenderer-data", "children"),
    Input("bond-table", "cellRendererData"),
    State("bond-store", "data"),
    prevent_initial_call=True
)
def handle_menu_actions(cell_renderer_data, data):
    print("Cell Renderer Data Callback Triggered")
    if cell_renderer_data:
        col_id = cell_renderer_data.get("colId", "")
        row_index = cell_renderer_data.get("rowIndex", -1)
        value = cell_renderer_data.get("value", "")
        print(f"Cell Renderer Data: col_id={col_id}, row_index={row_index}, value={value}")

        timetable_content = ""
        cellrenderer_text = f"You selected option {value} from the colId {col_id}, rowIndex {row_index}."

        if row_index >= 0 and col_id == "menu":
            if value == "delete":
                bond_to_delete = data[row_index]["Bond"]
                data = [d for d in data if d["Bond"] != bond_to_delete]
            elif value == "timetable":
                bond = data[row_index]
                coupon = float(bond["Coupon"]) / 100
                accrual_start = datetime.strptime(bond["Accrual Start"], "%Y-%m-%d")
                maturity = datetime.strptime(bond["Maturity"], "%Y-%m-%d")
                frequency = f"{int(bond['Frequency'])}QE"
                currency = bond["Currency"]
                notional = float(bond["Notional"])

                bond_obj = FixedBond(currency, coupon, accrual_start, maturity, frequency)
                events = bond_obj.print_events()
                timetable_content = html.Pre(events)

        return data, timetable_content, cellrenderer_text
    return dash.no_update, dash.no_update, "No menu item selected."

# Callback to update the table data
@app.callback(Output("bond-table", "rowData"), Input("bond-store", "data"))
def update_table(data):
    return data

# Callback to handle bond data changes and pricing
@app.callback(
    Output("bond-store", "data", allow_duplicate=True),
    Input("bond-table", "cellValueChanged"),
    State("bond-store", "data"),
    prevent_initial_call=True
)
def update_bond_data(cell_change, data):
    if cell_change:
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

# Callback to show timetable in the off-canvas
@app.callback(
    [Output("timetable-content", "children"),
     Output("offcanvas-timetable", "is_open")],
    Input("bond-table", "cellRendererData"),
    State("bond-store", "data"),
)
def show_timetable(menu_data, data):
    if menu_data and menu_data.get("value") == MenuAction.SHOW_TIMETABLE.value:
        row_index = menu_data.get("rowIndex", -1)
        if row_index >= 0 and row_index < len(data):
            bond = data[row_index]
            coupon = float(bond["Coupon"]) / 100
            accrual_start = datetime.strptime(bond["Accrual Start"], "%Y-%m-%d")
            maturity = datetime.strptime(bond["Maturity"], "%Y-%m-%d")
            frequency = f"{int(bond['Frequency'])}QE"
            currency = bond["Currency"]
            notional = float(bond["Notional"])

            bond_obj = FixedBond(currency, coupon, accrual_start, maturity, frequency)
            events = bond_obj.print_events()

            return html.Pre(events), True

    return "No timetable available.", False

if __name__ == "__main__":
    app.run_server(debug=True)
