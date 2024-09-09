from datetime import datetime
import numpy as np
from qablet.base.fixed import FixedModel
from qablet_contracts.timetable import py_to_ts
from src.bond import bond_dict_to_obj

def update_price(data, rate_data):
    """Update missing prices and calculate duration for all bonds in the table, in place."""

    # Check if all bonds already have valid prices
    if all([item["Price"] for item in data]):
        return  # All prices are valid

    # Initial discount data based on the current rates
    discount_data = (
        "ZERO_RATES",
        np.array([[rate["Year"], rate["Rate"] / 100] for rate in rate_data]),
    )
    dataset = {
        "BASE": "USD",
        "PRICING_TS": py_to_ts(datetime(2023, 12, 31)).value,
        "ASSETS": {"USD": discount_data},
    }
    
    model = FixedModel()
    shock_size = 0.01  # 1% rate shock

    # Recalculate prices and durations for all bonds
    for bond in data:
        if bond["Price"]:
            continue  # Skip bonds with existing prices

        # Convert bond dictionary to bond object and retrieve notional
        bond_obj, notional = bond_dict_to_obj(bond)
        timetable = bond_obj.timetable()

        # 1. Calculate initial price
        price, _ = model.price(timetable, dataset)
        bond["Price"] = f"${price * notional:.6f}"

        # 2. Shock rates up by 1%
        discount_data_up = (
            "ZERO_RATES",
            np.array([[rate["Year"], (rate["Rate"] / 100) + shock_size] for rate in rate_data]),
        )
        dataset_up = {
            "BASE": "USD",
            "PRICING_TS": py_to_ts(datetime(2023, 12, 31)).value,
            "ASSETS": {"USD": discount_data_up},
        }
        price_up, _ = model.price(timetable, dataset_up)

        # 3. Shock rates down by 1%
        discount_data_down = (
            "ZERO_RATES",
            np.array([[rate["Year"], (rate["Rate"] / 100) - shock_size] for rate in rate_data]),
        )
        dataset_down = {
            "BASE": "USD",
            "PRICING_TS": py_to_ts(datetime(2023, 12, 31)).value,
            "ASSETS": {"USD": discount_data_down},
        }
        price_down, _ = model.price(timetable, dataset_down)

        # 4. Calculate DV (Dollar Value of 1%)
        dv = (price_up - price_down) / (2 * shock_size)

        # 5. Calculate duration
        duration = dv / price
        bond["Duration"] = f"{duration:.6f}"  # Add duration to the bond data
        
        print(price_up * 100)
        print(price_down * 100)
        print(dv)
        print(duration)
