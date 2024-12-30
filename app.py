import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(page_title="Stock Dashboard", layout="wide")

# Function to manage navigation state
def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Overview"

# Sidebar navigation with buttons
st.sidebar.title("Navigation")
if st.sidebar.button("Overview"):
    navigate_to("Overview")
if st.sidebar.button("Top 5 Companies"):
    navigate_to("Top 5 Companies")
if st.sidebar.button("Forecast"):
    navigate_to("Forecast")

# Current page display
current_page = st.session_state["current_page"]

# Overview Page
if current_page == "Overview":
    st.title("Stock Dashboard - Overview")
    st.write("""
        Welcome to the Stock Dashboard!  
        This application helps beginner investors by forecasting the top 5 companies with the least risk for tomorrow's trading.  
        It also provides detailed forecasts for individual stocks based on selected timeframes.  
    """)

# Top 5 Companies Page
elif current_page == "Top 5 Companies":
    st.title("Top 5 Companies to Invest Tomorrow")
    # Mock data for top 5 companies
    mock_top_5 = pd.DataFrame({
        "Company": ["Company A", "Company B", "Company C", "Company D", "Company E"],
        "Predicted Return (%)": [10.5, 8.2, 7.8, 6.4, 5.9]
    })

    st.bar_chart(mock_top_5.set_index("Company")["Predicted Return (%)"])
    st.write("This chart represents the top 5 companies predicted to have the least risk and highest returns tomorrow.")

# Forecast Page
elif current_page == "Forecast":
    st.title("Forecast for Individual Stocks")

    # Forecast slider
    forecast_range = st.slider("Select Forecast Range", 1, 30, 7, step=1)
    st.write(f"Forecasting for the next {forecast_range} days.")

    # Input for ticker
    ticker = st.text_input("Enter Stock Ticker:", value="AAPL")

    if st.button("Generate Forecast"):
        # Mock data for forecast
        days = np.arange(1, forecast_range + 1)
        prices = np.random.uniform(low=100, high=200, size=forecast_range)

        forecast_data = pd.DataFrame({
            "Day": days,
            "Predicted Price": prices
        })

        # Line chart for the forecast
        st.line_chart(forecast_data.set_index("Day"))
        st.write(f"Forecasted stock prices for {ticker} over the next {forecast_range} days.")
