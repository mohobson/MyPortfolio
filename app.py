from flask import Flask, render_template, request, redirect, url_for, send_file
from database import Database
import create_charts
from Yahoo.yfinance_fetch import fetch_stock_data
from Yahoo.yfinance_fetch import get_one_year_daily_close_price
from Schwab.api import schwab
import time
from datetime import datetime, timedelta, timezone
import io
import csv

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

    sector_dictionary = {
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

    # get sectors for legend at top
    sectors = list(sector_dictionary.keys())

    # Sort portfolio by sector
    portfolio_data = portfolio_data.sort_values("Sector")

    # Prepare data for rendering with sector-specific classes
    portfolio_with_classes = [
        {
            "row": row,
            "sector_class": row.Sector.replace(' ', '-').lower() if row.Sector else "default-sector",
        }
        for row in portfolio_data.itertuples()
    ]

    return render_template("dashboard.html", sectors=sectors, portfolio=portfolio_with_classes)

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
        sector_weightings = fetch_stock_data(ticker)[1]  # returns a dictionary of sector weights

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
            
    # Sort sectors by percentage in descending order
    sorted_sectors = dict(sorted(total_sector_allocation.items(), key=lambda item: item[1], reverse=True))

    sector_dictionary = {
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

    # Abbreviation mapping
    abbreviations = sector_dictionary # defined at bottom of this module

    sectors = list(sorted_sectors.keys())
    percentages = list(sorted_sectors.values())

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
        color_discrete_map=sector_colors,  # Map sectors to manually defined colors
        text=[f"{p:.1f}%" for p in percentages]  # Add text labels
    )

    # Customize layout
    fig.update_traces(textposition="auto") # auto-position labels
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

@app.route("/update_price_target", methods=["POST"])
def update_price_target():
    # Update the price target for a specific ticker
    ticker = request.form.get("ticker")
    new_target = request.form.get("price_target")
    if ticker and new_target:
        db.update_price_target(ticker, float(new_target))
    return redirect(url_for("dashboard"))

@app.route("/update_notes", methods=["POST"])
def update_ticker_notes():
    # Update the ticker notes for a specific ticker
    ticker = request.form.get("tick")
    new_notes = request.form.get("ticker_notes")
    print(new_notes, 0)
    if ticker and new_notes:
        print(new_notes)
        db.update_ticker_notes(ticker, new_notes)
    return redirect(url_for("dashboard"))

@app.route("/delete_note", methods=["POST"])
def delete_note():
    ticker = request.form["tick"]
    db.delete_ticker_notes(ticker)
    return redirect(url_for("dashboard"))

@app.route("/refresh")
def refresh_data():
    # Fetch new data from the API and update the database
    # {'ABC': {longQuantity: float, stockPrice: float, marketValue: float, longOpenProfitLoss: float, percentPortfolio: float, analystRating: string, priceTarget: form}}

    # gather my tickers from Schwab
    positions_dict = schwab()
    tickers = list(positions_dict.keys())

    stock_data = []
    ticker_count = 0 # just tracking how many requests I'm sending to yahoo
    for ticker in tickers:
        ticker_count += 1
        # print(ticker_count, ticker)
        yahoo_dict = fetch_stock_data(ticker)[0] # gather info from yahoo api - been getting too many requests error
        # time.sleep(1.5)
        stock_price = yahoo_dict[ticker]['stock_price']
        trailing_pe = yahoo_dict[ticker]['trailing_pe']
        forward_pe = yahoo_dict[ticker]['forward_pe']
        analyst_rating = yahoo_dict[ticker]['analyst_rating']
        if analyst_rating == "N/A" or analyst_rating == "none":
            analyst_rating = '-'
        analyst_price_target = yahoo_dict[ticker]['analyst_price_target']
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

        try:
            stock_price = round(stock_price, 1)
        except:
            print(f'{stock_price} not a float')
        try:
            trailing_pe = round(trailing_pe, 1)
        except:
            # print(f'{trailing_pe} not a float')
            trailing_pe = '-'
        try:
            forward_pe = round(forward_pe, 1)
        except:
            # print(f'{forward_pe} not a float')
            forward_pe = '-'
        try:
            analyst_price_target = round(analyst_price_target, 1)
        except:
            # print(f'{analyst_price_target} not a float')
            analyst_price_target = '-'
        try:
            long_quantity = round(long_quantity, 1)
        except:
            print(f'{long_quantity} not a float')
        try:
            market_value = round(market_value, 1)
        except:
            print(f'{market_value} not a float')
        try:
            long_open_profit_loss = round(long_open_profit_loss, 1)
        except:
            print(f'{long_open_profit_loss} not a float')

        price_target = db.get_price_target(ticker)

        sector = yahoo_dict[ticker]['sector']

        ticker_notes = db.get_ticker_notes(ticker)

        stock_data.append((ticker, long_quantity, stock_price, market_value, long_open_profit_loss, None, trailing_pe, forward_pe, analyst_rating, analyst_price_target, price_target, sector, ticker_notes))

    # load up the database
    db.load_data_into_db(stock_data)
    # Remove positions that are no longer in the latest API fetch
    db.remove_missing_positions(tickers)

    # Calculate percent of portfolio based on holdings
    holdings = {key: value['long_quantity'] for key, value in positions_dict.items()}
    db.calculate_and_update_percent_portfolio(holdings)

    return redirect(url_for("dashboard"))

@app.route("/charts", methods=["GET", "POST"])
def charts():
    tickers = db.fetch_all_data()["Ticker"].tolist()
    charts = []
    signal_filter = "all"
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "search":
            tickers_input = request.form["tickers"].upper().replace(" ", "")
            tickers = tickers_input.split(",") if tickers_input else tickers

        elif form_type == "filter":
            signal_filter = request.form.get("signal_filter", "all")

    days_lookback = 5
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_lookback) # LOOK AT CHANGING FROM UTC TO EST

    for ticker in tickers:
        df = get_one_year_daily_close_price(ticker)
        df = create_charts.calculate_sma(df)
        df_signals = create_charts.generate_signals(df.copy(), ticker)  # Only for signals
        
        # Reindex signals to match main DataFrame and fill NaN with False
        df['Buy Signal'] = df_signals.reindex(df.index)['Buy Signal'].fillna(False)
        df['Sell Signal'] = df_signals.reindex(df.index)['Sell Signal'].fillna(False)

        recent_signals = df_signals.loc[cutoff_date:]

        show_chart = False
        if signal_filter == "buy" and recent_signals["Buy Signal"].any():
            show_chart = True
        elif signal_filter == "sell" and recent_signals["Sell Signal"].any():
            show_chart = True
        elif signal_filter == "all":
            show_chart = True

        if show_chart:
            charts.append(create_charts.create_plot(df, ticker))

    return render_template("charts.html", charts=charts)

