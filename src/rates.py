import pandas as pd
import numpy as np
import plotly.graph_objects as go
from qablet.base.utils import Discounter

# Function to fetch the rates dynamically from the Treasury website using a CSV URL
def fetch_treasury_rates():
    csv_url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2024/all?type=daily_treasury_yield_curve&field_tdr_date_value=2024&page&_format=csv"
    df = pd.read_csv(csv_url)
    return df

# Helper function to get the rates for a specific pricing date
def get_rates_for_date(pricing_datetime):
    df = fetch_treasury_rates()
    # Convert date column to datetime and filter for the closest available date
    df['Date'] = pd.to_datetime(df['Date'])
    closest_date = df.iloc[(df['Date'] - pricing_datetime).abs().argsort()[:1]]
    return closest_date

# Function to convert the Treasury yield curve rates into a usable format for pricing
def treasury_rates_to_rate_data(df_row):
    return [
        {"Year": 1 / 12, "Rate": df_row['1 Mo'].values[0]},
        {"Year": 2 / 12, "Rate": df_row['2 Mo'].values[0]},
        {"Year": 3 / 12, "Rate": df_row['3 Mo'].values[0]},
        {"Year": 4 / 12, "Rate": df_row['4 Mo'].values[0]},
        {"Year": 6 / 12, "Rate": df_row['6 Mo'].values[0]},
        {"Year": 1.0, "Rate": df_row['1 Yr'].values[0]},
        {"Year": 2.0, "Rate": df_row['2 Yr'].values[0]},
        {"Year": 3.0, "Rate": df_row['3 Yr'].values[0]},
        {"Year": 5.0, "Rate": df_row['5 Yr'].values[0]},
        {"Year": 7.0, "Rate": df_row['7 Yr'].values[0]},
        {"Year": 10.0, "Rate": df_row['10 Yr'].values[0]},
        {"Year": 20.0, "Rate": df_row['20 Yr'].values[0]},
        {"Year": 30.0, "Rate": df_row['30 Yr'].values[0]},
    ]

# Function to calculate the rates for plotting and pricing
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

# Function to plot the rates
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
