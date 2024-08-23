import numpy as np
import pandas as pd
import plotly.graph_objects as go
from qablet.base.utils import Discounter


def rates_table(rate_data):
    discount_data = (
        "ZERO_RATES",
        np.array([[rate["Year"], rate["Rate"] / 100] for rate in rate_data]),
    )
    discounter = Discounter(discount_data)

    max_t = rate_data[-1]["Year"]
    times = np.linspace(0, max_t, 21)
    starts = times[:-1]
    ends = times[1:]
    term_rates = discounter.rate(ends, ends * 0)  # rate from 0 to t

    fwd_rates = discounter.rate(ends, starts)  # rate from t to t+1

    return pd.DataFrame({"Time": ends, "Term Rate": term_rates, "Fwd Rate": fwd_rates})


def plot_rates(rates_df):
    # Create traces
    term_rate_trace = go.Scatter(
        x=rates_df["Time"],
        y=rates_df["Term Rate"],
        mode="lines",
        name="Term Rate",
        line=dict(shape="linear"),
    )

    fwd_rate_trace = go.Scatter(
        x=rates_df["Time"],
        y=rates_df["Fwd Rate"],
        mode="lines",
        name="Fwd Rate",
        line=dict(shape="vh"),
    )

    # Create the figure
    fig = go.Figure(data=[term_rate_trace, fwd_rate_trace])

    # Move the legend inside the graph and set the origin to zero
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255,255,255,0.5)",
        ),
        xaxis=dict(range=[0, rates_df["Time"].max()]),
        yaxis=dict(
            range=[
                0,
                1.1 * max(rates_df["Term Rate"].max(), rates_df["Fwd Rate"].max()),
            ],
            tickformat=".2%",
        ),
        height=300,  # Adjust the height of the graph
    )

    return fig


if __name__ == "__main__":
    rate_data = [
        {"Year": 2.0, "Rate": 2.0},
        {"Year": 5.0, "Rate": 4.0},
    ]
    rates_df = rates_table(rate_data)
    print(rates_df)

    fig = plot_rates(rates_df)
    fig.write_html("scratch/first_figure.html", auto_open=True)
