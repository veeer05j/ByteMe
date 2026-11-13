
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "DATA" / "health_tracker.db"

USER_ID = "local_prototype"


# ============================================================
# DATABASE TABLES
# ============================================================

def create_health_table(conn):

    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_records (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            record_date TEXT NOT NULL,

            weight_kg REAL,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            heart_rate_bpm INTEGER,
            glucose_mmol_l REAL,

            water_l REAL,
            sleep_hours REAL,
            activity_minutes INTEGER,

            notes TEXT,
            created_at TEXT

        )
    """)


def create_profile_table(conn):

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (

            user_id TEXT PRIMARY KEY,
            gender TEXT,
            height_cm REAL

        )
    """)


# ============================================================
# DATABASE INITIALIZATION AND MIGRATION
# ============================================================

def initialize_database(db_path=DB_PATH):

    Path(db_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(db_path) as conn:

        conn.row_factory = sqlite3.Row

        existing = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'health_records'
        """).fetchone()

        required_columns = {
            "id",
            "user_id",
            "record_date",
            "weight_kg",
            "systolic_bp",
            "diastolic_bp",
            "heart_rate_bpm",
            "glucose_mmol_l",
            "water_l",
            "sleep_hours",
            "activity_minutes",
            "notes",
            "created_at"
        }

        if existing:

            existing_columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(health_records)"
                ).fetchall()
            }

            if not required_columns.issubset(existing_columns):

                old_records = [
                    dict(row)
                    for row in conn.execute(
                        "SELECT * FROM health_records"
                    ).fetchall()
                ]

                conn.execute("""
                    DROP INDEX IF EXISTS idx_health_date
                """)

                legacy_table = (
                    "health_records_legacy_"
                    + datetime.now().strftime("%Y%m%d%H%M%S%f")
                )

                conn.execute(
                    f'ALTER TABLE health_records RENAME TO "{legacy_table}"'
                )

                create_health_table(conn)

                for row in old_records:

                    def get_value(*names):

                        for name in names:

                            if (
                                name in row
                                and row[name] is not None
                            ):
                                return row[name]

                        return None

                    conn.execute("""
                        INSERT INTO health_records (

                            id,
                            user_id,
                            record_date,

                            weight_kg,
                            systolic_bp,
                            diastolic_bp,
                            heart_rate_bpm,
                            glucose_mmol_l,

                            water_l,
                            sleep_hours,
                            activity_minutes,

                            notes,
                            created_at

                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?
                        )
                    """, (

                        get_value("id"),

                        get_value("user_id") or USER_ID,

                        str(
                            get_value("record_date", "date")
                            or date.today().isoformat()
                        ),

                        get_value("weight_kg", "weight"),
                        get_value("systolic_bp", "systolic"),
                        get_value("diastolic_bp", "diastolic"),
                        get_value("heart_rate_bpm", "heart_rate"),
                        get_value("glucose_mmol_l", "glucose"),
                        get_value("water_l", "water"),
                        get_value("sleep_hours", "sleep"),
                        get_value("activity_minutes", "activity"),
                        get_value("notes"),

                        get_value("created_at")
                        or datetime.now().isoformat()

                    ))

                conn.execute(
                    f'DROP TABLE "{legacy_table}"'
                )

        else:

            create_health_table(conn)

        create_profile_table(conn)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_date
            ON health_records(user_id, record_date)
        """)

        conn.commit()


# ============================================================
# DATABASE OPERATIONS
# ============================================================

def load_records(db_path=DB_PATH):

    with sqlite3.connect(db_path) as conn:

        df = pd.read_sql_query("""
            SELECT *
            FROM health_records
            WHERE user_id = ?
            ORDER BY record_date ASC, id ASC
        """, conn, params=(USER_ID,))

    return df


