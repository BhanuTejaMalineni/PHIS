CREATE TABLE IF NOT EXISTS insights (
    insight_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    device_name VARCHAR(255),
    metric_involved VARCHAR(100),
    anomaly_type VARCHAR(100), -- e.g., 'high_hr', 'low_steps', 'overall_if'
    insight_text TEXT,
    severity VARCHAR(50), -- e.g., 'low', 'moderate', 'high'
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add an index for faster querying by timestamp and device
CREATE INDEX IF NOT EXISTS idx_insights_timestamp ON insights (timestamp);
CREATE INDEX IF NOT EXISTS idx_insights_device ON insights (device_name);