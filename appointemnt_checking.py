from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import time

# ---------------- CONFIG ----------------
DISTANCE_THRESHOLD = 200       # metres: farther than this = "not at the hospital"
REMINDER_BEFORE = timedelta(minutes=60)   # start reminding this long before the appointment
GRACE_AFTER = timedelta(minutes=30)       # keep reminding this long after the start time
CHECK_INTERVAL = 10            # seconds between checks

# Hospital GPS coordinates (lat, lon) - one place to maintain them
HOSPITALS = {
    "Victoria Hospital": (-20.279224, 57.477006),
    "City Hospital": None,      # TODO: add real coordinates
    "Central Clinic": None,     # TODO: add real coordinates
}

# Store appointments (hospital location is looked up from HOSPITALS)
appointments = [
    {"id": 1, "doctor": "Dr. Smith", "hospital": "City Hospital",
     "date": "2026-11-16", "time": "10:00", "notified": False},
    {"id": 2, "doctor": "Dr. John", "hospital": "Central Clinic",
     "date": "2026-11-17", "time": "14:30", "notified": False},
    {"id": 3, "doctor": "Dr. Sarah", "hospital": "Victoria Hospital",
     "date": "2026-11-13", "time": "09:00", "notified": False},
]


def calculate_distance(location1, location2):
    """Haversine distance in metres between two (lat, lon) tuples."""
    lat1, lon1 = map(radians, location1)
    lat2, lon2 = map(radians, location2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    a = min(1.0, max(0.0, a))  # guard against floating point error

    return 6371000 * 2 * atan2(sqrt(a), sqrt(1 - a))


def check_appointments(user_location, now=None):
    """
    Return a list of reminder dicts for appointments that are:
      - inside the reminder window (REMINDER_BEFORE before -> GRACE_AFTER after)
      - not already notified
      - and the user is farther than DISTANCE_THRESHOLD from the hospital
    """
    now = now or datetime.now()
    reminders = []

    for appt in appointments:
        if appt["notified"]:
            continue

        try:
            appt_dt = datetime.strptime(f"{appt['date']} {appt['time']}", "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"Skipping appointment {appt['id']}: bad date/time format")
            continue

        # Only inside the window (not forever after the appointment)
        if not (appt_dt - REMINDER_BEFORE <= now <= appt_dt + GRACE_AFTER):
            continue

        hospital_location = HOSPITALS.get(appt["hospital"])
        if hospital_location is None:
            print(f"Skipping appointment {appt['id']}: no GPS coordinates for {appt['hospital']}")
            continue

        distance = calculate_distance(user_location, hospital_location)

        if distance > DISTANCE_THRESHOLD:
            appt["notified"] = True
            reminders.append({
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
            })

    return reminders


def get_user_location():
    """Placeholder: the front end will send the real GPS location."""
    return (-20.300000, 57.490000)


if __name__ == "__main__":
    # Only runs when you execute this file directly, NOT when the front end imports it
    try:
        while True:
            for r in check_appointments(get_user_location()):
                print("\nAPPOINTMENT REMINDER")
                print(r["message"])
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")