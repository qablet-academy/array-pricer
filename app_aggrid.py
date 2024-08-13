import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output, State
from dash_ag_grid import AgGrid

from src.aggrid_utils import datestring_cell, numeric_cell, select_cell
from src.bond import bond_dict_to_obj, create_default_bond
from src.price import update_price
from src.rates import rates_table

from enum import Enum

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

# Define the enum for menu actions
class MenuAction(Enum):
    DELETE = 1
    SHOW_TIMETABLE = 2

# Function to generate initial bond data
def generate_initial_data():
    return [create_default_bond(index=1)]

# Column definitions for AG Grid with the row menu column
column_defs = [
    {"headerName": "...", "field": "Menu", "cellRenderer": "rowMenu", "width": 100},
    {"headerName": "Bond", "field": "Bond", "editable": False, "width": 100},
    select_cell("Currency", ["USD", "EUR"]),
    numeric_cell("Coupon"),
    datestring_cell("Accrual Start"),
    datestring_cell("Maturity"),
    numeric_cell("Frequency"),
    numeric_cell("Notional"),
    {"headerName": "Price", "field": "Price", "editable": False, "width": 100},
]

# Layout of the app
app.layout = html.Div(
    [
        html.Button(
            "Add Bond", id="add-bond-button", n_clicks=0, style={"margin-top": "20px"}
        ),
        html.Button(
            "Rate Editor",
            id="rate-editor-button",
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
        dbc.Offcanvas(
            dcc.Markdown(id="timetable-content"),
            id="offcanvas-timetable",
            title="Bond Timetable",
            is_open=False,
            placement="end",
            backdrop=True,
        ),
        dbc.Offcanvas(
            html.Div(
                [
                    AgGrid(
                        id="rate-editor",
                        rowData=[
                            {"Year": 0.0, "Rate": 4.0},
                            {"Year": 2.0, "Rate": 4.0},
                            {"Year": 5.0, "Rate": 4.0},
                        ],
                        columnDefs=[
                            numeric_cell("Year", editable=False),
                            numeric_cell("Rate"),
                        ],
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
                        style={"height": "30vh", "width": "100%"},
                    ),
                    dcc.Graph(id="rate-graph"),
                ]
            ),
            id="offcanvas-rate-editor",
            title="Rate Editor",
            is_open=False,
            placement="end",
            backdrop=True,
            style={"width": "50%"},  # Adjust the width of the off-canvas here
        ),
    ]
)

# Combined callback to handle bond updates, additions, and deletions
@app.callback(
    Output("bond-store", "data"),
    [
        Input("add-bond-button", "n_clicks"),
        Input("bond-table", "cellValueChanged"),
        Input("bond-table", "cellRendererData"),
        Input("rate-editor", "cellValueChanged"),
    ],
    State("bond-store", "data"),
)
def update_bond_data(
    n_clicks_add,
    cell_change,
    menu_data,
    _rate_change,
    data,
):
    ctx = callback_context

    if not ctx.triggered:
        return data

    trigger = ctx.triggered[0]["prop_id"]

    # Handle Add Bond
    if trigger == "add-bond-button.n_clicks" and n_clicks_add > 0:
        new_index = len(data) + 1
        new_bond = create_default_bond(index=new_index)
        data.append(new_bond)

    # Handle Delete Bond from Row Menu
    elif trigger == "bond-table.cellRendererData":
        if menu_data and menu_data.get("value") == MenuAction.DELETE.value:
            row = menu_data.get("rowIndex")
            if row < len(data):
                del data[row]

    # Handle Cell Value Change
    elif trigger == "bond-table.cellValueChanged" and cell_change:
        if isinstance(cell_change, list):
            for change in cell_change:
                row_id = int(change.get("rowIndex", -1))
                field = change.get("colId", "")
                new_value = change.get("value", "")
                if row_id >= 0 and field in data[0]:
                    data[row_id][field] = new_value
                    data[row_id]["Price"] = (
                        None  # Set Price to None to trigger recalculation
                    )
    elif trigger == "rate-editor.cellValueChanged":
        # Invalidate all prices when the rate data is updated
        for bond in data:
            bond["Price"] = None

    return data

# Callback to update the grid data, when the bond data is updated
@app.callback(
    Output("bond-table", "rowData"),
    Input("bond-store", "data"),
    State("rate-editor", "rowData"),
)
def update_table(data, rate_data):
    # Update the prices of the bonds that need to be recalculated
    update_price(data, rate_data=rate_data)
    return data

# Callback to show timetable in the off-canvas
@app.callback(
    [Output("timetable-content", "children"), Output("offcanvas-timetable", "is_open")],
    Input("bond-table", "cellRendererData"),
    State("bond-store", "data"),
)
def show_timetable(menu_data, data):
    if menu_data and menu_data.get("value") == MenuAction.SHOW_TIMETABLE.value:
        row_index = menu_data.get("rowIndex", -1)
        if row_index >= 0 and row_index < len(data):
            bond_obj, _ = bond_dict_to_obj(data[row_index])

            full_text = f"```\n{bond_obj.to_string()}\n```"
            return full_text, True

    return "", False

# Callback to handle Rate Editor Off-canvas
@app.callback(
    Output("offcanvas-rate-editor", "is_open"),
    [Output("rate-graph", "figure")],
    Input("rate-editor-button", "n_clicks"),
    [State("offcanvas-rate-editor", "is_open"),
     State("rate-editor", "rowData")],
)
def toggle_rate_editor(n_clicks, is_open, rate_data):
    if n_clicks:
        rates_df = rates_table(rate_data)

        # Plotting the graph
        fig = px.line(rates_df, x='Time', y=['Term Rate', 'Fwd Rate'],
                      labels={"value": "Rate", "variable": "Rate Type"},
                      title="Term Rates and Forward Rates")

        fig.update_layout(height=300)  # Adjust the height of the graph

        return not is_open, fig
    return is_open, dash.no_update

if __name__ == "__main__":
    app.run_server(debug=True)
