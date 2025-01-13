import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Function to get a fresh database connection
def get_db_connection():
    return sqlite3.connect('klse_tickers.db', check_same_thread=False)

# Function to get categories from the database
def get_categories():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM companies")
        categories = [row[0] for row in cursor.fetchall()]
    return categories

# Function to get companies by category
def get_companies_by_category(category):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM companies WHERE category = ?", (category,))
        companies = [row[0] for row in cursor.fetchall()]
    return companies

# Function to get company details from the financials table
def get_company_details(company_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.ticker, f.pe_ratio, f.market_cap, f.revenue, f.net_income, f.earnings_per_share
            FROM companies c
            JOIN financials f ON c.ticker = f.ticker
            WHERE c.name = ?
            ORDER BY f.date DESC LIMIT 1
            """,
            (company_name,),
        )
        company_details = cursor.fetchone()
    return company_details

def get_stock_data_from_db(ticker):
    # Fetch the stock data from the database
    with get_db_connection() as conn:
        query = f"SELECT * FROM stock_prices WHERE ticker = '{ticker}'"
        stock_data = pd.read_sql(query, conn)

    # Debugging: Check the first few rows of stock data after fetching it
    print("Stock data sample:")
    print(stock_data.head())
    
    # Debugging: Check if 'date' exists and its data type
    if 'date' not in stock_data.columns:
        raise KeyError("The 'date' column is missing from the stock data.")
    print(f"'date' column type: {stock_data['date'].dtype}")
    
    return stock_data

# Function to create features for the Random Forest model
def create_features(data):
    if 'date' not in data.columns:
        raise KeyError("The 'date' column is missing in the data passed to create_features.")

    # Convert 'date' to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')

    # Remove rows where 'date' could not be converted
    data = data.dropna(subset=['date'])

    # Set 'date' as the index
    data.set_index('date', inplace=True)
    data = data.resample('D').ffill()

    # Create lag features
    for i in range(1, 6):  # Lags for 1, 2, 3, 4, 5 days
        data[f'lag_{i}'] = data['close'].shift(i)

    # Create rolling mean features
    data['rolling_mean_5'] = data['close'].rolling(window=5).mean()

    # Drop rows with NaN values that were created during the shift
    data.dropna(inplace=True)

    # Drop 'ticker' column from the features since it's not numeric
    data = data.drop('ticker', axis=1, errors='ignore')

    # Create the feature matrix X and target vector y
    X = data.drop('close', axis=1)  # Features should only include numerical columns
    y = data['close']  # Target should be the stock price (close)

    # Debugging: Check the columns in X and y
    print(f"Feature matrix columns: {X.columns}")
    print(f"Target column: {y.name}")

    return X, y

# Function to display today's and tomorrow's price with arrows
def display_prices_and_arrows(today_price, tomorrow_price):
    if tomorrow_price > today_price:
        arrow = "🔼"  # Green arrow (up)
        color = "green"
    else:
        arrow = "🔽"  # Red arrow (down)
        color = "red"

    # Display today's price and tomorrow's price with the arrow
    st.markdown(
        f"### Today's Price: {round(today_price, 2)} RM  |  "
        f"**Tomorrow's Price: {round(tomorrow_price, 2)} RM** {arrow}",
        unsafe_allow_html=True
    )

# Function to train Random Forest and make predictions
def random_forest_forecast(data, forecast_range=7):
    # Prepare the features and target
    X, y = create_features(data)

    # Debugging: Check the data types of the features
    print(X.dtypes)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Initialize and train the Random Forest model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict the next forecast_range days
    forecast_data = X.tail(forecast_range)
    forecast_predictions = model.predict(forecast_data)

    # Calculate metrics
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r_squared = model.score(X_test, y_test)

    return forecast_predictions, mae, r_squared

def display_search_button(ticker):
    # Creating a Google search URL for the user to search for stock news
    search_url = f"https://www.google.com/search?q={ticker}+stock+news"
    
    # Creating a clean, contrasting styled button with custom CSS
    st.markdown(
        f"""
        <style>
            .search-button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #28a745;  /* Green for better visibility */
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: background-color 0.3s ease, transform 0.2s ease;
            }}
            .search-button:hover {{
                background-color: #218838;  /* Darker green on hover */
                transform: translateY(-2px);
            }}
            .search-button:active {{
                background-color: #1e7e34;  /* Even darker green when clicked */
            }}
        </style>
        <a class="search-button" href="{search_url}" target="_blank">Search for {ticker} Stock News</a>
        """, unsafe_allow_html=True)

# Streamlit Application
def page3():
    st.title("Stock Dashboard")

    # Search barstreamlit
    search_term = st.text_input("Search for a company or ticker:", "")

    # Filter by category dropdown
    category = st.selectbox("Filter by category:", ["All"] + get_categories())

    # Display companies based on category or search term
    if category != "All":
        companies = get_companies_by_category(category)
    else:
        companies = []
        if search_term:
            # If there's a search term, get companies matching the search
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM companies WHERE name LIKE ?", ('%' + search_term + '%',))
                companies = [row[0] for row in cursor.fetchall()]

    # Dropdown to select a company from the filtered list
    company_name = st.selectbox("Select a company:", companies)

    # If a company is selected, fetch and display details
    if company_name:
        company_details = get_company_details(company_name)
        if company_details:
            ticker, pe_ratio, market_cap, revenue, net_income, eps = company_details
            st.subheader(f"Details for {company_name} ({ticker})")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("P/E Ratio", round(pe_ratio, 2) if pe_ratio else "N/A")
            with col2:
                st.metric("Market Cap", f"${market_cap / 1e9:.2f} B" if market_cap else "N/A")
            with col3:
                st.metric("Revenue", f"${revenue / 1e9:.2f} B" if revenue else "N/A")
            with col4:
                st.metric("Net Income", f"${net_income / 1e6:.2f} M" if net_income else "N/A")
            with col5:
                st.metric("EPS", round(eps, 2) if eps else "N/A")
        else:
            st.warning("Company details not found.")
    else:
        st.warning("Please select a company to view details.")

    # Forecasting Section with Random Forest
    st.title("Forecast for Selected Stock")

    # Input for forecast range and stock ticker
    forecast_range = st.slider("Select Forecast Range (days)", 1, 30, 7, step=1)

    # Fetch stock data for the selected company
    if company_name:
        company_details = get_company_details(company_name)
        if company_details:
            ticker = str(company_details[0])
            stock_data = get_stock_data_from_db(ticker)

            # Debugging: Check the stock data
            print(stock_data.head())

            # Convert 'close' column to numeric, coercing errors to NaN
            stock_data['close'] = pd.to_numeric(stock_data['close'], errors='coerce')

            # Debugging: Check if the 'close' column has been converted correctly
            print(stock_data['close'].head())

            if stock_data.empty:
                st.warning(f"No historical data found for ticker {ticker}.")
                return

            # Display a sample of the stock data
            if st.checkbox("Show raw data"):
                st.dataframe(stock_data, height=500)

            # Generate forecast data when button is pressed
            if st.button("Generate Forecast"):
                try:
                    forecast_predictions, mae, r_squared = random_forest_forecast(stock_data, forecast_range)

                    # Prepare forecast data
                    forecast_dates = pd.date_range(
                        start=stock_data['date'].max(), periods=forecast_range + 1, freq='D'
                    )[1:]
                    forecast_data = pd.DataFrame({'Date': forecast_dates, 'Predicted Price': forecast_predictions})

                     # Get today's price (last value from the historical data)
                    today_price = stock_data['close'].iloc[-1]

                    # Display today's price and tomorrow's forecast price with arrows
                    tomorrow_price = forecast_predictions[0]  # Forecast for the next day
                    display_prices_and_arrows(today_price, tomorrow_price)

                    # Display metrics in Streamlit with layman explanation
                    r_squared_percentage = r_squared * 100

                    st.markdown(
                        f"""
                        - **Forecasted using**: Random Forest Regressor
                        - **Model Accuracy**: {r_squared_percentage:.2f}%  
                          *(This means the model explains {r_squared_percentage:.2f}% of the price movements based on historical data.)*
                        - **Mean Absolute Error (MAE)**: ±{mae:.2f} RM  
                          *(On average, predictions deviate from actual prices by this amount.)*

                        *The forecast is based on historical trends and assumes market conditions remain stable.*
                        """
                    )

                    # Create Plotly figure
                    fig = go.Figure()

                    # Add historical price trace
                    fig.add_trace(go.Scatter(
                        x=stock_data['date'],
                        y=stock_data['close'],
                        mode='lines',
                        name='Historical Prices',
                        line=dict(color='blue')
                    ))

                    # Add forecasted price trace with color change based on price rise or fall
                    for i in range(1, len(forecast_predictions)):
                        color = 'green' if forecast_predictions[i] > forecast_predictions[i - 1] else 'red'
                        fig.add_trace(go.Scatter(
                            x=[forecast_dates[i - 1], forecast_dates[i]],
                            y=[forecast_predictions[i - 1], forecast_predictions[i]],
                            mode='lines',
                            name='Forecast Prices',
                            line=dict(color=color),
                            showlegend=False
                        ))

                    # Layout and styling for the plot
                    fig.update_layout(
                        title=f"Stock Price Forecast for {ticker}",
                        xaxis_title="Date",
                        yaxis_title="Price (RM)",
                        template="plotly_dark",
                        dragmode="pan",  # Enable drag-to-pan functionality
                        hovermode="x unified",  # Improve hover interaction
                    )

                    # Enable scroll zoom
                    fig.update_layout(
                        xaxis=dict(fixedrange=False),  # Allow zooming on x-axis
                        yaxis=dict(fixedrange=False),  # Allow zooming on y-axis
                    )

                    # Display forecast plot with interactivity
                    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

                except Exception as e:
                    st.error(f"An error occurred during forecasting: {e}")

                display_search_button(ticker)
