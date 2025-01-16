import sqlite3
import streamlit as st
import page1 as p1  # Ensure these files exist with corresponding page functions
import page2 as p2
import page3 as p3
from datetime import datetime, timedelta, time

# Database connection
conn = sqlite3.connect('klse_tickers.db')
c = conn.cursor()

# Create user table if not exists
def create_usertable():
    c.execute('''
    CREATE TABLE IF NOT EXISTS userstable(
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    conn.commit()

# Add user data
def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?, ?)', (username, password))
    conn.commit()

# Login validation
def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    return c.fetchall()

# Get market status
def get_market_status():
    now = datetime.now()
    market_open_morning = datetime.combine(now.date(), time(9, 0))
    market_close_morning = datetime.combine(now.date(), time(12, 30))
    market_open_afternoon = datetime.combine(now.date(), time(14, 30))
    market_close_afternoon = datetime.combine(now.date(), time(17, 0))

    if now < market_open_morning:
        status = "Market Closed"
        time_remaining = market_open_morning - now
        message = f"Time until market opens: {str(time_remaining).split('.')[0]}"
    elif market_open_morning <= now <= market_close_morning:
        status = "Market Open"
        time_remaining = market_close_morning - now
        message = f"Time until morning session closes: {str(time_remaining).split('.')[0]}"
    elif market_close_morning < now < market_open_afternoon:
        status = "Market Closed"
        time_remaining = market_open_afternoon - now
        # Format time explicitly to remove microseconds
        hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        message = f"Time until afternoon session opens: {hours:02}:{minutes:02}:{seconds:02}"
    elif market_open_afternoon <= now <= market_close_afternoon:
        status = "Market Open"
        time_remaining = market_close_afternoon - now
        # Format time explicitly to remove microseconds
        hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        message = f"Time until market closes: {hours:02}:{minutes:02}:{seconds:02}"
    else:
        status = "Market Closed"
        next_day_open = market_open_morning + timedelta(days=1)
        time_remaining = next_day_open - now
        hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        message = f"Time until market opens tomorrow: {hours:02}:{minutes:02}:{seconds:02}"

    return status, message


# Main dashboard
def main_dashboard():
    
    # Initialize session state for current page
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Overview"

    # Market status
    status, message = get_market_status()

    # Sidebar structure
    st.sidebar.title(f"Welcome, {st.session_state.get('username', 'Guest')}")
    st.sidebar.markdown(f"📅 **{datetime.now().strftime('%A, %d %B %Y')}**")

    # Navigation menu
    PAGES = {
        "Overview": p1.page1,
        "Sector Prediction": p2.page2,
        "Company Prediction": p3.page3,
    }

    st.sidebar.subheader("Menu Navigation")
    for page_name in PAGES.keys():
        if st.sidebar.button(page_name):
            st.session_state["current_page"] = page_name

    # Add GIF
    st.sidebar.markdown('<img src="https://i.gifer.com/7D7o.gif" width="250">', unsafe_allow_html=True)

    # Market timing info
    st.sidebar.markdown(f"**Status:** {status}")
    st.sidebar.markdown(f"⏰ {message}")

    # Logout button
    if st.sidebar.button("Logout"):
        logout()

    # Footer
    st.sidebar.markdown("""
        <hr>
        <p style="font-size: 13px; text-align: center;">&copy; Group 7</p>
    """, unsafe_allow_html=True)

    # Display selected page
    current_page = st.session_state["current_page"]
    PAGES[current_page]()

# Login page
def login_page():
    menu = ["Home", "Login", "Signup"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        # Landing page content
        st.markdown("## Stock Dashboard: Beginner's Tool Guide")
        st.markdown("### Your first step to investing begins here!")
        st.markdown("---")
        st.markdown("Please log in or sign up to access the full dashboard.")

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            create_usertable()
            if login_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Logged in as {username}")
                main_dashboard()
            else:
                st.warning("Incorrect Username or Password")
    elif choice == "Signup":
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')
        if st.button("Signup"):
            if new_password == confirm_password:
                create_usertable()
                add_userdata(new_user, new_password)
                st.success("Account created successfully")
                st.info("Go to Login to access the dashboard")
            else:
                st.error("Passwords do not match")

# Logout function
def logout():
    st.session_state.clear()
    st.rerun()

# Main app logic
if __name__ == "__main__":
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login_page()
    else:
        main_dashboard()
