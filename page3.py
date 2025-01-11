import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
import itertools

# Function to load the NYSE tickers CSV
def load_nyse_tickers():
    tickers_df = pd.read_csv("nyse_tickers.csv")  # Ensure path is correct
    return tickers_df

# Function to query stock data from the SQLite database
def get_stock_data_from_db(ticker):
    conn = sqlite3.connect("stock_data.db")  # Ensure path to DB is correct
    query = f"SELECT * FROM stock_data WHERE Ticker = '{ticker}' ORDER BY Timestamp DESC LIMIT 365"
    stock_data = pd.read_sql(query, conn)
    conn.close()
    return stock_data

# Function to calculate model accuracy (Mean Absolute Error)
def calculate_accuracy(actual, forecasted):
    return np.mean(np.abs((actual - forecasted) / actual))

# Function for grid search over ARIMA parameters (p, d, q)
def grid_search_arima(data, column, max_p=2, max_d=1, max_q=2):
    p_values = range(0, max_p + 1)
    d_values = range(0, max_d + 1)
    q_values = range(0, max_q + 1)

    best_aic = np.inf
    best_model = None
    best_order = None
    best_accuracy = 0

    for p, d, q in itertools.product(p_values, d_values, q_values):
        try:
            # Fit ARIMA model
            model = ARIMA(data[column], order=(p, d, q))
            model_fit = model.fit(maxiter=50, disp=False)
            
            # Train/test split evaluation
            train_size = int(len(data) * 0.8)
            train, test = data.iloc[:train_size], data.iloc[train_size:]
            model_fit_train = ARIMA(train[column], order=(p, d, q)).fit()
            predictions_test = model_fit_train.forecast(steps=len(test))
            accuracy_test = mean_absolute_error(test[column], predictions_test)
            
            # Last 7 days evaluation
            test_data_last_7 = data[column].tail(7)
            if len(test_data_last_7) >= 7:
                predictions_last_7 = model_fit.forecast(steps=7)
                accuracy_last_7 = calculate_accuracy(test_data_last_7, predictions_last_7)
                avg_price_last_7 = np.mean(test_data_last_7)
                accuracy_percentage_last_7 = 100 - (accuracy_last_7 * 100)

            # Log results
            print(f"Order: ({p}, {d}, {q}) | AIC: {model_fit.aic:.2f} | Test MAE: {accuracy_test:.2f} | Last 7 Days Accuracy: {accuracy_percentage_last_7:.2f}%")
            
            # Update best model
            if model_fit.aic < best_aic and accuracy_last_7 <= 0.7:
                best_aic = model_fit.aic
                best_order = (p, d, q)
                best_model = model_fit
                best_accuracy = accuracy_last_7

        except Exception as e:
            print(f"Error with order ({p}, {d}, {q}): {e}")
            continue

    return best_order, best_model, best_accuracy


def page3():
    st.title("Forecast for Individual Stocks")
    
    # Load the NYSE tickers data
    tickers_df = load_nyse_tickers()
    
    # Get the list of tickers from the 'Ticker' column
    tickers = tickers_df['Ticker'].tolist()

    # Input for forecast range and stock ticker
    forecast_range = st.slider("Select Forecast Range (weeks)", 1, 30, 7, step=1)
    ticker = st.selectbox("Select Stock Ticker:", tickers)
    
    # Fetch historical data from the database for the selected ticker
    stock_data = get_stock_data_from_db(ticker)
    
    if stock_data.empty:
        st.warning(f"No historical data found for ticker {ticker}.")
        return

    # Convert Timestamp column to datetime format
    stock_data['Timestamp'] = pd.to_datetime(stock_data['Timestamp'])

    # Display historical data
    st.write(f"Historical data for {ticker}:")
    st.write(stock_data.tail())

    # Generate forecast data when button is pressed
    if st.button("Generate Forecast"):
        # ARIMA Forecasting Logic
        try:
            # Preprocess data for ARIMA
            stock_data.set_index("Timestamp", inplace=True)
            stock_data = stock_data.resample("W").last()  # Resample weekly
            stock_data.dropna(subset=["Close"], inplace=True)  # Ensure Close column has no missing values
        
            # Use grid search to find the best ARIMA model
            best_order, best_model, best_accuracy = grid_search_arima(stock_data, "Close")
        
            if best_model:
                # Generate forecast with the best model
                forecast_result = best_model.get_forecast(steps=forecast_range, alpha=0.05)
                forecast = forecast_result.predicted_mean  # The forecasted values
                conf_int = forecast_result.conf_int()      # The confidence intervals
            
                forecast_index = pd.date_range(start=stock_data.index[-1] + pd.Timedelta(weeks=1), 
                                           periods=forecast_range, freq="W")
            
                # Prepare data for plotting
                forecast_data = pd.DataFrame({
                    "Date": forecast_index,
                    "Predicted Price": forecast
                })
            
                # Create Plotly figure
                fig = go.Figure()
            
                # Add historical price trace
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data["Close"],
                    mode='lines',
                    name='Historical Prices',
                    line=dict(color='blue')
                ))
            
                # Add forecasted price trace
                fig.add_trace(go.Scatter(
                    x=forecast_data["Date"],
                    y=forecast_data["Predicted Price"],
                    mode='lines',
                    name='Forecast Prices',
                    line=dict(color='orange', dash='dash')
                ))

                # Add confidence intervals
                fig.add_trace(go.Scatter(
                    x=forecast_index,
                    y=conf_int.iloc[:, 0],  # Lower bound
                    mode='lines',
                    name='Lower Confidence Interval',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_index,
                    y=conf_int.iloc[:, 1],  # Upper bound
                    mode='lines',
                    name='Upper Confidence Interval',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(255, 182, 193, 0.3)',
                    showlegend=False,
                    hoverinfo="skip"
                ))

                # Update layout
                fig.update_layout(
                    title=f"Stock Prices for {ticker} (Best ARIMA Model: {best_order}, Accuracy: {best_accuracy:.2f} MAE)",
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
                st.write(f"Model Accuracy (Mean Absolute Error) on last 7 days: {best_accuracy:.2f}")
        
            else:
                st.write("No suitable ARIMA model found.")
        
        except Exception as e:
            st.error(f"Error during ARIMA prediction: {e}")
