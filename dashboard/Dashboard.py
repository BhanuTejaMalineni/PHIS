import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import extras # Still imported but not directly used for DictCursor
from dotenv import load_dotenv
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration & Database Connection ---
load_dotenv(dotenv_path='/Users/bhanutejamalineni/phis_project/backend/.env') # Ensure this path is correct for your Mac

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# --- Define expected column names for DataFrames ---
# These lists MUST match the order and names of columns in your PostgreSQL tables
HEALTH_DATA_COLUMNS = [
    'id', 'timestamp', 'device_name', 'brand', 'model', 'heart_rate', 'steps',
    'calories', 'activity_level', 'sleep_duration', 'oxygen_saturation',
    'body_temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic'
]

INSIGHTS_COLUMNS = [
    'insight_id', 'timestamp', 'device_name', 'metric_involved', 'anomaly_type',
    'insight_text', 'severity', 'is_read', 'created_at'
]

# --- Database Functions ---
def get_db_connection():
    """Establishes and returns a database connection."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

@st.cache_data(ttl=60) # Cache health data for 60 seconds
def fetch_health_data_from_db():
    """Fetches all health data from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor() # Use a regular cursor
        # Explicitly select columns to ensure correct naming and order for pandas
        cur.execute("""
            SELECT id, timestamp, device_name, brand, model, heart_rate, steps, calories, 
                   activity_level, sleep_duration, oxygen_saturation, body_temperature, 
                   blood_pressure_systolic, blood_pressure_diastolic
            FROM health_data 
            ORDER BY timestamp DESC;
        """) 
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        if not data:
            st.info("No rows found in 'health_data' table. Simulator might not be running or data not saved.")
            return pd.DataFrame(columns=HEALTH_DATA_COLUMNS) # Return empty DF with correct columns

        df = pd.DataFrame(data, columns=HEALTH_DATA_COLUMNS) # Explicitly pass column names
        
        # Type conversion and validation
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True) # Drop rows where timestamp couldn't be parsed

        numeric_cols = ['heart_rate', 'steps', 'calories', 'sleep_duration',
                        'oxygen_saturation', 'body_temperature',
                        'blood_pressure_systolic', 'blood_pressure_diastolic']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce') 
                # Optional: fill NaNs if you want to ensure no NaNs for display/metrics
                # df[col].fillna(df[col].mean(), inplace=True) 

        return df
    except Exception as e:
        st.error(f"Error fetching health data: {e}")
        return pd.DataFrame(columns=HEALTH_DATA_COLUMNS) # Return empty DataFrame on error

@st.cache_data(ttl=30) # Cache insights for 30 seconds
def fetch_insights_from_db():
    """Fetches all insights from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor() # Use a regular cursor
        # Explicitly select columns for insights
        cur.execute("""
            SELECT insight_id, timestamp, device_name, metric_involved, anomaly_type, 
                   insight_text, severity, is_read, created_at
            FROM insights 
            ORDER BY created_at DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        if not data:
            st.info("No rows found in 'insights' table. ML pipeline might not be running or insights not saved.")
            return pd.DataFrame(columns=INSIGHTS_COLUMNS) # Return empty DF with correct columns

        df = pd.DataFrame(data, columns=INSIGHTS_COLUMNS) # Explicitly pass column names
        
        # Type conversion and validation
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df.dropna(subset=['timestamp', 'created_at'], inplace=True) # Drop rows with invalid timestamps

        # Ensure 'is_read' is boolean
        if 'is_read' in df.columns:
            df['is_read'] = df['is_read'].astype(bool)

        return df
    except Exception as e:
        st.error(f"Error fetching insights: {e}")
        return pd.DataFrame(columns=INSIGHTS_COLUMNS) # Return empty DataFrame on error

