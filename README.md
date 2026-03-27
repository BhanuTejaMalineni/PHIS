# Proactive Health Insight System (PHIS)

**PHIS** is a fully local, privacy-preserving pipeline for wearable data analysis. It simulates health metrics (heart rate, steps, sleep, etc.), detects anomalies with ML (Z-score + Isolation Forest), generates insights, and visualizes via Streamlit dashboard—all without cloud [file:75].

[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-orange)](https://streamlit.io)

## 🎯 Objectives
- Simulate wearable data from Kaggle datasets (Wearable Health Device Performance + Sports Health Monitoring).
- Flask + PostgreSQL backend for storage.
- Per-device baselines, anomaly detection, rule-based insights.
- Interactive dashboard with Plotly charts [file:75].

## 🛠️ Tech Stack
| Layer | Technologies |
|-------|--------------|
| Backend | Flask, PostgreSQL, psycopg2 |
| ML | scikit-learn (Isolation Forest, Z-score) |
| Dashboard | Streamlit, Plotly |
| Data | Pandas, NumPy |
| Other | python-dotenv, requests [file:75] |

## 🚀 Quick Start
1. Clone: `git clone https://github.com/[yourusername]/phis_project.git`
2. Env: `conda create -n phis python=3.9 && conda activate phis`
3. Deps: `pip install -r requirements.txt`
4. Setup DB (PostgreSQL): Update `.env`, create `healthdata`/`insights` tables.
5. Run:

streamlit run dashboard.py # Dashboard
python app.py # Backend
jupyter notebook # Simulator/ML notebook


Demo: Insights on anomalies like "High heart rate above baseline" [file:75].

## 📊 Key Results
- Processed 410k+ simulated records across 15 devices (e.g., Apple Watch, WHOOP).
- Generated 1,285+ insights (e.g., low sleep + high HR stress patterns).
- Local end-to-end latency: 2-3s [file:75].

| Metric | Value |
|--------|-------|
| Records | 410,380 |
| Insights | 1,285 |
| Anomaly Rate | ~1% [file:75] |

## 🗂️ Structure

phis_project/
├── README.md
├── .gitignore
├── requirements.txt
├── app.py # Flask backend
├── .env.example
├── notebooks/ # Simulator + ML
├── dashboard.py # Streamlit
└── data/ # Processed Kaggle CSVs

## 📖 Background
Capstone for MSc Software Engineering, University of Europe for Applied Sciences. Addresses cloud/privacy issues in wearables with local ML insights. **Author: Bhanu Teja Malineni** (btm portfolio) [file:75].

## 🔮 Future Work
- Real wearable APIs (Fitbit/Garmin).
- LSTM/Transformers for time-series.
- Docker deployment [file:75].

## 📄 License
MIT. See your report appendices for full schema/code snippets [file:75].

