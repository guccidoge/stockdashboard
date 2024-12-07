import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import time

# Load tickers from CSV
def load_tickers_from_csv(filename="nyse_tickers.csv"):
    df = pd.read_csv(filename)
    return df["Ticker"].tolist()

# Fetch real-time stock data (including Open, High, Low, Close, Volume)
def fetch_current_price(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.history(period="1d", interval="1m")  # 1-minute interval for real-time data
            if not info.empty:
                latest = info.iloc[-1]  # Get the latest data point
                data.append({
                    "Ticker": ticker,
                    "Open": round(latest["Open"], 2),
                    "High": round(latest["High"], 2),
                    "Low": round(latest["Low"], 2),
                    "Close": round(latest["Close"], 2),
                    "Volume": int(latest["Volume"]),
                    "Current Price": round(latest["Close"], 2),  # Close is usually considered the current price
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return pd.DataFrame(data)

# Update database with current data (keeping previous data as CSV formatted text)
def update_database(current_data, db_name="stock_data.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create table if it doesn't exist
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

        # Insert or update data
        for _, row in current_data.iterrows():
            price_data = f"{row['Timestamp']}:{row['Current Price']}"  # Create CSV-like entry

            # Check if ticker already exists
            cursor.execute("SELECT * FROM stock_data WHERE ticker=?", (row["Ticker"],))
            existing_data = cursor.fetchone()

            if existing_data:
                # If data exists, append the new price to the historical_price_history
                existing_history = existing_data[9] if existing_data[9] else ""
                updated_history = existing_history + f", {price_data}"  # Append new price data
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
                    row["Timestamp"], updated_history, row["Ticker"]
                ))
            else:
                # If data does not exist, insert a new record
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

# Schedule updates at regular intervals (every minute)
def run_real_time_updates(interval=60, db_name="stock_data.db"):
    tickers = load_tickers_from_csv("nyse_tickers.csv")
    print(f"Loaded {len(tickers)} tickers.")
    while True:
        current_data = fetch_current_price(tickers)
        print(f"Fetched data for {len(current_data)} tickers.")
        update_database(current_data, db_name=db_name)
        print(f"Database updated. Sleeping for {interval} seconds...")
        time.sleep(interval)

# Main execution
if __name__ == "__main__":
    try:
        run_real_time_updates(interval=60)  # Update every 60 seconds (1 minute)
    except KeyboardInterrupt:
        print("Real-time updates stopped.")