def save_record(data, db_path=DB_PATH):

    with sqlite3.connect(db_path) as conn:

        conn.execute("""
            INSERT INTO health_records (

                user_id,
                record_date,

                weight_kg,
                systolic_bp,
                diastolic_bp,
                heart_rate_bpm,
                glucose_mmol_l,

                water_l,
                sleep_hours,
                activity_minutes,

                notes,
                created_at

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            USER_ID,

            data["date"].isoformat(),

            data["weight"],
            data["systolic"],
            data["diastolic"],
            data["heart_rate"],
            data["glucose"],

            data["water"],
            data["sleep"],
            data["activity"],

            data["notes"],

            datetime.now().isoformat()

        ))

        conn.commit()


def delete_record(record_id, db_path=DB_PATH):

    with sqlite3.connect(db_path) as conn:

        conn.execute("""
            DELETE FROM health_records
            WHERE id = ?
            AND user_id = ?
        """, (record_id, USER_ID))

        conn.commit()


# ============================================================
# PERSONAL PROFILE
# ============================================================

def load_profile(db_path=DB_PATH):

    with sqlite3.connect(db_path) as conn:

        row = conn.execute("""
            SELECT gender, height_cm
            FROM user_profile
            WHERE user_id = ?
        """, (USER_ID,)).fetchone()

    if row:

        return {
            "gender": row[0],
            "height_cm": row[1]
        }

    return {
        "gender": "Prefer not to say",
        "height_cm": None
    }


def save_profile(gender, height_cm, db_path=DB_PATH):

    with sqlite3.connect(db_path) as conn:

        conn.execute("""
            INSERT INTO user_profile (
                user_id,
                gender,
                height_cm
            )

            VALUES (?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                gender = excluded.gender,
                height_cm = excluded.height_cm

        """, (
            USER_ID,
            gender,
            height_cm
        ))

        conn.commit()


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state(profile):
    """Initialize HealthSpace UI state once per Streamlit session."""

    defaults = {

        "health_page": "Overview",

        "health_period": "Last 30 days",

        "water_goal": 2.0,

        "sleep_goal": 8.0,

        "activity_goal": 30,

        "health_history_search": ""

    }

    for key, default_value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = default_value

    gender_options = [
        "Prefer not to say",
        "Male",
        "Female",
        "Other"
    ]

    saved_gender = (
        profile.get("gender")
        or "Prefer not to say"
    )

    if saved_gender not in gender_options:

        saved_gender = "Prefer not to say"

    if "health_profile_gender" not in st.session_state:

        st.session_state["health_profile_gender"] = saved_gender

    if "health_profile_height_cm" not in st.session_state:

        st.session_state["health_profile_height_cm"] = (
            profile.get("height_cm")
        )


# ============================================================
# BMI CALCULATION
# ============================================================

def calculate_bmi(weight_kg, height_cm):

    if weight_kg is None or height_cm is None:
        return None

    if pd.isna(weight_kg) or pd.isna(height_cm):
        return None

    if weight_kg <= 0 or height_cm <= 0:
        return None

    height_m = height_cm / 100

    return weight_kg / (height_m ** 2)


def bmi_category(bmi):

    if bmi is None:
        return "Not available"

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesity"


# ============================================================
# DESIGN / CSS
# ============================================================

def apply_design():

    st.markdown("""
    <style>

    [data-testid="stAppViewContainer"] {
        background-color: #eef0f4;
    }

    [data-testid="stHeader"] {
        background-color: transparent;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8ebf0;
    }

    [data-testid="stSidebar"] h1 {
        color: #1555d5;
    }

    .dashboard-heading {
        font-size: 32px;
        font-weight: 750;
        color: #20232a;
        line-height: 1.3;
        margin-bottom: 5px;
    }

    .dashboard-subtitle {
        color: #818995;
        font-size: 14px;
        margin-bottom: 20px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border: 1px solid #e9edf3;
        border-radius: 19px;
        padding: 12px;
    }

    [data-testid="stMetric"] {
        background: #f6f8fc;
        border-radius: 13px;
        padding: 13px;
    }

    [data-testid="stMetricLabel"] {
        color: #737d8c;
    }

    [data-testid="stMetricValue"] {
        color: #252a33;
        font-weight: 750;
    }

    .weight-card {
        background: linear-gradient(
            135deg,
            #1555d5,
            #3479ed
        );

        color: white;
        padding: 22px;
        border-radius: 17px;
        min-height: 150px;
    }

    .weight-card .small {
        font-size: 13px;
        opacity: 0.85;
    }

    .weight-card .big {
        font-size: 37px;
        font-weight: 750;
        margin: 12px 0 5px 0;
    }

    .weight-card .description {
        font-size: 12px;
        opacity: 0.85;
    }

    .bmi-card {
        background: #ffffff;
        border: 1px solid #e9edf3;
        border-radius: 17px;
        padding: 18px;
        margin-top: 12px;
    }

    .bmi-label {
        font-size: 13px;
        font-weight: 600;
        color: #737d8c;
    }

    .bmi-value {
        font-size: 32px;
        font-weight: 750;
        color: #1555d5;
        margin: 8px 0;
    }

    .bmi-description {
        color: #737d8c;
        font-size: 13px;
    }

    .section-heading {
        font-size: 18px;
        font-weight: 700;
        color: #282d36;
        margin-bottom: 8px;
    }

    .blue-text {
        color: #1555d5;
        font-weight: 700;
    }

    .stButton button[kind="primary"] {
        background-color: #1555d5;
        border-radius: 10px;
    }

    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    @media(max-width: 900px) {

        .dashboard-heading {
            font-size: 24px;
        }

    }

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# COMMON DATA HELPERS
# ============================================================

def chart_dates(df):

    dates = pd.to_datetime(
        df["record_date"],
        errors="coerce"
    )

    return dates.dt.strftime("%d %b %Y").tolist()


def filter_records_by_period(df, period):

    if df.empty or period == "All records":
        return df.copy()

    days = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90
    }.get(period)

    if days is None:
        return df.copy()

    start = pd.Timestamp(date.today()) - pd.Timedelta(
        days=days - 1
    )

    dates = pd.to_datetime(
        df["record_date"],
        errors="coerce"
    )

    mask = dates >= start

    return df.loc[mask.fillna(False)].copy()


def latest_measurement(df, column):

    if df.empty:
        return None, None

    data = df.dropna(
        subset=[column]
    )

    if data.empty:
        return None, None

    latest = data.iloc[-1]

    return (
        latest[column],
        latest["record_date"]
    )


# ============================================================
# COMMON CHART SETTINGS
# ============================================================

def chart_style(fig, title, y_title, height=280):

    fig.update_layout(

        title=dict(
            text=title,
            font=dict(
                size=17,
                color="#252a33"
            ),
            x=0.02
        ),

        template="plotly_white",

        height=height,

        margin=dict(
            l=25,
            r=20,
            t=55,
            b=45
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Arial",
            color="#343a46",
            size=11
        ),

        xaxis=dict(
            showgrid=False,
            tickangle=0,
            automargin=True
        ),

        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor="#edf0f4",
            automargin=True
        ),

        hovermode=False,

        showlegend=False

    )

    return fig


