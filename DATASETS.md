# DATASETS

This project uses two public Kaggle datasets for wearable health analytics and simulation.

---

# 1. Wearable Health Device Performance Data 2025

## Description

Dataset containing:
- wearable device specifications
- performance scores
- battery metrics
- heart-rate accuracy
- sleep-tracking accuracy
- device metadata

Used in PHIS for:
- device profile simulation
- dashboard metadata
- wearable benchmarking

## Source

:contentReference[oaicite:2]{index=2}

---

# 2. Wearable Sports Health Monitoring Dataset

## Description

Dataset containing:
- heart rate
- steps
- calories
- sleep duration
- oxygen saturation
- body temperature
- blood pressure

Used in PHIS for:
- physiological time-series simulation
- anomaly detection
- baseline modeling
- insight generation

## Source

:contentReference[oaicite:3]{index=3}

---

# Dataset Storage

Recommended structure:

```text
data/
├── raw/
└── processed/
```

---

# Notes

- Raw datasets are excluded from the repository.
- Download datasets manually from Kaggle.
- Processed outputs can be regenerated using preprocessing notebooks.