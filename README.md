# CLIMA — Climate Risk Intelligence Platform

> "Weather happens to everyone. Only you'll know what it means."

A real-time AI platform that predicts weather-driven logistics
disruptions across Indian supply chains — 72 hours before they happen.

---

## The Problem

India loses Rs.15,000+ crore annually to weather-driven
logistics disruptions. Logistics managers check weather apps
manually, guess delivery timelines, and react after delays happen.

CLIMA predicts disruptions BEFORE they happen —
and tells you exactly what they'll cost.

---

## What CLIMA Does

- Ingests live weather + AQI data from **6 cities** every hour
- Predicts route-level delay probability (rule-based engine, LSTM model in progress)
- Calculates financial impact in Rs. for each disruption
- Suggests optimal alternative routes automatically
- Sends Telegram morning briefings to logistics teams *(planned)*
- Monitors news for real-time disruption events via NLP *(planned)*
- Auto-retrains when data patterns shift *(planned)*

---

## Routes Covered

| Route | Highway | Distance | Avg Transit |
|-------|---------|----------|-------------|
| Bengaluru → Mumbai | NH48 | 984 km | 18 hrs |
| Bengaluru → Chennai | NH48 | 346 km | 6 hrs |
| Bengaluru → Hyderabad | NH44 | 574 km | 10 hrs |
| Bengaluru → Pune | NH48 | 840 km | 15 hrs |
| Bengaluru → Delhi | NH44 | 2150 km | 40 hrs |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Ingestion | Python, WAQI API |
| Stream Processing | APScheduler, GitHub Actions |
| ML Models | PyTorch LSTM, XGBoost *(in progress)* |
| Risk Engine | Custom rule-based scoring (v1), ML upgrade planned |
| API | FastAPI *(in progress)* |
| Dashboard | Streamlit, Folium, Plotly *(in progress)* |
| Alerts | Telegram Bot API *(planned)* |
| Monitoring | Evidently AI *(planned)* |
| Deployment | Docker, Render *(planned)* |

---

## Project Status (30-Day Build)

| Day | Status | What Was Done |
|-----|--------|---------------|
| Day 1 | ✅ Done | Project structure, folder layout, Git setup |
| Day 2 | ✅ Done | Live AQI ingestion via WAQI API (5 cities) |
| Day 3 | ✅ Done | Preprocessing pipeline, GitHub Actions hourly, risk engine, route database |
| **Day 4** | ✅ Done | **Bug fixes: Pune added, Mumbai sensor validation, encoding fix, GitHub Actions improved, all 5 routes now scoring** |
| Day 5 | 🔲 Next | Historical data backfill (WAQI 30-day), OpenWeatherMap integration |
| Day 6–9 | 🔲 | Data validation, XGBoost risk model training |
| Day 10–12 | 🔲 | PyTorch LSTM — architecture, training, 72h forecast |
| Day 13–14 | 🔲 | FastAPI endpoints + auth + Swagger UI |
| Day 15–18 | 🔲 | Streamlit dashboard — map, charts, live risk display |
| Day 19 | 🔲 | Telegram morning briefing bot |
| Day 20 | 🔲 | News NLP disruption detection |
| Day 21–22 | 🔲 | Evidently AI monitoring + auto-retrain pipeline |
| Day 23–24 | 🔲 | Docker + deploy to Render (free tier, live URL) |
| Day 25–30 | 🔲 | Testing, optimization, README overhaul, monetization |

---

## Running Locally

```bash
# 1. Clone
git clone https://github.com/sumithhiremath/air-quality-forecasting.git
cd air-quality-forecasting

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your WAQI API token
# Get free token at: https://aqicn.org/data-platform/token/
echo "WAQI_TOKEN=your_token_here" > .env

# 5. Run data ingestion (collects today's data)
python src/ingestion.py

# 6. Run live risk assessment
python src/risk/live_risk.py general
```

---

## Known Data Notes

- **Mumbai temperature**: The WAQI station for Mumbai returns an anomalous temperature value. The ingestion pipeline now automatically detects and rejects this bad reading — Mumbai weather data is flagged but AQI is still used.
- **Data volume**: Only a few weeks of data collected so far. LSTM training will begin once 30+ days of data is available.
- **GitHub Actions**: Hourly data collection runs automatically when `WAQI_TOKEN` is set as a repository secret.

---

## Author

**Sumith Hiremath**
B.E. AI & ML — SSIT Tumkur
GitHub: [@sumithhiremath](https://github.com/sumithhiremath)