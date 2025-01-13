import numpy as np
import pandas as pd
import sqlite3
import plotly.graph_objs as go
import plotly.express as px
import streamlit as st

# Placeholder function to calculate risk score (you should replace this with your actual risk calculation logic)
def calculate_risk(ticker):
    # Example: random risk score for demonstration (replace with actual calculation)
    np.random.seed(hash(ticker) % 1000)  # Consistent random values for each ticker
    return np.random.randint(0, 101)  # Risk score between 0 and 100

def page2():
    # Connect to the SQLite database
    conn = sqlite3.connect('klse_tickers.db')
    
    # Fetch the necessary data from the database
    query = """
    SELECT sp.ticker, sp.date, sp.close, c.category 
    FROM stock_prices sp
    JOIN companies c ON sp.ticker = c.ticker
    WHERE sp.date BETWEEN '2024-01-15' AND '2025-01-13'  
    """
    df = pd.read_sql(query, conn)
    
    # Calculate the highest closing price
    highest_close_row = df.loc[df['close'].idxmax()]
    highest_close = highest_close_row['close']
    highest_close_ticker = highest_close_row['ticker']
    
    # Calculate the performance for each sector (percentage return for each sector)
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['yearly_return'] = (df.groupby('ticker')['close'].transform('last') - df.groupby('ticker')['close'].transform('first')) / df.groupby('ticker')['close'].transform('first') * 100

    # Add risk score to the dataframe
    df['risk_score'] = df['ticker'].apply(calculate_risk)

    # Get the average yearly return and risk by sector
    sector_performance = df.groupby('category')['yearly_return'].mean()
    sector_risk = df.groupby('category')['risk_score'].mean()

    # Identify the best and worst performing sectors
    best_sector = sector_performance.idxmax()
    best_sector_risk = sector_risk[best_sector]

    worst_sector = sector_performance.idxmin()
    worst_sector_risk = sector_risk[worst_sector]

    # Streamlit UI to display the metrics
    st.subheader("Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Highest Close This Year", f"${highest_close:.2f}", highest_close_ticker)
    col2.metric("Best Performing Sector", f"{best_sector} (Risk: {best_sector_risk:.2f})")
    col3.metric("Worst Performing Sector", f"{worst_sector} (Risk: {worst_sector_risk:.2f})")

    # Add Heatmap of Sector Performance
    st.subheader("Heatmap of Sector Performance")

    # Calculate monthly performance for each sector
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    monthly_sector_performance = (
        df.groupby(['category', 'month'])['yearly_return']
        .mean()
        .unstack(level='month')
    )

    # Convert PeriodIndex to string for Plotly compatibility
    monthly_sector_performance.columns = monthly_sector_performance.columns.astype(str)

    # Replace NaN with 0 for better visualization
    monthly_sector_performance = monthly_sector_performance.fillna(0)

    # Heatmap
    fig_heatmap = px.imshow(
        monthly_sector_performance,
        title="Sector Performance Heatmap",
        labels=dict(color="Avg Monthly Return (%)", x="Month", y="Sector"),
        color_continuous_scale="RdYlGn",
        zmin=-10,  # Lower bound of the color scale
        zmax=10    # Upper bound of the color scale
    )
    st.plotly_chart(fig_heatmap)

    # Sector-Wide Risk Distribution Box Plot
    st.subheader("Sector-Wide Risk Distribution")
    fig_box = px.box(
        df,
        x='category',
        y='risk_score',
        title="Sector-Wide Risk Distribution",
        labels={'category': "Sector", 'risk_score': "Risk Score"},
        color='category'
    )
    st.plotly_chart(fig_box)

    # Filter sectors based on user selection
    st.subheader("Select Sectors to Display on Historical Chart")
    sectors = df['category'].unique()
    selected_sectors = st.multiselect('Select Sectors', sectors, default=sectors[:3])

    # Filter the DataFrame for selected sectors
    filtered_df = df[df['category'].isin(selected_sectors)]

    # Create line chart for selected sectors
    traces = []
    for sector in selected_sectors:
        sector_data = filtered_df[filtered_df['category'] == sector]
        sector_avg = sector_data.groupby('date')['close'].mean().reset_index()

        trace = go.Scatter(
            x=sector_avg['date'],
            y=sector_avg['close'],
            mode='lines',
            name=sector
        )
        traces.append(trace)

    layout = go.Layout(
        title="Price Trend of Stocks by Sector",
        xaxis=dict(
            title="Date",
            rangeslider=dict(visible=True),
            type='date',
        ),
        yaxis=dict(title="Average Closing Price (USD)"),
        showlegend=True,
        hovermode='x unified',
        dragmode='zoom'
    )
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig)

    # Close the database connection
    conn.close()