def show_chart(fig):

    st.plotly_chart(

        fig,

        use_container_width=True,

        config={
            "displayModeBar": False,
            "staticPlot": True,
            "responsive": True
        }

    )


# ============================================================
# BLOOD PRESSURE CHART
# ============================================================

def blood_pressure_chart(df):

    data = df.dropna(
        subset=[
            "systolic_bp",
            "diastolic_bp"
        ]
    ).tail(10)

    if data.empty:

        st.info(
            "No complete blood pressure measurements recorded yet."
        )

        return

    labels = chart_dates(data)

    fig = go.Figure()

    fig.add_trace(go.Scatter(

        x=labels,
        y=data["systolic_bp"],

        mode="lines+markers+text",

        name="Systolic",

        text=[
            str(int(v))
            for v in data["systolic_bp"]
        ],

        textposition="top center",

        line=dict(
            color="#1555d5",
            width=3,
            shape="spline"
        ),

        marker=dict(
            size=8,
            color="#1555d5"
        ),

        cliponaxis=False

    ))

    fig.add_trace(go.Scatter(

        x=labels,
        y=data["diastolic_bp"],

        mode="lines+markers+text",

        name="Diastolic",

        text=[
            str(int(v))
            for v in data["diastolic_bp"]
        ],

        textposition="bottom center",

        line=dict(
            color="#55a5ed",
            width=2,
            shape="spline"
        ),

        marker=dict(
            size=7,
            color="#55a5ed"
        ),

        cliponaxis=False

    ))

    chart_style(
        fig,
        "♥ Blood Pressure Statistics",
        "mmHg",
        300
    )

    fig.update_layout(

        showlegend=True,

        legend=dict(
            orientation="h",
            y=1.14,
            x=0.02
        )

    )

    show_chart(fig)


# ============================================================
# TRACKING CONSISTENCY
# ============================================================

def consistency_chart(df):

    today = pd.Timestamp(date.today())

    weeks = []
    counts = []

    if df.empty:

        dates = pd.Series(
            dtype="datetime64[ns]"
        )

    else:

        dates = pd.to_datetime(
            df["record_date"],
            errors="coerce"
        ).dt.normalize()

    for week in range(4, -1, -1):

        end = today - pd.Timedelta(
            days=week * 7
        )

        start = end - pd.Timedelta(
            days=6
        )

        weeks.append(
            start.strftime("%d %b")
        )

        count = dates[
            (dates >= start.normalize()) &
            (dates <= end.normalize())
        ].nunique()

        counts.append(int(count))

    fig = go.Figure()

    fig.add_trace(go.Bar(

        x=weeks,
        y=counts,

        text=[
            f"{v}/7"
            for v in counts
        ],

        textposition="outside",
        cliponaxis=False,

        marker=dict(

            color=[
                "#1555d5" if i == 4 else "#30343b"
                for i in range(5)
            ],

            line=dict(width=0)

        ),

        width=0.55

    ))

    chart_style(
        fig,
        "▥ Tracking Consistency",
        "Days logged",
        300
    )

    fig.update_yaxes(
        range=[0, 8],
        tickvals=[0, 2, 4, 6, 7]
    )

    show_chart(fig)


