import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from database import Database


def calculate_sma(df, short_window=50, long_window=200):
    """Calculate SMA50 and SMA200."""
    df["SMA50"] = df["Close"].rolling(window=short_window).mean()
    df["SMA200"] = df["Close"].rolling(window=long_window).mean()
    return df

def generate_signals(df, ticker):
    # Make sure the dataframe has no missing values
    df = df.dropna()

    # Create new columns initialized to False
    df["Buy Signal"] = False
    df["Sell Signal"] = False

    # Check for crossover events
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        # SMA50 crosses above SMA200 => Buy
        if prev["SMA50"] < prev["SMA200"] and curr["SMA50"] > curr["SMA200"]:
            df.at[df.index[i], "Buy Signal"] = True

        # Price crosses above SMA50 or SMA200 => Buy
        if (prev["Close"] < prev["SMA50"] and curr["Close"] > curr["SMA50"]) or \
           (prev["Close"] < prev["SMA200"] and curr["Close"] > curr["SMA200"]):
            df.at[df.index[i], "Buy Signal"] = True

        # SMA50 crosses below SMA200 => Sell
        if prev["SMA50"] > prev["SMA200"] and curr["SMA50"] < curr["SMA200"]:
            df.at[df.index[i], "Sell Signal"] = True

        # Price crosses below SMA50 or SMA200 => Sell
        if (prev["Close"] > prev["SMA50"] and curr["Close"] < curr["SMA50"]) or \
           (prev["Close"] > prev["SMA200"] and curr["Close"] < curr["SMA200"]):
            df.at[df.index[i], "Sell Signal"] = True

    return df



def create_plot(df, ticker):
    """Generate a Plotly chart for a given stock."""
    fig = go.Figure()

    # Stock price
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode='lines', name=f"{ticker} Price", line=dict(color="black")))

    # SMAs
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], mode='lines', name="SMA50", line=dict(color="blue", dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], mode='lines', name="SMA200", line=dict(color="red", dash="dot")))

    # Buy signals
    buy_signals = df[df["Buy Signal"]]
    fig.add_trace(go.Scatter(
        x=buy_signals.index, y=buy_signals["Close"], mode='markers', name="Buy Signal",
        marker=dict(symbol="triangle-up", color="green", size=10)
    ))

    # Sell signals
    sell_signals = df[df["Sell Signal"]]
    fig.add_trace(go.Scatter(
        x=sell_signals.index, y=sell_signals["Close"], mode='markers', name="Sell Signal",
        marker=dict(symbol="triangle-down", color="red", size=10)
    ))

    fig.update_layout(title=f"{ticker} - SMA Breakouts", xaxis_title="Date", yaxis_title="Price", template="plotly_white")
    
    return pio.to_html(fig, full_html=False)