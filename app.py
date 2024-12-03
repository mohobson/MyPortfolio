from flask import Flask, render_template, request, redirect, url_for
from database import Database
from Yahoo.yfinance_fetch import fetch_stock_data
from Schwab.api import schwab

import pandas as pd

app = Flask(__name__)
db = Database()

@app.route("/")
def dashboard():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    return render_template("dashboard.html", portfolio=portfolio_data)

@app.route("/sectors")
def sector_breakdown():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    return render_template("sectors.html", portfolio=portfolio_data)

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
        yahoo_dict = fetch_stock_data(ticker) # gather info from yahoo api
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

        stock_data.append((ticker, long_quantity, stock_price, market_value, long_open_profit_loss, None, analyst_rating, None))

    # load up the database
    db.load_data_into_db(stock_data)

    # Calculate percent of portfolio based on holdings
    holdings = {key: value['long_quantity'] for key, value in positions_dict.items()}
    db.calculate_and_update_percent_portfolio(holdings)

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
