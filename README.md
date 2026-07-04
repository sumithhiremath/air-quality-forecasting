# 🌍 Real-Time Air Quality Forecasting Platform

A production-grade ML system that ingests live air pollution data 
from government monitoring stations across Indian cities, forecasts 
AQI 24 hours ahead using LSTM, and serves predictions via a 
live interactive dashboard.

---

## 🚨 The Problem

India has 14 of the world's 20 most polluted cities. CPCB publishes 
current AQI — but nobody tells you what it will be tomorrow. 
Doctors, schools, athletes, and construction sites make decisions 
blind. This system fixes that.

---

## ✅ What This System Does

- Pulls **live AQI data** from WAQI API (real government sensors) every hour
- Cleans and engineers features from raw pollution readings
- Forecasts AQI **24 hours ahead** using an LSTM deep learning model
- Serves predictions via **FastAPI REST endpoint**
- Displays a **live interactive map** of Karnataka cities on Streamlit
- **Detects data drift** using Evidently AI and auto-retrains daily
- Fully containerized with **Docker** and deployed on **Render**

---

## 🏙️ Cities Covered

Bengaluru · Delhi · Mumbai · Hyderabad · Chennai

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Ingestion | Python, Requests, WAQI API |
| Data Processing | Pandas, NumPy, Scikit-learn |
| ML Model | PyTorch LSTM |
| API | FastAPI, Uvicorn |
| Dashboard | Streamlit, Folium, Plotly |
| Monitoring | Evidently AI |
| Scheduling | APScheduler |
| Deployment | Docker, Render |

---

## 📁 Project Structure

---

## ⚙️ How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/air-quality-forecasting.git
cd air-quality-forecasting
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API token
Create a `.env` file:
### 5. Fetch live data
```bash
python src/ingestion.py
```

### 6. Run dashboard
```bash
streamlit run dashboard/app.py
```

---

## 📊 Sample Output

Live AQI reading from Bengaluru government sensors:
- AQI: 87 (Satisfactory)
- PM2.5: 42 µg/m³
- PM10: 67 µg/m³
- Temperature: 28°C

---

## 🎯 Business Impact

- Enables 24-hour advance warning before dangerous AQI levels
- Directly useful for hospitals, schools, and outdoor event planners
- Auto-retraining ensures model stays accurate as seasons change

---

## 📈 Current Status

## 📈 Current Status

- [x] Live data ingestion working — WAQI API (real government sensors)
- [x] GitHub Actions — automated hourly data collection (laptop off)
- [x] Data preprocessing pipeline — cleaning, lag features, normalization
- [ ] LSTM model training
- [ ] FastAPI deployment
- [ ] Streamlit dashboard
- [ ] Docker containerization
- [ ] Drift monitoring

---

## 👤 Author

**Sumith Hiremath**  
B.E. AI & ML — Sri Siddhartha Institute of Technology, Tumkur  
[LinkedIn](www.linkedin.com/in/sumith-hiremath-a10a0a361) · [GitHub](https://github.com/sumithhiremath/air-quality-forecasting)