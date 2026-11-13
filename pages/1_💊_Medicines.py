from datetime import datetime

import streamlit as st
import medicine_reminder
from reminder_sound import play_reminder_sound

st.set_page_config(page_title="Medicines", page_icon="💊")
st.title("💊 Medicine Reminders")


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "pending_popups" not in st.session_state:
    st.session_state.pending_popups = []

if "history" not in st.session_state:
    st.session_state.history = []

if "seen_count" not in st.session_state:
    st.session_state.seen_count = len(medicine_reminder.notifications)


# ---------------------------------------------------------
# Medicine reminder popup
# ---------------------------------------------------------
@st.dialog("💊 Medicine Reminder")
def show_popup(messages):

    for m in messages:
        st.markdown(f"### {m}")

    if st.button("✅ OK, I'll take it", use_container_width=True):

        st.rerun()


# ---------------------------------------------------------
# 1. Add a medicine
# ---------------------------------------------------------
st.subheader("Add a Medicine")

with st.form("add_med_form", clear_on_submit=True):

    med_name = st.text_input("Medicine Name (e.g. Aspirin)")
    med_time = st.time_input("Time to take")

    if st.form_submit_button("Add Medicine"):

        if med_name.strip():

            time_str = med_time.strftime("%H:%M")

            medicine_reminder.add_medicine(
                med_name.strip(),
                time_str
            )

            st.success(f"Added {med_name} at {time_str}")

        else:
            st.error("Please enter a medicine name.")


st.divider()


# ---------------------------------------------------------
# 2. Medicine schedule
# ---------------------------------------------------------
st.subheader("Your Medicine Schedule")

if not medicine_reminder.reminders:

    st.info("No medicines added yet.")

else:

    for i, med in enumerate(medicine_reminder.reminders):

        c1, c2, c3 = st.columns([2, 2, 1])

        c1.write(f"**{med['medicine']}**")
        c2.write(f"⏰ {med['time']}")

        if c3.button("❌ Remove", key=f"del_{i}"):

            medicine_reminder.remove_medicine(
                med["medicine"],
                med["time"]
            )

            st.rerun()


st.divider()


# ---------------------------------------------------------
# 3. Reminder checker (every 10 seconds)
# ---------------------------------------------------------
@st.fragment(run_every=10)
def checker():

    medicine_reminder.check_reminders()

    notes = medicine_reminder.notifications

    new = notes[st.session_state.seen_count:]

    st.session_state.seen_count = len(notes)

    if new:

        st.session_state.pending_popups.extend(new)
        st.session_state.history.extend(new)

        st.rerun()

    st.caption(
        f"Last checked: {datetime.now().strftime('%H:%M:%S')}"
    )


st.subheader("Alerts")

checker()


# ---------------------------------------------------------
# Alert history
# ---------------------------------------------------------
if st.session_state.history:

    with st.expander("Alert history"):

        for h in reversed(st.session_state.history):
            st.write(h)


# ---------------------------------------------------------
# 4. Display popup
# ---------------------------------------------------------
if st.session_state.pending_popups:

    msgs = st.session_state.pending_popups

    st.session_state.pending_popups = []
    play_reminder_sound()
    show_popup(msgs)