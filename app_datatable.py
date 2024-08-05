"""ArrayPricer for Bonds using DataTable"""

from datetime import datetime

import dash
import numpy as np
from dash import html
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State
from qablet.base.fixed import FixedModel
from qablet_contracts.bnd.fixed import FixedBond
from qablet_contracts.timetable import py_to_ts

# Initialize the Dash app
app = dash.Dash(__name__)

# Initial data for the table
initial_data = [
    {
        "Bond": "Bond 1",
        "Currency": "USD",
        "Coupon": 0,
        "Accrual Start": datetime.today().strftime("%Y-%m-%d"),
        "Maturity": datetime.today().strftime("%Y-%m-%d"),
        "Frequency": 1,
        "Notional": 100,
        "Price": "",
    }
]

# Layout of the app
app.layout = html.Div(
    [
        DataTable(
            id="bond-table",
            columns=[
                {"name": "Bond", "id": "Bond", "editable": False},
                {"name": "Currency", "id": "Currency", "presentation": "dropdown"},
                {"name": "Coupon", "id": "Coupon", "type": "numeric"},
                {"name": "Accrual Start", "id": "Accrual Start", "type": "datetime"},
                {"name": "Maturity", "id": "Maturity", "type": "datetime"},
                {"name": "Frequency", "id": "Frequency", "type": "numeric"},
                {"name": "Notional", "id": "Notional", "type": "numeric"},
                {"name": "Price", "id": "Price", "editable": False},
            ],
            data=initial_data,
            editable=True,
            row_deletable=True,
            dropdown={
                "Currency": {
                    "options": [
                        {"label": "USD", "value": "USD"},
                        {"label": "EUR", "value": "EUR"},
                    ]
                }
            },
        ),
        html.Button(
            "Add Bond", id="add-bond-button", n_clicks=0, style={"margin-top": "20px"}
        ),
    ]
)


# Combined callback to add new rows to the table and calculate bond price
@app.callback(
    Output("bond-table", "data"),
    [Input("add-bond-button", "n_clicks"), Input("bond-table", "data_timestamp")],
    [State("bond-table", "data")],
)
def update_table(n_clicks, timestamp, rows):
    ctx = dash.callback_context

    # Handle Add Bond button click
    if ctx.triggered and ctx.triggered[0]["prop_id"].split(".")[0] == "add-bond-button":
        new_index = len(rows)
        new_row = {
            "Bond": f"Bond {new_index + 1}",
            "Currency": "USD",
            "Coupon": 0,
            "Accrual Start": datetime.today().strftime("%Y-%m-%d"),
            "Maturity": datetime.today().strftime("%Y-%m-%d"),
            "Frequency": 1,
            "Notional": 100,
            "Price": "",
        }
        rows.append(new_row)

    # Calculate bond prices
    for row in rows:
        try:
            currency = row["Currency"]
            coupon = float(row["Coupon"]) / 100
            accrual_start = datetime.strptime(row["Accrual Start"], "%Y-%m-%d")
            maturity = datetime.strptime(row["Maturity"], "%Y-%m-%d")
            frequency = f"{row['Frequency']}QE"
            notional = float(row["Notional"])

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

            # Calculate the final price
            final_price = notional * price
            row["Price"] = f"${final_price:.6f}"
        except Exception as e:
            print(f"Error calculating price for bond {row['Bond']}: {e}")
            row["Price"] = "Error"

    return rows


if __name__ == "__main__":
    app.run_server(debug=True)
