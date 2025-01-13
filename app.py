import sqlite3
import streamlit as st
import page1 as p1  # Ensure this file exists and has the 'page1' function
import page2 as p2  # Ensure this file exists and has the 'page2' function
import page3 as p3  # Ensure this file exists and has the 'page3' function

# Connect to the existing klse_tickers.db
conn = sqlite3.connect('klse_tickers.db')
c = conn.cursor()

# Create user table if not exists (within the existing database)
def create_usertable():
    c.execute('''
    CREATE TABLE IF NOT EXISTS userstable(
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    conn.commit()

# Add user to the user table
def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, password))
    conn.commit()

# Login user validation
def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data

# View all users (for profile page)
def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

# Main dashboard function (after login)
def main_dashboard():
    st.title("Stock Dashboard")

    # Pages dictionary for navigation
    PAGES = {
        "Overview": p1.page1,  # Assuming the 'page1' function exists in page1.py
        "Sector Prediction": p2.page2,  # Assuming the 'page2' function exists in page2.py
        "Company Prediction": p3.page3,  # Assuming the 'page3' function exists in page3.py
    }

    # Initialize session state for navigation if not already initialized
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Overview"

    # Sidebar
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        # Replace "Navigation" with "Welcome, username"
        st.sidebar.title(f"Welcome, {st.session_state['username']}")
    else:
        st.sidebar.title("Navigation")
    
    # Sidebar navigation with big buttons
    for page_name in PAGES.keys():
        if st.sidebar.button(page_name, key=page_name):  # Ensure a unique key for each button
            st.session_state["current_page"] = page_name

    # Add GIF below the big buttons
    st.sidebar.markdown('<img src="https://i.gifer.com/7D7o.gif" width="250">', unsafe_allow_html=True)

    # Logout button with custom styling (smaller size)
    st.sidebar.markdown("""
        <style>
        .logout-btn {
            border: 1px solid red;
            color: red;
            padding: 5px;
            font-size: 12px;
            text-align: center;
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True)

    if st.sidebar.button("Logout", key="logout_button", help="Click to log out", on_click=logout):
        # Perform logout when clicked
        st.session_state["logged_in"] = False
        st.experimental_rerun()  # Rerun the app to redirect to login page

    # Add copyright symbol with logo at the bottom
    st.sidebar.markdown("""
        <p style="font-size: 13px; text-align: left;">&copy; Group 7 
        """, unsafe_allow_html=True)

    # Display the current page
    current_page = st.session_state["current_page"]
    PAGES[current_page]()

# Login page logic with big buttons
def login_page():
    # Sidebar for navigation, will always be visible
    menu = ["Home", "Login", "Signup"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        # Display the text and GIF
        st.markdown("### Welcome to the Stock Dashboard!")
        st.markdown("Use the sidebar to navigate between pages.")
    
        # Adding the GIF here
        st.markdown('<img src="https://i.gifer.com/ZJtH.gif" width="300">', unsafe_allow_html=True)

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login", key="login_button"):
            create_usertable()  # Ensure the user table exists
            result = login_user(username, password)
            if result:
                st.session_state["logged_in"] = True  # Set logged_in flag in session state
                st.session_state["username"] = username  # Store the username
                st.success(f"Logged In as {username}")
                main_dashboard()  # After successful login, show dashboard
            else:
                st.warning("Incorrect Username or Password")
    elif choice == "Signup":
        st.subheader("Signup")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')

        if st.button("Signup", key="signup_button"):
            if new_password == confirm_password:
                create_usertable()  # Ensure the user table exists
                add_userdata(new_user, new_password)
                st.success("Account Created Successfully")
                st.info("Go to Login to Access the Dashboard")

# Logout function to clear session and redirect
def logout():
    st.session_state.clear()  # Clear the session state
    st.session_state["logged_in"] = False  # Ensure logged_in is set to False
    st.experimental_rerun()  # Rerun the app to show the login page

# Main app logic
if __name__ == "__main__":
    # Check if the user is logged in
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login_page()  # Show login page if not logged in
    else:
        main_dashboard()  # Show the main dashboard if logged in
