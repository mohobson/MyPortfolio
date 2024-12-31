from flask import Flask, render_template, request, redirect, url_for
from database import Database
from Yahoo.yfinance_fetch import fetch_stock_data
from Schwab.api import schwab

import pandas as pd
# import matplotlib
# matplotlib.use('Agg')  # Use non-interactive backend
# import matplotlib.pyplot as plt
import plotly.express as px
import json

app = Flask(__name__)
db = Database()


@app.route("/")
def dashboard():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    return render_template("dashboard.html", portfolio=portfolio_data)

@app.route('/sectors')
def sector_breakdown():
    # Fetch portfolio weights as a dictionary for easy lookup
    portfolio_weights = dict(db.get_portfolio_weights())

    # Initialize a dictionary to hold the total sector allocation
    total_sector_allocation = {}

    # Fetch all tickers in your portfolio
    # positions_dict = schwab()
    positions_list = db.fetch_all_data()["Ticker"].tolist()

    for ticker in positions_list:
        # Fetch sector weightings for the current ticker
        sector_weightings = fetch_stock_data(ticker)[1]  # Assuming this returns a dictionary of sector weights

        # Get the portfolio weight for this ticker
        try:
            percent_of_portfolio = float(portfolio_weights.get(ticker, 0))
        except TypeError:
            percent_of_portfolio = 0.0

        # Add sector contributions to total allocation
        for sector, weight in sector_weightings.items():
            total_sector_allocation[sector] = total_sector_allocation.get(sector, 0) + (percent_of_portfolio * float(weight))

    # Normalize the total sector allocation to percentages
    total_invested = sum(total_sector_allocation.values())
    if total_invested > 0:
        total_sector_allocation = {
            sector: (allocation / total_invested) * 100
            for sector, allocation in total_sector_allocation.items()
        }

    # Print or return the total sector allocation
    print("Sector Allocations:")
    for sector, allocation in total_sector_allocation.items():
        print(f"{sector}: {allocation:.2f}%")
            
    # Sort sectors by percentage in descending order
    sorted_sectors = dict(sorted(total_sector_allocation.items(), key=lambda item: item[1], reverse=True))

    # Abbreviation mapping
    abbreviations = {
        'Technology': 'INFT',
        'Financial Services': 'FINL',
        'Communication Services': 'TELS',
        'Industrials': 'INDU',
        'Consumer Cyclical': 'COND',
        'Consumer Defensive': 'CONS',
        'Healthcare': 'HLTH',
        'Utilities': 'UTIL',
        'Real Estate': 'REAL',
        'Energy': 'ENRS',
        'Basic Materials': 'MATR',
    }

    sectors = list(sorted_sectors.keys())
    percentages = list(sorted_sectors.values())

    # plt.figure(figsize=(10, 6))
    # plt.barh(sectors, percentages, color='skyblue')
    # plt.xlabel('Percentage of Portfolio')
    # plt.ylabel('Sectors')
    # plt.title('Portfolio Sector Allocation')
    # plt.gca().invert_yaxis()
    # plt.tight_layout()
    # plt.savefig('static/sector_allocation.png')
    # Manually defined sector colors
    sector_colors = {
        "Real Estate": "#ee82ee",
        "Consumer Cyclical": "#e53935",
        "Basic Materials": "#fdd835",
        "Consumer Defensive": "#6d4c41",
        "Technology": "#fb8c00",
        "Communication Services": "#00ACC1",
        "Financial Services": "#1e88e5",
        "Utilities": "#d81b60",
        "Industrials": "#546e7a",
        "Energy": "#7cb342",
        "Healthcare": "#8e24aa",
        "Unknown": "#708090",
    }

    # Create the Plotly bar chart
    fig = px.bar(
        x=percentages,
        y=sectors,
        orientation="h",
        title="Portfolio Sector Allocation",
        labels={"x": "Percentage of Portfolio", "y": "Sector"},
        color=sectors,  # Set the color based on sectors
        color_discrete_map=sector_colors  # Map sectors to manually defined colors
    )

    # Customize layout
    fig.update_layout(
        title_font_size=20,
        xaxis=dict(title="Percentage of Portfolio", tickformat=".1f"),
        yaxis=dict(title=""),
        bargap=0.2,
        font_color="#bdc1c6",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Save as an HTML file
    fig.write_html("static/sector_allocation.html")

    return render_template('sectors.html', sectors=sorted_sectors, abbreviations=abbreviations)



# https://ranaroussi.github.io/yfinance/reference/api/yfinance.Screener.html#yfinance.Screener
@app.route("/screener")
def screener():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    return render_template("screener.html", portfolio=portfolio_data)

@app.route("/update", methods=["POST"])
def update_price_target():
    # Update the price target for a specific ticker
    ticker = request.form.get("ticker")
    new_target = request.form.get("price_target")
    if ticker and new_target:
        db.update_price_target(ticker, float(new_target))
    return redirect(url_for("dashboard"))

@app.route("/refresh")
def refresh_data():
    # Fetch new data from the API and update the database
    # {'ABC': {longQuantity: float, stockPrice: float, marketValue: float, longOpenProfitLoss: float, percentPortfolio: float, analystRating: string, priceTarget: form}}

    # gather my tickers from Schwab
    positions_dict = schwab()
    tickers = list(positions_dict.keys())

    stock_data = []
    for ticker in tickers:
        yahoo_dict = fetch_stock_data(ticker)[0] # gather info from yahoo api
        stock_price = yahoo_dict[ticker]['stock_price']
        analyst_rating = yahoo_dict[ticker]['analyst_rating']
        long_quantity = positions_dict[ticker]['long_quantity']
        market_value = positions_dict[ticker]['market_value']
        long_open_profit_loss = positions_dict[ticker]['long_profit_loss']

        # handle any stock_price errors (some cannot be found on Yahoo)
        try:
            stock_price = float(market_value) / float(long_quantity)
        except (ZeroDivisionError, ValueError) as e:
            stock_price = stock_price  # Default value or handle error appropriately
            print(f"Error calculating stock_price: {e}")

        # round my numbers
        stock_price = round(stock_price, 1)
        long_quantity = round(long_quantity, 1)
        market_value = round(market_value, 1)
        long_open_profit_loss = round(long_open_profit_loss, 1)

        price_target = db.get_price_target(ticker)

        sector = yahoo_dict[ticker]['sector']

        stock_data.append((ticker, long_quantity, stock_price, market_value, long_open_profit_loss, None, analyst_rating, price_target, sector))

    # load up the database
    db.load_data_into_db(stock_data)
    # Remove positions that are no longer in the latest API fetch
    db.remove_missing_positions(tickers)

    # Calculate percent of portfolio based on holdings
    holdings = {key: value['long_quantity'] for key, value in positions_dict.items()}
    db.calculate_and_update_percent_portfolio(holdings)

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
