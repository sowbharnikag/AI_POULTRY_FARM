import streamlit as st
import joblib
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import pytz

# --- Configuration ---
st.set_page_config(page_title="AI Fogger Control", page_icon="🌡", layout="centered")
ESP32_IP = "http://192.168.43.196"  # Change this if ESP32 IP changes
FIREBASE_URL = "https://aipoultryctrl-default-rtdb.asia-southeast1.firebasedatabase.app/"  # Your Firebase URL

# --- Load AI Model ---
@st.cache_resource
def load_model():
    return joblib.load("fogger_dt_model.pkl")

model = load_model()

# --- UI Header ---
st.markdown("<h1 style='text-align: center;'>🌡 AI-Powered Poultry Farm Control</h1>", unsafe_allow_html=True)

# --- Fetch Sensor Data ---
try:
    sensor_data = requests.get(f"{ESP32_IP}/sensor", timeout=2).json()
    current_temperature = sensor_data.get('temperature', 30.0)
    current_humidity = sensor_data.get('humidity', 60.0)
except Exception as e:
    st.warning("⚠ Could not connect to ESP32. Using fallback values.")
    current_temperature = 30.0
    current_humidity = 60.0

# --- AI Prediction ---
input_data = [[current_temperature, current_humidity]]
ai_prediction = model.predict(input_data)[0]

# --- Display Metrics ---
col1, col2 = st.columns(2)
col1.metric("Temperature (°C)", f"{current_temperature:.1f}")
col2.metric("Humidity (%)", f"{current_humidity:.1f}")

st.divider()
st.subheader("🧠 Fogger Mode & Manual Control")

# --- Session State ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'auto'

# --- Control Buttons ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Auto (AI Mode)"):
        st.session_state.mode = 'auto'
with col2:
    if st.button("✅ Force ON"):
        st.session_state.mode = 'force_on'
with col3:
    if st.button("❌ Force OFF"):
        st.session_state.mode = 'force_off'

# --- Determine Final Fogger State ---
if st.session_state.mode == 'auto':
    fogger_state = ai_prediction
elif st.session_state.mode == 'force_on':
    fogger_state = 1
elif st.session_state.mode == 'force_off':
    fogger_state = 0

# --- Send Command to ESP32 ---
try:
    control_response = requests.get(f"{ESP32_IP}/control?fogger={fogger_state}", timeout=2)
    if control_response.status_code == 200:
        st.success(f"✅ Fogger Command Sent ({st.session_state.mode.upper()} Mode)")
    else:
        st.error("❌ ESP32 responded with error.")
except Exception as e:
    st.warning("⚠ Failed to send control command to ESP32.")

# --- Display Fogger Status ---
if fogger_state == 1:
    st.success("🚿 Fogger is ON")
else:
    st.error("🌡 Fogger is OFF")

st.divider()
st.subheader("📊 Historical Data from Firebase")

# --- Firebase Historical Data ---
try:
    response = requests.get(FIREBASE_URL)
    data = response.json()

    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
        df['humidity'] = pd.to_numeric(df['humidity'], errors='coerce')
        df = df.dropna().sort_values('timestamp')
    else:
        df = pd.DataFrame()
except Exception as e:
    st.error("❌ Could not fetch data from Firebase.")
    df = pd.DataFrame()

# --- Plotting Historical Data ---
if not df.empty:
    fig = px.line(df, x='timestamp', y=['temperature', 'humidity'],
                  title='Temperature & Humidity Over Time', markers=True)
    fig.update_layout(xaxis_title="Timestamp", yaxis_title="Value", legend_title="Sensor")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No historical data to display yet.")

# --- Timestamp ---
now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%H:%M:%S")
st.caption(f"🕒 Last updated: {now}")