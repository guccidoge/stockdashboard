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
        DataFrame containing weekly data for all tickers and a list of failed tickers.
    """
    all_data = []
    failed_tickers = []  # To track tickers that failed to fetch data
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval="1wk")  # Fetch weekly data
            if data.empty:
                raise ValueError("No data found")  # Handle empty data explicitly
            data.reset_index(inplace=True)
            data["Ticker"] = ticker  # Add ticker column
            # Ensure columns match database schema
            data.rename(columns={"Date": "Timestamp", "Stock Splits": "Stock_Splits"}, inplace=True)
            # Convert Timestamp to ISO format for SQLite compatibility
            data["Timestamp"] = data["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
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
        cursor = conn.cursor()

        # Create the database table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            Timestamp TEXT,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER,
            Dividends REAL,
            Stock_Splits REAL,
            Ticker TEXT,
            PRIMARY KEY (Ticker, Timestamp)
        );
        """)

        # Store data
        data.to_sql("stock_data", conn, if_exists="append", index=False)
        conn.commit()  # Commit changes
        print("Data successfully stored in the database.")
    except Exception as e:
        print(f"Error storing data to database: {e}")
    finally:
        conn.close()

def update_database(current_data, db_name="stock_data.db"):
    """
    Update the database with new stock data, checking for existing records.
    Args:
        current_data: DataFrame containing new stock data.
        db_name: Name of the SQLite database file.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        for _, row in current_data.iterrows():
            # Check if a record already exists
            cursor.execute("""
            SELECT 1 FROM stock_data WHERE Ticker = ? AND Timestamp = ?;
            """, (row["Ticker"], row["Timestamp"]))
            exists = cursor.fetchone()

            if exists:
                # Update the existing record
                cursor.execute("""
                UPDATE stock_data SET
                    Open = ?, 
                    High = ?, 
                    Low = ?, 
                    Close = ?, 
                    Volume = ?, 
                    Dividends = ?, 
                    Stock_Splits = ?
                WHERE Ticker = ? AND Timestamp = ?;
                """, (
                    row["Open"], row["High"], row["Low"], row["Close"], 
                    row["Volume"], row["Dividends"], row["Stock_Splits"], 
                    row["Ticker"], row["Timestamp"]
                ))
            else:
                # Insert a new record if it doesn't exist
                cursor.execute("""
                INSERT INTO stock_data (Timestamp, Open, High, Low, Close, Volume, Dividends, Stock_Splits, Ticker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    row["Timestamp"], row["Open"], row["High"], row["Low"], row["Close"], 
                    row["Volume"], row["Dividends"], row["Stock_Splits"], row["Ticker"]
                ))

        conn.commit()  # Commit changes
        print(f"Updated {len(current_data)} records in the database.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
