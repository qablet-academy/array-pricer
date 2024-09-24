from datetime import datetime
import numpy as np
from qablet.base.fixed import FixedModel
from qablet_contracts.timetable import py_to_ts
from src.bond import bond_dict_to_obj
import copy


def price_shocked(model, timetable, dataset_orig, shock):
    dataset = copy.deepcopy(dataset_orig)
    zero_rates = dataset["ASSETS"]["USD"][1]
    zero_rates[:, 1] = zero_rates[:, 1] + shock
    dataset["ASSETS"]["USD"] = ("ZERO_RATES", zero_rates)

    price, _ = model.price(timetable, dataset)

    return price


def update_price(data, rate_data):
    """Update missing prices and calculate duration and convexity for all bonds in the table, in place."""

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

    # Recalculate prices, durations, and convexity for all bonds
    for bond in data:
        if bond["Price"]:
            continue  # Skip bonds with existing prices

        # Convert bond dictionary to bond object and retrieve notional
        bond_obj, notional = bond_dict_to_obj(bond)
        timetable = bond_obj.timetable()

        # 1. Calculate initial price
        price, _ = model.price(timetable, dataset)
        bond["Price"] = f"${price * notional:.6f}"

        # 2. Calculate price with shocks
        price_up = price_shocked(model, timetable, dataset, shock=shock_size)
        price_down = price_shocked(model, timetable, dataset, shock=-shock_size)
        dv = (price_up - price_down) / (2 * shock_size)

        # 3. Calculate duration
        bond["Duration"] = f"{-dv / price:.6f}"  # Add duration to the bond data

        # 4. Calculate convexity
        convexity = (price_up + price_down - 2 * price) / (shock_size * shock_size)
        bond["Convexity"] = f"{convexity:.6f}"  # Add convexity to the bond data