# ============================================================
# WEIGHT CARD
# ============================================================

def weight_card(df):

    weight_data = df.dropna(
        subset=["weight_kg"]
    ).tail(2)

    if weight_data.empty:

        current = None
        difference = None

    else:

        current = float(
            weight_data.iloc[-1]["weight_kg"]
        )

        difference = None

        if len(weight_data) > 1:

            previous = float(
                weight_data.iloc[-2]["weight_kg"]
            )

            difference = current - previous

    if current is None:

        value = "—"
        description = "No weight recorded yet"

    else:

        value = f"{current:.1f} kg"

        if difference is None:

            description = "Latest recorded measurement"

        else:

            description = (
                f"{difference:+.1f} kg compared with previous entry"
            )

    html = (
        f'<div class="weight-card">'
        f'<div class="small">⚖ WEIGHT OVERVIEW</div>'
        f'<div class="big">{value}</div>'
        f'<div class="description">{description}</div>'
        f'</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ============================================================
# BMI CARD
# ============================================================

def bmi_card(df, height_cm):

    weight_data = df.dropna(
        subset=["weight_kg"]
    )

    if weight_data.empty or height_cm is None:

        bmi = None

    else:

        latest_weight = float(
            weight_data.iloc[-1]["weight_kg"]
        )

        bmi = calculate_bmi(
            latest_weight,
            height_cm
        )

    if bmi is None:

        value = "—"
        category = "Enter your height and record your weight"

    else:

        value = f"{bmi:.1f}"
        category = bmi_category(bmi)

    html = (
        f'<div class="bmi-card">'
        f'<div class="bmi-label">BMI OVERVIEW</div>'
        f'<div class="bmi-value">{value}</div>'
        f'<div class="bmi-description">{category}</div>'
        f'</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )

    st.caption(
        "BMI is an adult screening measure, not a medical diagnosis."
    )


# ============================================================
# HYDRATION GAUGE
# ============================================================

def hydration_chart(df, water_goal):

    if df.empty:

        today_records = df.copy()

    else:

        dates = pd.to_datetime(
            df["record_date"],
            errors="coerce"
        )

        today_mask = dates.dt.date == date.today()

        today_records = df.loc[today_mask].copy()

    today_records = today_records.dropna(
        subset=["water_l"]
    )

    has_record = not today_records.empty

    if has_record:

        water = float(
            today_records.iloc[-1]["water_l"]
        )

    else:

        water = 0.0

    gauge_max = max(
        water_goal * 1.4,
        water * 1.2,
        1
    )

    fig = go.Figure(go.Indicator(

        mode="gauge+number",

        value=water,

        number=dict(
            suffix=" L",
            valueformat=".1f",
            font=dict(
                size=27,
                color="#272e3a"
            )
        ),

        gauge=dict(

            shape="angular",

            axis=dict(
                range=[0, gauge_max],
                tickwidth=0,
                tickcolor="#ffffff",
                showticklabels=False
            ),

            bar=dict(
                color="#1555d5",
                thickness=0.28
            ),

            bgcolor="#f0f2f6",

            borderwidth=0,

            steps=[
                dict(
                    range=[0, gauge_max],
                    color="#edf0f5"
                )
            ],

            threshold=dict(
                line=dict(
                    color="#252a33",
                    width=3
                ),

                thickness=0.8,

                value=water_goal
            )

        )

    ))

    fig.update_layout(

        height=165,

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=5
        ),

        paper_bgcolor="rgba(0,0,0,0)"

    )

    st.markdown(
        '<div class="section-heading">💧 Hydration Level</div>',
        unsafe_allow_html=True
    )

    show_chart(fig)

    if has_record:

        st.caption(
            f"Today's recorded intake: {water:.1f} L | "
            f"Your chosen goal: {water_goal:.1f} L"
        )

    else:

        st.caption(
            f"No water intake recorded today. "
            f"Your chosen goal: {water_goal:.1f} L"
        )


# ============================================================
# SLEEP CHART
# ============================================================

def sleep_chart(df, sleep_goal):

    data = df.dropna(
        subset=["sleep_hours"]
    ).tail(7)

    if data.empty:

        st.info(
            "No sleep measurements recorded yet."
        )

        return

    labels = chart_dates(data)
    values = data["sleep_hours"].tolist()

    colors = [
        "#1555d5" if v >= sleep_goal else "#30343b"
        for v in values
    ]

    fig = go.Figure(go.Bar(

        x=labels,
        y=values,

        marker_color=colors,

        text=[
            f"{v:.1f} h"
            for v in values
        ],

        textposition="outside",
        cliponaxis=False

    ))

    chart_style(
        fig,
        "☾ Sleep History",
        "Hours",
        265
    )

    fig.update_yaxes(
        range=[
            0,
            max(
                max(values) * 1.3,
                sleep_goal * 1.3,
                1
            )
        ]
    )

    show_chart(fig)

    st.caption(
        f"Your chosen sleep goal: {sleep_goal:.1f} hours"
    )


# ============================================================
# ACTIVITY CHART
# ============================================================

def activity_chart(df, activity_goal):

    data = df.dropna(
        subset=["activity_minutes"]
    ).tail(7)

    if data.empty:

        st.info(
            "No physical activity records available."
        )

        return

    labels = chart_dates(data)
    values = data["activity_minutes"].tolist()

    colors = [
        "#1555d5" if v >= activity_goal else "#30343b"
        for v in values
    ]

    fig = go.Figure(go.Bar(

        x=labels,
        y=values,

        marker_color=colors,

        text=[
            f"{int(v)} min"
            for v in values
        ],

        textposition="outside",
        cliponaxis=False

    ))

    chart_style(
        fig,
        "🏃 Physical Activity",
        "Minutes",
        265
    )

    fig.update_yaxes(
        range=[
            0,
            max(
                max(values) * 1.3,
                activity_goal * 1.3,
                1
            )
        ]
    )

    show_chart(fig)


# ============================================================
# REUSABLE HISTORY CHART
# ============================================================

def render_history_chart(
    df,
    column,
    title,
    y_title,
    chart_type="line",
    unit=""
):

    data = df.dropna(
        subset=[column]
    ).tail(20)

    if data.empty:

        st.info(
            f"No {title.lower()} measurements recorded yet."
        )

        return

    labels = chart_dates(data)
    values = data[column].tolist()

    if chart_type == "bar":

        fig = go.Figure(go.Bar(

            x=labels,
            y=values,

            marker_color="#1555d5",

            text=[
                f"{v:g} {unit}"
                for v in values
            ],

            textposition="outside",
            cliponaxis=False

        ))

    else:

        fig = go.Figure(go.Scatter(

            x=labels,
            y=values,

            mode="lines+markers+text",

            text=[
                f"{v:g} {unit}"
                for v in values
            ],

            textposition="top center",

            line=dict(
                color="#1555d5",
                width=3,
                shape="spline"
            ),

            marker=dict(size=8),

            cliponaxis=False

        ))

    chart_style(
        fig,
        title,
        y_title
    )

    show_chart(fig)


# ============================================================
# OVERVIEW DASHBOARD
# ============================================================

def render_dashboard(
    df,
    period,
    water_goal,
    sleep_goal,
    activity_goal,
    profile
):

    st.markdown(
        """
        <div class="dashboard-heading">
            Take Care Of Your Health Easily
        </div>

        <div class="dashboard-subtitle">
            Your personal health and daily wellbeing dashboard
        </div>
        """,
        unsafe_allow_html=True
    )

    chart_df = filter_records_by_period(
        df,
        period
    )

    # TOP ROW

    col1, col2, col3 = st.columns(
        [1.05, 1.45, 0.9],
        gap="medium"
    )

    with col1:

        with st.container(border=True):

            blood_pressure_chart(chart_df)

        with st.container(border=True):

            hydration_chart(
                df,
                water_goal
            )

    with col2:

        with st.container(border=True):

            consistency_chart(df)

            recent_dates = pd.to_datetime(
                df["record_date"],
                errors="coerce"
            ).dt.date if not df.empty else pd.Series(dtype="object")

            logged_days = recent_dates[
                recent_dates >= (
                    date.today() - timedelta(days=6)
                )
            ].nunique()

            st.metric(
                "Days with entries this week",
                f"{logged_days}/7"
            )

    with col3:

        with st.container(border=True):

            weight_card(df)

        bmi_card(
            df,
            profile["height_cm"]
        )

    st.write("")

    # BOTTOM ROW

    col4, col5, col6 = st.columns(
        [1.05, 1.25, 1.1],
        gap="medium"
    )

    with col4:

        with st.container(border=True):

            st.markdown(
                '<div class="section-heading">☀ Daily Wellbeing</div>',
                unsafe_allow_html=True
            )

            st.write(
                "Your most recent recorded daily measurements."
            )

            st.metric(
                "Gender",
                profile["gender"]
            )

            st.metric(
                "Height",
                (
                    f"{profile['height_cm']:.1f} cm"
                    if profile["height_cm"] is not None
                    else "Not recorded"
                )
            )

            if df.empty:

                st.info(
                    "Add your first health measurement to get started."
                )

            else:

                sleep_value, _ = latest_measurement(
                    df,
                    "sleep_hours"
                )

                st.metric(
                    "Sleep",
                    (
                        f"{sleep_value:.1f} hours"
                        if sleep_value is not None
                        else "Not recorded"
                    )
                )

                activity_value, _ = latest_measurement(
                    df,
                    "activity_minutes"
                )

                st.metric(
                    "Physical activity",
                    (
                        f"{int(activity_value)} minutes"
                        if activity_value is not None
                        else "Not recorded"
                    )
                )

                water_value, _ = latest_measurement(
                    df,
                    "water_l"
                )

                st.metric(
                    "Water intake",
                    (
                        f"{water_value:.1f} L"
                        if water_value is not None
                        else "Not recorded"
                    )
                )

    with col5:

        with st.container(border=True):

            activity_chart(
                chart_df,
                activity_goal
            )

    with col6:

        with st.container(border=True):

            sleep_chart(
                chart_df,
                sleep_goal
            )


# ============================================================
# HEALTH TRENDS PAGE
# ============================================================

def render_trends(
    df,
    water_goal,
    sleep_goal,
    activity_goal,
    profile
):

    st.markdown(
        '<div class="dashboard-heading">Health Analytics</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Explore your recorded health measurements over time."
    )

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            blood_pressure_chart(df)

        with st.container(border=True):

            render_history_chart(
                df,
                "weight_kg",
                "Weight History",
                "Weight (kg)",
                "line",
                "kg"
            )

        with st.container(border=True):

            bmi_data = df.dropna(
                subset=["weight_kg"]
            ).tail(20).copy()

            if (
                not bmi_data.empty
                and profile["height_cm"] is not None
            ):

                bmi_data["bmi"] = bmi_data["weight_kg"].apply(
                    lambda weight: calculate_bmi(
                        weight,
                        profile["height_cm"]
                    )
                )

                render_history_chart(
                    bmi_data,
                    "bmi",
                    "BMI History",
                    "BMI",
                    "line"
                )

                st.caption(
                    "Historical BMI is calculated using your current saved height."
                )

            else:

                st.info(
                    "Enter your height and record your weight to see BMI history."
                )

        with st.container(border=True):

            activity_chart(
                df,
                activity_goal
            )

    with col2:

        with st.container(border=True):

            render_history_chart(
                df,
                "heart_rate_bpm",
                "Heart Rate History",
                "BPM",
                "bar",
                "bpm"
            )

        with st.container(border=True):

            render_history_chart(
                df,
                "glucose_mmol_l",
                "Blood Glucose History",
                "mmol/L",
                "line",
                "mmol/L"
            )

        with st.container(border=True):

            sleep_chart(
                df,
                sleep_goal
            )

        with st.container(border=True):

            hydration_chart(
                df,
                water_goal
            )


# ============================================================
# ADD MEASUREMENTS
# ============================================================

def render_add_entry(db_path):

    st.markdown(
        '<div class="dashboard-heading">Add Health Measurements</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Record your latest measurements and daily wellbeing."
    )

    with st.container(border=True):

        with st.form(
            "health_entry",
            clear_on_submit=True
        ):

            record_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
                key="health_entry_date"
            )

            st.subheader("Body Measurements")

            c1, c2, c3 = st.columns(3)

            weight = c1.number_input(
                "Weight (kg)",
                min_value=0.1,
                max_value=500.0,
                value=None,
                step=0.1,
                placeholder="Not recorded",
                key="health_entry_weight"
            )

            systolic = c2.number_input(
                "Systolic pressure (mmHg)",
                min_value=1,
                max_value=300,
                value=None,
                placeholder="Not recorded",
                key="health_entry_systolic"
            )

            diastolic = c3.number_input(
                "Diastolic pressure (mmHg)",
                min_value=1,
                max_value=200,
                value=None,
                placeholder="Not recorded",
                key="health_entry_diastolic"
            )

            st.subheader("Other Measurements")

            c4, c5, c6 = st.columns(3)

            heart_rate = c4.number_input(
                "Heart rate (bpm)",
                min_value=1,
                max_value=250,
                value=None,
                placeholder="Not recorded",
                key="health_entry_heart_rate"
            )

            glucose = c5.number_input(
                "Blood glucose (mmol/L)",
                min_value=0.1,
                max_value=60.0,
                value=None,
                step=0.1,
                placeholder="Not recorded",
                key="health_entry_glucose"
            )

            water = c6.number_input(
                "Water intake (L)",
                min_value=0.0,
                max_value=20.0,
                value=None,
                step=0.1,
                placeholder="Not recorded",
                key="health_entry_water"
            )

            st.subheader("Daily Wellbeing")

            c7, c8 = st.columns(2)

            sleep = c7.number_input(
                "Sleep duration (hours)",
                min_value=0.0,
                max_value=24.0,
                value=None,
                step=0.5,
                placeholder="Not recorded",
                key="health_entry_sleep"
            )

            activity = c8.number_input(
                "Physical activity (minutes)",
                min_value=0,
                max_value=1440,
                value=None,
                step=5,
                placeholder="Not recorded",
                key="health_entry_activity"
            )

            notes = st.text_area(
                "Additional notes",
                max_chars=500,
                placeholder="Add any relevant notes...",
                key="health_entry_notes"
            )

            submitted = st.form_submit_button(
                "Save Health Record",
                type="primary",
                use_container_width=True
            )

        if submitted:

            errors = []

            if (
                (systolic is None)
                != (diastolic is None)
            ):

                errors.append(
                    "Enter both systolic and diastolic pressure."
                )

            if (
                systolic is not None
                and diastolic is not None
                and systolic <= diastolic
            ):

                errors.append(
                    "Systolic pressure must be greater than diastolic pressure."
                )

            measurements = [
                weight,
                systolic,
                diastolic,
                heart_rate,
                glucose,
                water,
                sleep,
                activity
            ]

            if all(
                value is None
                for value in measurements
            ):

                errors.append(
                    "Enter at least one measurement."
                )

            if errors:

                for error in errors:
                    st.error(error)

            else:

                data = {

                    "date": record_date,

                    "weight": weight,
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "heart_rate": heart_rate,
                    "glucose": glucose,

                    "water": water,
                    "sleep": sleep,
                    "activity": activity,

                    "notes": notes

                }

                try:

                    save_record(
                        data,
                        db_path
                    )

                    st.success(
                        "Your health record has been saved."
                    )

                    st.rerun()

                except sqlite3.Error as error:

                    st.error(
                        f"Database error: {error}"
                    )


