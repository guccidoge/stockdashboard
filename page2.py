import numpy as np
import pandas as pd
import sqlite3
import plotly.graph_objs as go
import plotly.express as px
import streamlit as st

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
    
    # Get the average yearly return by sector
    sector_performance = df.groupby('category')['yearly_return'].mean()
    
    # Identify the best and worst performing sectors
    best_sector = sector_performance.idxmax()
    worst_sector = sector_performance.idxmin()

    # Latest news placeholder
    latest_news = "Market sees growth after strong earnings report from tech companies."

    # Streamlit UI to display the metrics
    st.subheader("Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Highest Close This Year", f"${highest_close:.2f}", highest_close_ticker)
    col2.metric("Best Performing Sector", best_sector)
    col3.metric("Worst Performing Sector", worst_sector)

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

    # Display the raw data for inspection
    st.write("Monthly Sector Performance DataFrame:")
    st.dataframe(monthly_sector_performance)

    # Adjust color scale for better visibility
    fig_heatmap = px.imshow(
        monthly_sector_performance,
        title="Sector Performance Heatmap",
        labels=dict(color="Avg Monthly Return (%)", x="Month", y="Sector"),
        color_continuous_scale="RdYlGn",
        zmin=-10,  # Lower bound of the color scale
        zmax=10    # Upper bound of the color scale
    )

    # Plot the heatmap
    st.plotly_chart(fig_heatmap)

    # Streamlit UI to allow user to select sectors for historical performance chart
    st.subheader("Select Sectors to Display on Historical Chart")
    sectors = df['category'].unique()
    selected_sectors = st.multiselect('Select Sectors', sectors, default=sectors[:3])  # Default to first 3 sectors

    # Filter the DataFrame for selected sectors
    filtered_df = df[df['category'].isin(selected_sectors)]

    # Create an empty list to store the plotly line traces for historical chart
    traces = []

    # Loop through each selected sector and calculate the average closing price per sector for each date
    for sector in selected_sectors:
        sector_data = filtered_df[filtered_df['category'] == sector]
        
        # Calculate the average closing price per date for each sector
        sector_avg = sector_data.groupby('date')['close'].mean().reset_index()

        # Add a line trace for each sector's average closing price
        trace = go.Scatter(
            x=sector_avg['date'],
            y=sector_avg['close'],
            mode='lines',
            name=sector  # Name of the line will be the sector name
        )
        traces.append(trace)

    
    # Create the layout for the historical performance chart
    layout = go.Layout(
        title="Price Trend of Stocks by Sector",
        xaxis=dict(
            title="Date",
            rangeslider=dict(visible=True),  # Add a range slider for the x-axis
            type='date',  # Treat the x-axis as date type for zooming
        ),
        yaxis=dict(
            title="Average Closing Price (USD)"
        ),
        showlegend=True,
        hovermode='x unified',  # Show hover info for all lines at the same point
        dragmode='zoom'  # Allow zooming by dragging on the chart
    )

    # Create the figure for historical performance
    fig = go.Figure(data=traces, layout=layout)

    # Display the interactive chart using Streamlit
    st.plotly_chart(fig)

    # Close the database connection
    conn.close()
