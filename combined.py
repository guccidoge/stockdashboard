import pandas as pd
import numpy as np
import sqlite3
from statsmodels.tsa.arima.model import ARIMA
from collections import defaultdict
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ---------------- Streamlit Configuration ----------------
st.set_page_config(page_title="Stock Dashboard", layout="wide")

# ---------------- Utility Functions ----------------
def get_nyse_tickers():
    # Mock function to simulate fetching NYSE tickers
    return pd.DataFrame({"Ticker": ["AAPL", "MSFT", "GOOGL"], "Sector": ["Tech", "Tech", "Tech"]})

def fetch_weekly_data(tickers, period="1y"):
    all_data = []
    failed_tickers = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval="1wk")
            if data.empty:
                raise ValueError("No data found")
            data.reset_index(inplace=True)
            data["Ticker"] = ticker
            data.rename(columns={"Date": "Timestamp", "Stock Splits": "Stock_Splits"}, inplace=True)
            data["Timestamp"] = data["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
            all_data.append(data)
        except Exception as e:
            failed_tickers.append((ticker, str(e)))
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(), failed_tickers

def store_data_to_database(data, db_name="stock_data.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
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
        data.to_sql("stock_data", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()

def fetch_and_merge_data(db_path, csv_path):
    conn = sqlite3.connect(db_path)
    stock_data = pd.read_sql("SELECT * FROM stock_data", conn)
    conn.close()
    nyse_tickers_df = pd.read_csv(csv_path)
    stock_data = stock_data.merge(nyse_tickers_df[['Ticker', 'Sector']], on='Ticker', how='left')
    stock_data['Sector'] = stock_data['Sector'].fillna('Unknown')
    return stock_data

def preprocess_data_for_arima(stock_data):
    stock_data['Timestamp'] = pd.to_datetime(stock_data['Timestamp'])
    stock_data.set_index('Timestamp', inplace=True)
    stock_data = stock_data.resample('W').last()
    return stock_data

def predict_stock_prices(stock_data):
    try:
        model = ARIMA(stock_data['Close'], order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=1)
        return forecast[0]
    except Exception as e:
        raise RuntimeError(f"ARIMA failed: {e}")

def predict_stock_prices_by_sector(stock_data):
    predictions_by_sector = defaultdict(list)
    grouped_data = stock_data.groupby('Sector')
    for sector, group in grouped_data:
        sector_predictions = []
        for ticker, ticker_data in group.groupby('Ticker'):
            ticker_data = preprocess_data_for_arima(ticker_data)
            if len(ticker_data) < 10:
                continue
            try:
                predicted_price = predict_stock_prices(ticker_data)
                sector_predictions.append({'Ticker': ticker, 'Predicted Price': predicted_price})
            except Exception as e:
                continue
        predictions_by_sector[sector] = pd.DataFrame(sector_predictions)
    return predictions_by_sector

# ---------------- Streamlit Pages ----------------
def overview_page():
    st.title("Stock Dashboard - Overview")
    st.write("""
        Welcome to the Stock Dashboard!  
        This application forecasts the top 5 companies with the least risk for tomorrow's trading.  
        It also provides detailed forecasts for individual stocks based on selected timeframes.
    """)

def top_5_companies_page():
    st.title("Top 5 Companies to Invest Tomorrow")
    mock_top_5 = pd.DataFrame({
        "Company": ["Company A", "Company B", "Company C", "Company D", "Company E"],
        "Predicted Return (%)": [10.5, 8.2, 7.8, 6.4, 5.9]
    })
    st.bar_chart(mock_top_5.set_index("Company")["Predicted Return (%)"])
    st.write("This chart represents the top 5 companies predicted to have the least risk and highest returns tomorrow.")

def forecast_page():
    st.title("Forecast for Individual Stocks")
    
    # Input for forecast range and stock ticker
    forecast_range = st.slider("Select Forecast Range (days)", 1, 30, 7, step=1)
    ticker = st.text_input("Enter Stock Ticker:", value="AAPL")
    
    # Fetch historical data
    if ticker:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="1y")
        hist_data.reset_index(inplace=True)
        
        if not hist_data.empty:
            st.write(f"Historical prices for {ticker}:")
            st.write(hist_data.tail())
        else:
            st.warning("No historical data found for the given ticker.")
            return
    
    # Generate forecast data
    if st.button("Generate Forecast"):
        # Simulated forecast prices (replace with ARIMA logic later)
        last_close = hist_data["Close"].iloc[-1] if not hist_data.empty else 100
        days = np.arange(1, forecast_range + 1)
        forecast_prices = last_close + np.random.uniform(-5, 5, forecast_range).cumsum()

        # Prepare data for plotting
        forecast_data = pd.DataFrame({
            "Day": pd.date_range(start=hist_data["Date"].iloc[-1], periods=forecast_range + 1, freq="D")[1:],
            "Predicted Price": forecast_prices
        })
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add historical price trace
        fig.add_trace(go.Scatter(
            x=hist_data["Date"],
            y=hist_data["Close"],
            mode='lines',
            name='Historical Prices',
            line=dict(color='blue')
        ))
        
        # Add forecasted price trace
        fig.add_trace(go.Scatter(
            x=forecast_data["Day"],
            y=forecast_data["Predicted Price"],
            mode='lines',
            name='Forecast Prices',
            line=dict(color='orange', dash='dash')
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Stock Prices for {ticker}",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            legend=dict(x=0.1, y=1.1),
            height=500
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display forecast data
        st.write(f"Forecasted prices for {ticker}:")
        st.write(forecast_data)

# ---------------- Main Execution ----------------
# Sidebar navigation
st.sidebar.title("Navigation")
page_options = ["Overview", "Top 5 Companies", "Forecast"]
selected_page = st.sidebar.radio("Select Page:", page_options)

# Render the selected page
if selected_page == "Overview":
    overview_page()
elif selected_page == "Top 5 Companies":
    top_5_companies_page()
elif selected_page == "Forecast":
    forecast_page()
