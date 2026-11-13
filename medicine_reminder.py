from datetime import datetime

reminders = []
notifications = [] 
already_sent = set() 

def add_medicine(medicine, time_str):
    reminders.append({"medicine": medicine, "time": time_str})

def remove_medicine(medicine, time_str):
    """Finds the exact medicine and time and removes it from the list."""
    global reminders
    reminders = [r for r in reminders if not (r["medicine"] == medicine and r["time"] == time_str)]

def check_reminders(now=None):
    now = now or datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    for r in reminders:
        key = (r["medicine"], r["time"], today)
        if r["time"] == current_time and key not in already_sent:
            already_sent.add(key)
            msg = f"💊 MEDICINE: It's time to take {r['medicine']}!"
            notifications.append(msg)