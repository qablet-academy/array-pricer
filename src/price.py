from datetime import datetime

import numpy as np
from qablet.base.fixed import FixedModel
from qablet_contracts.timetable import py_to_ts

from src.bond import bond_dict_to_obj


def update_price(data, rate_data):
    """Update missing prices of all bonds in the table, in place."""

    if all([item["Price"] for item in data]):
        return  # All prices are valid

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

    # Recalculate prices for all bonds
    for bond in data:
        if bond["Price"]:
            continue  # Skip bonds with existing prices
        bond_obj, notional = bond_dict_to_obj(bond)
        timetable = bond_obj.timetable()

        price, _ = model.price(timetable, dataset)
        bond["Price"] = f"${price * notional:.6f}"
