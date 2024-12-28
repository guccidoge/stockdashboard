# RTD.py

import yfinance as yf
import pandas as pd
import sqlite3

def fetch_weekly_data(tickers, period="1y"):
    """
    Fetch weekly historical stock data for a list of tickers.
    Args:
        tickers: List of stock tickers.
        period: Time period for the historical data (default: 1 year).
    Returns:
        DataFrame containing weekly data for all tickers.
    """
    all_data = []
    failed_tickers = []  # To track tickers that failed to fetch data
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval="1wk")  # Weekly data
            if data.empty:
                raise ValueError("No data found")  # Handle empty data explicitly
            data.reset_index(inplace=True)
            data["Ticker"] = ticker  # Add ticker column
            all_data.append(data)
        except Exception as e:
            failed_tickers.append((ticker, str(e)))  # Record the ticker and error message
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(), failed_tickers

def store_data_to_database(data, db_name="stock_data.db"):
    """
    Store historical data into a SQLite database.
    Args:
        data: DataFrame containing the stock data.
        db_name: Name of the SQLite database file.
    """
    try:
        conn = sqlite3.connect(db_name)
        data.to_sql("stock_data", conn, if_exists="replace", index=False)  # Replace old table
        print("Data successfully stored in the database.")
    except Exception as e:
        print(f"Error storing data to database: {e}")
    finally:
        conn.close()

def update_database(current_data, db_name="stock_data.db"):
    """
    Update the database with new or existing stock data.
    Args:
        current_data: DataFrame with the latest stock data to update.
        db_name: Name of the SQLite database.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            current_price REAL NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            historical_price_history TEXT
        );
        """)

        for _, row in current_data.iterrows():
            price_data = f"{row['Timestamp']}:{row['Current Price']}"

            cursor.execute("SELECT * FROM stock_data WHERE ticker=?", (row["Ticker"],))
            existing_data = cursor.fetchone()

            if existing_data:
                cursor.execute("""
                UPDATE stock_data SET
                    current_price = ?, 
                    open_price = ?,
                    high_price = ?,
                    low_price = ?,
                    close_price = ?,
                    volume = ?,
                    timestamp = ?, 
                    historical_price_history = ?
                WHERE ticker = ?;
                """, (
                    row["Current Price"], row["Open"], row["High"], row["Low"], row["Close"], row["Volume"],
                    row["Timestamp"], price_data, row["Ticker"]
                ))
            else:
                cursor.execute("""
                INSERT INTO stock_data (ticker, current_price, open_price, high_price, low_price, close_price, volume, timestamp, historical_price_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    row["Ticker"], row["Current Price"], row["Open"], row["High"], row["Low"], row["Close"], row["Volume"],
                    row["Timestamp"], price_data
                ))

        conn.commit()
        print(f"Updated {len(current_data)} records in the database.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
