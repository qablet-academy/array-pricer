from datetime import datetime
from enum import Enum

import dash
import dash_bootstrap_components as dbc
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output, State
from dash_ag_grid import AgGrid

from src.aggrid_utils import datestring_cell, numeric_cell, select_cell
from src.bond import bond_dict_to_obj, create_default_bond
from src.price import calculate_key_rate_duration, update_price
from src.rates import (
    RATE_TENOR_LABELS,
    get_rates_for_date,
    plot_rates,
    rates_table,
)

# Constant for default pricing date
DEFAULT_PRICING_DATE = datetime(2024, 1, 2)

# Fetch default rate data dynamically for the default pricing date
DEFAULT_RATE_DATA = get_rates_for_date(DEFAULT_PRICING_DATE)

HEATMAP_STYLE = {
    "styleConditions": [
        {
            "condition": "params.value === null",
            "style": {"backgroundColor": "white"},
        },
        {
            "condition": "params.value > 0",
            "style": {"backgroundColor": "rgba(0, 128, 0, 0.3)"},
        },
        {
            "condition": "params.value < 0",
            "style": {"backgroundColor": "rgba(255, 0, 0, 0.3)"},
        },
    ],
    "defaultStyle": {"backgroundColor": "white"},
}


# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)


# Enum for menu actions
class MenuAction(Enum):
    DELETE = 1
    SHOW_TIMETABLE = 2


# Function to generate initial bond data
def generate_initial_data(pricing_datetime):
    return [create_default_bond(index=1, pricing_datetime=pricing_datetime)]


# Column definitions for AG Grid with the row menu column
column_defs = [
    {
        "headerName": "...",
        "field": "Menu",
        "cellRenderer": "rowMenu",
        "width": 100,
    },
    {"headerName": "Bond", "field": "Bond", "editable": False, "width": 100},
    select_cell("Currency", ["USD", "EUR"]),
    numeric_cell("Coupon"),
    datestring_cell("Accrual Start"),
    datestring_cell("Maturity"),
    numeric_cell("Frequency"),
    numeric_cell("Notional"),
    {"headerName": "Price", "field": "Price", "editable": False, "width": 100},
    {
        "headerName": "Duration",
        "field": "Duration",
        "editable": False,
        "width": 100,
    },
    {
        "headerName": "Convexity",
        "field": "Convexity",
        "editable": False,
        "width": 100,
    },
]

# Layout of the app
app.layout = html.Div(
    [
        html.Button(
            "Add Bond",
            id="add-bond-button",
            n_clicks=0,
            style={"margin-top": "20px"},
        ),
        dcc.DatePickerSingle(
            id="pricing-datetime-picker",
            date=DEFAULT_PRICING_DATE,
            display_format="YYYY-MM-DD",
            style={"margin-top": "20px"},
        ),
        html.Button(
            "Rate Editor",
            id="rate-editor-button",
            n_clicks=0,
            style={"margin-top": "20px"},
        ),
        html.Button(
            "Show Key Rate Duration",
            id="show-krd-button",
            n_clicks=0,
            style={"margin-top": "20px"},
        ),
        AgGrid(
            id="bond-table",
            rowData=generate_initial_data(DEFAULT_PRICING_DATE),
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
        dcc.Store(
            id="bond-store", data=generate_initial_data(DEFAULT_PRICING_DATE)
        ),
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
                    dcc.Graph(id="rate-graph"),
                    AgGrid(
                        id="rate-editor",
                        rowData=DEFAULT_RATE_DATA,
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
                        style={"flex": 1, "width": "100%"},
                    ),
                ]
            ),
            id="offcanvas-rate-editor",
            title="Rate Editor",
            is_open=False,
            placement="end",
            backdrop=True,
            style={"width": "30%"},
        ),
        dbc.Offcanvas(
            AgGrid(
                id="krd-report-table",
                columnDefs=[
                    {"headerName": "Bond", "field": "Bond"},
                    {
                        "headerName": "Maturity (Years)",
                        "field": "Maturity (Years)",
                    },
                ]
                + [
                    {
                        "headerName": label,
                        "field": label,
                        "editable": False,
                        "cellStyle": HEATMAP_STYLE,
                    }
                    for label in RATE_TENOR_LABELS
                ],
                dashGridOptions={"suppressMovableColumns": True},
                defaultColDef={
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    "width": 88,
                },
                style={"height": "60vh", "width": "100%"},
            ),
            id="offcanvas-krd-report",
            title="Key Rate Duration Report",
            is_open=False,
            placement="end",
            backdrop=True,
            style={"width": "80%"},
        ),
    ]
)


# Callback to update the bond store data
@app.callback(
    Output("bond-store", "data"),
    [
        Input("add-bond-button", "n_clicks"),
        Input("bond-table", "cellValueChanged"),
        Input("bond-table", "cellRendererData"),
        Input("rate-editor", "cellValueChanged"),
        Input("pricing-datetime-picker", "date"),
    ],
    State("bond-store", "data"),
)
def update_bond_data(
    n_clicks_add, cell_change, menu_data, _rate_change, pricing_datetime, data
):
    ctx = callback_context

    if not ctx.triggered:
        return data

    trigger = ctx.triggered[0]["prop_id"]

    # Handle Add Bond
    if trigger == "add-bond-button.n_clicks" and n_clicks_add > 0:
        new_index = len(data) + 1
        new_bond = create_default_bond(
            index=new_index,
            pricing_datetime=datetime.fromisoformat(pricing_datetime),
        )
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


# Callback to update the bond table data
@app.callback(
    Output("bond-table", "rowData"),
    Input("bond-store", "data"),
    Input("pricing-datetime-picker", "date"),
    State("rate-editor", "rowData"),
)
def update_table(data, pricing_datetime, rate_data):
    update_price(
        data,
        rate_data=rate_data,
        pricing_datetime=datetime.fromisoformat(pricing_datetime),
    )
    return data


# Callback to update the rate editor data dynamically based on the selected pricing date
@app.callback(
    Output("rate-editor", "rowData"),
    Input("pricing-datetime-picker", "date"),
)
def update_rate_editor_data(pricing_datetime):
    if pricing_datetime is None:
        pricing_datetime = DEFAULT_PRICING_DATE
    rate_data = get_rates_for_date(pricing_datetime)
    return rate_data


# Callback to update the rate graph instantly when rates are edited
@app.callback(
    Output("rate-graph", "figure"),
    Input("rate-editor", "cellValueChanged"),
    State("rate-editor", "rowData"),
)
def update_rate_graph(_rate_change, rate_data):
    rates_df = rates_table(rate_data)
    return plot_rates(rates_df)


# Callback to show timetable in the off-canvas
@app.callback(
    [
        Output("timetable-content", "children"),
        Output("offcanvas-timetable", "is_open"),
    ],
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
    Input("rate-editor-button", "n_clicks"),
    [State("offcanvas-rate-editor", "is_open")],
)
def toggle_rate_editor(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


# Callback to handle Key Rate Duration Report Off-canvas
@app.callback(
    [
        Output("krd-report-table", "rowData"),
        Output("offcanvas-krd-report", "is_open"),
    ],
    Input("show-krd-button", "n_clicks"),
    State("bond-store", "data"),
    State("rate-editor", "rowData"),
    State("pricing-datetime-picker", "date"),
)
def show_krd_report(n_clicks, data, rate_data, pricing_datetime):
    if n_clicks == 0:
        return [], False

    krd_data = calculate_key_rate_duration(
        data, rate_data, datetime.fromisoformat(pricing_datetime)
    )
    return krd_data, True


if __name__ == "__main__":
    app.run_server(debug=True)
