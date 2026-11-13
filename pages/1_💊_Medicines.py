import streamlit as st
import httpx
import medicine_reminder
import time

st.set_page_config(page_title="Medicines", page_icon="💊")
st.title("💊 Medicine Reminders")

API_URL = "http://127.0.0.1:8000"

# --- 1. Add a new medicine ---
st.subheader("Add a Medicine")
with st.form("add_med_form", clear_on_submit=True):
    med_name = st.text_input("Medicine Name (e.g. Aspirin)")
    med_time = st.time_input("Time to take")
    
    if st.form_submit_button("Add Medicine"):
        if med_name:
            # Format time as HH:MM
            time_str = med_time.strftime("%H:%M")
            medicine_reminder.add_medicine(med_name, time_str)
            st.success(f"Added {med_name} at {time_str}")
        else:
            st.error("Please enter a medicine name.")

st.divider()

# --- 2. Display the Table of Medicines ---
st.subheader("Your Medicine Schedule")

if not medicine_reminder.reminders:
    st.info("No medicines added yet.")
else:
    # We create a visual table with a Remove button next to each row
    for i, med in enumerate(medicine_reminder.reminders):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        col1.write(f"**{med['medicine']}**")
        col2.write(f"⏰ {med['time']}")
        
        # Remove button
        if col3.button("❌ Remove", key=f"del_{i}"):
            medicine_reminder.remove_medicine(med['medicine'], med['time'])
            st.rerun() # Refresh the page to show the updated table

st.divider()

# --- 3. Popup / Alert Logic ---
st.subheader("Active Alerts")
st.write("The app checks the backend every 10 seconds.")

# We use a Streamlit fragment to auto-refresh the alerts without reloading the whole page
@st.fragment(run_every=10)
def check_alerts():
    try:
        res = httpx.get(f"{API_URL}/api/alerts")
        alerts = res.json()
        
        if alerts:
            for alert in alerts:
                # If it's a medicine alert, show a popup and toast
                if "MEDICINE" in alert:
                    st.toast(f"🚨 {alert}", icon="💊")
                    st.warning(alert)
    except Exception:
        pass # Ignore if server is still booting

check_alerts()
