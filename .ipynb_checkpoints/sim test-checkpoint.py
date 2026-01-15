import pandas as pd
import time
import random
from datetime import datetime, timedelta
import re # Import regex for blood pressure parsing

# --- Configuration ---
DATA_PATH = "/Users/bhanutejamalineni/phis_project/data/raw/" # Relative path to your data folder
# Only keeping the second dataset as the primary source for actual sensor data
DATASET_TO_USE_FILE = 'Second Dataset.csv' # CONFIRM EXACT FILENAME

# Simulation parameters
SIMULATION_INTERVAL_SECONDS = 5 # How often to simulate a new data point
NUM_READINGS_PER_INTERVAL = 1 # How many rows to "stream" at each interval

# --- Load Dataset ---
df_source = pd.DataFrame() # Initialize as empty

try:
    df_source = pd.read_csv(DATA_PATH + DATASET_TO_USE_FILE)
    print(f"Loaded {DATASET_TO_USE_FILE} with {len(df_source)} rows.")
    print("--- Dataset Head ---")
    print(df_source.head())
    print("--- Dataset Columns ---")
    print(df_source.columns.tolist())
    # Convert column names to lowercase, replace spaces with underscores for easier access
    df_source.columns = df_source.columns.str.lower().str.replace(' ', '_')

except FileNotFoundError:
    print(f"Error: {DATASET_TO_USE_FILE} not found. Please ensure it's in the '{DATA_PATH}' directory.")
    exit() # Exit if the critical dataset isn't found
except Exception as e:
    print(f"Error loading {DATASET_TO_USE_FILE}: {e}")
    exit() # Exit on other loading errors

if df_source.empty:
    print("Error: Loaded DataFrame is empty. Exiting simulation.")
    exit()

print(f"\nProcessing DataFrame for simulation...")
temp_df = pd.DataFrame() # Start with an empty temp DataFrame

# --- Define desired output columns and their mapping from original dataset ---
# This list specifies the final columns we want in our simulated data
desired_output_columns = {
    'heart_rate': ['heart_rate', 'hr'],
    'steps': ['step_count', 'steps'], # From df_source.columns: 'step_count'
    'body_temperature': ['body_temperature', 'temp'], # From df_source.columns: 'body_temperature'
    'oxygen_saturation': ['blood_oxygen', 'spo2', 'oxygen_saturation'], # From df_source.columns: 'blood_oxygen'
    'activity_level': ['activity_status', 'activity_level'], # From df_source.columns: 'activity_status'
    'blood_pressure': ['blood_pressure'], # Special handling for this string column
    'calories': None, # To be derived or filled
    'sleep_duration': None # To be filled randomly
}

# Iterate through desired output columns and populate temp_df
for desired_col, possible_names in desired_output_columns.items():
    if possible_names: # If there are possible names to map
        found_col = None
        for name in possible_names:
            if name in df_source.columns:
                found_col = name
                break
        
        if found_col:
            temp_df[desired_col] = df_source[found_col]
        else:
            # If column is explicitly specified but not found, initialize with NA
            temp_df[desired_col] = pd.NA
    else: # If possible_names is None, it means it's a derived/filled column
        temp_df[desired_col] = pd.NA

# --- Special Handling for Blood_Pressure ---
if 'blood_pressure' in temp_df.columns:
    # Function to parse blood pressure string (e.g., "120/80")
    def parse_blood_pressure(bp_str):
        if pd.isna(bp_str):
            return pd.NA, pd.NA
        match = re.match(r'(\d+)/(\d+)', str(bp_str))
        if match:
            return int(match.group(1)), int(match.group(2))
        return pd.NA, pd.NA

    temp_df[['blood_pressure_systolic', 'blood_pressure_diastolic']] = \
        temp_df['blood_pressure'].apply(lambda x: pd.Series(parse_blood_pressure(x)))
    temp_df.drop(columns=['blood_pressure'], inplace=True) # Drop the original string column
else:
    # If blood_pressure column wasn't even initialized, create the new ones
    temp_df['blood_pressure_systolic'] = pd.NA
    temp_df['blood_pressure_diastolic'] = pd.NA


