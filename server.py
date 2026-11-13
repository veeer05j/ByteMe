import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import appointment_reminder
import medicine_reminder
from reminder_sound import play_sound

# Global variable to hold the user's GPS location
user_location = None

async def background_loop():
    """Runs every 10 seconds to check for appointments and medicines."""
    while True:
        # 1. Run the logic checks
        appointment_reminder.check_appointments(user_location)
        medicine_reminder.check_reminders()
        
        # 2. If either logic module found something, play the sound!
        if appointment_reminder.notifications or medicine_reminder.notifications:
            play_sound()
            
        await asyncio.sleep(10) # Wait 10 seconds before checking again

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background loop when the server starts
    task = asyncio.create_task(background_loop())
    yield
    # Stop the loop when server shuts down
    task.cancel()

server = FastAPI(lifespan=lifespan)

# --- API ENDPOINTS (Streamlit uses these) ---

@server.post("/api/location")
def update_location(lat: float, lng: float):
    global user_location
    user_location = (lat, lng)
    return {"status": "ok"}

@server.get("/api/alerts")
def get_alerts():
    """Streamlit fetches this to show popups on the screen."""
    # Combine alerts from both modules
    all_alerts = appointment_reminder.notifications + medicine_reminder.notifications
    
    # Clear them so we don't show them twice
    appointment_reminder.notifications.clear()
    medicine_reminder.notifications.clear()
    
    return all_alerts