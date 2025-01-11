import streamlit as st
import page1 as p1
import page2 as p2
import page3 as p3

# Set page configuration
st.set_page_config(page_title="Stock Dashboard", layout="wide")

# Pages dictionary for navigation
PAGES = {
    "Overview": p1.page1,
    "Sector Prediction": p2.page2,
    "Company Prediction": p3.page3,
}

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Overview"

# Sidebar navigation with buttons
st.sidebar.title("Navigation")
for page_name in PAGES.keys():
    if st.sidebar.button(page_name):
        st.session_state["current_page"] = page_name

# Display the current page
current_page = st.session_state["current_page"]
PAGES[current_page]()
