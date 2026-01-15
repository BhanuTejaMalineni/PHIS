# phiss_project/simulate_wearable_data.py (UPDATED)

import pandas as pd
import time
import random
import os
import json
import requests # New: for making HTTP requests

# --- Configuration ---
DATA_SOURCE_PATH = "/Users/bhanutejamalineni/phis_project/combined_data_for_simulation.csv"
SIMULATION_INTERVAL_SECONDS = 3 # Matching your desired interval
MAX_VARIABILITY = 0.02
BACKEND_URL = 'http://127.0.0.1:5001/health_metrics' # New: URL of your Flask endpoint

# --- Function to generate simulated data ---
def generate_simulated_data(df, start_index=0):
    """
    Generator that yields one data point from the DataFrame at a time,
    with added minor random variability to numerical fields.
    """
    for i in range(start_index, len(df)):
        row = df.iloc[i].to_dict()

        # Add minor variability to numerical fields (excluding timestamp and Athlete_ID)
        for key, value in row.items():
            if isinstance(value, (int, float)) and key not in ['timestamp', 'Athlete_ID']:
                variability = 1 + (random.uniform(-MAX_VARIABILITY, MAX_VARIABILITY))
                row[key] = value * variability
                # Ensure values stay positive and within reasonable bounds if needed
                if key == 'heart_rate':
                    row[key] = max(30, min(220, int(row[key])))
                elif key == 'steps':
                    row[key] = max(0, int(row[key]))
                elif key == 'body_temperature':
                    row[key] = round(max(35.0, min(42.0, row[key])), 1) # Body temp bounds
                elif key == 'blood_oxygen':
                    row[key] = max(90, min(100, int(row[key]))) # Blood oxygen bounds

        # Convert timestamp to ISO format string for easy transfer (e.g., JSON)
        if 'timestamp' in row and isinstance(row['timestamp'], pd.Timestamp):
            row['timestamp'] = row['timestamp'].isoformat()

        yield row
        time.sleep(SIMULATION_INTERVAL_SECONDS)

