import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from collections import defaultdict

def preprocess_data_for_arima(stock_data):
    """
    Preprocess stock data for ARIMA model.
    - Convert 'Timestamp' to datetime
    - Set 'Timestamp' as index
    - Resample to weekly frequency if needed
    """
    stock_data['Timestamp'] = pd.to_datetime(stock_data['Timestamp'])
    stock_data.set_index('Timestamp', inplace=True)
    stock_data = stock_data.resample('W').last()  # Resample to weekly data
    return stock_data

def predict_stock_prices(stock_data):
    """
    Apply ARIMA model to predict the next week's stock price.
    """
    # Assuming we're predicting the 'Close' price
    model = ARIMA(stock_data['Close'], order=(5, 1, 0))  # Example ARIMA configuration
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=1)  # Forecast for the next week
    return forecast[0]  # Return predicted stock price

def predict_stock_prices_by_sector(stock_data):
    """
    Predict the stock price for all companies, grouped by sector.
    """
    predictions_by_sector = defaultdict(list)

    # Group by Sector
    grouped_data = stock_data.groupby('Sector')

    for sector, group in grouped_data:
        print(f"Processing sector: {sector}")
        sector_predictions = []

        # Process each stock in the sector
        for ticker, ticker_data in group.groupby('Ticker'):
            ticker_data = preprocess_data_for_arima(ticker_data)
            try:
                predicted_price = predict_stock_prices(ticker_data)
                sector_predictions.append({'Ticker': ticker, 'Predicted Price': predicted_price})
            except Exception as e:
                print(f"Error predicting price for {ticker}: {e}")
        
        predictions_by_sector[sector] = pd.DataFrame(sector_predictions)

    return predictions_by_sector

def fetch_and_merge_data(db_path="stock_data.db", csv_path="nyse_tickers.csv"):
    """
    Fetch stock data from database and merge with sector information from CSV.
    Args:
        db_path (str): Path to the SQLite database file.
        csv_path (str): Path to the CSV file containing ticker and sector information.
    Returns:
        DataFrame: Merged DataFrame with stock and sector data.
    """
    # Fetch stock data from database
    conn = sqlite3.connect(db_path)
    stock_data = pd.read_sql("SELECT * FROM stock_data", conn)
    conn.close()

    # Load sector information
    nyse_tickers_df = pd.read_csv(csv_path)

    # Merge on the 'Ticker' column
    stock_data = stock_data.merge(nyse_tickers_df[['Ticker', 'Sector']], on='Ticker', how='left')

    # Optional: Handle missing sectors
    stock_data['Sector'] = stock_data['Sector'].fillna('Unknown')  # Or drop rows with missing sectors

    return stock_data
