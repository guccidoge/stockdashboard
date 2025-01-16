import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import time

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

    return X, y

# Function to display today's and tomorrow's price with arrows
def display_prices_and_arrows(today_price, tomorrow_price):
    if tomorrow_price > today_price:
        arrow = "↑"  # Green arrow (up)
        color = "green"
    else:
        arrow = "↓"  # Red arrow (down)
        color = "red"

    # Display today's price and tomorrow's price with the arrow
    st.markdown(
        f"### Today's Price: MYR {round(today_price, 2)}  |  "
        f"**Tomorrow's Price: MYR {round(tomorrow_price, 2)}** <span style='color:{color};'>{arrow}</span>",
        unsafe_allow_html=True
    )

# Function to train Random Forest and make predictions
def random_forest_forecast(data, forecast_range=7):
    # Prepare the features and target
    X, y = create_features(data)

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
    
    # Custom circular button styling with updated contrast and visibility
    st.markdown(
        f"""
        <style>
            .search-button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: white;
                color: #007BFF;
                text-decoration: none;
                border-radius: 50px;  /* Circular border */
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #007BFF;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: background-color 0.3s ease, transform 0.2s ease;
            }}
            .search-button:hover {{
                background-color: #007BFF;  /* Blue background on hover */
                color: white;
                transform: translateY(-2px);
            }}
            .search-button:active {{
                background-color: #0056b3;  /* Darker blue when clicked */
                border-color: #0056b3;
            }}
        </style>
        <a class="search-button" href="{search_url}" target="_blank">Search for {ticker} Stock News</a>
        """, unsafe_allow_html=True)

# Function to calculate volatility (standard deviation of daily returns)
def calculate_volatility(ticker):
    with get_db_connection() as conn:
        query = """
        SELECT date, open, close FROM stock_prices WHERE ticker = ? ORDER BY date DESC LIMIT 252
        """
        stock_data = pd.read_sql(query, conn, params=(ticker,))

        # Calculate daily returns (percentage change)
        stock_data['daily_return'] = stock_data['close'].pct_change()

        # Calculate volatility (standard deviation of daily returns)
        volatility = stock_data['daily_return'].std() * np.sqrt(252)  # Annualize the volatility

    return volatility

# Function to calculate revenue growth
def calculate_revenue_growth(ticker):
    with get_db_connection() as conn:
        query = """
        SELECT date, revenue FROM financials WHERE ticker = ? ORDER BY date DESC LIMIT 2
        """
        revenue_data = pd.read_sql(query, conn, params=(ticker,))

    if len(revenue_data) == 2:
        revenue_growth = (
            (revenue_data.iloc[0]['revenue'] - revenue_data.iloc[1]['revenue'])
            / revenue_data.iloc[1]['revenue']
        ) * 100
        return revenue_growth
    else:
        return None  # Not enough data for revenue growth

# Function to calculate profit margin
def calculate_profit_margin(ticker):
    with get_db_connection() as conn:
        query = """
        SELECT revenue, net_income FROM financials WHERE ticker = ? ORDER BY date DESC LIMIT 1
        """
        financial_data = pd.read_sql(query, conn, params=(ticker,))

    if len(financial_data) > 0:
        revenue = financial_data.iloc[0]['revenue']
        net_income = financial_data.iloc[0]['net_income']

        if revenue > 0:  # To avoid division by zero
            return (net_income / revenue) * 100
    return None

# Function to calculate normalized metrics by sector
def normalize_by_sector(ticker):
    with get_db_connection() as conn:
        # Fetch the sector for the given ticker
        query_sector = "SELECT category FROM companies WHERE ticker = ?"
        sector = pd.read_sql(query_sector, conn, params=(ticker,)).iloc[0]['category']

        # Fetch sector-wide metrics
        query_sector_data = """
        SELECT f.ticker, f.market_cap, f.pe_ratio, f.revenue, f.net_income
        FROM financials f
        JOIN companies c ON f.ticker = c.ticker
        WHERE c.category = ?
        """
        sector_data = pd.read_sql(query_sector_data, conn, params=(sector,))

        # Calculate sector averages
        sector_avg = sector_data.mean(numeric_only=True)

        # Fetch the target company's financial data
        query_company = """
        SELECT market_cap, pe_ratio, revenue, net_income
        FROM financials
        WHERE ticker = ? ORDER BY date DESC LIMIT 1
        """
        company_data = pd.read_sql(query_company, conn, params=(ticker,))

    if company_data.empty or sector_data.empty:
        return None  # Return None if data is insufficient

    # Normalize company metrics against sector averages
    normalized_metrics = {
        'market_cap': company_data.iloc[0]['market_cap'] / sector_avg['market_cap'],
        'pe_ratio': company_data.iloc[0]['pe_ratio'] / sector_avg['pe_ratio'],
        'revenue': company_data.iloc[0]['revenue'] / sector_avg['revenue'],
        'net_income': company_data.iloc[0]['net_income'] / sector_avg['net_income'],
    }

    return normalized_metrics

