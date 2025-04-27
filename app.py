import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime

# Use st.cache_resource to cache the AI model (Decision Tree)
@st.cache_resource
def load_model():
    return joblib.load('fogger_dt_model.pkl')

# Load Trained AI Model (Decision Tree)
model = load_model()

# Streamlit UI
st.title("🌡️ Poultry Farm Temperature Control System (AI Powered)")

# Real-time Sensor Data Simulation (for testing purposes)
st.subheader("Sensor Data")

# Simulate sensor data (use real data if available)
# Simulating hourly data for the past 24 hours
hours = np.arange(0, 24, 1)  # Hours from 0 to 23
temperature = 25 + 5 * np.sin(np.pi * hours / 12)  # Simulated temperature with a sine wave pattern
humidity = 50 + 10 * np.cos(np.pi * hours / 12)  # Simulated humidity with a cosine wave pattern

# Display the current temperature and humidity
current_temperature = temperature[-1]  # Last value in the simulated array
current_humidity = humidity[-1]  # Last value in the simulated array
st.metric(label="Current Temperature (°C)", value=f"{current_temperature:.2f}")
st.metric(label="Current Humidity (%)", value=f"{current_humidity:.2f}")

# AI Prediction based on the latest data
input_features = [[current_temperature, current_humidity]]
fogger_prediction = model.predict(input_features)

if fogger_prediction[0] == 1:
    st.success("✅ AI Decision: Turn ON the Fogger")
else:
    st.error("❌ AI Decision: Fogger Not Needed")

# Create a DataFrame for plotting
df = pd.DataFrame({
    'Hour': hours,
    'Temperature (°C)': temperature,
    'Humidity (%)': humidity
})

# Plot Temperature and Humidity over time
fig = px.line(df, x='Hour', y=['Temperature (°C)', 'Humidity (%)'], title='Temperature and Humidity Over Time')
fig.update_layout(
    xaxis_title="Hour of the Day",
    yaxis_title="Value",
    legend_title="Metrics",
    template="plotly_dark"
)

# Display the graph in the Streamlit app
st.plotly_chart(fig)

# Display the current time in digital format (HH:MM:SS)
current_time = datetime.now().strftime("%H:%M:%S")
st.subheader(f"Current Time: {current_time}")

# Manual Control
st.subheader("Manual Override Control")
manual_fogger = st.radio("Manual Fogger Control", ("Auto (AI)", "Force ON", "Force OFF"))

# Send control command based on manual override or AI decision
if manual_fogger == "Auto (AI)":
    fogger_state = fogger_prediction[0]
elif manual_fogger == "Force ON":
    fogger_state = 1
else:
    fogger_state = 0

# Display the control command
if fogger_state == 1:
    st.info("Control Command: Turn ON the Fogger")
else:
    st.info("Control Command: Turn OFF the Fogger")

# Footer
st.caption("Built with ❤️ using Streamlit and AI")
