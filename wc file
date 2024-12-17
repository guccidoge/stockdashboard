import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import sqlite3
import seaborn as sns

# Step 1: Data Retrieval
def fetch_stock_data(ticker, start_date, end_date):
    """Retrieve stock data from Yahoo Finance."""
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Step 2: Save Data to SQL Database
def save_to_database(data, db_name, table_name):
    """Save DataFrame to an SQLite database."""
    conn = sqlite3.connect(db_name)
    data.to_sql(table_name, conn, if_exists='replace', index=True)
    conn.close()

# Step 3: Feature Engineering
def prepare_features(data):
    """Generate features for the model."""
    data['Return'] = data['Adj Close'].pct_change()
    data['MA10'] = data['Adj Close'].rolling(10).mean()
    data['MA50'] = data['Adj Close'].rolling(50).mean()
    data['EMA10'] = data['Adj Close'].ewm(span=10, adjust=False).mean()
    data['EMA50'] = data['Adj Close'].ewm(span=50, adjust=False).mean()
    data['Volatility'] = data['Return'].rolling(10).std()
    data.dropna(inplace=True)
    return data

# Step 4: Train-Test Split
def split_data(data):
    """Split data into training and testing sets."""
    X = data[['MA10', 'MA50', 'EMA10', 'EMA50', 'Volatility']]
    y = data['Adj Close']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test

# Step 5: Train Model
def train_model(X_train, y_train):
    """Train a Random Forest model."""
    y_train = y_train.values.ravel()  # Convert to NumPy array and flatten
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

# Step 6: Evaluate Model
def evaluate_model(model, X_test, y_test):
    """Evaluate the model and return the RMSE."""
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    return rmse, predictions

# Step 7: Visualization
def visualize_results(predictions, y_test):
    """Visualize actual vs predicted stock prices."""
    plt.figure(figsize=(12, 6))
    y_test_flat = y_test.values.flatten()  # Flatten to 1D
    predictions_flat = predictions.flatten() if len(predictions.shape) > 1 else predictions
    sns.lineplot(x=range(len(y_test_flat)), y=y_test_flat, label='Actual', color='blue')
    sns.lineplot(x=range(len(predictions_flat)), y=predictions_flat, label='Predicted', color='orange')
    plt.title('Stock Price Prediction')
    plt.xlabel('Days')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.show()

# Main Function
def main():
    print("Welcome to the Stock Prediction System!")
    ticker = input("Enter the stock ticker symbol (e.g., AAPL for Apple): ").strip().upper()
    start_date = "2020-01-01"
    end_date = "2023-01-01"
    
    try:
        # Step 1: Fetch Data
        data = fetch_stock_data(ticker, start_date, end_date)
        if data.empty:
            print(f"No data found for the ticker '{ticker}'. Please check the ticker symbol.")
            return
        
        # Step 2: Save Data to SQL
        db_name = "stock_data.db"
        table_name = f"{ticker.lower()}_stock"
        save_to_database(data, db_name, table_name)
        print(f"Data for {ticker} saved to {db_name} in table {table_name}.")
        
        # Step 3: Feature Engineering
        data = prepare_features(data)
        
        # Step 4: Split Data
        X_train, X_test, y_train, y_test = split_data(data)
        
        # Step 5: Train Model
        model = train_model(X_train, y_train)
        
        # Step 6: Evaluate Model
        rmse, predictions = evaluate_model(model, X_test, y_test)
        print(f"Root Mean Squared Error for {ticker}: {rmse}")
        
        # Step 7: Visualization
        visualize_results(predictions, y_test)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
