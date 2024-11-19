from flask import Flask, render_template, request, redirect, url_for
from database import Database
from Yahoo.yfinance_fetch import fetch_stock_data

app = Flask(__name__)
db = Database()

@app.route("/")
def dashboard():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    return render_template("dashboard.html", portfolio=portfolio_data)

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
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN"]  # Example tickers
    stock_data = fetch_stock_data(tickers)

    # Replace existing data in the database
    db.load_data_into_db(stock_data)

    # Calculate percent of portfolio based on holdings
    holdings = {"AAPL": 10, "GOOGL": 2, "MSFT": 15, "AMZN": 5}
    db.calculate_and_update_percent_portfolio(holdings)

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
