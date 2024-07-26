import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash_ag_grid import AgGrid
from datetime import datetime
from qablet_contracts.bnd.fixed import FixedBond
from qablet_contracts.timetable import py_to_ts
from qablet.base.fixed import FixedModel
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Initial data for the table
initial_data = [
    {
        'Bond': 'Bond 1',
        'Currency': 'USD',
        'Coupon': 0.02,
        'Accrual Start': datetime.today().strftime('%Y-%m-%d'),
        'Maturity': datetime.today().strftime('%Y-%m-%d'),
        'Frequency': 1,
        'Notional': 100,
        'Price': ''
    }
]

# Column definitions for AG Grid
column_defs = [
    {'headerName': 'Bond', 'field': 'Bond', 'editable': False},
    {'headerName': 'Currency', 'field': 'Currency', 'editable': True, 'cellEditor': 'agSelectCellEditor', 
     'cellEditorParams': {'values': ['USD', 'EUR']}},
    {'headerName': 'Coupon', 'field': 'Coupon', 'editable': True, 'type': 'numericColumn', 'cellEditor': 'agNumberCellEditor'},
    {'headerName': 'Accrual Start', 'field': 'Accrual Start', 'editable': True, 'cellEditor': 'agTextCellEditor'},
    {'headerName': 'Maturity', 'field': 'Maturity', 'editable': True, 'cellEditor': 'agTextCellEditor'},
    {'headerName': 'Frequency', 'field': 'Frequency', 'editable': True, 'type': 'numericColumn', 'cellEditor': 'agNumberCellEditor'},
    {'headerName': 'Notional', 'field': 'Notional', 'editable': True, 'type': 'numericColumn', 'cellEditor': 'agNumberCellEditor'},
    {'headerName': 'Price', 'field': 'Price', 'editable': False}
]

# Layout of the app
app.layout = html.Div([
    AgGrid(
        id='bond-table',
        rowData=initial_data,
        columnDefs=column_defs,
        defaultColDef={'sortable': True, 'filter': True, 'resizable': True, 'editable': True},
        dashGridOptions={'editable': True, 'rowSelection': 'single', 'animateRows': True},
        style={'height': '300px', 'width': '100%'}
    ),
    html.Button('Add Bond', id='add-bond-button', n_clicks=0, style={'margin-top': '20px'}),
    dcc.Store(id='bond-store', data=initial_data)
])

# Callback to add new rows to the table
@app.callback(
    Output('bond-store', 'data'),
    Input('add-bond-button', 'n_clicks'),
    State('bond-store', 'data')
)
def add_bond(n_clicks, data):
    if n_clicks > 0:
        new_index = len(data)
        new_bond = {
            'Bond': f'Bond {new_index + 1}',
            'Currency': 'USD',
            'Coupon': 0.025,
            'Accrual Start': datetime.today().strftime('%Y-%m-%d'),
            'Maturity': datetime.today().strftime('%Y-%m-%d'),
            'Frequency': 1,
            'Notional': 100,
            'Price': ''
        }
        data.append(new_bond)
    return data

# Callback to update bond prices
@app.callback(
    Output('bond-table', 'rowData'),
    Input('bond-store', 'data'),
    Input('bond-table', 'cellValueChanged')
)
def update_bond_data(data, cell_change):
    if cell_change:
        for change in cell_change:
            row_id = change['rowIndex']
            field = change['colId']
            new_value = change['value']
            data[row_id][field] = new_value

    for bond in data:
        # Convert and validate inputs
        coupon = float(bond['Coupon']) / 100
        accrual_start = datetime.strptime(bond['Accrual Start'], '%Y-%m-%d')
        maturity = datetime.strptime(bond['Maturity'], '%Y-%m-%d')
        frequency = f"{int(bond['Frequency'])}QE"
        currency = bond['Currency']
        notional = float(bond['Notional'])

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

        bond['Price'] = f"${price * notional:.6f}"
    
    return data


if __name__ == '__main__':
    app.run_server(debug=True)
