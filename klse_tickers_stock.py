import sqlite3
import yfinance as yf
import pandas as pd
import time
from tqdm import tqdm

# Connect to SQLite database
conn = sqlite3.connect('klse_tickers.db')
cursor = conn.cursor()

# Fetch historical data for specific stocks based on their available data
def fetch_data_for_new_stocks(tickers):
    for ticker in tickers:
        try:
            # Fetch the data using Yahoo Finance
            company = yf.Ticker(ticker)
            stock_data = company.history(period='max')  # Fetch max available data

            # Convert the index to timezone-naive if it's timezone-aware
            if stock_data.index.tz is not None:
                stock_data.index = stock_data.index.tz_localize(None)  # Make index timezone-naive

            # Calculate the date range to fetch, either 1 year or based on the available data
            start_date = stock_data.index.min().date()  # Get the earliest available date
            end_date = pd.to_datetime('today').date()  # Today's date

            # If data is less than a year, we can still fetch available data
            stock_data_filtered = stock_data.loc[start_date:end_date]

            # Insert data into stock_prices table
            for date, row in stock_data_filtered.iterrows():
                cursor.execute('''INSERT OR REPLACE INTO stock_prices (ticker, date, open, close, high, low, volume)
                                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
                               (ticker, date.date(), row['Open'], row['Close'], row['High'], row['Low'], row['Volume']))
            
            conn.commit()
            print(f"Data fetched for {ticker} from {start_date} to {end_date}")
        
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

# Main function
if __name__ == "__main__":
    try:
        # Specify the new stocks
        new_stocks = ['0325.KL', '5326.KL', '5329.KL']
        
        # Fetch and insert data for the new stocks
        fetch_data_for_new_stocks(new_stocks)
        print("Data fetched for new stocks successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
