import streamlit as st

def page1():
    # Page Title
    st.title("🌟 Stock Dashboard Overview 🌟")

    # Welcome Message
    st.markdown(
        """
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: #333;">Welcome to the <b>Stock Dashboard</b>!</h3>
            <p style="color: #666; font-size: 16px;">
                This tool provides real-time predictions and analysis for stock market trends. 
                Explore sector-based insights, company-specific forecasts, and historical data to make 
                informed investment decisions. 🌱💹
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # How to Use Section
    st.subheader("📘 How to Use the Dashboard")
    st.markdown(
        """
        1. **Overview**: 🏙️ View main market KLSE market trends and insights.
        2. **Sector Prediction**: 🏢 Analyze predictions for specific market sectors.
        3. **Company Prediction**: 🏦 Dive into detailed predictions for individual companies.
        """
    )

    # Features & Functionality Section
    st.subheader("✨ Features & Functionality")
    st.markdown(
        """
        - 📊 **Historical stock data** and trend predictions.
        - 🔍 **Sector and company-specific analysis** for deeper insights.
        - 📈 **Interactive charts** to explore data visually.
        - 📜 **Historical trend analysis** to identify patterns over time.
        """
    )

    # Data Sources Section
    st.subheader("📡 Data Sources")
    st.markdown(
        """
        This dashboard pulls data from **[Yahoo Finance](https://finance.yahoo.com/)**, with predictions 
        powered by our **Machine Learning model**. We prioritize accurate, up-to-date, and reliable financial data. 🔗
        """
    )

    # Contact Section
    st.subheader("📩 Contact & Feedback")
    st.markdown(
        """
        Have questions or suggestions? We'd love to hear from you! 
        Reach out via email at **[eilliyahfong@gmail.com](mailto:eilliyahfong@gmail.com)**. 📨
        """
    )

    # Closing Note
    st.markdown(
        """
        <div style="text-align: center; font-size: 14px; margin-top: 20px; color: #888;">
            <em>Happy investing! 🚀💰</em>
        </div>
        """,
        unsafe_allow_html=True
    )