# Updated function to calculate the risk score
def calculate_risk(ticker):
    with get_db_connection() as conn:
        query = """
        SELECT market_cap, pe_ratio FROM financials WHERE ticker = ? ORDER BY date DESC LIMIT 1
        """
        financial_data = pd.read_sql(query, conn, params=(ticker,))

        if len(financial_data) > 0:
            market_cap = financial_data.iloc[0]['market_cap']
            pe_ratio = financial_data.iloc[0]['pe_ratio']

            # Calculate metrics
            volatility = calculate_volatility(ticker)
            revenue_growth = calculate_revenue_growth(ticker)
            profit_margin = calculate_profit_margin(ticker)

            # Normalize metrics to 0-100 scale
            risk_score = 0

            # Volatility: Higher volatility = higher risk
            if volatility and volatility < 0.1:
                risk_score += 10
            elif volatility and volatility < 0.2:
                risk_score += 30
            else:
                risk_score += 50

            # Revenue Growth: Negative growth = higher risk
            if revenue_growth is not None:
                if revenue_growth > 10:
                    risk_score += 10  # Low risk
                elif revenue_growth > 0:
                    risk_score += 30  # Moderate risk
                else:
                    risk_score += 50  # High risk

            # Profit Margin: Lower profit margin = higher risk
            if profit_margin is not None:
                if profit_margin > 15:
                    risk_score += 10
                elif profit_margin > 5:
                    risk_score += 30
                else:
                    risk_score += 50

            # Ensure risk score doesn't exceed 100
            risk_score = min(risk_score, 100)

            return risk_score

    return None


