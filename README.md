# 🌐 CLIMA — Climate Risk Intelligence Platform

> "Weather happens to everyone. Only you'll know what it means."

A real-time AI platform that predicts weather-driven logistics 
disruptions across Indian supply chains — 72 hours before they happen.

---

## 🚨 The Problem

India loses ₹15,000+ crore annually to weather-driven 
logistics disruptions. Logistics managers check weather apps 
manually, guess delivery timelines, and react after delays happen.

CLIMA predicts disruptions BEFORE they happen — 
and tells you exactly what they'll cost.

---

## ✅ What CLIMA Does

- Ingests live weather + AQI data from 5 cities every hour
- Predicts route-level delay probability 72 hours ahead
- Calculates financial impact in ₹ for each disruption
- Suggests optimal alternative routes automatically  
- Sends Telegram morning briefings to logistics teams
- Monitors news for real-time disruption events (NLP)
- Auto-retrains when data patterns shift

---

## 🛣️ Routes Covered

| Route | Highway | Distance | Avg Transit |
|-------|---------|----------|-------------|
| Bengaluru → Mumbai | NH48 | 984 km | 18 hrs |
| Bengaluru → Chennai | NH48 | 346 km | 6 hrs |
| Bengaluru → Hyderabad | NH44 | 574 km | 10 hrs |
| Bengaluru → Pune | NH48 | 840 km | 15 hrs |
| Bengaluru → Delhi | NH44 | 2150 km | 40 hrs |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Ingestion | Python, WAQI API, OpenWeatherMap |
| Stream Processing | APScheduler, GitHub Actions |
| ML Models | PyTorch LSTM, XGBoost |
| Risk Engine | Custom scoring algorithm |
| API | FastAPI |
| Dashboard | Streamlit, Folium, Plotly |
| Alerts | Telegram Bot API |
| Monitoring | Evidently AI |
| Deployment | Docker, Render |

---

## 📈 Current Status

- [x] Live weather + AQI data ingestion (5 cities)
- [x] GitHub Actions automated hourly collection
- [x] Data preprocessing pipeline
- [x] Route database (5 major routes)
- [x] Risk scoring engine with financial impact
- [ ] LSTM forecasting model
- [ ] FastAPI deployment
- [ ] Streamlit dashboard
- [ ] Telegram alert bot
- [ ] News NLP disruption detection
- [ ] Docker + cloud deployment

---

## 👤 Author

**Sumith Hiremath**  
B.E. AI & ML — SSIT Tumkur  
GitHub: sumithhiremath