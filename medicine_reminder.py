from datetime import datetime
import time

# ---------------------------------------------------
# Storage: list of dicts -> {"medicine": "Aspirin", "time": "08:00"}
# Times are 24-hour "HH:MM" format
# ---------------------------------------------------
reminders = []


def add_medicine(medicine, time_str):
    """Add a medicine and its reminder time (24h format HH:MM)."""
    try:
        datetime.strptime(time_str, "%H:%M")  # validate format
    except ValueError:
        raise ValueError("Time must be in 24-hour HH:MM format, e.g. '08:30' or '21:00'")

    reminders.append({"medicine": medicine, "time": time_str})


def remove_medicine(medicine, time_str=None):
    """Remove a medicine. If time_str is given, only remove that specific time."""
    global reminders
    reminders = [
        r for r in reminders
        if not (r["medicine"] == medicine and (time_str is None or r["time"] == time_str))
    ]


def get_all_reminders():
    """Return all reminders (handy for the frontend to display)."""
    return reminders


def send_message(medicine):
    """
    Called when it's time to take a medicine.
    Right now it just prints; your friend can replace this with
    a push notification, websocket message, email, SMS, etc.
    """
    message = f"It's time to take your medicine: {medicine}"
    print(message)
    return message


def check_reminders(now=None, notify=send_message):
    """Check if any reminder matches the current time (HH:MM). Returns list of messages sent."""
    now = now or datetime.now()
    current_time = now.strftime("%H:%M")

    sent = []
    for r in reminders:
        if r["time"] == current_time:
            sent.append(notify(r["medicine"]))
    return sent


def run_reminder_loop(notify=send_message, check_interval=1):
    """Keeps running and checks the time. Makes sure each reminder only fires once per minute."""
    already_sent = set()  # (medicine, time, date)

    print("Medication reminder running... (Ctrl+C to stop)")
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        for r in reminders:
            key = (r["medicine"], r["time"], today)
            if r["time"] == current_time and key not in already_sent:
                notify(r["medicine"])
                already_sent.add(key)

        time.sleep(check_interval)


# ---------------------------------------------------
# Example usage
# ---------------------------------------------------
if __name__ == "__main__":
    add_medicine("Aspirin", "08:00")
    add_medicine("Vitamin D", "13:30")
    add_medicine("Ibuprofen", "21:00")

    # Test: add one for the next minute
    # add_medicine("Test Med", datetime.now().strftime("%H:%M"))

    try:
        run_reminder_loop()
    except KeyboardInterrupt:
        print("\nStopped.")