import sqlite3
import pandas as pd

class Database:
    def __init__(self, db_path="portfolio.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    Ticker TEXT PRIMARY KEY,
                    Shares REAL,
                    Stock_Price REAL,
                    Market_Value REAL,
                    Profit_Loss REAL,
                    Percent_of_Portfolio REAL,
                    Trailing_PE REAL,
                    Forward_PE REAL,
                    Analyst_Rating TEXT,
                    Analyst_Price_Target REAL,
                    Price_Target REAL,
                    Sector TEXT
                )
            """)
            conn.commit()

    def load_data_into_db(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO portfolio (Ticker, Shares, Stock_Price, Market_Value, Profit_Loss, Percent_of_Portfolio, Trailing_PE, Forward_PE, Analyst_Rating, Analyst_Price_Target, Price_Target, Sector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()


    def remove_missing_positions(self, current_tickers):
        """
        Remove positions from the database that are not in the current list of tickers.
        :param current_tickers: List of tickers fetched from the latest API call.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create a placeholder string for the query, e.g., (?, ?, ?)
            placeholders = ', '.join('?' for _ in current_tickers)
            query = f"""
                DELETE FROM portfolio
                WHERE Ticker NOT IN ({placeholders})
            """
            cursor.execute(query, current_tickers)
            conn.commit()

    def calculate_and_update_percent_portfolio(self, holdings):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Ticker, Stock_Price FROM portfolio")
            rows = cursor.fetchall()

            total_value = sum(
                holdings[ticker] * float(price)
                for ticker, price in rows
                if ticker in holdings and price not in (None, 0)
            )

            for ticker, price in rows:
                if ticker in holdings and price not in (None, 0):
                    holding_value = holdings[ticker] * float(price)
                    percent_portfolio = (holding_value / total_value) * 100 if total_value else 0
                    cursor.execute("""
                        UPDATE portfolio
                        SET Percent_of_Portfolio = ?
                        WHERE Ticker = ?
                    """, (percent_portfolio, ticker))
            conn.commit()
    
    def get_portfolio_weights(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Ticker, Percent_of_Portfolio FROM portfolio")
            return cursor.fetchall()

    def fetch_all_data(self):
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM portfolio", conn)
        return df

    def get_price_target(self, ticker):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Price_Target
                FROM portfolio
                WHERE Ticker = ?
            """, (ticker,))
            result = cursor.fetchone()
            # If the ticker is found, return the price target; otherwise, return None
            return result[0] if result else None

    def update_price_target(self, ticker, price_target):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE portfolio
                SET Price_Target = ?
                WHERE Ticker = ?
            """, (price_target, ticker))
            conn.commit()