def update_insight_status(insight_id, is_read):
    """Updates the 'is_read' status of an insight in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE insights SET is_read = %s WHERE insight_id = %s;", (is_read, insight_id))
        conn.commit()
        cur.close()
        conn.close()
        st.cache_data.clear() # Clear cache to refetch updated insights after status change
        st.session_state['rerun_flag'] = True # Set a flag to trigger rerun outside the callback
    except Exception as e:
        st.error(f"Error updating insight status: {e}")
        if conn:
            conn.close()

# --- Basic Authentication ---
def check_password():
    """Returns `True` if the user has entered the correct password."""
    REQUIRED_PASSWORD = "phis_user_pass" # This is your dashboard password

    def password_entered():
        if st.session_state["password"] == REQUIRED_PASSWORD:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Password incorrect")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# --- Streamlit App Layout ---

# Initialize rerun_flag if it doesn't exist
if 'rerun_flag' not in st.session_state:
    st.session_state['rerun_flag'] = False

# Handle rerun triggered by update_insight_status (must be outside of callbacks)
if st.session_state['rerun_flag']:
    st.session_state['rerun_flag'] = False # Reset the flag
    st.rerun()

if check_password():
    st.set_page_config(layout="wide", page_title="PHIS Dashboard")
    st.title("Proactive Health Insight System (PHIS) Dashboard 📈")

    # --- Sidebar ---
    st.sidebar.header("Navigation")
    dashboard_mode = st.sidebar.radio("Go to", ["Overview", "Raw Data Explorer", "Insights & Alerts"])

    # --- Data Fetching ---
    # These will use the cached versions or refetch if cache expired/cleared
    health_data_df = fetch_health_data_from_db()
    insights_df = fetch_insights_from_db()

    # --- Overview Mode ---
    if dashboard_mode == "Overview":
        st.header("Overview: Current Status & Key Metrics")

        if health_data_df.empty:
            st.warning("No health data available. Please ensure the simulator and backend are running and data is being saved.")
        else:
            latest_data = health_data_df.sort_values(by='timestamp', ascending=False).iloc[0]
            st.subheader("Latest Readings:")
            col1, col2, col3, col4, col5 = st.columns(5)
            # Use .get() with a default for robust access in case a column is unexpectedly missing
            col1.metric("Heart Rate", f"{latest_data.get('heart_rate', 'N/A')} bpm")
            col2.metric("Steps", f"{latest_data.get('steps', 'N/A')}")
            col3.metric("Calories", f"{latest_data.get('calories', 'N/A')} kcal")
            col4.metric("Sleep Duration", f"{latest_data.get('sleep_duration', 'N/A') or 'N/A'} hrs")
            col5.metric("Oxygen Saturation", f"{latest_data.get('oxygen_saturation', 'N/A') or 'N/A'} %")

            st.subheader("Recent Trends (Last 24 Hours)")
            
            # Check if 'timestamp' is in columns before using it
            if 'timestamp' in health_data_df.columns:
                time_ago = datetime.now() - timedelta(hours=24)
                recent_data = health_data_df[health_data_df['timestamp'] >= time_ago].copy()
            else:
                recent_data = pd.DataFrame() # No timestamp column, so no recent data can be filtered

            if not recent_data.empty:
                # Ensure device_name exists for color mapping in plot
                if 'device_name' in recent_data.columns and not recent_data['device_name'].isnull().all():
                    if 'heart_rate' in recent_data.columns:
                        fig_hr = px.line(recent_data, x='timestamp', y='heart_rate', title='Heart Rate Trend', color='device_name')
                        st.plotly_chart(fig_hr, use_container_width=True)
                    if 'steps' in recent_data.columns:
                        fig_steps = px.line(recent_data, x='timestamp', y='steps', title='Steps Trend', color='device_name')
                        st.plotly_chart(fig_steps, use_container_width=True)
                else: # No device_name or all null, plot without color differentiation
                    if 'heart_rate' in recent_data.columns:
                        fig_hr = px.line(recent_data, x='timestamp', y='heart_rate', title='Heart Rate Trend')
                        st.plotly_chart(fig_hr, use_container_width=True)
                    if 'steps' in recent_data.columns:
                        fig_steps = px.line(recent_data, x='timestamp', y='steps', title='Steps Trend')
                        st.plotly_chart(fig_steps, use_container_width=True)
            else:
                st.info("Not enough recent data for trend analysis within the last 24 hours. Keep the simulator running!")

        st.subheader("Recent Insights Summary")
        if not insights_df.empty:
            unread_insights = insights_df[insights_df['is_read'] == False]
            if not unread_insights.empty:
                st.warning(f"You have {len(unread_insights)} unread insights!")
                # Ensure all displayed columns exist
                display_cols = ['timestamp', 'device_name', 'anomaly_type', 'insight_text', 'severity']
                display_cols = [col for col in display_cols if col in unread_insights.columns]
                st.dataframe(unread_insights[display_cols], use_container_width=True)
            else:
                st.success("No new unread insights at the moment!")
            st.text(f"Total insights generated: {len(insights_df)}")
        else:
            st.info("No insights have been generated yet.")


    # --- Raw Data Explorer Mode ---
    elif dashboard_mode == "Raw Data Explorer":
        st.header("Raw Health Data Explorer")
        if not health_data_df.empty:
            st.dataframe(health_data_df, use_container_width=True)

            st.subheader("Filter and Visualize")
            # Ensure device_name exists and is not all null for selectbox options
            device_options = ['All']
            if 'device_name' in health_data_df.columns and not health_data_df['device_name'].isnull().all():
                device_options.extend(list(health_data_df['device_name'].unique()))
            selected_device = st.selectbox("Select Device", options=device_options)
            
            # Filter metric options to only those present in the DataFrame
            all_metric_options = ['heart_rate', 'steps', 'calories', 'sleep_duration', 'oxygen_saturation', 'body_temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic']
            available_metric_options = [m for m in all_metric_options if m in health_data_df.columns]
            selected_metric = st.selectbox("Select Metric", options=available_metric_options)


            filtered_df = health_data_df.copy()
            if selected_device != 'All':
                filtered_df = filtered_df[filtered_df['device_name'] == selected_device]

            if not filtered_df.empty and selected_metric: # Check selected_metric is not empty string
                if selected_metric in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[selected_metric]):
                    # Check if 'device_name' exists and is useful for color before using it
                    if 'device_name' in filtered_df.columns and selected_device == 'All' and not filtered_df['device_name'].isnull().all():
                        fig = px.line(filtered_df, x='timestamp', y=selected_metric, title=f'{selected_metric} Trend', color='device_name')
                    else:
                        fig = px.line(filtered_df, x='timestamp', y=selected_metric, title=f'{selected_metric} Trend')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Cannot plot '{selected_metric}'. It might be non-numeric or missing for the selected device.")
            else:
                st.info("No data for the selected device/metric.")
        else:
            st.warning("No health data available.")

    # --- Insights & Alerts Mode ---
    elif dashboard_mode == "Insights & Alerts":
        st.header("Your Health Insights and Alerts")

        if not insights_df.empty:
            st.subheader("Filter Insights")
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            # Ensure device_name exists and is not all null for selectbox options
            insight_device_options = ['All']
            if 'device_name' in insights_df.columns and not insights_df['device_name'].isnull().all():
                insight_device_options.extend(list(insights_df['device_name'].unique()))
            filter_device = col_filter1.selectbox("Filter by Device", options=insight_device_options, key='filter_device_insights')
            
            filter_status = col_filter2.selectbox("Filter by Status", options=['All', 'Unread', 'Read'], key='filter_status_insights')
            filter_severity = col_filter3.selectbox("Filter by Severity", options=['All', 'low', 'moderate', 'high'], key='filter_severity_insights')

            filtered_insights = insights_df.copy()
            if filter_device != 'All':
                filtered_insights = filtered_insights[filtered_insights['device_name'] == filter_device]
            if filter_status == 'Unread':
                filtered_insights = filtered_insights[filtered_insights['is_read'] == False]
            elif filter_status == 'Read':
                filtered_insights = filtered_insights[filtered_insights['is_read'] == True]
            if filter_severity != 'All':
                filtered_insights = filtered_insights[filtered_insights['severity'] == filter_severity]

            st.subheader(f"Displaying {len(filtered_insights)} Insights:")

            if not filtered_insights.empty:
                # Ensure required columns for display exist
                required_insight_cols = ['insight_id', 'timestamp', 'device_name', 'anomaly_type', 'insight_text', 'severity', 'is_read']
                if not all(col in filtered_insights.columns for col in required_insight_cols):
                    st.error("Missing essential columns in insights data for display. Check DB schema and fetch functions.")
                else:
                    for i, row in filtered_insights.iterrows():
                        button_key = f"mark_read_{row['insight_id']}"
                        
                        card_style = ""
                        if not row['is_read']:
                            card_style = "background-color: #fff3cd; border-left: 5px solid orange; padding: 10px; margin-bottom: 10px; border-radius: 5px;"
                        else:
                            card_style = "background-color: #f8f9fa; border-left: 5px solid #007bff; padding: 10px; margin-bottom: 10px; border-radius: 5px;"

                        with st.container(border=True):
                            st.markdown(f"<div style='{card_style}'>", unsafe_allow_html=True)
                            st.write(f"**Device:** {row['device_name']}")
                            st.write(f"**Timestamp:** {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**Anomaly Type:** `{row['anomaly_type']}`")
                            st.markdown(f"**Insight:** {row['insight_text']}")
                            st.write(f"**Severity:** :red[{row['severity'].upper()}]" if row['severity'] == 'high' else f"**Severity:** :orange[{row['severity'].upper()}]" if row['severity'] == 'moderate' else f"**Severity:** {row['severity'].upper()}")
                            
                            if row['is_read']:
                                if st.button("Mark as Unread", key=button_key, on_click=update_insight_status, args=(row['insight_id'], False)):
                                    pass
                            else:
                                if st.button("Mark as Read", key=button_key, type="primary", on_click=update_insight_status, args=(row['insight_id'], True)):
                                    pass
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("---")
            else:
                st.info("No insights match your current filters.")
        else:
            st.info("No insights have been generated yet.")