import pandas as pd
import time
import random
from datetime import datetime, timedelta
import numpy as np
import requests # Import the requests library
import os # For checking file existence

# --- Configuration ---
# Adjust DATA_PATH relative to where your Jupyter notebook is located
# Assuming your notebook is in phis_project/scripts/
# And your data is in phis_project/data/raw/
DATA_PATH = "/Users/bhanutejamalineni/phis_project/data/raw" # Relative path to your data folder
DATASET_1_FILE = 'First Dataset.csv' # Device profiles
DATASET_2_FILE = 'Second Dataset.csv' # Physiological data patterns

# Flask Backend URL
# Ensure this matches the address where your Flask app is running
BACKEND_URL = "http://127.0.0.1:5000/health_data"

# Simulation parameters
SIMULATION_INTERVAL_SECONDS = 5
# Note: NUM_READINGS_PER_INTERVAL is not directly used in the current loop,
# but can be useful if you wanted to generate multiple readings per interval.

# --- Data Loading ---
print("--- Starting Data Loading ---")

# Construct full paths
full_path_dataset1 = os.path.join(DATA_PATH, DATASET_1_FILE)
full_path_dataset2 = os.path.join(DATA_PATH, DATASET_2_FILE)

# Load the first dataset (Device Profiles)
try:
    df_devices = pd.read_csv(full_path_dataset1)
    print(f"Loaded {DATASET_1_FILE} with {len(df_devices)} rows.")
    print("--- First Dataset Head (Device Profiles) ---")
    print(df_devices.head())
    print("--- First Dataset Columns (Device Profiles) ---")
    print(df_devices.columns.tolist())
except FileNotFoundError:
    print(f"Error: {DATASET_1_FILE} not found at {full_path_dataset1}")
    exit()
except Exception as e:
    print(f"Error loading {DATASET_1_FILE}: {e}")
    exit()


# Load the second dataset (Physiological Data Patterns)
try:
    df_physiology = pd.read_csv(full_path_dataset2)
    print(f"\nLoaded {DATASET_2_FILE} with {len(df_physiology)} rows.")
    print("--- Second Dataset Head (Physiological Data Patterns) ---")
    print(df_physiology.head())
    print("--- Second Dataset Columns (Physiological Data Patterns) ---")
    print(df_physiology.columns.tolist())
except FileNotFoundError:
    print(f"Error: {DATASET_2_FILE} not found at {full_path_dataset2}")
    exit()
except Exception as e:
    print(f"Error loading {DATASET_2_FILE}: {e}")
    exit()

# --- Data Preprocessing for Simulation ---
print("\nProcessing Second Dataset for physiological simulation patterns...")

# Define desired physiological columns for simulation
desired_physiological_columns = [
    'heart_rate', 'steps', 'calories', 'activity_level', 'sleep_duration',
    'oxygen_saturation', 'body_temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic'
]

# Rename columns for consistency (if needed) and select subset
# Example: If your df_physiology has 'Heart_Rate' and you want 'heart_rate'
column_mapping = {
    'Heart_Rate': 'heart_rate',
    'Step_Count': 'steps',
    # 'Calories' might need to be created if not present
    'Activity_Status': 'activity_level',
    # 'Sleep_Duration' might need to be created/simulated
    'Blood_Oxygen': 'oxygen_saturation',
    'Body_Temperature': 'body_temperature',
    # 'Blood_Pressure' needs splitting into systolic/diastolic
}

sim_physiology_data = df_physiology.copy()

# Apply column renaming
sim_physiology_data.rename(columns=column_mapping, inplace=True)

# Handle Blood_Pressure splitting if it exists
if 'Blood_Pressure' in sim_physiology_data.columns:
    bp_split = sim_physiology_data['Blood_Pressure'].str.split('/', expand=True)
    sim_physiology_data['blood_pressure_systolic'] = pd.to_numeric(bp_split[0], errors='coerce')
    sim_physiology_data['blood_pressure_diastolic'] = pd.to_numeric(bp_split[1], errors='coerce')
    sim_physiology_data.drop(columns=['Blood_Pressure'], inplace=True)

# Add 'calories' column if it doesn't exist (and fill with a default/random value)
if 'calories' not in sim_physiology_data.columns:
    sim_physiology_data['calories'] = np.random.randint(50, 300, size=len(sim_physiology_data))

# Add 'sleep_duration' if it doesn't exist
if 'sleep_duration' not in sim_physiology_data.columns:
    sim_physiology_data['sleep_duration'] = np.random.uniform(5.0, 9.0, size=len(sim_physiology_data))

# Ensure 'activity_level' is present, fill NaNs if necessary with a common value
if 'activity_level' not in sim_physiology_data.columns:
    sim_physiology_data['activity_level'] = 'unknown' # Default if not in dataset
sim_physiology_data['activity_level'] = sim_physiology_data['activity_level'].fillna('unknown')

# Select only the desired columns for simulation patterns
sim_physiology_data = sim_physiology_data[desired_physiological_columns].copy()