@app.route("/download_portfolio")
def download_portfolio():
    # Fetch all data from the database
    portfolio_data = db.fetch_all_data()
    
    # Create a string buffer to write the CSV data
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Write headers
    cw.writerow(['Ticker', 'Shares', 'Stock Price', 'Market Value', 'Profit/Loss', 
                 '% of Portfolio', 'Trailing PE', 'Forward PE', 'Analyst Rating', 
                 'Analyst Price Target', 'Price Target', 'Notes'])
    
    # Write data rows
    for _, row in portfolio_data.iterrows():
        cw.writerow([
            row['Ticker'],
            row['Shares'],
            row['Stock_Price'],
            row['Market_Value'],
            row['Profit_Loss'],
            f"{row['Percent_of_Portfolio']:.2f}" if pd.notnull(row['Percent_of_Portfolio']) else "0.00",
            row['Trailing_PE'],
            row['Forward_PE'],
            row['Analyst_Rating'],
            row['Analyst_Price_Target'],
            row['Price_Target'],
            row['Notes']
        ])
    
    # Get the string value and encode it
    output = si.getvalue().encode('utf-8')
    si.close()
    
    # Create a BytesIO buffer for the response
    output_buffer = io.BytesIO(output)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        output_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'portfolio_data_{timestamp}.csv'
    )

if __name__ == "__main__":
    app.run(debug=True)
