# app.py
import streamlit as st
import pandas as pd
import requests
import datetime
import pytz
import time

# Title
st.title("📈 Poultry Farm Dashboard")

# Real-time Clock
current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
st.subheader(f"🕰 Current Time: {current_time}")

# Read Data from Google Sheets
SHEETDB_URL = "https://sheetdb.io/api/v1/fdqe7xmup9c8d"

try:
    response = requests.get(SHEETDB_URL)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert Timestamp
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')  # because millis()/1000 sent

    # Sorting
    df = df.sort_values('Timestamp')

    # Display Table
    st.dataframe(df.tail(10))

    # Plot Temperature
    st.subheader("🌡 Temperature over Time")
    st.line_chart(df.set_index('Timestamp')['Temperature'])

    # Plot Humidity
    st.subheader("💧 Humidity over Time")
    st.line_chart(df.set_index('Timestamp')['Humidity'])

except Exception as e:
    st.error(f"Error fetching data: {e}")

# Auto Refresh every 10 seconds
time.sleep(10)
st.experimental_rerun()
