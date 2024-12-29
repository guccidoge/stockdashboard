import pandas as pd
from functions import fetch_weekly_data, store_data_to_database, update_database
from nyse_tickers import get_nyse_tickers

def main():
    # Step 1: Scrape tickers using nyse_tickers.py
    try:
        print("Fetching NYSE tickers...")
        nyse_tickers_df = get_nyse_tickers()
        tickers = nyse_tickers_df["Ticker"].tolist()
        print(f"Fetched {len(tickers)} tickers from Wikipedia.")
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return  # Exit if ticker fetching fails

    # Step 2: Fetch weekly stock data for the tickers
    try:
        print(f"Fetching data for {len(tickers)} tickers...")
        weekly_data, failed_tickers = fetch_weekly_data(tickers)
        print("Fetched weekly data.")
    except Exception as e:
        print(f"Error fetching weekly data: {e}")
        return  # Exit if data fetching fails

    # Step 3: Print failed tickers if any
    if failed_tickers:
        print("\nFailed to fetch data for the following tickers:")
        for ticker, error in failed_tickers:
            print(f"{ticker}: {error}")
    else:
        print("Successfully fetched data for all tickers.")

    # Step 4: Store the data in the database
    if not weekly_data.empty:
        print("Storing data to database...")
        store_data_to_database(weekly_data)
    else:
        print("No data to store in the database.")

    # Step 5: Optionally, update the database with new data
    if not weekly_data.empty:
        print("Updating the database with new data...")
        update_database(weekly_data)
    else:
        print("No data to update in the database.")

if __name__ == "__main__":
    main()
