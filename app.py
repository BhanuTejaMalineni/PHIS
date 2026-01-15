# PHIS_Project/backend/app.py

from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path='/Users/bhanutejamalineni/phis_project/backend/.env') # Adjust this path if your .env is elsewhere

app = Flask(__name__)

# Database connection details from environment variables
DB_NAME = os.getenv("DB_NAME", "phis_db")
DB_USER = os.getenv("DB_USER", "phis_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "70403") # Use your actual password
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

@app.route('/')
def index():
    return "PHIS Backend is running!"

@app.route('/health_data', methods=['POST'])
def receive_health_data():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()
    print(f"Received data: {data}") # Log incoming data

    # Prepare data for insertion (handle potential missing keys and type conversions)
    try:
        timestamp = data.get('timestamp')
        device_name = data.get('device_name')
        brand = data.get('brand')
        model = data.get('model')
        heart_rate = int(data['heart_rate']) if data.get('heart_rate') is not None else None
        steps = int(data['steps']) if data.get('steps') is not None else None
        calories = int(data['calories']) if data.get('calories') is not None else None
        activity_level = data.get('activity_level')
        sleep_duration = float(data['sleep_duration']) if data.get('sleep_duration') is not None else None
        oxygen_saturation = float(data['oxygen_saturation']) if data.get('oxygen_saturation') is not None else None
        body_temperature = float(data['body_temperature']) if data.get('body_temperature') is not None else None
        blood_pressure_systolic = int(data['blood_pressure_systolic']) if data.get('blood_pressure_systolic') is not None else None
        blood_pressure_diastolic = int(data['blood_pressure_diastolic']) if data.get('blood_pressure_diastolic') is not None else None

        # Insert into database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO health_data (timestamp, device_name, brand, model, heart_rate, steps, calories,
                                     activity_level, sleep_duration, oxygen_saturation, body_temperature,
                                     blood_pressure_systolic, blood_pressure_diastolic)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (timestamp, device_name, brand, model, heart_rate, steps, calories,
             activity_level, sleep_duration, oxygen_saturation, body_temperature,
             blood_pressure_systolic, blood_pressure_diastolic)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"msg": "Data received and saved successfully!", "data": data}), 201

    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"msg": "Error processing data", "error": str(e)}), 400

if __name__ == '__main__':
    # For development, you can run directly. For production, use a WSGI server.
    app.run(debug=True, port=5000)