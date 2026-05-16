import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration & Database Connection ---
load_dotenv(dotenv_path='/Users/bhanutejamalineni/phis_project/backend/.env') # Path to your .env file

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

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

@st.cache_data(ttl=60) # Cache data for 60 seconds to avoid constant DB queries
def fetch_health_data_from_db():
    """Fetches all health data from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM health_data ORDER BY timestamp DESC;") # Fetch most recent first
        data = cur.fetchall()
        cur.close()
        conn.close()
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error fetching health data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30) # Cache insights for 30 seconds
def fetch_insights_from_db():
    """Fetches all insights from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM insights ORDER BY created_at DESC;")
        data = cur.fetchall()
        cur.close()
        conn.close()
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    except Exception as e:
        st.error(f"Error fetching insights: {e}")
        return pd.DataFrame()

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
        st.success("Insight status updated.")
        st.cache_data.clear() # Clear cache to refetch updated insights
    except Exception as e:
        st.error(f"Error updating insight status: {e}")
        if conn:
            conn.close()

# --- Basic Authentication ---
def check_password():
    """Returns `True` if the user has entered the correct password."""
    # This is a very basic, hardcoded password check for prototype purposes.
    # In a real application, use a secure authentication system (e.g., OAuth, JWT).

    def password_entered():
        if st.session_state["password"] == "phis_user_pass": # You can change this password
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("😕 Password incorrect")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# --- Streamlit App Layout ---

if check_password():
    st.set_page_config(layout="wide", page_title="PHIS Dashboard")
    st.title("Proactive Health Insight System (PHIS) Dashboard 📈")

    # --- Sidebar ---
    st.sidebar.header("Navigation")
    dashboard_mode = st.sidebar.radio("Go to", ["Overview", "Raw Data Explorer", "Insights & Alerts"])

    # --- Data Fetching ---
    health_data_df = fetch_health_data_from_db()
    insights_df = fetch_insights_from_db()

    # --- Overview Mode ---
    if dashboard_mode == "Overview":
        st.header("Overview: Current Status & Key Metrics")

        if health_data_df.empty:
            st.warning("No health data available. Please ensure the simulator and backend are running.")
        else:
            latest_data = health_data_df.sort_values(by='timestamp', ascending=False).iloc[0]
            st.subheader("Latest Readings:")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Heart Rate", f"{latest_data.get('heart_rate', 'N/A')} bpm")
            col2.metric("Steps", f"{latest_data.get('steps', 'N/A')}")
            col3.metric("Calories", f"{latest_data.get('calories', 'N/A')} kcal")
            col4.metric("Sleep Duration", f"{latest_data.get('sleep_duration', 'N/A') or 'N/A'} hrs")
            col5.metric("Oxygen Saturation", f"{latest_data.get('oxygen_saturation', 'N/A') or 'N/A'} %")

            st.subheader("Recent Trends (Last 24 Hours)")
            
            # Filter for last 24 hours
            time_ago = datetime.now() - timedelta(hours=24)
            recent_data = health_data_df[health_data_df['timestamp'] >= time_ago]

            if not recent_data.empty:
                # Plot Heart Rate
                fig_hr = px.line(recent_data, x='timestamp', y='heart_rate', title='Heart Rate Trend', color='device_name')
                st.plotly_chart(fig_hr, use_container_width=True)

                # Plot Steps
                fig_steps = px.line(recent_data, x='timestamp', y='steps', title='Steps Trend', color='device_name')
                st.plotly_chart(fig_steps, use_container_width=True)
            else:
                st.info("Not enough recent data for trend analysis. Keep the simulator running!")

        st.subheader("Recent Insights Summary")
        if not insights_df.empty:
            unread_insights = insights_df[insights_df['is_read'] == False]
            if not unread_insights.empty:
                st.warning(f"You have {len(unread_insights)} unread insights!")
                st.dataframe(unread_insights[['timestamp', 'device_name', 'anomaly_type', 'insight_text', 'severity']], use_container_width=True)
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
            selected_device = st.selectbox("Select Device", options=['All'] + list(health_data_df['device_name'].unique()))
            selected_metric = st.selectbox("Select Metric", options=['heart_rate', 'steps', 'calories', 'sleep_duration', 'oxygen_saturation', 'body_temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic'])

            filtered_df = health_data_df.copy()
            if selected_device != 'All':
                filtered_df = filtered_df[filtered_df['device_name'] == selected_device]

            if not filtered_df.empty:
                fig = px.line(filtered_df, x='timestamp', y=selected_metric, title=f'{selected_metric} Trend', color='device_name' if selected_device == 'All' else None)
                st.plotly_chart(fig, use_container_width=True)
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
            filter_device = col_filter1.selectbox("Filter by Device", options=['All'] + list(insights_df['device_name'].unique()), key='filter_device_insights')
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
                # Display insights with a button to mark as read
                for i, row in filtered_insights.iterrows():
                    # Create a unique key for each button to avoid Streamlit errors
                    button_key = f"mark_read_{row['insight_id']}"
                    
                    # Highlight unread insights
                    card_style = ""
                    if not row['is_read']:
                        card_style = "background-color: #fff3cd; border-left: 5px solid orange; padding: 10px; margin-bottom: 10px; border-radius: 5px;"
                    else:
                        card_style = "background-color: #f8f9fa; border-left: 5px solid #007bff; padding: 10px; margin-bottom: 10px; border-radius: 5px;"

                    with st.container(border=True): # Use st.container for better visual grouping
                        st.markdown(f"<div style='{card_style}'>", unsafe_allow_html=True)
                        st.write(f"**Device:** {row['device_name']}")
                        st.write(f"**Timestamp:** {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Anomaly Type:** `{row['anomaly_type']}`")
                        st.markdown(f"**Insight:** {row['insight_text']}")
                        st.write(f"**Severity:** :red[{row['severity'].upper()}]" if row['severity'] == 'high' else f"**Severity:** :orange[{row['severity'].upper()}]" if row['severity'] == 'moderate' else f"**Severity:** {row['severity'].upper()}")
                        
                        # Mark as Read/Unread button
                        if row['is_read']:
                            if st.button("Mark as Unread", key=button_key):
                                update_insight_status(row['insight_id'], False)
                                st.rerun()
                        else:
                            if st.button("Mark as Read", key=button_key, type="primary"):
                                update_insight_status(row['insight_id'], True)
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---") # Separator between insights
            else:
                st.info("No insights match your current filters.")
        else:
            st.info("No insights have been generated yet.")