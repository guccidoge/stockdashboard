import pandas as pd
import sqlite3
from functions import fetch_weekly_data, store_data_to_database, update_database
from functions_ml import train_model, get_top_5_low_risk

def load_data_from_database(db_path, table_name):
    """
    Load data from the database for machine learning.
    Args:
        db_path: Path to the SQLite database file.
        table_name: Name of the table to fetch data from.
    Returns:
        DataFrame with the fetched data.
    """
    conn = sqlite3.connect(db_path)
    try:
        query = f"SELECT * FROM {table_name}"
        data = pd.read_sql(query, conn)
    finally:
        conn.close()
    return data

def preprocess_data(data):
    """
    Add necessary columns for machine learning.
    Args:
        data: DataFrame containing stock data.
    Returns:
        DataFrame with calculated features.
    """
    # Calculate Volatility (rolling 4-week standard deviation of % changes in Close prices)
    data['Volatility'] = data['Close'].pct_change().rolling(window=4).std()
    
    # Calculate Sharpe Ratio (assuming risk-free rate is 0.02 for simplicity)
    data['Sharpe Ratio'] = (data['Close'].rolling(window=4).mean() - 0.02) / data['Volatility']
    
    # Drop rows with NaN values after calculations
    return data.dropna(subset=['Volatility', 'Sharpe Ratio'])

def main():
    # Database path and table name
    db_path = "stock_data.db"
    table_name = "stock_data"

    # Step 1: Load data from the database
    print("Loading data from the database...")
    weekly_data = load_data_from_database(db_path, table_name)

    if not weekly_data.empty:
        # Step 2: Preprocess data
        print("Preprocessing data...")
        weekly_data = preprocess_data(weekly_data)

        # Step 3: Train the machine learning model
        print("Training machine learning model...")
        model = train_model(weekly_data)

        # Step 4: Predict risk
        print("Predicting risk for companies...")
        weekly_data['Risk_Prediction'] = model.predict(weekly_data[['Volatility', 'Sharpe Ratio']])

        # Step 5: Get the top 5 low-risk companies
        print("Getting top 5 low-risk companies...")
        top_5_companies = get_top_5_low_risk(weekly_data)

        print("Top 5 Low-Risk Companies:")
        print(top_5_companies)
    else:
        print("No data available for processing.")

if __name__ == "__main__":
    main()
