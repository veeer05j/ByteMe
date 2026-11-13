import sys
from pathlib import Path

# Add the ByteMe project root to Python's search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the health tracker
from app.health_tracker import render_health_tracker

# Display the health tracker
render_health_tracker()