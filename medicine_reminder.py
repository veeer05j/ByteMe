from datetime import datetime

reminders = []
notifications = []
_fired = set()


# ---------------------------------------------------------
# Add a medicine
# ---------------------------------------------------------
def add_medicine(name: str, time_str: str, repeat_daily: bool = False) -> None:

    reminders.append({
        "medicine": name,
        "time": time_str,
        "repeat_daily": repeat_daily
    })

    # Allow the same one-time medicine to be added again
    _fired.discard(("once", name, time_str))


# ---------------------------------------------------------
# Remove a medicine
# ---------------------------------------------------------
def remove_medicine(name: str, time_str: str) -> None:

    reminders[:] = [
        r for r in reminders
        if not (r["medicine"] == name and r["time"] == time_str)
    ]


# ---------------------------------------------------------
# Check medicine reminders
# ---------------------------------------------------------
def check_reminders() -> None:
    """Checks every 10 seconds for medicines that are due."""

    now = datetime.now()
    current = now.strftime("%H:%M")
    today = now.date()

    for r in reminders[:]:

        if r["time"] != current:
            continue

        name = r["medicine"]
        time_str = r["time"]

        if r["repeat_daily"]:

            # Daily medicine: trigger once per day
            key = ("daily", name, time_str, today)

        else:

            # One-time medicine: trigger only once
            key = ("once", name, time_str)

        if key not in _fired:

            _fired.add(key)

            notifications.append(
                f"Time to take {name} ({time_str})"
            )

            # Remove one-time medicine after triggering
            if not r["repeat_daily"]:
                reminders.remove(r)