# Display the risk for a selected company
def display_risk_for_selected_company(ticker):
    if not ticker:
        st.error("Please select a company first.")
        return

    risk_score = calculate_risk(ticker)

    if risk_score is not None:
        # Show the risk score and company name in the Streamlit UI
        st.subheader(f"Risk Analysis for {ticker}")

        # Determine risk level and color
        if risk_score < 30:
            risk_level = "Low Risk"
            color = "green"
        elif risk_score < 60:
            risk_level = "Medium Risk"
            color = "yellow"
        else:
            risk_level = "High Risk"
            color = "red"

        # Display risk level text
        st.markdown(
            f"""
            <div style="text-align: center; font-weight: bold; color: {color}; font-size: 18px; margin-bottom: 10px;">
                {risk_level}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Animated progress bar
        placeholder = st.empty()  # Create a placeholder for dynamic content

        for i in range(risk_score + 1):
            placeholder.markdown(
                f"""
                <div style="height: 15px; width: 100%; background-color: lightgrey; border-radius: 10px; overflow: hidden;">
                    <div style="height: 100%; width: {i}%; background-color: {color};"></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            time.sleep(0.02)  # Adjust speed of the animation

        with st.expander("How is this calculated?"):
            st.markdown("""
            The risk level is calculated based on the following factors:
            - **Volatility**: Measured by the standard deviation of stock returns.
            - **Beta**: The stock's sensitivity to market movements.
            - **Sharpe Ratio**: The risk-adjusted return of the stock.
            - **Sector Risk**: Average risk score of the sector.
                        
            Formulas:
            - Volatility: $\\sigma = \\sqrt{\\frac{1}{N}\\sum_{i=1}^N (r_i - r_{\text{avg}})^2}$
            - Beta: $\\beta = \\frac{\\text{Cov}(r_{\\text{stock}}, r_{\\text{market}})}{\\text{Var}(r_{\\text{market}})}$
            - Sharpe Ratio: $S = \\frac{r - r_f}{\\sigma}$
            - Risk Score: $R = w_1 \\cdot \\sigma + w_2 \\cdot \\beta + w_3 \\cdot (1 - S) + w_4 \\cdot \\text{Sector Risk}$
            """)

def get_all_companies():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM companies")
        companies = [row[0] for row in cursor.fetchall()]
    return companies

# Function to format large numbers as M or B, handling negative numbers
def format_large_number(value):
    if value is None:  # Handle cases where value might be None
        return "N/A"
    
    abs_value = abs(value)  # Get the absolute value to determine the scale
    if abs_value >= 1e9:  # Billions
        return f"{value / 1e9:.2f}B"
    elif abs_value >= 1e6:  # Millions
        return f"{value / 1e6:.2f}M"
    elif abs_value >= 1e3:  # Thousands (if needed)
        return f"{value / 1e3:.2f}K"
    else:
        return f"{value:.2f}"

# Streamlit Application
def page3():
    st.title("Stock Dashboard")

    # Filter by category dropdown
    category = st.selectbox("Filter by category:", ["All"] + get_categories())

    # Display companies based on category or search term
    if category != "All":
        companies = get_companies_by_category(category)
    else:
        companies = get_all_companies()
    company_name = st.selectbox("Select a company:", companies)

    # If a company is selected, fetch and display details
    if company_name:
        company_details = get_company_details(company_name)
        if company_details:
            ticker, pe_ratio, market_cap, revenue, net_income, eps = company_details
            st.subheader(f"Details for {company_name} ({ticker})")
        
            # Adjust column widths and avoid overflow
            col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 3])  # Adjust the width ratio as needed
        
            # P/E Ratio
            with col1:
                st.metric("P/E Ratio", round(pe_ratio, 2) if pe_ratio else "N/A")
                with st.expander("What is P/E Ratio?"):
                    st.write("""
                        Low P/E means the stock might be undervalued, suggesting a good buying opportunity. 
                        High P/E means people expect big growth, but the stock may be expensive.
                    """)
        
            # Market Cap
            with col2:
                st.metric("Market Cap", format_large_number(market_cap) if market_cap else "N/A")
                with st.expander("What is Market Cap?"):
                    st.write("""
                        How big the company is. 
                        Larger companies have larger market cap, meaning generally safer to invest.
                        Small companies could also offer high growth but are riskier.
                    """)
        
            # Revenue
            with col3:
                st.metric("Revenue", format_large_number(revenue) if revenue else "N/A")
                with st.expander("What is Revenue?"):
                    st.write("""
                        Total amount of money a company earns from selling goods or services.
                        High revenue means high income generated.
                    """)
        
            # Net Income
            with col4:
                st.metric("Net Income", format_large_number(net_income) if net_income else "N/A")
                with st.expander("What is Net Income?"):
                    st.write("""
                        Company's total profit, after paying all expenses.
                        Positive Net means a profitable company.
                    """)
        
            # Earnings Per Share
            with col5:
                st.metric("Earnings Per Share", round(eps, 2) if eps else "N/A")
                with st.expander("What is Earnings Per Share (EPS)?"):
                    st.write("""
                        How much profit company makes per share. 
                        High EPS means company is earning more from each share.
                    """)
        else:
            st.warning("Company details not found.")

    # Forecasting Section with Random Forest
    st.title("Forecast for Selected Stock")

    # Input for forecast range using select buttons
    forecast_options = {
        "1 week": 7,
        "2 weeks": 14,
        "3 weeks": 21,
        "1 month": 30
    }
    forecast_range_label = st.selectbox(
        "Select forecast duration:",
        options=list(forecast_options.keys()),
        index=0  # Default selection is "1 week"
    )

    # Map the selected label to its corresponding value in days
    forecast_range = forecast_options[forecast_range_label]

    # Fetch stock data for the selected company
    if company_name:
        company_details = get_company_details(company_name)
        if company_details:
            ticker = str(company_details[0])
            stock_data = get_stock_data_from_db(ticker)

            # Convert 'close' column to numeric, coercing errors to NaN
            stock_data['close'] = pd.to_numeric(stock_data['close'], errors='coerce')

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

                    with st.expander("Model Forecast Details", expanded=False):
                        st.markdown(
                            f"""
                            **Forecast Method:** Random Forest Regressor

                            **Model Accuracy:** {r_squared_percentage:.2f}% | _This means the model explains {r_squared_percentage:.2f}% of the price movements based on historical data._

                            **Mean Absolute Error (MAE):** ±RM{mae:.2f} | _On average, the predictions deviate from actual prices by this amount._

                            **Note:** The forecast is based on historical trends and assumes market conditions remain stable.
                            """
                        )


                    display_risk_for_selected_company(ticker)

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

