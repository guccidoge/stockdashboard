import pandas as pd
import sqlite3
import plotly.graph_objs as go
import streamlit as st

# Helper: Define performance-to-color mapping
def performance_to_color_scale(value):
    if value > 3:
        return 'darkgreen'  # more than 3%
    elif value > 1:
        return 'green'  # more than 1%
    elif value > 0:
        return 'lightgreen'  # less than 1%
    elif value > -1:
        return 'pink'  # decline less than 1%
    elif value > -3:
        return 'red'  # decline more than 1%
    else:
        return 'darkred'  # decline more than 3%

# Helper: Read holdings from the database
def get_holdings_from_db():
    db_path = 'klse_tickers.db'  # Path to your SQLite database
    query = """
    SELECT sp.ticker AS Ticker, 
           c.category AS Sector,
           c.name AS Company, 
           sp.close * sp.volume AS 'Market Value', 
           ((sp.close - sp.open) / sp.open) * 100 AS 'Daily Performance'
    FROM stock_prices sp
    JOIN companies c ON sp.ticker = c.ticker
    WHERE sp.date = (SELECT MAX(date) FROM stock_prices)
    """
    with sqlite3.connect(db_path) as conn:
        data = pd.read_sql(query, conn)
    return data

# Helper: Create the heatmap for market capital
def create_market_cap_heatmap(holdings):
    # Add color scale based on daily performance
    holdings['Color'] = holdings['Daily Performance'].apply(performance_to_color_scale)

    # Create text labels
    holdings['Text'] = holdings.apply(
        lambda row: f"{row['Ticker']} - {row['Company']}<br>{row['Daily Performance']:.2f}%", axis=1
    )

    # Create the heatmap figure
    fig = go.Figure(go.Treemap(
        ids=holdings['Ticker'],
        labels=holdings['Ticker'],
        parents=[""] * len(holdings),  # Single level treemap
        values=holdings['Market Value'],
        textinfo="text",
        text=holdings['Text'],
        marker=dict(colors=holdings['Color'], line=dict(width=1))
    ))

    fig.update_layout(
        margin=dict(t=25, l=25, r=25, b=25),
        title="Market Capitalization Heatmap"
    )

    return fig

# Helper: Create sector-based heatmap
def create_sector_based_heatmap(data):
    # Aggregate sector market values
    sector_data = data.groupby('Sector')['Market Value'].sum().reset_index()
    sector_data['id'] = sector_data['Sector']
    sector_data['parent'] = ""

    # Prepare stock data with sector as parent
    stock_data = data.copy()
    stock_data['id'] = stock_data['Ticker']
    stock_data['parent'] = stock_data['Sector']
    stock_data['Label'] = stock_data['Ticker'] + " - " + stock_data['Company']

    # Concatenate sector and stock data
    treemap_data = pd.concat([sector_data, stock_data], sort=False)

    # Create the treemap figure
    fig = go.Figure(go.Treemap(
        ids=treemap_data['id'],
        labels=treemap_data['Label'].fillna(treemap_data['Sector']),
        parents=treemap_data['parent'],
        values=treemap_data['Market Value'],
        marker=dict(colors=treemap_data['Color']),
        textinfo="label+value+percent entry",
        branchvalues='total'
    ))

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    return fig

# Helper: Get top and worst performing sectors
def get_top_and_worst_sectors(data):
    # Aggregate sector performance
    sector_performance = data.groupby('Sector')['Daily Performance'].mean().reset_index()

    # Get top and worst performing sectors
    top_sectors = sector_performance.nlargest(5, 'Daily Performance')
    worst_sectors = sector_performance.nsmallest(5, 'Daily Performance')

    return top_sectors, worst_sectors

