import sqlite3
import yfinance as yf
import pandas as pd
import time
from tqdm import tqdm  # Progress bar library

# Connect to SQLite database
conn = sqlite3.connect('klse_tickers.db')
cursor = conn.cursor()

# Create stock_prices table
cursor.execute('''CREATE TABLE IF NOT EXISTS stock_prices (
                    ticker TEXT,
                    date DATE,
                    open REAL,
                    close REAL,
                    high REAL,
                    low REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, date),
                    FOREIGN KEY (ticker) REFERENCES companies(ticker)
                )''')
conn.commit()

# Create necessary indexes
def create_indexes():
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON companies (category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON companies (name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker_companies ON companies (ticker);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker_prices ON stock_prices (ticker);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_prices ON stock_prices (date);")
    conn.commit()
    print("Indexes created successfully.")

# Fetch tickers from the database
def get_tickers_from_db():
    cursor.execute("SELECT ticker FROM companies")
    return [row[0] for row in cursor.fetchall()]

# Fetch historical stock prices in batches with progress bar
def fetch_historical_prices_in_batches(tickers, batch_size=50, delay=5):
    total_tickers = len(tickers)
    total_batches = (total_tickers - 1) // batch_size + 1

    for i in range(0, total_tickers, batch_size):
        batch = tickers[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1} of {total_batches}")
        
        with tqdm(total=len(batch), desc="Fetching tickers in batch", unit="ticker") as pbar:
            for ticker in batch:
                try:
                    # Fetch historical data for the past year
                    company = yf.Ticker(ticker)
                    stock_data = company.history(period='1y')
                    
                    # Insert data into stock_prices table
                    for date, row in stock_data.iterrows():
                        cursor.execute('''INSERT OR REPLACE INTO stock_prices (ticker, date, open, close, high, low, volume)
                                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                       (ticker, date.date(), row['Open'], row['Close'], row['High'], row['Low'], row['Volume']))
                    
                    conn.commit()
                except Exception as e:
                    print(f"Error fetching data for {ticker}: {e}")
                finally:
                    pbar.update(1)  # Update progress bar for each ticker
        
        # Introduce delay after each batch
        if i + batch_size < total_tickers:
            print(f"Batch {i // batch_size + 1} completed. Waiting for {delay} seconds before next batch...")
            time.sleep(delay)

# Main function
if __name__ == "__main__":
    try:
        # Create indexes
        create_indexes()
        
        # Fetch tickers and process batches with progress bar
        tickers = get_tickers_from_db()
        fetch_historical_prices_in_batches(tickers, batch_size=50, delay=5)
        print("All stock prices fetched successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
