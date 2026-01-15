CREATE TABLE IF NOT EXISTS health_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    device_name VARCHAR(255),
    brand VARCHAR(255),
    model VARCHAR(255),
    heart_rate INTEGER,
    steps INTEGER,
    calories INTEGER,
    activity_level VARCHAR(50),
    sleep_duration NUMERIC(5,2),
    oxygen_saturation NUMERIC(4,1),
    body_temperature NUMERIC(4,2),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER
);