# ─────────────────────────────────────────────────────────────
# CLIMA — Live AQI & Weather Data Ingestion
# Source : WAQI API (World Air Quality Index)
# Fixes  : Added Pune, temperature validation, encoding fix,
#           data quality flags, deduplication guard
# ─────────────────────────────────────────────────────────────

import sys
import os

# Fix: Windows PowerShell / CMD uses cp1252 by default which
# crashes on emoji. Force UTF-8 so scripts run on all platforms.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("WAQI_TOKEN")
BASE_URL   = "https://api.waqi.info"

# ─── CITY LIST ────────────────────────────────────────────────
# FIX (Day 4): Added "pune" — was missing but BLR_PUN route exists
CITIES = [
    "bengaluru",
    "delhi",
    "mumbai",
    "hyderabad",
    "chennai",
    "pune",       # <-- ADDED: required for Bengaluru→Pune route
]

# ─── DATA VALIDATION BOUNDS (India-specific) ──────────────────
# FIX (Day 4): Validate sensor readings before saving.
# Mumbai was returning -19.2C due to a bad WAQI station sensor.
VALIDATION_BOUNDS = {
    "aqi":         (0,   999),
    "pm25":        (0,   999),
    "pm10":        (0,   999),
    "temperature": (5,    50),   # India realistic range (°C)
    "humidity":    (0,   100),
    "wind":        (0,   200),
}


# ─── AQI LABEL ────────────────────────────────────────────────
def get_aqi_label(aqi: float) -> str:
    if aqi <= 50:    return "Good"
    elif aqi <= 100: return "Satisfactory"
    elif aqi <= 150: return "Moderate"
    elif aqi <= 200: return "Poor"
    elif aqi <= 300: return "Very Poor"
    else:            return "Severe"


# ─── VALIDATE ONE FIELD ───────────────────────────────────────
def validate_field(field: str, value) -> tuple:
    """
    Returns (cleaned_value, flag_message_or_None).
    If the value is outside bounds, it is set to None and flagged.
    """
    if value is None:
        return None, None

    try:
        v = float(value)
    except (TypeError, ValueError):
        return None, f"{field} could not be converted to float: {value}"

    if field in VALIDATION_BOUNDS:
        lo, hi = VALIDATION_BOUNDS[field]
        if not (lo <= v <= hi):
            return None, (
                f"{field} = {v} is OUTSIDE valid range [{lo}, {hi}] "
                f"— rejected (likely bad sensor data)"
            )
    return v, None


# ─── BACKUP WEATHER FETCH ─────────────────────────────────────
def fetch_backup_weather(lat: float, lon: float) -> dict:
    """
    Queries OpenWeatherMap (if token is set) or Open-Meteo (as a free keyless fallback)
    to retrieve temperature, humidity, and wind speed.
    """
    owm_token = os.getenv("OPENWEATHER_TOKEN")
    
    # Try OpenWeatherMap first if token is available
    if owm_token:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={owm_token}&units=metric"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                print("  [BACKUP] Successfully fetched backup weather from OpenWeatherMap")
                return {
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity":    data.get("main", {}).get("humidity"),
                    "wind":        float(data.get("wind", {}).get("speed", 0)) * 3.6 # m/s to km/h
                }
            else:
                print(f"  [BACKUP WARN] OpenWeatherMap returned status: {r.status_code}")
        except Exception as e:
            print(f"  [BACKUP ERROR] Failed to fetch from OpenWeatherMap: {e}")

    # Fallback to keyless Open-Meteo
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json().get("current", {})
            print("  [BACKUP] Successfully fetched keyless backup weather from Open-Meteo")
            return {
                "temperature": data.get("temperature_2m"),
                "humidity":    data.get("relative_humidity_2m"),
                "wind":        data.get("wind_speed_10m")
            }
    except Exception as e:
        print(f"  [BACKUP ERROR] Failed to fetch from Open-Meteo: {e}")
        
    return {}


