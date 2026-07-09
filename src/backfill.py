# ─────────────────────────────────────────────────────────────
# CLIMA — Historical Data Backfill Script
# Source : Open-Meteo Air Quality & Weather Archive APIs
# Purpose: Pulls 30 days of hourly data to train LSTM/XGBoost
# ─────────────────────────────────────────────────────────────

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta

# Force UTF-8 encoding on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# City coordinates list from existing live data
CITIES = {
    "bengaluru": {
        "lat": 12.938539,
        "lon": 77.5901,
        "station": "Open-Meteo Archive (Hombegowda Nagar)"
    },
    "delhi": {
        "lat": 28.612498,
        "lon": 77.237388,
        "station": "Open-Meteo Archive (Major Dhyan Chand Stadium)"
    },
    "mumbai": {
        "lat": 19.072830,
        "lon": 72.882607,
        "station": "Open-Meteo Archive (US Consulate Mumbai)"
    },
    "hyderabad": {
        "lat": 17.384050,
        "lon": 78.456360,
        "station": "Open-Meteo Archive (US Consulate Hyderabad)"
    },
    "chennai": {
        "lat": 13.087840,
        "lon": 80.278473,
        "station": "Open-Meteo Archive (US Consulate Chennai)"
    },
    "pune": {
        "lat": 18.529603,
        "lon": 73.849586,
        "station": "Open-Meteo Archive (Shivajinagar)"
    }
}

def backfill_city_data(city: str, lat: float, lon: float, station: str, days: int = 30):
    print(f"\n🚀 Backfilling {city.upper()} for past {days} days...")
    
    # Calculate start and end date (YYYY-MM-DD)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)
    
    start_date_str = start_dt.strftime("%Y-%m-%d")
    end_date_str = end_dt.strftime("%Y-%m-%d")
    
    # 1. Fetch Air Quality Archive
    aq_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}&hourly=pm2_5,pm10,nitrogen_dioxide,"
        f"carbon_monoxide,ozone,sulphur_dioxide,us_aqi&"
        f"start_date={start_date_str}&end_date={end_date_str}"
    )
    
    # 2. Fetch Weather Archive
    weather_url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,"
        f"relative_humidity_2m,wind_speed_10m&"
        f"start_date={start_date_str}&end_date={end_date_str}"
    )
    
    try:
        print("  Downloading Air Quality Archive...")
        aq_res = requests.get(aq_url, timeout=15)
        aq_res.raise_for_status()
        aq_data = aq_res.json().get("hourly", {})
        
        print("  Downloading Weather Archive...")
        w_res = requests.get(weather_url, timeout=15)
        w_res.raise_for_status()
        w_data = w_res.json().get("hourly", {})
        
        # Check matching timestamps
        time_list = aq_data.get("time", [])
        if not time_list or len(time_list) != len(w_data.get("time", [])):
            print(f"  [ERROR] Time arrays mismatch or empty for {city}")
            return
            
        print(f"  Retrieved {len(time_list)} hourly records. Saving CSV files...")
        
        os.makedirs("data/raw", exist_ok=True)
        
        saved_count = 0
        for i in range(len(time_list)):
            raw_time_str = time_list[i] # YYYY-MM-DDTHH:MM
            dt = datetime.strptime(raw_time_str, "%Y-%m-%dT%H:%M")
            
            # Match schema:
            # city,station,aqi,pm25,pm10,no2,co,o3,so2,temperature,humidity,wind,
            # latitude,longitude,last_updated,fetched_at,data_quality_flags,quality_ok
            reading = {
                "city": city,
                "station": station,
                "aqi": float(aq_data["us_aqi"][i]) if aq_data["us_aqi"][i] is not None else 50.0,
                "pm25": float(aq_data["pm2_5"][i]) if aq_data["pm2_5"][i] is not None else 0.0,
                "pm10": float(aq_data["pm10"][i]) if aq_data["pm10"][i] is not None else 0.0,
                "no2": float(aq_data["nitrogen_dioxide"][i]) if aq_data["nitrogen_dioxide"][i] is not None else 0.0,
                "co": float(aq_data["carbon_monoxide"][i]) if aq_data["carbon_monoxide"][i] is not None else 0.0,
                "o3": float(aq_data["ozone"][i]) if aq_data["ozone"][i] is not None else 0.0,
                "so2": float(aq_data["sulphur_dioxide"][i]) if aq_data["sulphur_dioxide"][i] is not None else 0.0,
                "temperature": float(w_data["temperature_2m"][i]) if w_data["temperature_2m"][i] is not None else 25.0,
                "humidity": float(w_data["relative_humidity_2m"][i]) if w_data["relative_humidity_2m"][i] is not None else 50.0,
                "wind": float(w_data["wind_speed_10m"][i]) if w_data["wind_speed_10m"][i] is not None else 0.0,
                "latitude": lat,
                "longitude": lon,
                "last_updated": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "fetched_at": dt.isoformat(),
                "data_quality_flags": "OK",
                "quality_ok": 1
            }
            
            # Format filename to fit hourly conventions: city_YYYYMMDD_HHMM.csv
            file_timestamp = dt.strftime("%Y%m%d_%H%M")
            filename = f"data/raw/{city}_{file_timestamp}.csv"
            
            df = pd.DataFrame([reading])
            df.to_csv(filename, index=False)
            saved_count += 1
            
        print(f"  ✅ Successfully backfilled {saved_count} files for {city.upper()}")
        
    except Exception as e:
        print(f"  [ERROR] Failed to backfill {city}: {e}")

if __name__ == "__main__":
    days_to_backfill = 30
    if len(sys.argv) > 1:
        try:
            days_to_backfill = int(sys.argv[1])
        except ValueError:
            pass
            
    print("=" * 60)
    print(f"  CLIMA - Starting Historical Data Backfill ({days_to_backfill} days)")
    print("=" * 60)
    
    for city, config in CITIES.items():
        backfill_city_data(city, config["lat"], config["lon"], config["station"], days=days_to_backfill)
        
    print("\n" + "=" * 60)
    print("  Backfill process complete.")
    print("=" * 60)
