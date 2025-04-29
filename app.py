# --- Imports ---
import streamlit as st
import joblib
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="AI Fogger Control", page_icon="🌡", layout="wide")

# --- Load Model ---
@st.cache_resource
def load_model():
    return joblib.load('fogger_dt_model.pkl')

model = load_model()

# --- URLs ---
ESP32_IP = "http://192.168.43.196"
FIREBASE_URL = "https://aipoultryctrl-default-rtdb.asia-southeast1.firebasedatabase.app/sensor_data.json"

# --- Title ---
st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>🌡 AI-Powered Fogger Control for Poultry</h1>
""", unsafe_allow_html=True)

# --- Sensor Data ---
try:
    sensor_data = requests.get(f"{ESP32_IP}/sensor", timeout=2).json()
    current_temperature = sensor_data['temperature']
    current_humidity = sensor_data['humidity']
except:
    st.warning("⚠ Could not connect to ESP32. Using fallback values.")
    current_temperature = 30.0
    current_humidity = 60.0

# --- AI Prediction ---
input_features = [[current_temperature, current_humidity]]
fogger_ai_prediction = model.predict(input_features)[0]

# --- Display Sensor Cards ---
st.markdown("### 🌡 Live Sensor Readings")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Temperature (°C)", value=f"{current_temperature:.1f}", delta="Auto" if st.session_state.get("mode") == "auto" else "")
with col2:
    st.metric(label="Humidity (%)", value=f"{current_humidity:.1f}", delta="Auto" if st.session_state.get("mode") == "auto" else "")

st.markdown("---")

# --- Control Mode Buttons ---
st.markdown("### ⚙️ Fogger Control Panel")

if 'mode' not in st.session_state:
    st.session_state.mode = 'auto'

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Auto (AI Mode)", use_container_width=True):
        st.session_state.mode = 'auto'
with col2:
    if st.button("✅ Force Fogger ON", use_container_width=True):
        st.session_state.mode = 'force_on'
with col3:
    if st.button("❌ Force Fogger OFF", use_container_width=True):
        st.session_state.mode = 'force_off'

# --- Determine State ---
if st.session_state.mode == 'auto':
    fogger_state = fogger_ai_prediction
elif st.session_state.mode == 'force_on':
    fogger_state = 1
else:
    fogger_state = 0

# --- Send Command to ESP32 ---
try:
    control_response = requests.get(f"{ESP32_IP}/control?fogger={fogger_state}", timeout=2)
    if control_response.status_code == 200:
        st.success(f"✅ Command Sent | Mode: {st.session_state.mode.upper()}")
except:
    st.warning("⚠ ESP32 not reachable for control command.")

# --- Display Fogger Status ---
status_container = st.container()
if fogger_state == 1:
    status_container.success(f"🚿 Fogger is ON ({st.session_state.mode.capitalize()} Mode)")
else:
    status_container.error(f"🌡 Fogger is OFF ({st.session_state.mode.capitalize()} Mode)")

st.markdown("---")

# --- Firebase Data ---
st.markdown("### 📈 Temperature & Humidity History")

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
except:
    st.error("❌ Could not load Firebase data.")
    df = pd.DataFrame()

# --- Graphs and Trends with Interactivity ---
st.sidebar.markdown("### Select Metrics")
metrics = st.sidebar.multiselect('Choose Metrics to Display', ['Temperature', 'Humidity'])
if 'Temperature' in metrics:
    fig_temperature = px.line(df, x='timestamp', y='temperature',
                              labels={'timestamp': 'Time', 'temperature': 'Temperature (°C)'},
                              title="📊 Temperature Trends", markers=True)
    st.plotly_chart(fig_temperature, use_container_width=True)

if 'Humidity' in metrics:
    fig_humidity = px.line(df, x='timestamp', y='humidity',
                           labels={'timestamp': 'Time', 'humidity': 'Humidity (%)'},
                           title="📊 Humidity Trends", markers=True)
    st.plotly_chart(fig_humidity, use_container_width=True)

st.markdown("---")

# --- Real-Time Temperature/Humidity Forecast ---
st.markdown("### ⏳ Temperature & Humidity Forecast (Next 3 Hours)")

# Example forecast (replace with actual forecast logic)
forecast_time = [datetime.now() + timedelta(hours=i) for i in range(1, 4)]
forecast_temperature = [current_temperature + 0.5 * i for i in range(1, 4)]
forecast_humidity = [current_humidity - 1.0 * i for i in range(1, 4)]

forecast_df = pd.DataFrame({
    'timestamp': forecast_time,
    'temperature': forecast_temperature,
    'humidity': forecast_humidity
})

fig_forecast = px.line(forecast_df, x='timestamp', y=['temperature', 'humidity'],
                       labels={'timestamp': 'Time', 'value': 'Forecasted Value'},
                       title="🔮 Temperature & Humidity Forecast")
st.plotly_chart(fig_forecast, use_container_width=True)

st.markdown("---")

# --- Data Export/Download Option ---
st.markdown("### 📥 Download Data")
st.download_button(
    label="Download Sensor Data",
    data=df.to_csv().encode('utf-8'),
    file_name='sensor_data.csv',
    mime='text/csv'
)

st.markdown("---")

# --- Actionable Alerts for Users ---
if current_temperature > 35:
    st.warning("⚠ High Temperature detected! Switching to manual mode.")
    st.session_state.mode = 'force_on'

if current_humidity > 70:
    st.warning("⚠ High Humidity detected! Switching to manual mode.")
    st.session_state.mode = 'force_on'
