from qablet.base.utils import Discounter
import numpy as np
import pandas as pd


def rates_table(rate_data):
    discount_data = (
        "ZERO_RATES",
        np.array([[rate["Year"], rate["Rate"] / 100] for rate in rate_data]),
    )
    discounter = Discounter(discount_data)

    max_t = rate_data[-1]["Year"]
    times = np.linspace(0, max_t, 21)
    term_rates = discounter.rate(times, times * 0)  # rate from 0 to t

    fwd_rates = discounter.rate(times[1:], times[:-1])  # rate from t to t+1
    fwd_rates = np.append(fwd_rates, [np.nan])

    return pd.DataFrame({"Time": times, "Term Rate": term_rates, "Fwd Rate": fwd_rates})


if __name__ == "__main__":
    rate_data = [
        {"Year": 0.0, "Rate": 0.0},
        {"Year": 2.0, "Rate": 2.0},
        {"Year": 5.0, "Rate": 4.0},
    ]
    rates_df = rates_table(rate_data)
    print(rates_df)
