from datetime import datetime

reminders = []       # [{"medicine": "Aspirin", "time": "08:30"}, ...]
notifications = []   # list of alert message strings
_fired = set()       # (medicine, time, date) already triggered


def add_medicine(name: str, time_str: str) -> None:
    reminders.append({"medicine": name, "time": time_str})


def remove_medicine(name: str, time_str: str) -> None:
    reminders[:] = [
        r for r in reminders
        if not (r["medicine"] == name and r["time"] == time_str)
    ]


def check_reminders() -> None:
    """Called every 10s. Adds a notification when a medicine is due."""
    now = datetime.now()
    current = now.strftime("%H:%M")
    today = now.date()

    for r in reminders:
        key = (r["medicine"], r["time"], today)

        if r["time"] == current and key not in _fired:
            _fired.add(key)
            notifications.append(
                f"Time to take {r['medicine']} ({r['time']})"
            )