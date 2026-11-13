import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="DayWeave Clinic Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, PREMIUM DARK MODE look
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #0F172A; /* Deep Slate */
    }

    /* Hide Streamlit Default Menu/Footer/Nav */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;} /* Hides the 'app' menu */

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    
    /* Text Colors */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #F8FAFC !important;
    }
    
    /* Custom Card Styling */
    .custom-card {
        background-color: #1E293B;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    
    .card-title {
        color: #94A3B8 !important;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .card-value {
        color: #F8FAFC !important;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .card-delta {
        font-size: 14px;
        font-weight: 500;
        color: #34D399 !important; /* Emerald Green */
    }

    /* Appointment List Item */
    .appointment-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        border-bottom: 1px solid #334155;
    }
    
    .appointment-item:last-child {
        border-bottom: none;
    }
    
    .apt-time {
        font-weight: 600;
        color: #38BDF8 !important; /* Sky Blue */
        background: rgba(56, 189, 248, 0.1);
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 14px;
        min-width: 70px;
        text-align: center;
    }
    
    .apt-details {
        flex-grow: 1;
        padding-left: 20px;
    }
    
    .apt-clinic {
        font-weight: 600;
        color: #F8FAFC !important;
        font-size: 16px;
    }
    
    .apt-type {
        color: #94A3B8 !important;
        font-size: 13px;
    }
    
    .status-badge {
        background: rgba(52, 211, 153, 0.1);
        color: #34D399 !important;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .status-badge.pending {
        background: rgba(251, 191, 36, 0.1);
        color: #FBBF24 !important;
    }

    /* Streamlit Button Override */
    .stButton>button {
        background-color: #0EA5E9;
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #0284C7;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #38BDF8; font-size: 24px;'>🏥 DayWeave</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 14px; margin-top: -15px;'>Clinic Portal</p>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
    
    # Profile
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background: #334155; display: flex; align-items: center; justify-content: center; font-size: 20px;">👩‍⚕️</div>
        <div>
            <div style="font-weight: 600; color: #F8FAFC;">Dr. Smith</div>
            <div style="font-size: 12px; color: #94A3B8;">General Practitioner</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-weight: 600; color: #F8FAFC; font-size: 14px;'>Navigation</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #38BDF8; font-size: 14px; font-weight: 600;'>📊 Dashboard</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 14px;'>📅 Appointments</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 14px;'>👥 Patients</p>", unsafe_allow_html=True)


# --- MAIN CONTENT ---
st.markdown("<br>", unsafe_allow_html=True)

# Header
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown(f"<h1 style='font-size: 32px; font-weight: 700; color: #F8FAFC; margin-bottom: 0;'>Good morning, Dr. Smith 👋</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8; margin-top: 4px;'>{datetime.now().strftime('%A, %B %d, %Y')}</p>", unsafe_allow_html=True)
with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("➕ New Appointment", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- METRICS ROW ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="custom-card">
        <div class="card-title">Next Appointment</div>
        <div class="card-value">Victoria Hospital</div>
        <div class="card-delta">🕒 Today at 14:00</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="custom-card">
        <div class="card-title">Routine Progress</div>
        <div class="card-value">75%</div>
        <div class="card-delta">✅ 3 of 4 tasks done</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="custom-card">
        <div class="card-title">Nearby Services</div>
        <div class="card-value">4 Open</div>
        <div class="card-delta">📍 Within 2km radius</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- BOTTOM SECTION ---
left_col, right_col = st.columns([2, 1])

with left_col:
    # THE FIX: Using single block string with NO indentation to prevent Streamlit from rendering it as code
    appointment_html = """<div class="custom-card" style="padding: 0;">
<div style="padding: 20px; border-bottom: 1px solid #334155;">
<h3 style="margin: 0; font-size: 18px; color: #F8FAFC;">Upcoming Appointments</h3>
</div>
<div style="padding: 0 20px;">
<div class="appointment-item">
<div class="apt-time">14:00</div>
<div class="apt-details">
<div class="apt-clinic">Victoria Hospital</div>
<div class="apt-type">General Checkup</div>
</div>
<div class="status-badge">Confirmed</div>
</div>
<div class="appointment-item">
<div class="apt-time">09:30</div>
<div class="apt-details">
<div class="apt-clinic">C-Care Moka</div>
<div class="apt-type">Blood Test</div>
</div>
<div class="status-badge pending">Pending</div>
</div>
<div class="appointment-item">
<div class="apt-time">10:00</div>
<div class="apt-details">
<div class="apt-clinic">Jeetoo Hospital</div>
<div class="apt-type">Cardiology</div>
</div>
<div class="status-badge">Confirmed</div>
</div>
</div>
</div>"""
    st.markdown(appointment_html, unsafe_allow_html=True)

    # Chart Card
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin: 0; font-size: 18px; color: #F8FAFC; margin-bottom: 20px;'>Weekly Wellbeing Progress</h3>", unsafe_allow_html=True)
    
    chart_data = pd.DataFrame(
        {
            "Hydration (Glasses)": [6, 8, 7, 8, 5, 9, 8],
            "Stretching (Mins)": [10, 15, 12, 20, 5, 15, 10]
        },
        index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )
    # Using Streamlit's dark mode compatible area chart
    st.area_chart(chart_data, color=["#38BDF8", "#34D399"])
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    # Routine Checklist Card
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin: 0; font-size: 18px; color: #F8FAFC; margin-bottom: 20px;'>Today's Routine</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #94A3B8; margin-top: -15px;'>Synced from mobile app</p>", unsafe_allow_html=True)
    
    st.checkbox("💧 Drink 2L of water", value=True)
    st.checkbox("💊 Take morning medication", value=True)
    st.checkbox("🧘 15 min stretching", value=True)
    st.checkbox("🫁 Breathing exercise", value=False)
    st.checkbox("🚶 5,000 steps", value=False)
    
    st.markdown("<hr style='margin: 20px 0; border-color: #334155;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin: 0; font-size: 18px; color: #F8FAFC; margin-bottom: 15px;'>Health Tips</h3>", unsafe_allow_html=True)
    
    # Custom Info/Alert boxes for dark mode
    st.markdown("""
    <div style="background: rgba(56, 189, 248, 0.1); border-left: 4px solid #38BDF8; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
        <span style="color: #38BDF8; font-size: 14px;">💧 Drink plenty of water before your appointment today.</span>
    </div>
    <div style="background: rgba(52, 211, 153, 0.1); border-left: 4px solid #34D399; padding: 12px; border-radius: 4px;">
        <span style="color: #34D399; font-size: 14px;">✅ You are on track with your daily steps!</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)