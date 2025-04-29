# --- Imports ---
import streamlit as st
import joblib
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import pytz

# --- Streamlit Config ---
st.set_page_config(page_title="AI Fogger Control", page_icon="🌡", layout="centered")

# --- Load AI Model ---
@st.cache_resource
def load_model():
    return joblib.load('fogger_dt_model.pkl')

model = load_model()

# --- ESP32 and Firebase URLs ---
ESP32_IP = "http://192.168.43.196"  # <-- Your ESP32 IP
FIREBASE_URL = "https://aipoultryctrl-default-rtdb.asia-southeast1.firebasedatabase.app/"  # <-- Your Firebase Realtime Database URL

# --- Fetch Real-Time Sensor Data ---
try:
    sensor_data = requests.get(f"{ESP32_IP}/sensor", timeout=2).json()
    current_temperature = sensor_data['temperature']
    current_humidity = sensor_data['humidity']
except:
    st.warning("⚠ Could not connect to ESP32. Using fallback values.")
    current_temperature = 30.0
    current_humidity = 60.0

# --- AI Prediction ---
input_features = [[current_temperature, current_humidity]]  # Only Temp and Humidity
fogger_ai_prediction = model.predict(input_features)[0]

# --- Streamlit UI ---
st.markdown("<h1 style='text-align: center;'>🌡 Poultry Farm Temperature Control (AI Powered)</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Current Temperature (°C)", value=f"{current_temperature:.1f}")
with col2:
    st.metric(label="Current Humidity (%)", value=f"{current_humidity:.1f}")

st.markdown("---")
st.subheader("Fogging System Status and Manual Control")

# --- Initialize Session State ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'auto'

# --- Control Buttons ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Auto (AI Mode)"):
        st.session_state.mode = 'auto'
with col2:
    if st.button("✅ Force Fogger ON"):
        st.session_state.mode = 'force_on'
with col3:
    if st.button("❌ Force Fogger OFF"):
        st.session_state.mode = 'force_off'

# --- Determine Fogger State ---
if st.session_state.mode == 'auto':
    fogger_state = fogger_ai_prediction
elif st.session_state.mode == 'force_on':
    fogger_state = 1
elif st.session_state.mode == 'force_off':
    fogger_state = 0

# --- Send Control Command to ESP32 ---
try:
    control_response = requests.get(f"{ESP32_IP}/control?fogger={fogger_state}", timeout=2)
    if control_response.status_code == 200:
        st.success(f"✅ Fogger command sent! Mode: {st.session_state.mode.upper()}")
except:
    st.warning("⚠ Failed to send control command to ESP32.")

# --- Show Fogger Status ---
if fogger_state == 1:
    st.success(f"🚿 Fogger is ON ({st.session_state.mode.capitalize()} Mode)")
else:
    st.error(f"🌡 Fogger is OFF ({st.session_state.mode.capitalize()} Mode)")

st.markdown("---")

# --- Fetch Historical Data from Firebase ---
try:
    response = requests.get(FIREBASE_URL)
    data = response.json()

    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
        df['humidity'] = pd.to_numeric(df['humidity'], errors='coerce')
        df = df.dropna()
        df = df.sort_values('timestamp')
    else:
        df = pd.DataFrame()
except:
    st.error("❌ Could not load data from Firebase.")
    df = pd.DataFrame()

# --- Plot Historical Data ---
if not df.empty:
    fig = px.line(
        df,
        x='timestamp',
        y=['temperature', 'humidity'],
        title='Live Temperature and Humidity History',
        markers=True
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Values",
        legend_title="Metrics",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Show Current Time ---
current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%H:%M:%S")
st.caption(f"🕒 Current System Time: {current_time}")