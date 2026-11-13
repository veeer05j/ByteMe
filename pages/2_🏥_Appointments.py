import streamlit as st
import httpx
from datetime import datetime, timedelta
import appointment_reminder

st.set_page_config(page_title="Appointments", page_icon="🏥")
st.title("🏥 Hospital Appointments")

API_URL = "http://127.0.0.1:8000"

# --- 1. Add an Appointment ---
st.subheader("Add an Appointment")
st.write("*(Tip: To test the real GPS alert, set the time to 30 minutes from now, and make sure you clicked 'Sync Location' on the Home page).*")

with st.form("add_appt_form", clear_on_submit=True):
    doctor = st.text_input("Doctor Name (e.g. Dr. Smith)")
    hospital = st.selectbox("Hospital", list(appointment_reminder.HOSPITALS.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        appt_date = st.date_input("Date")
    with col2:
        # Default to 30 minutes from now for easy testing
        test_time = (datetime.now() + timedelta(minutes=30)).time()
        appt_time = st.time_input("Time", value=test_time)
        
    if st.form_submit_button("Add Appointment"):
        if doctor and hospital:
            date_str = appt_date.strftime("%Y-%m-%d")
            time_str = appt_time.strftime("%H:%M")
            appointment_reminder.add_appointment(doctor, hospital, date_str, time_str)
            st.success(f"Appointment with {doctor} added!")
        else:
            st.error("Please fill in all fields.")

st.divider()

# --- 2. Display Table ---
st.subheader("Your Appointments")
if not appointment_reminder.appointments:
    st.info("No appointments scheduled.")
else:
    for appt in appointment_reminder.appointments:
        col1, col2, col3 = st.columns([3, 3, 1])
        col1.write(f"**{appt['doctor']}**\n\n{appt['date']} at {appt['time']}")
        col2.write(f"📍 {appt['hospital']}")
        
        if col3.button("❌ Delete", key=f"del_appt_{appt['id']}"):
            appointment_reminder.remove_appointment(appt['id'])
            st.rerun() 

st.divider()

# --- 3. Testing & Alerts ---
st.subheader("🔔 Test the Sound")
if st.button("🚨 Force Test Alert"):
    # We append directly to the module's notification list
    appointment_reminder.force_test_alert()
    st.toast("Alert sent! Waiting for server to play sound...", icon="🔊")

# --- 4. The Auto-Refreshing Alert Catcher ---
# This continuously pings the FastAPI server for new alerts
@st.fragment(run_every=5) # Check every 5 seconds
def check_alerts():
    try:
        res = httpx.get(f"{API_URL}/api/alerts")
        alerts = res.json()
        if alerts:
            for alert in alerts:
                st.toast(f"🚨 {alert}", icon="🏥")
                st.warning(alert)
    except Exception:
        pass

check_alerts()