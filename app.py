import streamlit as st
import threading
import uvicorn
import httpx
import time
from datetime import datetime, timedelta
import appointment_reminder
import medicine_reminder
from server import server

# ==========================================
# 1. START THE BACKEND SERVER IN BACKGROUND
# ==========================================
def run_backend():
    # We run the FastAPI server on port 8000
    uvicorn.run(server, host="127.0.0.1", port=8000, log_level="error")

# Only start the thread once (Streamlit re-runs the script on every click)
if "backend_started" not in st.session_state:
    threading.Thread(target=run_backend, daemon=True).start()
    st.session_state["backend_started"] = True
    time.sleep(1) # Give the server a second to boot up

API_URL = "http://127.0.0.1:8000"

# ==========================================
# 2. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Health Companion", page_icon="🩺")
st.title("🩺 Health Companion")

# --- Location Sync ---
if st.button("📍 Sync My Location"):
    # We send a dummy location for testing (Mauritius). 
    # In production, you would grab the real GPS from the browser.
    httpx.post(f"{API_URL}/api/location?lat=-20.3000&lng=57.4900")
    st.success("Location synced! (You are far from the hospitals)")

st.divider()

# --- Add Data (For live demo testing) ---
st.subheader("Add Reminders")
col1, col2 = st.columns(2)

with col1:
    if st.button("➕ Add Test Appointment (In 1 hr)"):
        future_time = datetime.now() + timedelta(minutes=60)
        date_str = future_time.strftime("%Y-%m-%d")
        time_str = future_time.strftime("%H:%M")
        appointment_reminder.add_appointment("Dr. Smith", "Victoria Hospital", date_str, time_str)
        st.success(f"Appointment added for {time_str}!")

with col2:
    if st.button("➕ Add Test Medicine (This minute)"):
        current_time = datetime.now().strftime("%H:%M")
        medicine_reminder.add_medicine("Aspirin", current_time)
        st.success(f"Medicine added for {current_time}!")

st.divider()

# --- Check Alerts ---
st.subheader("Alerts")
st.write("The backend checks every 10 seconds. The sound will play automatically if an alert triggers.")

if st.button("🔔 Check for Alerts"):
    res = httpx.get(f"{API_URL}/api/alerts")
    alerts = res.json()
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.info("No new alerts right now.")