# ============================================================
# HEALTH HISTORY
# ============================================================

def render_history(df, db_path, profile):

    st.markdown(
        '<div class="dashboard-heading">Health History</div>',
        unsafe_allow_html=True
    )

    if df.empty:

        st.info(
            "No health records available. Add your first entry."
        )

        return

    history = df.sort_values(
        ["record_date", "id"],
        ascending=False
    ).copy()

    history["bmi"] = history["weight_kg"].apply(
        lambda weight: calculate_bmi(
            weight,
            profile["height_cm"]
        )
    )

    valid_dates = pd.to_datetime(
        history["record_date"],
        errors="coerce"
    ).dropna()

    if valid_dates.empty:

        st.error(
            "No valid dates are available in your health records."
        )

        return

    minimum_date = valid_dates.min().date()
    maximum_date = valid_dates.max().date()

    st.markdown("### Filter records")

    c1, c2 = st.columns(2)

    start_date = c1.date_input(
        "From",
        value=minimum_date,
        min_value=minimum_date,
        max_value=maximum_date,
        key="history_start_date"
    )

    end_date = c2.date_input(
        "To",
        value=maximum_date,
        min_value=minimum_date,
        max_value=maximum_date,
        key="history_end_date"
    )

    if start_date > end_date:

        st.error(
            "The starting date cannot be later than the ending date."
        )

        return

    parsed_dates = pd.to_datetime(
        history["record_date"],
        errors="coerce"
    ).dt.date

    history = history.loc[
        (parsed_dates >= start_date) &
        (parsed_dates <= end_date)
    ].copy()

    history = history.rename(columns={

        "id": "ID",
        "record_date": "Date",
        "weight_kg": "Weight (kg)",
        "bmi": "BMI",
        "systolic_bp": "Systolic (mmHg)",
        "diastolic_bp": "Diastolic (mmHg)",
        "heart_rate_bpm": "Heart Rate (bpm)",
        "glucose_mmol_l": "Glucose (mmol/L)",
        "water_l": "Water (L)",
        "sleep_hours": "Sleep (hours)",
        "activity_minutes": "Activity (minutes)",
        "notes": "Notes"

    })

    search = st.text_input(
        "Search health records",
        placeholder="Search notes or measurements...",
        key="health_history_search"
    )

    columns = [

        "ID",
        "Date",
        "Weight (kg)",
        "BMI",
        "Systolic (mmHg)",
        "Diastolic (mmHg)",
        "Heart Rate (bpm)",
        "Glucose (mmol/L)",
        "Water (L)",
        "Sleep (hours)",
        "Activity (minutes)",
        "Notes"

    ]

    if search:

        mask = history[columns].astype(str).apply(

            lambda column: column.str.contains(
                search,
                case=False,
                na=False,
                regex=False
            )

        ).any(axis=1)

        history = history[mask]

    st.markdown("### Recorded Measurements")

    if history.empty:

        st.info(
            "No records match your selected filters."
        )

    else:

        st.dataframe(
            history[columns],
            hide_index=True,
            use_container_width=True
        )

        st.download_button(

            "Download CSV",

            data=history[columns].to_csv(
                index=False
            ).encode("utf-8"),

            file_name="health_history.csv",

            mime="text/csv"

        )

    st.divider()

    with st.expander("Delete a health record"):

        record_id = st.selectbox(
            "Select record ID",
            options=df["id"].tolist(),
            key="delete_record_id"
        )

        confirm = st.checkbox(
            "Confirm deletion",
            key="confirm_delete_record"
        )

        if st.button(
            "Delete record",
            disabled=not confirm,
            key="delete_health_record"
        ):

            try:

                delete_record(
                    record_id,
                    db_path
                )

                st.success(
                    "Record deleted successfully."
                )

                st.rerun()

            except sqlite3.Error as error:

                st.error(
                    f"Unable to delete record: {error}"
                )


