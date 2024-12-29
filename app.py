import streamlit as st

# Title
st.title('Stock Dashboard')

# Display some text
st.write('Here is the data visualization you requested!')

# Add a button to see if it's responding
if st.button('Click Me'):
    st.write('Button clicked!')

# Example of a simple chart
st.line_chart([1, 2, 3, 4, 5])
