import yfinance as yf
# documentation: https://ranaroussi.github.io/yfinance/reference/index.html

def fetch_stock_data(ticker):
    # ticker = format_ticker_name(ticker)
    data = {}
    stock = yf.Ticker(ticker)
    info = stock.info
    # for key, value in info.items():
    #     print(key, value)
    #     print('\n')
    price = info.get("currentPrice")
    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    rating = info.get("recommendationKey", "N/A")
    analyst_price_target = info.get("targetMeanPrice")

    # print(analyst_price_target, trailing_pe, forward_pe)
    # print(info.get('quoteType', ''))

    if "ETF" in info.get("quoteType", "") or "MUTUALFUND" in info.get("quoteType", ""):  # Check if it's an ETF or Mutual Fund
        # holdings = stock.get_funds_data(ticker).equity_holdings
        sector_weightings = {}
        unformatted_sector_weightings = stock.get_funds_data().sector_weightings
        for sector, weight in unformatted_sector_weightings.items():
            sector = format_sector_name(sector)
            sector_weightings[sector] = weight
        top_sector = max(sector_weightings, key=sector_weightings.get)
        sector = top_sector
        sector = format_sector_name(sector)
    else:
        sector = info.get("sector", "Unknown")
        sector = format_sector_name(sector)
        sector_weightings = {sector: 1.0}
    # print(sector)

    data[ticker] = {'stock_price': price,
                    'trailing_pe': trailing_pe,
                    'forward_pe': forward_pe,
                    'analyst_rating': rating,
                    'analyst_price_target': analyst_price_target,
                    'sector': sector}
    return data, sector_weightings

# some tickers will require formatting for yahoo
# one ex is BRK.B (schwab) which is BRK-B in yahoo
def format_ticker_name(ticker):
    if ticker == 'BRK.B':
        ticker = 'BRK-B'
    return ticker

def format_sector_name(sector):
    if sector == 'realestate':
        sector = 'Real Estate'
    elif sector == 'consumer_cyclical':
        sector = 'Consumer Cyclical'
    elif sector == 'basic_materials':
        sector = 'Basic Materials'
    elif sector == 'consumer_defensive':
        sector = 'Consumer Defensive'
    elif sector == 'technology':
        sector = 'Technology'
    elif sector == 'communication_services':
        sector = 'Communication Services'
    elif sector == 'financial_services':
        sector = 'Financial Services'
    elif sector == 'utilities':
        sector = 'Utilities'
    elif sector == 'industrials':
        sector = 'Industrials'
    elif sector == 'energy':
        sector = 'Energy'
    elif sector == 'healthcare':
        sector = 'Healthcare'
    return(sector)

def get_one_year_daily_close_price(ticker, period="1y"):
    """Fetch stock data from Yahoo Finance."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df[['Close']]

# fetch_stock_data('SPY')