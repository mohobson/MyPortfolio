import os
from dotenv import load_dotenv
load_dotenv()

appKey = os.getenv('appKey')
appSecret = os.getenv('appSecret')


import streamlit as st
import numpy as np
import pandas as pd

# Sample data pulled from your API
data = {
    "Ticker": ["AAPL", "GOOGL", "MSFT", "AMZN"],
    "Stock Price": [150, 2800, 300, 3400],
    "Percent of Portfolio": [25, 30, 20, 25],
    "Analyst Rating": [4.5, 3.8, 4.2, 4.0],
    "Price Target": [160, 2900, 320, 3500]  # initial target prices
}

# Convert data to a DataFrame
df = pd.DataFrame(data)

st.title("Portfolio Dashboard")

# Display table headers
st.write("### Portfolio Overview")

header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns(5)
header_col1.write("**Ticker**")
header_col2.write("**Stock Price**")
header_col3.write("**% of Portfolio**")
header_col4.write("**Analyst Rating**")
header_col5.write("**Price Target**")

# To store updated price targets, we create an editable form
updated_targets = []
for i, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Display each row with editable price target
    with col1:
        st.write(row["Ticker"])
    with col2:
        st.write(f"${row['Stock Price']}")
    with col3:
        st.write(f"{row['Percent of Portfolio']}%")
    with col4:
        st.write(row["Analyst Rating"])
    with col5:
        # Editable price target input
        price_target = st.number_input(f"Target for {row['Ticker']}", value=row["Price Target"], key=f"target_{i}")
        updated_targets.append(price_target)

# Update the DataFrame with new targets
df["Price Target"] = updated_targets

# Show the updated table
st.write("### Updated Portfolio with Custom Price Targets")
st.dataframe(df)

# Additional analyses or charts could be added here