# Fill any remaining NaNs in numeric columns with reasonable defaults
# And convert to appropriate types for robustness
for col in desired_physiological_columns:
    if col in sim_physiology_data.columns:
        if sim_physiology_data[col].dtype == 'object' and col != 'activity_level': # Handle non-numeric objects (e.g., if blood pressure split failed)
            print(f"Warning: Column '{col}' is still object type after processing. Attempting to convert to numeric.")
            sim_physiology_data[col] = pd.to_numeric(sim_physiology_data[col], errors='coerce')

        if pd.api.types.is_numeric_dtype(sim_physiology_data[col]):
            if col == 'heart_rate':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.randint(60, 100)).astype(int)
            elif col == 'steps':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.randint(0, 500)).astype(int)
            elif col == 'calories':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.randint(50, 300)).astype(int)
            elif col == 'sleep_duration':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.uniform(5.0, 9.0)).astype(float)
            elif col == 'oxygen_saturation':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.uniform(95.0, 99.0)).astype(float)
            elif col == 'body_temperature':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.uniform(36.0, 37.5)).astype(float)
            elif col == 'blood_pressure_systolic':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.randint(100, 130)).astype(int)
            elif col == 'blood_pressure_diastolic':
                sim_physiology_data[col] = sim_physiology_data[col].fillna(random.randint(60, 85)).astype(int)
        elif col == 'activity_level':
            sim_physiology_data[col] = sim_physiology_data[col].fillna(random.choice(['sedentary', 'light', 'moderate', 'active']))

# Final check for empty dataframes after processing
if sim_physiology_data.empty:
    print("Critical Error: Second Dataset is empty or failed to load/process. Cannot simulate physiological data patterns.")
    exit()

if df_devices.empty:
    print("Critical Error: First Dataset is empty or failed to load. Cannot simulate device profiles.")
    exit()

print(f"Prepared physiological data patterns with {len(sim_physiology_data)} rows.")
print("--- Physiological Data Patterns Head for Simulation ---")
print(sim_physiology_data.head())
print("--- Physiological Data Patterns Columns ---")
print(sim_physiology_data.columns.tolist())


# --- Simulation Loop ---
print("\nStarting comprehensive data simulation (press Ctrl+C to stop)...")
current_time = datetime.now()

try:
    while True:
        simulated_reading = {}

        # 1. Randomly pick a device profile
        random_device_profile = df_devices.sample(n=1).iloc[0]
        
        # Add device metadata to the simulated reading
        simulated_reading['device_name'] = random_device_profile['Device_Name']
        simulated_reading['brand'] = random_device_profile['Brand']
        simulated_reading['model'] = random_device_profile['Model']
        
        # Get accuracy for potential modulation
        # Ensure these columns exist in your df_devices (adjust names if needed)
        hr_accuracy = random_device_profile.get('Heart_Rate_Accuracy_Percent', 100) / 100
        steps_accuracy = random_device_profile.get('Step_Count_Accuracy_Percent', 100) / 100

        # 2. Randomly pick a physiological pattern
        random_physiology_pattern = sim_physiology_data.sample(n=1).iloc[0]

        # 3. Combine and (optionally) modulate physiological data based on device accuracy
        simulated_reading['timestamp'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        for col in desired_physiological_columns:
            value = random_physiology_pattern[col]
            
            # Apply some noise based on device accuracy (simplified for demonstration)
            if col == 'heart_rate' and hr_accuracy < 1.0 and pd.notna(value):
                noise_range = (1 - hr_accuracy) * value * 0.5 # Up to 50% of the inaccuracy margin as noise
                value = value + random.uniform(-noise_range, noise_range)
                value = max(0, int(round(value))) # Ensure non-negative and integer
            elif col == 'steps' and steps_accuracy < 1.0 and pd.notna(value):
                noise_range = (1 - steps_accuracy) * value * 0.5
                value = value + random.uniform(-noise_range, noise_range)
                value = max(0, int(round(value))) # Ensure non-negative and integer
            elif pd.isna(value): # If value is NaN from physiology data even after initial fill
                if col == 'heart_rate': value = random.randint(60, 100)
                elif col == 'steps': value = random.randint(0, 500)
                elif col == 'calories': value = random.randint(50, 300)
                elif col == 'activity_level': value = random.choice(['sedentary', 'light', 'moderate', 'active'])
                elif col == 'sleep_duration': value = random.uniform(5.0, 9.0)
                elif col == 'oxygen_saturation': value = random.uniform(95.0, 99.0)
                elif col == 'body_temperature': value = random.uniform(36.0, 37.5)
                elif col == 'blood_pressure_systolic': value = random.randint(100, 130)
                elif col == 'blood_pressure_diastolic': value = random.randint(60, 85)
            
            # Convert numpy types to native Python types for JSON serialization
            if isinstance(value, np.integer):
                simulated_reading[col] = int(value)
            elif isinstance(value, np.floating):
                simulated_reading[col] = float(value)
            else:
                simulated_reading[col] = value
        
        print(f"Simulated Data: {simulated_reading}")
        
        # Send data to Flask backend
        try:
            response = requests.post(BACKEND_URL, json=simulated_reading)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            print(f"Data sent successfully! Status: {response.status_code}, Response: {response.json().get('msg')}")
        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Is the Flask backend running at {BACKEND_URL}?")
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Error: {err}, Response: {response.text}")
        except Exception as e:
            print(f"An unexpected error occurred while sending data: {e}")

        current_time += timedelta(seconds=SIMULATION_INTERVAL_SECONDS)
        time.sleep(SIMULATION_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nSimulation stopped by user.")
except Exception as e:
    print(f"An error occurred during simulation: {e}")