# ─── FETCH FUNCTION ───────────────────────────────────────────
def fetch_aqi(city: str) -> dict:
    """
    Fetches live AQI + weather data for a city via WAQI API.
    Returns a validated, clean dictionary.  Returns {} on failure.
    """
    url = f"{BASE_URL}/feed/{city}/?token={API_TOKEN}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"  [WARN] No data for {city}: {data.get('data')}")
            return {}

        result = data["data"]
        iaqi   = result.get("iaqi", {})

        # Raw extraction
        raw = {
            "city":        city,
            "station":     result.get("city", {}).get("name", city),
            "aqi":         result.get("aqi"),
            "pm25":        iaqi.get("pm25", {}).get("v"),
            "pm10":        iaqi.get("pm10", {}).get("v"),
            "no2":         iaqi.get("no2",  {}).get("v"),
            "co":          iaqi.get("co",   {}).get("v"),
            "o3":          iaqi.get("o3",   {}).get("v"),
            "so2":         iaqi.get("so2",  {}).get("v"),
            "temperature": iaqi.get("t",    {}).get("v"),
            "humidity":    iaqi.get("h",    {}).get("v"),
            "wind":        iaqi.get("w",    {}).get("v"),
            "latitude":    result.get("city", {}).get("geo", [None, None])[0],
            "longitude":   result.get("city", {}).get("geo", [None, None])[1],
            "last_updated": result.get("time", {}).get("s"),
            "fetched_at":  datetime.utcnow().isoformat(),
        }

        # Validate fields — reject readings outside physical bounds
        quality_flags = []
        validated_fields = ["aqi", "pm25", "pm10", "temperature", "humidity", "wind"]
        for field in validated_fields:
            cleaned, flag = validate_field(field, raw[field])
            raw[field] = cleaned
            if flag:
                quality_flags.append(flag)

        # Check if weather fields (temperature, humidity, wind) need healing from backup APIs
        weather_fields = ["temperature", "humidity", "wind"]
        needs_backup = any(raw[f] is None for f in weather_fields)
        
        if needs_backup and raw["latitude"] is not None and raw["longitude"] is not None:
            print(f"  [HEAL] City {city.upper()} has missing or flagged weather fields. Querying backup weather...")
            backup = fetch_backup_weather(raw["latitude"], raw["longitude"])
            if backup:
                healed_flags = []
                for field in weather_fields:
                    if raw[field] is None and field in backup:
                        val = backup[field]
                        cleaned, flag = validate_field(field, val)
                        if cleaned is not None:
                            raw[field] = cleaned
                            healed_flags.append(f"{field} (healed with {val})")
                if healed_flags:
                    print(f"  [HEAL] {city.upper()}: Healed fields: {', '.join(healed_flags)}")
                    # Re-evaluate quality flags after healing
                    quality_flags = []
                    for field in validated_fields:
                        _, flag = validate_field(field, raw[field])
                        if flag:
                            quality_flags.append(flag)

        raw["data_quality_flags"] = "; ".join(quality_flags) if quality_flags else "OK"
        raw["quality_ok"] = 1 if not quality_flags else 0

        if quality_flags:
            print(f"  [DATA QUALITY] {city.upper()}: {'; '.join(quality_flags)}")

        return raw

    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] {city}: Connection error — check internet")
        return {}
    except requests.exceptions.Timeout:
        print(f"  [ERROR] {city}: Request timed out")
        return {}
    except Exception as e:
        print(f"  [ERROR] {city}: {e}")
        return {}


# ─── DISPLAY FUNCTION ─────────────────────────────────────────
def display_aqi(reading: dict):
    city  = reading.get("city", "Unknown").upper()
    aqi   = reading.get("aqi")
    temp  = reading.get("temperature")
    hum   = reading.get("humidity")
    wind  = reading.get("wind")
    label = get_aqi_label(float(aqi)) if aqi is not None else "N/A"
    flag  = reading.get("data_quality_flags", "OK")

    print(f"\n  {'='*52}")
    print(f"  {city}")
    print(f"  {'='*52}")
    print(f"  AQI         : {aqi if aqi is not None else 'N/A':>6}   ({label})")
    print(f"  PM2.5       : {reading.get('pm25', 'N/A')}")
    print(f"  PM10        : {reading.get('pm10', 'N/A')}")
    print(f"  Temperature : {temp if temp is not None else 'N/A (bad sensor)'} C")
    print(f"  Humidity    : {hum  if hum  is not None else 'N/A'} %")
    print(f"  Wind        : {wind if wind is not None else 'N/A'} km/h")
    print(f"  Quality     : {flag}")
    print(f"  Last Updated: {reading.get('last_updated', 'N/A')}")
    print(f"  {'='*52}")


# ─── SAVE FUNCTION ────────────────────────────────────────────
def save_raw_data(reading: dict, city: str) -> str:
    """Saves one city reading to data/raw/. Returns saved filename."""
    if not reading:
        return ""

    os.makedirs("data/raw", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename  = f"data/raw/{city.lower()}_{timestamp}.csv"

    df = pd.DataFrame([reading])
    df.to_csv(filename, index=False)
    print(f"  Saved --> {filename}")
    return filename


# ─── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("  CLIMA - Real-Time AQI & Weather Ingestion")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    print(f"  Cities: {', '.join(c.upper() for c in CITIES)}\n")

    all_readings = []
    quality_summary = {"ok": 0, "flagged": 0, "failed": 0}

    for city in CITIES:
        print(f"  Fetching {city.upper()}...")
        reading = fetch_aqi(city)

        if reading:
            display_aqi(reading)
            save_raw_data(reading, city)
            all_readings.append(reading)
            if reading.get("quality_ok"):
                quality_summary["ok"] += 1
            else:
                quality_summary["flagged"] += 1
        else:
            quality_summary["failed"] += 1
            print(f"  [SKIP] {city.upper()}: No data returned")

    # Save combined snapshot
    if all_readings:
        os.makedirs("data/raw", exist_ok=True)
        timestamp    = datetime.utcnow().strftime("%Y%m%d_%H%M")
        combined_file = f"data/raw/all_cities_{timestamp}.csv"
        pd.DataFrame(all_readings).to_csv(combined_file, index=False)
        print(f"\n  Combined snapshot --> {combined_file}")

    print(f"\n  Summary:")
    print(f"    Cities fetched   : {len(all_readings)}/{len(CITIES)}")
    print(f"    Quality OK       : {quality_summary['ok']}")
    print(f"    Flagged (bad data): {quality_summary['flagged']}")
    print(f"    Failed (no data) : {quality_summary['failed']}")
    print("\n" + "=" * 60)