# Helper: Create Top 5 Best Performers and Worst Performers by Sector
def create_sector_performance_charts(holdings):
    # Get top and worst performing sectors
    top_sectors, worst_sectors = get_top_and_worst_sectors(holdings)
    
    # Create Best Performers Bar Chart
    best_performers_chart = go.Figure(go.Bar(
        x=top_sectors['Sector'],
        y=top_sectors['Daily Performance'],
        marker=dict(color='green'),
        text=top_sectors['Daily Performance'].apply(lambda x: f"{x:.2f}%"),
        textposition='outside'
    ))

    best_performers_chart.update_layout(
        title="Top 5 Best Performing Sectors",
        xaxis_title="Sector",
        yaxis_title="Daily Performance (%)",
        margin=dict(t=25, l=25, r=25, b=25)
    )
    
    # Create Worst Performers Bar Chart
    worst_performers_chart = go.Figure(go.Bar(
        x=worst_sectors['Sector'],
        y=worst_sectors['Daily Performance'],
        marker=dict(color='red'),
        text=worst_sectors['Daily Performance'].apply(lambda x: f"{x:.2f}%"),
        textposition='outside'
    ))

    worst_performers_chart.update_layout(
        title="Top 5 Worst Performing Sectors",
        xaxis_title="Sector",
        yaxis_title="Daily Performance (%)",
        margin=dict(t=25, l=25, r=25, b=25)
    )

    return best_performers_chart, worst_performers_chart

# Streamlit page logic with added performance charts
def page2():
    # Display the title with a larger font size and styling
    st.title("Sector Prediction")
    st.markdown("""
        Welcome to the **Sector Prediction** dashboard! This tool helps beginner investors visualize sector performance, 
        market capitalization, and best/worst-performing sectors to make informed decisions.
    """)

    # Load data from the database
    holdings = get_holdings_from_db()

    if holdings.empty:
        st.write("No data available in the database.")
        return

    # Display a button to refresh the data (optional)
    if st.button("Refresh Data"):
        holdings = get_holdings_from_db()

    # Get top and worst performing sectors
    top_sectors, worst_sectors = get_top_and_worst_sectors(holdings)

    # Display top and worst performing sectors in a nice layout
    st.subheader("Top and Worst Performing Sectors")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Top Performing Sectors**")
        st.write(top_sectors[['Sector', 'Daily Performance']].style.format({'Daily Performance': '{:.2f}%'}))
    with col2:
        st.write(f"**Worst Performing Sectors**")
        st.write(worst_sectors[['Sector', 'Daily Performance']].style.format({'Daily Performance': '{:.2f}%'}))

    # Create and display the performance charts for top 5 best and worst performing sectors
    st.subheader("Best and Worst Performing Sectors")
    best_performers_chart, worst_performers_chart = create_sector_performance_charts(holdings)
    
    # Display both charts side by side
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(best_performers_chart)
    with col4:
        st.plotly_chart(worst_performers_chart)

    # Add description before heatmap for clarity
    st.subheader("How to Read the Heatmap")
    st.markdown("""
        The **Market Capitalization Heatmap** shows the relative sizes of the companies, 
        with the color indicating their daily performance. Green shades represent positive performance, 
        while red shades indicate declines. Each box represents a stock, and the size of the box is proportional 
        to the company's market value.
    """)

    # Create the heatmap for market capital
    st.subheader("Market Capitalization Heatmap")
    market_cap_heatmap = create_market_cap_heatmap(holdings)

    # Show the heatmap for market cap
    st.plotly_chart(market_cap_heatmap)

    # Add description before sector-based heatmap
    st.subheader("Understanding the Sector-Based Heatmap")
    st.markdown("""
        The **Sector-Based Heatmap** shows the relative performance of each sector based on its market value. 
        The heatmap allows you to see which sectors are performing well and which are underperforming. 
        Green sectors are performing well, while red sectors are underperforming.
    """)

    # Create the sector-based heatmap
    st.subheader("Sector-Based Heatmap")
    sector_sorted_heatmap = create_sector_based_heatmap(holdings)

    # Show the sector-based heatmap
    st.plotly_chart(sector_sorted_heatmap)

# For testing in Streamlit
if __name__ == "__main__":
    page2()
