import pandas as pd
import sqlite3
import streamlit as st

# Function to fetch stock data and merge with sector data
def fetch_and_merge_data():
    # Path to your stock database and the CSV file with sector info
    db_path = "stock_data.db"  # Adjust the path to your database
    sector_csv_path = "nyse_tickers.csv"  # Adjust the path to your CSV file with sector data

    # Connect to the stock database
    conn = sqlite3.connect(db_path)
    stock_data = pd.read_sql("SELECT * FROM stock_data", conn)
    conn.close()

    # Load the sector information from the CSV
    sector_data = pd.read_csv(sector_csv_path)

    # Merge the stock data with the sector data on the Ticker column
    merged_data = pd.merge(stock_data, sector_data[['Ticker', 'Sector']], on='Ticker', how='left')

    return merged_data

# Page 2 - Stock Price Predictions by Sector
def page2():
    st.title("Stock Price Predictions by Sector")

    # Fetch and merge data
    stock_data = fetch_and_merge_data()

    # Get unique sectors
    sectors = stock_data['Sector'].dropna().unique()  # Drop NaN values to avoid errors
    selected_sector = st.selectbox("Select a Sector:", sectors)

    if selected_sector:
        st.write(f"Fetching data for sector: {selected_sector}...")

        # Filter data by selected sector
        sector_data = stock_data[stock_data['Sector'] == selected_sector]

        # Allow user to make prediction only after selecting a sector
        if st.button("Show Predictions for Selected Sector"):
            # Assuming you have a function to predict stock prices, e.g., using ML models
            predictions = predict_stock_prices_by_sector(sector_data)

            # Show predictions
            st.subheader(f"Predictions for Sector: {selected_sector}")
            st.dataframe(predictions)
        else:
            st.write("Please press the button to generate predictions.")

    else:
        st.warning("Please select a sector first.")

# Sample prediction function (Replace with actual model prediction)
def predict_stock_prices_by_sector(sector_data):
    # Placeholder prediction logic (you can replace this with your model)
    sector_data['Predicted Price'] = sector_data['Close'] * 1.05  # Fake prediction: 5% increase
    return sector_data[['Ticker', 'Predicted Price']]

if __name__ == "__main__":
    page2()
