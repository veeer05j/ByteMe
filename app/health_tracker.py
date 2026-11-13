
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DB_PATH = "DATA/health_tracker.db"


def initialize_database():
    """Create the database and health records table."""

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date TEXT NOT NULL,
            weight REAL,
            systolic INTEGER,
            diastolic INTEGER,
            heart_rate INTEGER,
            glucose REAL,
            water REAL,
            sleep REAL,
            activity INTEGER,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def save_health_record(
    record_date,
    weight,
    systolic,
    diastolic,
    heart_rate,
    glucose,
    water,
    sleep,
    activity,
    notes
):
    """Save a health record into SQLite."""

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        INSERT INTO health_records (
            record_date,
            weight,
            systolic,
            diastolic,
            heart_rate,
            glucose,
            water,
            sleep,
            activity,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_date.isoformat(),
        weight,
        systolic,
        diastolic,
        heart_rate,
        glucose,
        water,
        sleep,
        activity,
        notes
    ))

    conn.commit()
    conn.close()


def load_health_records():
    """Retrieve all saved health records."""

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT *
        FROM health_records
        ORDER BY record_date ASC, id ASC
    """, conn)

    conn.close()

    return df


def delete_health_record(record_id):
    """Delete a selected health record."""

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "DELETE FROM health_records WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def latest_value(df, column):
    """Get the latest non-empty measurement."""

    values = df.dropna(subset=[column])

    if values.empty:
        return None

    return values.iloc[-1][column]


# ==========================================
# PERSONAL HEALTH TRACKER
# ==========================================

def render_health_tracker():

    initialize_database()

    st.title("💙 Personal Health Tracker")

    st.write(
        "Monitor your health measurements and "
        "track your daily wellbeing."
    )

    st.info(
        "This application stores self-reported health "
        "information. It does not provide medical diagnoses."
    )

    records = load_health_records()

    # ======================================
    # TABS
    # ======================================

    overview_tab, trends_tab, history_tab = st.tabs([
        "📊 Overview & Add Entry",
        "📈 Health Trends",
        "📋 Health History"
    ])

    # ======================================
    # OVERVIEW TAB
    # ======================================

    with overview_tab:

        st.subheader("Latest Health Measurements")

        col1, col2, col3, col4 = st.columns(4)

        weight = latest_value(records, "weight")
        heart_rate = latest_value(records, "heart_rate")
        glucose = latest_value(records, "glucose")

        bp_records = records.dropna(
            subset=["systolic", "diastolic"]
        )

        blood_pressure = "—"

        if not bp_records.empty:
            latest_bp = bp_records.iloc[-1]

            blood_pressure = (
                f"{int(latest_bp['systolic'])}/"
                f"{int(latest_bp['diastolic'])}"
            )

        col1.metric(
            "Weight",
            f"{weight:.1f} kg" if pd.notna(weight) else "—"
        )

        col2.metric(
            "Blood Pressure",
            f"{blood_pressure} mmHg"
            if blood_pressure != "—" else "—"
        )

        col3.metric(
            "Heart Rate",
            f"{int(heart_rate)} bpm"
            if pd.notna(heart_rate) else "—"
        )

        col4.metric(
            "Blood Glucose",
            f"{glucose:.1f} mmol/L"
            if pd.notna(glucose) else "—"
        )

        st.divider()

        # ==================================
        # ADD HEALTH ENTRY
        # ==================================

        st.subheader("Add Health Measurements")

        st.caption(
            "Leave a measurement at 0 if you do not wish to record it."
        )

        with st.form("health_entry_form"):

            record_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today()
            )

            st.markdown("#### Body Measurements")

            col1, col2, col3 = st.columns(3)

            weight_input = col1.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=500.0,
                value=0.0,
                step=0.1
            )

            systolic_input = col2.number_input(
                "Systolic Pressure (mmHg)",
                min_value=0,
                max_value=300,
                value=0
            )

            diastolic_input = col3.number_input(
                "Diastolic Pressure (mmHg)",
                min_value=0,
                max_value=200,
                value=0
            )

            st.markdown("#### Other Measurements")

            col4, col5, col6 = st.columns(3)

            heart_rate_input = col4.number_input(
                "Heart Rate (bpm)",
                min_value=0,
                max_value=250,
                value=0
            )

            glucose_input = col5.number_input(
                "Blood Glucose (mmol/L)",
                min_value=0.0,
                max_value=60.0,
                value=0.0,
                step=0.1
            )

            water_input = col6.number_input(
                "Water Intake (L)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1
            )

            st.markdown("#### Daily Wellbeing")

            col7, col8 = st.columns(2)

            sleep_input = col7.number_input(
                "Sleep Duration (hours)",
                min_value=0.0,
                max_value=24.0,
                value=0.0,
                step=0.5
            )

            activity_input = col8.number_input(
                "Physical Activity (minutes)",
                min_value=0,
                max_value=1440,
                value=0
            )

            notes = st.text_area(
                "Additional Notes",
                placeholder="Add any relevant notes..."
            )

            submitted = st.form_submit_button(
                "Save Health Record",
                type="primary",
                use_container_width=True
            )

        if submitted:

            # Convert zero values into empty values.

            weight_value = weight_input or None
            systolic_value = systolic_input or None
            diastolic_value = diastolic_input or None
            heart_rate_value = heart_rate_input or None
            glucose_value = glucose_input or None
            water_value = water_input or None
            sleep_value = sleep_input or None
            activity_value = activity_input or None

            errors = []

            if (systolic_value is None) != (
                diastolic_value is None
            ):
                errors.append(
                    "Enter both blood pressure values."
                )

            if systolic_value is not None:

                if systolic_value <= diastolic_value:
                    errors.append(
                        "Check your blood pressure values."
                    )

            measurements = [
                weight_value,
                systolic_value,
                heart_rate_value,
                glucose_value,
                water_value,
                sleep_value,
                activity_value
            ]

            if all(value is None for value in measurements):
                errors.append(
                    "Enter at least one measurement."
                )

            if errors:

                for error in errors:
                    st.error(error)

            else:

                save_health_record(
                    record_date,
                    weight_value,
                    systolic_value,
                    diastolic_value,
                    heart_rate_value,
                    glucose_value,
                    water_value,
                    sleep_value,
                    activity_value,
                    notes.strip()
                )

                st.success(
                    "Health record saved successfully!"
                )

                st.rerun()

    # ======================================
    # HEALTH TRENDS TAB
    # ======================================

    with trends_tab:

        st.subheader("Health Trends")

        if records.empty:

            st.info(
                "No health records available yet. "
                "Add your first entry to see your charts."
            )

        else:

            chart_records = records.copy()

            chart_records["record_date"] = pd.to_datetime(
                chart_records["record_date"]
            )

            chart_records = chart_records.set_index(
                "record_date"
            )

            # Weight chart

            if chart_records["weight"].notna().any():

                st.markdown("#### Weight History")

                st.line_chart(
                    chart_records["weight"].dropna()
                )

            # Blood pressure chart

            if chart_records[
                ["systolic", "diastolic"]
            ].notna().any().any():

                st.markdown("#### Blood Pressure History")

                st.line_chart(
                    chart_records[
                        ["systolic", "diastolic"]
                    ].dropna(how="all")
                )

            # Heart rate chart

            if chart_records["heart_rate"].notna().any():

                st.markdown("#### Heart Rate History")

                st.line_chart(
                    chart_records["heart_rate"].dropna()
                )

            # Glucose chart

            if chart_records["glucose"].notna().any():

                st.markdown("#### Blood Glucose History")

                st.line_chart(
                    chart_records["glucose"].dropna()
                )

            # Daily wellbeing charts

            if chart_records["water"].notna().any():

                st.markdown("#### Water Consumption")

                st.line_chart(
                    chart_records["water"].dropna()
                )

            if chart_records["sleep"].notna().any():

                st.markdown("#### Sleep Duration")

                st.line_chart(
                    chart_records["sleep"].dropna()
                )

            if chart_records["activity"].notna().any():

                st.markdown("#### Physical Activity")

                st.line_chart(
                    chart_records["activity"].dropna()
                )

    # ======================================
    # HEALTH HISTORY TAB
    # ======================================

    with history_tab:

        st.subheader("Health Records History")

        if records.empty:

            st.info("No health records have been saved yet.")

        else:

            display_columns = [
                "id",
                "record_date",
                "weight",
                "systolic",
                "diastolic",
                "heart_rate",
                "glucose",
                "water",
                "sleep",
                "activity",
                "notes"
            ]

            history = records[display_columns].copy()

            history = history.rename(columns={
                "id": "ID",
                "record_date": "Date",
                "weight": "Weight (kg)",
                "systolic": "Systolic (mmHg)",
                "diastolic": "Diastolic (mmHg)",
                "heart_rate": "Heart Rate (bpm)",
                "glucose": "Glucose (mmol/L)",
                "water": "Water (L)",
                "sleep": "Sleep (hours)",
                "activity": "Activity (minutes)",
                "notes": "Notes"
            })

            history = history.sort_values(
                "Date",
                ascending=False
            )

            st.dataframe(
                history,
                hide_index=True,
                use_container_width=True
            )

            # CSV Export

            csv_data = history.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Download Health History (CSV)",
                data=csv_data,
                file_name="health_history.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.divider()

            # Delete a record

            st.subheader("Delete a Health Record")

            record_ids = records["id"].tolist()

            selected_id = st.selectbox(
                "Select record ID",
                record_ids
            )

            if st.button(
                "Delete Selected Record",
                type="secondary"
            ):

                delete_health_record(selected_id)

                st.success("Record deleted successfully.")

                st.rerun()
