import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from qablet.base.utils import Discounter

# CSV URL for fetching Treasury rates
CSV_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2024/all?type=daily_treasury_yield_curve&field_tdr_date_value=2024&page&_format=csv"

# Function to fetch Treasury rates from the Treasury website
def fetch_treasury_rates():
    df = pd.read_csv(CSV_URL)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# Function to get rates for a specific pricing date
def get_rates_for_date(pricing_datetime):
    # Convert pricing_datetime to datetime if it's a string
    if isinstance(pricing_datetime, str):
        pricing_datetime = datetime.fromisoformat(pricing_datetime)

    df = fetch_treasury_rates()
    # Find the row with the closest date to the provided pricing_datetime
    closest_date_row = df.iloc[(df['Date'] - pricing_datetime).abs().argsort()[:1]]
    return treasury_rates_to_rate_data(closest_date_row)

# Function to format Treasury yield curve data for the app's rate editor
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

# Function to process rates for calculations in pricing and plotting
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

# Function to plot the rates using Plotly
def plot_rates(rates_df):
    # Create traces for term rate and forward rate
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

    # Create the figure with a custom layout
    fig = go.Figure(data=[term_rate_trace, fwd_rate_trace])

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
        height=300,
    )

    return fig