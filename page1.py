import streamlit as st

# Overview Page Content
def page1():
    st.title("Stock Dashboard Overview")

    st.write("""
    Welcome to the **Stock Dashboard**. This tool provides real-time predictions and analysis for stock market trends. 
    You can explore predictions based on various sectors and individual companies, and access historical data to guide your investment decisions.
    """)

    st.subheader("How to Use the Dashboard")
    st.write("""
    1. **Overview**: Get an overview of key stock market trends and insights.
    2. **Sector Prediction**: Explore predictions based on specific market sectors.
    3. **Company Prediction**: View detailed predictions for individual companies.
    """)

    st.subheader("Features & Functionality")
    st.write("""
    - Real-time stock data and trend predictions.
    - Sector and company-specific analysis.
    - Interactive charts for data exploration.
    - Historical trend insights.
    """)

    st.subheader("Data Sources")
    st.write("""
    This dashboard uses data from [API Name], and predictions are powered by [your model/algorithm name]. 
    We strive to provide up-to-date and accurate information based on reliable financial data.
    """)

    st.subheader("Contact & Further Information")
    st.write("""
    For any inquiries or feedback, feel free to reach out to [your email].
    """)

    # Example Chart (Optional)
    # st.line_chart(data) # Display a sample chart for preview