# --- Main simulation logic ---
if __name__ == "__main__":
    print(f"Starting wearable data simulation. Data will be sent to {BACKEND_URL} every {SIMULATION_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop the simulation.")

    # Ensure the output directory exists
    output_dir = os.path.dirname(DATA_SOURCE_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- Preprocessing (to ensure the simulation source is ready) ---
    raw_data_path = 'data/raw'
    combined_df_for_sim = pd.DataFrame() # Initialize empty dataframe

    try:
        df1 = pd.read_csv(os.path.join(raw_data_path, 'First Dataset.csv'))
        df2 = pd.read_csv(os.path.join(raw_data_path, 'Second Dataset.csv'))

        def simple_preprocess(df, name):
            df_temp = df.copy()
            # Common renames - ADJUST THESE BASED ON YOUR ACTUAL DATASET COLUMNS
            # I'm inferring based on your simulation output
            if 'HeartRate' in df_temp.columns: df_temp = df_temp.rename(columns={'HeartRate': 'heart_rate'})
            elif 'heart_rate' not in df_temp.columns and 'heart_rate' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'heart_rate' for col in df_temp.columns if col.lower() == 'heart_rate'})

            if 'Steps' in df_temp.columns: df_temp = df_temp.rename(columns={'Steps': 'steps'})
            elif 'steps' not in df_temp.columns and 'steps' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'steps' for col in df_temp.columns if col.lower() == 'steps'})

            if 'BodyTemperature' in df_temp.columns: df_temp = df_temp.rename(columns={'BodyTemperature': 'body_temperature'})
            elif 'body_temperature' not in df_temp.columns and 'body_temperature' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'body_temperature' for col in df_temp.columns if col.lower() == 'body_temperature'})

            if 'BloodPressure' in df_temp.columns: df_temp = df_temp.rename(columns={'BloodPressure': 'blood_pressure'})
            elif 'blood_pressure' not in df_temp.columns and 'blood_pressure' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'blood_pressure' for col in df_temp.columns if col.lower() == 'blood_pressure'})

            if 'BloodOxygen' in df_temp.columns: df_temp = df_temp.rename(columns={'BloodOxygen': 'blood_oxygen'})
            elif 'blood_oxygen' not in df_temp.columns and 'blood_oxygen' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'blood_oxygen' for col in df_temp.columns if col.lower() == 'blood_oxygen'})

            if 'ActivityStatus' in df_temp.columns: df_temp = df_temp.rename(columns={'ActivityStatus': 'activity_status'})
            elif 'activity_status' not in df_temp.columns and 'activity_status' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'activity_status' for col in df_temp.columns if col.lower() == 'activity_status'})
            
            # Timestamp parsing based on your data:
            if 'Date' in df_temp.columns and 'Time' in df_temp.columns:
                df_temp['timestamp'] = pd.to_datetime(df_temp['Date'] + ' ' + df_temp['Time'])
            elif 'Timestamp' in df_temp.columns:
                df_temp['timestamp'] = pd.to_datetime(df_temp['Timestamp'])
            elif 'Date Time' in df_temp.columns:
                 df_temp['timestamp'] = pd.to_datetime(df_temp['Date Time'])
            # Assuming 'Athlete_ID' is consistent
            if 'Athlete_ID' not in df_temp.columns and 'athlete_id' in [col.lower() for col in df_temp.columns]:
                df_temp = df_temp.rename(columns={col: 'Athlete_ID' for col in df_temp.columns if col.lower() == 'athlete_id'})

            if 'timestamp' in df_temp.columns:
                df_temp = df_temp.sort_values('timestamp').reset_index(drop=True)

            # Select relevant columns ensuring Athlete_ID is also present for filtering
            # Ensure these match your HealthMetric model in app.py
            relevant_cols = [
                'timestamp', 'Athlete_ID', 'heart_rate', 'steps', 'body_temperature',
                'blood_pressure', 'blood_oxygen', 'activity_status'
            ]
            return df_temp[[col for col in relevant_cols if col in df_temp.columns]]
        
        df1_processed_for_sim = simple_preprocess(df1, 'First Dataset')
        df2_processed_for_sim = simple_preprocess(df2, 'Second Dataset')

        combined_df_for_sim = pd.concat([df1_processed_for_sim, df2_processed_for_sim], ignore_index=True)
        if 'timestamp' in combined_df_for_sim.columns:
            combined_df_for_sim = combined_df_for_sim.drop_duplicates(subset=['timestamp', 'Athlete_ID']).sort_values('timestamp').reset_index(drop=True)
        
        # Filter for a specific Athlete_ID for simulation as observed in your output
        TARGET_ATHLETE_ID = "ATH001" # This can be made configurable
        combined_df_for_sim = combined_df_for_sim[combined_df_for_sim['Athlete_ID'] == TARGET_ATHLETE_ID].reset_index(drop=True)
        print(f"Filtered data to simulate only for Athlete_ID: {TARGET_ATHLETE_ID} ({len(combined_df_for_sim)} rows out of original)")

        combined_df_for_sim.to_csv(DATA_SOURCE_PATH, index=False)
        print(f"Preprocessed data saved to {DATA_SOURCE_PATH}")

    except FileNotFoundError:
        print(f"FATAL ERROR: Raw data files not found in {raw_data_path}.")
        print(f"Please ensure 'First Dataset.csv' and 'Second Dataset.csv' are in the '{raw_data_path}' directory.")
        exit()
    except Exception as e:
        print(f"Error during initial preprocessing for simulation script: {e}")
        print(f"Attempting to load pre-existing data from {DATA_SOURCE_PATH}")
        try:
            combined_df_for_sim = pd.read_csv(DATA_SOURCE_PATH, parse_dates=['timestamp'])
            TARGET_ATHLETE_ID = "ATH001" # Default if not determined
            if 'Athlete_ID' in combined_df_for_sim.columns:
                 print(f"Loaded preprocessed data from {DATA_SOURCE_PATH} for Athlete_ID: {TARGET_ATHLETE_ID}")
            else:
                 print(f"Loaded preprocessed data from {DATA_SOURCE_PATH}")

        except FileNotFoundError:
            print(f"FATAL ERROR: No preprocessed data found at {DATA_SOURCE_PATH} and raw data loading failed.")
            exit()
        except Exception as e:
            print(f"FATAL ERROR: Could not load pre-existing data from {DATA_SOURCE_PATH}: {e}")
            exit()

    if combined_df_for_sim.empty:
        print("FATAL ERROR: No data available for simulation after preprocessing/loading.")
        exit()

    if 'timestamp' in combined_df_for_sim.columns:
        combined_df_for_sim['timestamp'] = pd.to_datetime(combined_df_for_sim['timestamp'])
    else:
        print("FATAL ERROR: 'timestamp' column is missing in the simulation data after loading.")
        exit()

    try:
        data_generator = generate_simulated_data(combined_df_for_sim)
        counter = 0
        for data_point in data_generator:
            try:
                # Send data to Flask backend
                response = requests.post(BACKEND_URL, json=data_point)
                if response.status_code == 201:
                    print(f"[{counter + 1}] Sent data for {data_point.get('Athlete_ID')} at {data_point.get('timestamp')}. Backend response: {response.json().get('message')}")
                else:
                    print(f"[{counter + 1}] Failed to send data for {data_point.get('Athlete_ID')} at {data_point.get('timestamp')}. Status: {response.status_code}, Response: {response.text}")
            except requests.exceptions.ConnectionError as ce:
                print(f"[{counter + 1}] Connection Error: Could not connect to Flask backend at {BACKEND_URL}. Is the backend running? Error: {ce}")
                time.sleep(10) # Wait a bit before retrying if connection is lost
                continue
            except Exception as e:
                print(f"[{counter + 1}] An error occurred while sending data: {e}")

            counter += 1
            if counter >= len(combined_df_for_sim):
                print("End of dataset reached. Simulation complete.")
                break

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")