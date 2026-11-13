from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

DISTANCE_THRESHOLD = 200
REMINDER_BEFORE = timedelta(minutes=60)
GRACE_AFTER = timedelta(minutes=30)

HOSPITALS = {
    "Victoria Hospital": (-20.279224, 57.477006),
    "City Hospital": (-20.260000, 57480000),
    "Central Clinic": None,
}

appointments = []
notifications = [] # The server reads this to play sound and show alerts
_next_id = 1

def add_appointment(doctor, hospital, date_str, time_str):
    global _next_id
    appt = {
        "id": _next_id, "doctor": doctor, "hospital": hospital,
        "date": date_str, "time": time_str, "notified": False,
    }
    appointments.append(appt)
    _next_id += 1
    return appt["id"]

def calculate_distance(loc1, loc2):
    lat1, lon1 = map(radians, loc1)
    lat2, lon2 = map(radians, loc2)
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 6371000 * 2 * atan2(sqrt(a), sqrt(1-a))

def check_appointments(user_location, now=None):
    if user_location is None: 
        return
    now = now or datetime.now()

    for appt in appointments:
        if appt["notified"]: 
            continue
            
        appt_dt = datetime.strptime(f"{appt['date']} {appt['time']}", "%Y-%m-%d %H:%M")
        
        # Check if we are in the 1 hour before or 30 mins after window
        if not (appt_dt - REMINDER_BEFORE <= now <= appt_dt + GRACE_AFTER): 
            continue

        hospital_location = HOSPITALS.get(appt["hospital"])
        if hospital_location is None: 
            continue

        distance = calculate_distance(user_location, hospital_location)

        # If user is further than 200m away, trigger the reminder
        if distance > DISTANCE_THRESHOLD:
            appt["notified"] = True
            msg = f"🏥 APPOINTMENT: {appt['doctor']} at {appt['hospital']} ({appt['time']}). You are {round(distance)}m away!"
            notifications.append(msg)