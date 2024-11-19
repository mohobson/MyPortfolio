import yfinance as yf

def fetch_stock_data(tickers):
    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice")
        rating = info.get("recommendationKey", "N/A")
        data.append((ticker, price, None, rating, None))
    return data
