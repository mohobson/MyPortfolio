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
                    Stock_Price REAL,
                    Percent_of_Portfolio REAL,
                    Analyst_Rating TEXT,
                    Price_Target REAL
                )
            """)
            conn.commit()

    def load_data_into_db(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO portfolio (Ticker, Stock_Price, Percent_of_Portfolio, Analyst_Rating, Price_Target)
                VALUES (?, ?, ?, ?, ?)
            """, data)
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

    def fetch_all_data(self):
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM portfolio", conn)
        return df

    def update_price_target(self, ticker, price_target):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE portfolio
                SET Price_Target = ?
                WHERE Ticker = ?
            """, (price_target, ticker))
            conn.commit()