# ============================================================
# MAIN APPLICATION
# ============================================================

def render_health_tracker(db_path=DB_PATH):

    # INITIALIZE DATABASE

    initialize_database(db_path)

    # DESIGN

    apply_design()

    # LOAD DATA

    df = load_records(db_path)

    profile = load_profile(db_path)

    # INITIALIZE SESSION STATE

    initialize_session_state(profile)

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.markdown(
            """
            <h1 style="font-size:28px;">✣</h1>

            <h3 style="color:#202a3a;">
                HealthSpace
            </h3>

            <p style="color:#89919e;font-size:12px;">
                PERSONAL WELLBEING
            </p>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        page = st.radio(

            "NAVIGATION",

            [
                "Overview",
                "Add measurements",
                "Health trends",
                "Health history"
            ],

            key="health_page"

        )

        # PERSONAL PROFILE

        st.divider()

        st.markdown("### Personal Profile")

        with st.form("personal_profile_form"):

            gender_options = [
                "Prefer not to say",
                "Male",
                "Female",
                "Other"
            ]

            gender = st.selectbox(

                "Gender",

                gender_options,

                key="health_profile_gender"

            )

            height_cm = st.number_input(

                "Height (cm)",

                min_value=50.0,
                max_value=250.0,

                step=0.5,

                placeholder="Enter your height",

                key="health_profile_height_cm"

            )

            save_profile_button = st.form_submit_button(

                "Save Profile",

                use_container_width=True

            )

            if save_profile_button:

                try:

                    save_profile(

                        st.session_state["health_profile_gender"],

                        st.session_state["health_profile_height_cm"],

                        db_path

                    )

                    st.success(
                        "Profile saved successfully."
                    )

                    st.rerun()

                except sqlite3.Error as error:

                    st.error(
                        f"Database error: {error}"
                    )

        # PERSONAL GOALS

        st.divider()

        st.markdown("### Personal Goals")

        water_goal = st.number_input(

            "Water goal (L)",

            min_value=0.1,
            max_value=10.0,

            step=0.1,

            key="water_goal"

        )

        sleep_goal = st.number_input(

            "Sleep goal (hours)",

            min_value=0.5,
            max_value=24.0,

            step=0.5,

            key="sleep_goal"

        )

        activity_goal = st.number_input(

            "Activity goal (minutes)",

            min_value=1,
            max_value=1440,

            step=5,

            key="activity_goal"

        )

        st.divider()

        st.caption("HealthSpace Prototype")

    # ========================================================
    # MAIN HEADER
    # ========================================================

    header_left, header_right = st.columns(
        [2.5, 1],
        vertical_alignment="center"
    )

    with header_left:

        st.markdown(
            f"""
            <div style="font-size:13px;color:#7d8795;">
                HOME / {page.upper()}
            </div>
            """,
            unsafe_allow_html=True
        )

    period = "All records"

    if page in ["Overview", "Health trends"]:

        with header_right:

            period = st.selectbox(

                "Dashboard period",

                [
                    "Last 7 days",
                    "Last 30 days",
                    "Last 90 days",
                    "All records"
                ],

                key="health_period",

                label_visibility="collapsed"

            )

    st.write("")

    # ========================================================
    # PAGE ROUTING
    # ========================================================

    if page == "Overview":

        render_dashboard(

            df,

            period,

            water_goal,

            sleep_goal,

            activity_goal,

            profile

        )

    elif page == "Add measurements":

        render_add_entry(db_path)

    elif page == "Health trends":

        filtered_df = filter_records_by_period(
            df,
            period
        )

        render_trends(

            filtered_df,

            water_goal,

            sleep_goal,

            activity_goal,

            profile

        )

    elif page == "Health history":

        render_history(
            df,
            db_path,
            profile
        )
