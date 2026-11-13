
import sys
import streamlit as st
from pathlib import Path

# Locate the project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Find health_tracker.py anywhere inside the project
matches = list(PROJECT_ROOT.rglob("health_tracker.py"))

if not matches:

    st.error("health_tracker.py could not be found.")

    st.write("Project directory:", str(PROJECT_ROOT))

    st.write(
        "Files in project directory:",
        [p.name for p in PROJECT_ROOT.iterdir()]
    )

    st.stop()

# Add the directory containing health_tracker.py
MODULE_DIRECTORY = str(matches[0].parent)

if MODULE_DIRECTORY not in sys.path:
    sys.path.insert(0, MODULE_DIRECTORY)

from health_tracker import render_health_tracker

render_health_tracker()
