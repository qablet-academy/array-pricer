import copy

import numpy as np
from qablet.base.fixed import FixedModel
from qablet_contracts.timetable import py_to_ts

from src.bond import bond_dict_to_obj
from src.rates import RATE_TENOR_MAP


def price_shocked(model, timetable, dataset_orig, shock):
    dataset = copy.deepcopy(dataset_orig)
    zero_rates = dataset["ASSETS"]["USD"][1]
    zero_rates[:, 1] = zero_rates[:, 1] + shock
    dataset["ASSETS"]["USD"] = ("ZERO_RATES", zero_rates)
    price, _ = model.price(timetable, dataset)
    return price


def update_price(data, rate_data, pricing_datetime):
    """Update missing prices and calculate duration/convexity for all bonds in the table, in place."""

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
        "PRICING_TS": py_to_ts(pricing_datetime).value,
        "ASSETS": {"USD": discount_data},
    }

    model = FixedModel()
    shock_size = 0.01  # 1% rate shock

    # Recalculate prices, durations, and convexities for all bonds
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
        price_down = price_shocked(
            model, timetable, dataset, shock=-shock_size
        )
        dv = (price_up - price_down) / (2 * shock_size)

        # Calculate duration
        bond["Duration"] = f"{-dv / price:.6f}"

        # Calculate convexity
        convexity = (price_up + price_down - 2 * price) / (shock_size**2)
        bond["Convexity"] = f"{convexity:.6f}"


def calculate_key_rate_duration(data, rate_data, pricing_datetime):
    """
    Calculate Key Rate Duration (KRD) for each bond in the data.
    Shocks each maturity rate in RATE_TENOR_MAP by 1%.
    """
    model = FixedModel()
    krd_report = []

    for bond in data:
        bond_obj, notional = bond_dict_to_obj(bond)
        timetable = bond_obj.timetable()

        # Calculate the bond's maturity in years from accrual start to maturity date
        maturity_years = (
            bond_obj.maturity - bond_obj.accrual_start
        ).days / 365
        bond_krd = {
            "Bond": bond["Bond"],
            "Maturity (Years)": round(maturity_years, 2),
        }

        # Initial dataset and price calculation
        initial_dataset = {
            "BASE": "USD",
            "PRICING_TS": py_to_ts(pricing_datetime).value,
            "ASSETS": {
                "USD": (
                    "ZERO_RATES",
                    np.array(
                        [
                            [rate["Year"], rate["Rate"] / 100]
                            for rate in rate_data
                        ]
                    ),
                ),
            },
        }
        initial_price, _ = model.price(timetable, initial_dataset)

        # Calculate KRD by shocking each rate point
        additional_point_included = False
        for rate in RATE_TENOR_MAP:
            rate_year = rate["Year"]
            rate_label = rate["Label"]

            # Include one additional rate point if it is the next maturity beyond bond maturity
            if rate_year > maturity_years:
                if not additional_point_included:
                    additional_point_included = True
                else:
                    bond_krd[rate_label] = None
                    continue

            # Shock the rate
            shocked_dataset = copy.deepcopy(initial_dataset)
            for i, r in enumerate(shocked_dataset["ASSETS"]["USD"][1]):
                if r[0] == rate_year:
                    shocked_dataset["ASSETS"]["USD"][1][i][1] += 0.01

            # Calculate shocked price and KRD
            shocked_price, _ = model.price(timetable, shocked_dataset)
            krd_value = (shocked_price - initial_price) * notional
            bond_krd[rate_label] = round(krd_value, 6)

        krd_report.append(bond_krd)

    return krd_report
