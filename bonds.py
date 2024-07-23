import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from datetime import datetime
from qablet_contracts.bnd.fixed import FixedBond
from qablet_contracts.timetable import py_to_ts
from qablet.base.fixed import FixedModel
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.Div([
        # Create a table to display bond inputs in columns
        html.Table([
            html.Thead(
                html.Tr([
                    html.Th("Bond"),
                    html.Th("Currency"),
                    html.Th("Coupon"),
                    html.Th("Accrual Start"),
                    html.Th("Maturity"),
                    html.Th("Frequency"),
                    html.Th("Price"),
                ])
            ),
            html.Tbody(id='bond-table-body', children=[
                html.Tr([
                    html.Td("Bond 1"),
                    html.Td(dcc.Dropdown(
                        id={'type': 'currency-dropdown', 'index': 0},
                        options=[
                            {'label': 'USD', 'value': 'USD'},
                            {'label': 'EUR', 'value': 'EUR'}
                        ],
                        value='USD'
                    )),
                    html.Td(dcc.Input(id={'type': 'coupon-input', 'index': 0}, type='number', placeholder='Coupon (%)')),
                    html.Td(dcc.DatePickerSingle(
                        id={'type': 'accrual-start-date', 'index': 0},
                        display_format='DD/MM/YYYY',
                        date=datetime.today().strftime('%Y-%m-%d')
                    )),
                    html.Td(dcc.DatePickerSingle(
                        id={'type': 'maturity-date', 'index': 0},
                        display_format='DD/MM/YYYY',
                        date=datetime.today().strftime('%Y-%m-%d')
                    )),
                    html.Td(dcc.Input(id={'type': 'frequency-input', 'index': 0}, type='number', placeholder='Frequency')),
                    html.Td(html.Div(id={'type': 'price-output', 'index': 0})),
                ])
            ])
        ], style={'width': '100%', 'border': '1px solid black', 'border-collapse': 'collapse'}),
        
        html.Button('Add Bond', id='add-bond-button', n_clicks=0, style={'margin-top': '20px'})
    ])
])

# Callback to add new rows to the table
@app.callback(
    Output('bond-table-body', 'children'),
    [Input('add-bond-button', 'n_clicks')],
    [State('bond-table-body', 'children')]
)
def add_bond(n_clicks, rows):
    new_index = len(rows)
    new_row = html.Tr([
        html.Td(f"Bond {new_index + 1}"),
        html.Td(dcc.Dropdown(
            id={'type': 'currency-dropdown', 'index': new_index},
            options=[
                {'label': 'USD', 'value': 'USD'},
                {'label': 'EUR', 'value': 'EUR'}
            ],
            value='USD'
        )),
        html.Td(dcc.Input(id={'type': 'coupon-input', 'index': new_index}, type='number', placeholder='Coupon (%)')),
        html.Td(dcc.DatePickerSingle(
            id={'type': 'accrual-start-date', 'index': new_index},
            display_format='DD/MM/YYYY',
            date=datetime.today().strftime('%Y-%m-%d')
        )),
        html.Td(dcc.DatePickerSingle(
            id={'type': 'maturity-date', 'index': new_index},
            display_format='DD/MM/YYYY',
            date=datetime.today().strftime('%Y-%m-%d')
        )),
        html.Td(dcc.Input(id={'type': 'frequency-input', 'index': new_index}, type='number', placeholder='Frequency')),
        html.Td(html.Div(id={'type': 'price-output', 'index': new_index})),
    ])
    rows.append(new_row)
    return rows

# Callback to calculate bond price
@app.callback(
    Output({'type': 'price-output', 'index': dash.ALL}, 'children'),
    [Input({'type': 'coupon-input', 'index': dash.ALL}, 'value'),
     Input({'type': 'accrual-start-date', 'index': dash.ALL}, 'date'),
     Input({'type': 'maturity-date', 'index': dash.ALL}, 'date'),
     Input({'type': 'frequency-input', 'index': dash.ALL}, 'value'),
     Input({'type': 'currency-dropdown', 'index': dash.ALL}, 'value')]
)
def update_price(coupons, accrual_starts, maturities, frequencies, currencies):
    prices = []

    # Determine the maximum length of all lists to prevent out-of-range errors
    max_len = max(len(coupons), len(accrual_starts), len(maturities), len(frequencies), len(currencies))

    for i in range(max_len):
        # Get values or default to None if index is out of range
        coupon = coupons[i] if i < len(coupons) else None
        accrual_start = accrual_starts[i] if i < len(accrual_starts) else None
        maturity = maturities[i] if i < len(maturities) else None
        frequency = frequencies[i] if i < len(frequencies) else None
        currency = currencies[i] if i < len(currencies) else None

        # Validate inputs
        if None in [coupon, accrual_start, maturity, frequency, currency]:
            prices.append("Missing Input")
            continue

        # Convert and validate inputs
        try:
            coupon = float(coupon) / 100
            accrual_start = datetime.strptime(accrual_start, '%Y-%m-%d')
            maturity = datetime.strptime(maturity, '%Y-%m-%d')
            frequency = f"{frequency}QE"
        except (ValueError, TypeError):
            prices.append("Invalid Input")
            continue

        # Create FixedBond with positional arguments
        bond = FixedBond(currency, coupon, accrual_start, maturity, frequency)
        timetable = bond.timetable()

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

        prices.append(f"${price:.6f}")

    return prices

if __name__ == '__main__':
    app.run_server(debug=True)
