"""
This module contains examples of fixed rate bonds.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
import pyarrow as pa

from qablet_contracts.ir.dcf import dcf_30_360 as dcf
from qablet_contracts.timetable import TS_EVENT_SCHEMA, Contract


def _const_dict_array(n, val):
    """Create a dictionary array of length n with constant values."""
    return pa.DictionaryArray.from_arrays(
        indices=np.full(n, 0, dtype=np.int64),
        dictionary=[val],
    )


def timetable_from_cf(
    ccy: str, dates: List[datetime], amounts: List[float], track: str = ""
):
    n = len(dates)
    return {
        "events": pa.RecordBatch.from_arrays(
            [
                pa.array(dates),
                _const_dict_array(n, "+"),  # ops
                pa.array(amounts),
                _const_dict_array(n, ccy),  # units
                _const_dict_array(n, track),  # tracks
            ],
            schema=TS_EVENT_SCHEMA,
        )
    }


@dataclass
class FixedCashFlows(Contract):
    """A set of **Fixed Cashflows** in a single currency. This example also shows how to create a timetable from arrays
    instead of a list of dictionaries, which is more efficient.

    Args:
        ccy: the currency of cashflows.
        times: a list or ndarray of cashflows times.
        amounts: a list ndarray of cashflows amounts.
        track: an optional identifier for the contract.

    Examples:
        >>> times = [datetime(2023, 12, 31), datetime(2024, 6, 30), datetime(2024, 12, 31)]
        >>> amounts = [0.05, 0.05, 1.05]
        >>> FixedCashFlows("USD", times, amounts).print_events()
              time op  quantity unit track
        12/31/2023  +      0.05  USD
        06/30/2024  +      0.05  USD
        12/31/2024  +      1.05  USD
    """

    ccy: str
    dates: List[datetime]
    amounts: List[float]
    track: str = ""

    def timetable(self):
        return timetable_from_cf(
            self.ccy, self.dates, self.amounts, self.track
        )


@dataclass
class FixedBond(Contract):
    """A **Fixed Rate Bond** pays a fixed rate at regular intervals, and the principal at maturity.

    Args:
        ccy: the currency of cashflows.
        coupon: the coupon rate per year.
        maturity: the maturity of the bond.
        freq: the number of coupon payments per year.
        track: an optional identifier for the contract.

    Examples:
        >>> FixedBond("USD", 0.05, datetime(2023, 12, 31), datetime(2025, 12, 31), "2QE").print_events()
              time op  quantity unit track
        06/30/2024  +     0.025  USD
        12/31/2024  +     0.025  USD
        06/30/2025  +     0.025  USD
        12/31/2025  +     1.025  USD
    """

    ccy: str
    coupon: float
    accrual_start: datetime
    maturity: datetime
    freq: str = "2BQE"
    track: str = ""

    def timetable(self):
        # Coupon period dates including the start of first period, and end of last period.
        cpn_dates = pd.bdate_range(
            self.accrual_start,
            self.maturity,
            freq=self.freq,
            inclusive="both",
        )

        amounts = [
            dcf(end, start) * self.coupon
            for start, end in zip(cpn_dates[:-1], cpn_dates[1:])
        ]

        amounts[-1] += 1  # The last payment includes the principal
        return timetable_from_cf(self.ccy, cpn_dates[1:], amounts, self.track)


if __name__ == "__main__":
    # Create a timetable from cashflows
    print("cashflows:\n")
    FixedCashFlows(
        "USD",
        [
            datetime(2023, 12, 31),
            datetime(2024, 6, 30),
            datetime(2024, 12, 31),
        ],
        [0.05, 0.05, 1.05],
    ).print_events()

    # Create a fixed bond timetable
    print("bond:\n")
    FixedBond(
        "USD", 0.05, datetime(2023, 12, 31), datetime(2025, 12, 31), "2QE"
    ).print_events()