import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="AI Fogger Control", page_icon="🌡️", layout="centered")

# --- Load AI Model (cached) ---
@st.cache_resource
def load_model():
    return joblib.load('fogger_dt_model.pkl')

model = load_model()

# --- Simulate Sensor Data ---
hours = np.arange(0, 24, 1)
temperature = 25 + 5 * np.sin(np.pi * hours / 12)
humidity = 50 + 10 * np.cos(np.pi * hours / 12)

current_temperature = temperature[-1]
current_humidity = humidity[-1]

# --- AI Prediction ---
input_features = [[current_temperature, current_humidity]]
fogger_ai_prediction = model.predict(input_features)[0]  # 1 or 0

# --- Streamlit UI ---

st.markdown("<h1 style='text-align: center;'>Temperature and Humidity Monitoring</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Temperature", value=f"{current_temperature:.1f}°C")
with col2:
    st.metric(label="Humidity", value=f"{current_humidity:.1f}%")

st.markdown("---")
st.subheader("Fogging Status")

# --- Initialize Session State ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'auto'  # Default is Auto (AI)

# --- Control Buttons ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Auto (AI)"):
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

# --- Display Fogger Status ---
if fogger_state == 1:
    st.success(f"🚿 Fogger is ON ({st.session_state.mode.capitalize()})")
else:
    st.error(f"🌡️ Fogger is OFF ({st.session_state.mode.capitalize()})")

# --- Plot Temperature and Humidity ---
df = pd.DataFrame({
    'Hour': hours,
    'Temperature (°C)': temperature,
    'Humidity (%)': humidity
})

fig = px.line(
    df, 
    x='Hour', 
    y=['Temperature (°C)', 'Humidity (%)'],
    title='Temperature and Humidity Over Time',
    markers=True
)

fig.update_layout(
    xaxis_title="Hour of the Day",
    yaxis_title="Reading",
    legend_title="Metrics",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- Show Current Time ---
current_time = datetime.now().strftime("%H:%M:%S")
st.caption(f"Current Time: {current_time}")
