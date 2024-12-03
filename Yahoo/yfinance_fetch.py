import yfinance as yf
# documentation: https://ranaroussi.github.io/yfinance/reference/index.html

def fetch_stock_data(ticker):
    data = {}
    stock = yf.Ticker(ticker)
    info = stock.info
    price = info.get("currentPrice")
    rating = info.get("recommendationKey", "N/A")
    data[ticker] = {'stock_price': price, 'analyst_rating': rating}
    return data
