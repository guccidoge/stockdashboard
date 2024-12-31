import sqlite3
import pandas as pd
from functions_ml import predict_stock_prices_by_sector

def fetch_stock_data():
    # Connect to the database
    conn = sqlite3.connect("stock_data.db")
    query = "SELECT * FROM stock_data"  # Assuming your table is named 'stock_data'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    # Fetch data from the database
    stock_data = fetch_stock_data()

    # Predict stock prices by sector using ARIMA
    predictions_by_sector = predict_stock_prices_by_sector(stock_data)

    # Display predictions (for now, just print them out)
    for sector, predictions in predictions_by_sector.items():
        print(f"Sector: {sector}")
        print(predictions)
        print("------")

if __name__ == "__main__":
    main()
