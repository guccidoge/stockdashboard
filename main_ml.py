import pandas as pd
from functions_ml import predict_stock_prices_by_sector, fetch_and_merge_data

def main():
    try:
        # Fetch and merge stock data with sector information
        stock_data = fetch_and_merge_data(
            db_path="stock_data.db",
            csv_path="nyse_tickers.csv"  # Ensure this file path is correct
        )
        print("Data successfully fetched and merged!")

        # Predict stock prices by sector using ARIMA
        print("Generating predictions by sector...")
        predictions_by_sector = predict_stock_prices_by_sector(stock_data)

        # Display predictions
        for sector, predictions in predictions_by_sector.items():
            print(f"Sector: {sector}")
            print(predictions)
            print("------")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
