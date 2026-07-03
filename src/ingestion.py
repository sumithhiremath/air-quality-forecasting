import requests
import pandas as pd
import os
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
# Paste your token from aqicn.org/data-platform/token/
API_TOKEN = "36b6772e4a3930417db631e2ddb53000ebae6aff"

BASE_URL = "https://api.waqi.info"

CITIES = [
    "bengaluru",
    "delhi",
    "mumbai",
    "hyderabad",
    "chennai"
]

# ─── AQI LABEL ────────────────────────────────────────────
def get_aqi_label(aqi: float) -> str:
    if aqi <= 50:    return "🟢 Good"
    elif aqi <= 100: return "🟡 Satisfactory"
    elif aqi <= 150: return "🟠 Moderate"
    elif aqi <= 200: return "🔴 Poor"
    elif aqi <= 300: return "🟣 Very Poor"
    else:            return "⚫ Severe"


# ─── FETCH FUNCTION ───────────────────────────────────────
def fetch_aqi(city: str) -> dict:
    """
    Fetches live AQI data for a city using WAQI API.
    Returns a clean dictionary of readings.
    """
    url = f"{BASE_URL}/feed/{city}/?token={API_TOKEN}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"⚠️  No data for {city}: {data.get('data')}")
            return {}

        result = data["data"]

        # Extract all pollutant values safely
        iaqi = result.get("iaqi", {})

        reading = {
            "city":         city,
            "station":      result.get("city", {}).get("name", city),
            "aqi":          result.get("aqi"),
            "pm25":         iaqi.get("pm25", {}).get("v"),
            "pm10":         iaqi.get("pm10", {}).get("v"),
            "no2":          iaqi.get("no2",  {}).get("v"),
            "co":           iaqi.get("co",   {}).get("v"),
            "o3":           iaqi.get("o3",   {}).get("v"),
            "so2":          iaqi.get("so2",  {}).get("v"),
            "temperature":  iaqi.get("t",    {}).get("v"),
            "humidity":     iaqi.get("h",    {}).get("v"),
            "wind":         iaqi.get("w",    {}).get("v"),
            "latitude":     result.get("city", {}).get("geo", [None, None])[0],
            "longitude":    result.get("city", {}).get("geo", [None, None])[1],
            "last_updated": result.get("time", {}).get("s"),
            "fetched_at":   datetime.utcnow().isoformat()
        }

        return reading

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error — check internet")
        return {}
    except requests.exceptions.Timeout:
        print(f"❌ Timeout for {city}")
        return {}
    except Exception as e:
        print(f"❌ Error for {city}: {e}")
        return {}


# ─── DISPLAY FUNCTION ─────────────────────────────────────
def display_aqi(reading: dict):
    city = reading.get("city", "Unknown").upper()
    aqi  = reading.get("aqi", "N/A")
    label = get_aqi_label(float(aqi)) if aqi else "N/A"

    print(f"\n{'='*55}")
    print(f"  {city} — {reading.get('station', '')}")
    print(f"{'='*55}")
    print(f"  AQI Overall : {aqi}  {label}")
    print(f"  {'─'*45}")
    print(f"  PM2.5       : {reading.get('pm25', 'N/A')} µg/m³")
    print(f"  PM10        : {reading.get('pm10', 'N/A')} µg/m³")
    print(f"  NO2         : {reading.get('no2',  'N/A')} µg/m³")
    print(f"  CO          : {reading.get('co',   'N/A')} µg/m³")
    print(f"  O3          : {reading.get('o3',   'N/A')} µg/m³")
    print(f"  Temperature : {reading.get('temperature', 'N/A')} °C")
    print(f"  Humidity    : {reading.get('humidity', 'N/A')} %")
    print(f"  {'─'*45}")
    print(f"  Last Updated: {reading.get('last_updated', 'N/A')}")
    print(f"{'='*55}\n")


# ─── SAVE FUNCTION ────────────────────────────────────────
def save_raw_data(reading: dict, city: str):
    if not reading:
        return

    os.makedirs("data/raw", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename  = f"data/raw/{city.lower()}_{timestamp}.csv"

    df = pd.DataFrame([reading])
    df.to_csv(filename, index=False)
    print(f"✅ Saved → {filename}")


# ─── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n🌍 Real-Time Air Quality Fetcher — India Cities\n")

    all_readings = []

    for city in CITIES:
        reading = fetch_aqi(city)

        if reading:
            display_aqi(reading)
            save_raw_data(reading, city)
            all_readings.append(reading)

    # Save all cities combined into one file too
    if all_readings:
        os.makedirs("data/raw", exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        combined_file = f"data/raw/all_cities_{timestamp}.csv"
        pd.DataFrame(all_readings).to_csv(combined_file, index=False)
        print(f"\n📦 Combined file saved → {combined_file}")
        print(f"✅ Total cities fetched: {len(all_readings)}")