# --- Fill missing columns with sensible defaults/derivations ---
# Iterate through the columns that are currently NA or need derivation
for col in ['calories', 'sleep_duration', 'heart_rate', 'steps', 'body_temperature',
            'oxygen_saturation', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'activity_level']:
    if col not in temp_df.columns or temp_df[col].isnull().all():
        if col == 'calories':
            # A simple heuristic: calories = steps * factor + base
            if 'steps' in temp_df.columns:
                # Fill NA steps first to avoid error in calculation
                temp_df['steps'] = temp_df['steps'].fillna(0)
                temp_df[col] = temp_df[col].fillna(temp_df['steps'] * 0.04 + 50) # Example factor
            else:
                temp_df[col] = temp_df[col].fillna(random.randint(50, 300))
        elif col == 'sleep_duration':
            temp_df[col] = temp_df[col].fillna(random.uniform(5.0, 9.0))
        elif col == 'heart_rate':
            temp_df[col] = temp_df[col].fillna(random.randint(60, 100))
        elif col == 'steps':
            temp_df[col] = temp_df[col].fillna(random.randint(0, 500))
        elif col == 'body_temperature':
            temp_df[col] = temp_df[col].fillna(random.uniform(36.0, 37.5))
        elif col == 'oxygen_saturation':
            temp_df[col] = temp_df[col].fillna(random.uniform(95.0, 99.0))
        elif col == 'blood_pressure_systolic':
            temp_df[col] = temp_df[col].fillna(random.randint(100, 130))
        elif col == 'blood_pressure_diastolic':
            temp_df[col] = temp_df[col].fillna(random.randint(60, 85))
        elif col == 'activity_level':
            temp_df[col] = temp_df[col].fillna(random.choice(['sedentary', 'light', 'moderate', 'active']))

# Ensure all numeric columns are of numeric type for later ML processing
numeric_cols = ['heart_rate', 'steps', 'calories', 'sleep_duration',
                'oxygen_saturation', 'body_temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic']
for col in numeric_cols:
    if col in temp_df.columns:
        # Convert to numeric, coercing errors to NaN, then fill remaining NaNs with mean or default
        temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce')
        if temp_df[col].isnull().any():
            if not temp_df[col].dropna().empty: # Fill with mean if some values exist
                temp_df[col] = temp_df[col].fillna(temp_df[col].mean())
            else: # Otherwise, fill with a hardcoded default (as a last resort)
                if col == 'heart_rate': temp_df[col] = temp_df[col].fillna(75)
                elif col == 'steps': temp_df[col] = temp_df[col].fillna(200)
                elif col == 'calories': temp_df[col] = temp_df[col].fillna(150)
                # ... add other specific defaults
                else: temp_df[col] = temp_df[col].fillna(0) # Generic numeric default


# Final check before simulation
master_df = temp_df.copy()

if master_df.empty or len(master_df) == 0:
    print("\nCritical Error: Master DataFrame is empty after all processing. Exiting.")
    exit()

print(f"\nPrepared master DataFrame with {len(master_df)} rows for simulation.")
print("--- Master DataFrame Head for Simulation ---")
print(master_df.head())
print("--- Master DataFrame Columns ---")
print(master_df.columns.tolist())


# --- Simulation Loop ---
print("\nStarting data simulation (press Ctrl+C to stop)...")
current_time = datetime.now()
data_index = 0

try:
    while True:
        readings_to_simulate = []
        for _ in range(NUM_READINGS_PER_INTERVAL):
            if data_index >= len(master_df):
                data_index = 0 # Loop back to start if we run out of data
            
            simulated_row = master_df.iloc[data_index].copy()
            simulated_row['timestamp'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

            readings_to_simulate.append(simulated_row.to_dict())
            data_index += 1
        
        for reading in readings_to_simulate:
            print(f"Simulated Data: {reading}")
            # In Phase 2, this is where you would send 'reading' to your Flask/FastAPI backend

        current_time += timedelta(seconds=SIMULATION_INTERVAL_SECONDS)
        time.sleep(SIMULATION_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nSimulation stopped by user.")
except Exception as e:
    print(f"An error occurred during simulation: {e}")