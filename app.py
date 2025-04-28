# --- Imports ---
import streamlit as st
import joblib
import numpy as np
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# --- Streamlit Page Config ---
st.set_page_config(page_title="AI Fogger Control", page_icon="🌡️", layout="centered")

# --- Load AI Model ---
@st.cache_resource
def load_model():
    return joblib.load('fogger_dt_model.pkl')  # Only your Decision Tree model

model = load_model()

# --- ESP32 IP Address ---
ESP32_IP = "http://192.168.1.10"   # Change this to your ESP32 actual IP Address

# --- Fetch Sensor Data ---
try:
    sensor_data = requests.get(f"{ESP32_IP}/sensor", timeout=2).json()
    current_temperature = sensor_data['temperature']
    current_humidity = sensor_data['humidity']
except Exception as e:
    st.warning("⚠️ Failed to connect to ESP32! Showing simulated data.")
    current_temperature = 30.0 + (datetime.now().second % 5)
    current_humidity = 60.0 + (datetime.now().second % 3)

# --- Current Hour ---
current_hour = datetime.now().hour

# --- AI Prediction ---
input_features = [[current_temperature, current_humidity, current_hour]]
fogger_ai_prediction = model.predict(input_features)[0]  # 1 or 0

# --- Streamlit UI ---
st.markdown("<h1 style='text-align: center;'>🌡️ Temperature and Humidity Monitoring</h1>", unsafe_allow_html=True)

# --- Display Current Temperature and Humidity ---
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Current Temperature (°C)", value=f"{current_temperature:.1f}")
with col2:
    st.metric(label="Current Humidity (%)", value=f"{current_humidity:.1f}")

st.markdown("---")
st.subheader("Fogging System Status and Control")

# --- Session State Initialization ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'auto'  # Default to Auto (AI mode)

# --- Control Buttons ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Auto (AI Control)"):
        st.session_state.mode = 'auto'
with col2:
    if st.button("✅ Force ON"):
        st.session_state.mode = 'force_on'
with col3:
    if st.button("❌ Force OFF"):
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
        st.success(f"✅ Fogger control command sent successfully! Mode: {st.session_state.mode.upper()}")
except Exception as e:
    st.warning("⚠️ Could not send fogger control command to ESP32.")

# --- Display Fogger Status ---
if fogger_state == 1:
    st.success(f"🚿 Fogger is ON ({st.session_state.mode.capitalize()})")
else:
    st.error(f"🌡️ Fogger is OFF ({st.session_state.mode.capitalize()})")

st.markdown("---")

# --- Plot Simulated 24-hour Temperature and Humidity (for better look) ---
hours = np.arange(0, 24, 1)
temp_sim = 25 + 5 * np.sin(np.pi * hours / 12)
hum_sim = 50 + 10 * np.cos(np.pi * hours / 12)

df = pd.DataFrame({
    'Hour': hours,
    'Temperature (°C)': temp_sim,
    'Humidity (%)': hum_sim
})

fig = px.line(
    df,
    x='Hour',
    y=['Temperature (°C)', 'Humidity (%)'],
    title='Simulated Temperature and Humidity Over 24 Hours',
    markers=True
)

fig.update_layout(
    xaxis_title="Hour of the Day",
    yaxis_title="Value",
    legend_title="Metrics",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- Show Current Time ---
current_time = datetime.now().strftime("%H:%M:%S")
st.caption(f"🕒 Current Time: {current_time}")
