from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import time

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
DISTANCE_THRESHOLD = 200                  # metres: farther than this = "not at the hospital"
REMINDER_BEFORE = timedelta(minutes=60)   # start reminding this long before the appointment
GRACE_AFTER = timedelta(minutes=30)       # keep checking this long after the start time
CHECK_INTERVAL = 10                       # seconds between checks

# Hospital GPS coordinates (lat, lon) - one place to maintain them
HOSPITALS = {
    "Victoria Hospital": (-20.279224, 57.477006),
    "City Hospital": None,      # TODO: add real coordinates
    "Central Clinic": None,     # TODO: add real coordinates
}

# ---------------------------------------------------
# Storage: list of dicts ->
# {"id": 1, "doctor": "Dr. Smith", "hospital": "City Hospital",
#  "date": "2026-11-16", "time": "10:00", "notified": False}
# Date is "YYYY-MM-DD", time is 24-hour "HH:MM"
# ---------------------------------------------------
appointments = []
_next_id = 1
_warned_hospitals = set()  # so the "no GPS" warning prints once, not every 10 seconds


def add_hospital(name, lat, lon):
    """Add a hospital or update its GPS coordinates."""
    HOSPITALS[name] = (lat, lon)
    _warned_hospitals.discard(name)


def add_appointment(doctor, hospital, date_str, time_str):
    """Add an appointment. Returns the new appointment id."""
    global _next_id

    try:
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("Date must be 'YYYY-MM-DD' and time must be 24-hour 'HH:MM'")

    if hospital not in HOSPITALS:
        raise ValueError(f"Unknown hospital '{hospital}'. Add it with add_hospital() first.")

    appt = {
        "id": _next_id,
        "doctor": doctor,
        "hospital": hospital,
        "date": date_str,
        "time": time_str,
        "notified": False,
    }
    appointments.append(appt)
    _next_id += 1
    return appt["id"]


def remove_appointment(appointment_id):
    """Remove an appointment by its id."""
    global appointments
    appointments = [a for a in appointments if a["id"] != appointment_id]


def get_all_appointments():
    """Return all appointments (handy for the frontend to display)."""
    return appointments


def calculate_distance(location1, location2):
    """Haversine distance in metres between two (lat, lon) tuples."""
    lat1, lon1 = map(radians, location1)
    lat2, lon2 = map(radians, location2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    a = min(1.0, max(0.0, a))  # guard against floating point error

    return 6371000 * 2 * atan2(sqrt(a), sqrt(1 - a))


def send_message(reminder):
    """
    Called when the user needs to be reminded about an appointment.
    Right now it just prints; your friend can replace this with
    a push notification, websocket message, email, SMS, etc.
    `reminder` is a dict (see check_appointments) so the frontend gets all the details.
    """
    print("\nAPPOINTMENT REMINDER")
    print(reminder["message"])
    return reminder["message"]


def check_appointments(user_location, now=None, notify=send_message):
    """
    Check all appointments. A reminder is sent when the appointment is:
      - inside the reminder window (REMINDER_BEFORE before -> GRACE_AFTER after)
      - not already notified
      - and the user is farther than DISTANCE_THRESHOLD from the hospital
    Returns a list of reminder dicts that were sent.
    """
    if user_location is None:
        return []  # no GPS from the frontend yet

    now = now or datetime.now()
    sent = []

    for appt in appointments:
        if appt["notified"]:
            continue

        appt_dt = datetime.strptime(f"{appt['date']} {appt['time']}", "%Y-%m-%d %H:%M")

        # Only inside the window (not forever after the appointment)
        if not (appt_dt - REMINDER_BEFORE <= now <= appt_dt + GRACE_AFTER):
            continue

        hospital_location = HOSPITALS.get(appt["hospital"])
        if hospital_location is None:
            if appt["hospital"] not in _warned_hospitals:
                print(f"Skipping appointment {appt['id']}: no GPS coordinates for {appt['hospital']}")
                _warned_hospitals.add(appt["hospital"])
            continue

        distance = calculate_distance(user_location, hospital_location)

        if distance > DISTANCE_THRESHOLD:
            appt["notified"] = True
            reminder = {
                "appointment_id": appt["id"],
                "doctor": appt["doctor"],
                "hospital": appt["hospital"],
                "time": appt["time"],
                "distance_metres": round(distance),
                "message": (
                    f"You have an appointment with {appt['doctor']} at "
                    f"{appt['hospital']} at {appt['time']}. "
                    f"You are approximately {round(distance)} metres away!"
                ),
            }
            notify(reminder)
            sent.append(reminder)

    return sent


def get_user_location():
    """Placeholder: the front end will send the real GPS location as (lat, lon)."""
    return (-20.300000, 57.490000)


def run_appointment_loop(get_location=get_user_location, notify=send_message,
                         check_interval=CHECK_INTERVAL):
    """Keeps running and checks appointments. Each appointment only notifies once."""
    print("Appointment reminder running... (Ctrl+C to stop)")
    while True:
        check_appointments(get_location(), notify=notify)
        time.sleep(check_interval)


# ---------------------------------------------------
# Example usage
# ---------------------------------------------------
if __name__ == "__main__":
    # Only runs when you execute this file directly, NOT when the front end imports it
    add_appointment("Dr. Smith", "City Hospital", "2026-11-16", "10:00")
    add_appointment("Dr. John", "Central Clinic", "2026-11-17", "14:30")
    add_appointment("Dr. Sarah", "Victoria Hospital", "2026-11-13", "09:00")

    try:
        run_appointment_loop()
    except KeyboardInterrupt:
        print("\nStopped.")