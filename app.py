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
    return joblib.load('fogger_dt_model.pkl')  # Ensure you have the model file 'fogger_dt_model.pkl'

model = load_model()

# --- ESP32 and Firebase URLs ---
ESP32_IP = "http://192.168.43.196"  # <-- Your ESP32 IP (ensure this is correct!)
FIREBASE_URL = "https://aipoultryctrl-default-rtdb.asia-southeast1.firebasedatabase.app/sensor_data.json"  # <-- Your Firebase URL

# --- Fetch Real-Time Sensor Data ---
def fetch_sensor_data():
    try:
        sensor_data = requests.get(f"{ESP32_IP}/sensor", timeout=10).json()  # Increased timeout
        current_temperature = sensor_data['temperature']
        current_humidity = sensor_data['humidity']
        return current_temperature, current_humidity
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠ Could not connect to ESP32: {e}")
        return 30.0, 60.0  # Fallback values

current_temperature, current_humidity = fetch_sensor_data()

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
def send_fogger_command(fogger_state):
    try:
        control_response = requests.get(f"{ESP32_IP}/control?fogger={fogger_state}", timeout=10)  # Increased timeout
        if control_response.status_code == 200:
            st.success(f"✅ Fogger command sent! Mode: {st.session_state.mode.upper()}")
        else:
            st.warning(f"⚠ Failed to send control command: {control_response.status_code}")
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠ Failed to send control command to ESP32: {e}")

send_fogger_command(fogger_state)

# --- Show Fogger Status ---
if fogger_state == 1:
    st.success(f"🚿 Fogger is ON ({st.session_state.mode.capitalize()} Mode)")
else:
    st.error(f"🌡 Fogger is OFF ({st.session_state.mode.capitalize()} Mode)")

st.markdown("---")

# --- Fetch Historical Data from Firebase ---
def fetch_firebase_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/sensor_data.json", timeout=10)  # Increased timeout
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame.from_dict(data, orient='index')
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                df['temperature'] = df['temperature'].astype(float)
                df['humidity'] = df['humidity'].astype(float)

                # Plotting Temperature and Humidity data
                fig = px.line(df, x='timestamp', y=['temperature', 'humidity'],
                              labels={'timestamp': 'Timestamp', 'value': 'Value'},
                              title="Temperature and Humidity Over Time")
                st.plotly_chart(fig)
                return df
            else:
                st.warning("⚠ No data available in Firebase")
                return pd.DataFrame()  # Return empty DataFrame if no data
        else:
            st.warning(f"⚠ Failed to fetch Firebase data: {response.status_code}")
            return pd.DataFrame()  # Return empty DataFrame if request fails
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠ Failed to connect to Firebase: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

df = fetch_firebase_data()

# --- Display Data and Insights ---
if not df.empty:
    st.subheader("Historical Data")
    st.dataframe(df)

    # --- Additional Insights ---
    st.subheader("Temperature and Humidity Statistics")
    st.write(f"Average Temperature: {df['temperature'].mean():.2f}°C")
    st.write(f"Average Humidity: {df['humidity'].mean():.2f}%")
    
    max_temp = df['temperature'].max()
    min_temp = df['temperature'].min()
    max_humidity = df['humidity'].max()
    min_humidity = df['humidity'].min()

    st.write(f"Max Temperature: {max_temp:.2f}°C")
    st.write(f"Min Temperature: {min_temp:.2f}°C")
    st.write(f"Max Humidity: {max_humidity:.2f}%")
    st.write(f"Min Humidity: {min_humidity:.2f}%")

else:
    st.warning("⚠ No historical data to display.")