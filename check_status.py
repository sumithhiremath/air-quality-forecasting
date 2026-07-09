"""CLIMA Day 4 - Status Check & Live Risk Assessment"""
import sys, os
sys.path.append(os.path.dirname(__file__))

import glob
import pandas as pd
from datetime import datetime
from src.risk.risk_engine import calculate_all_routes_risk

print("=" * 65)
print("  CLIMA - Day 4 Status Check")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 65)

# --- DATA COLLECTION STATUS ---
print("\n[DATA COLLECTION AUDIT]")
raw_files = sorted(glob.glob("data/raw/*.csv"))
city_files = [f for f in raw_files if "all_cities" not in os.path.basename(f)]
combined_files = [f for f in raw_files if "all_cities" in os.path.basename(f)]
print(f"  Total raw files   : {len(raw_files)}")
print(f"  Per-city files    : {len(city_files)}")
print(f"  Combined files    : {len(combined_files)}")

# Check date gaps
dates_seen = set()
for f in combined_files:
    bn = os.path.basename(f)
    # e.g. all_cities_20260704_1736.csv
    parts = bn.replace("all_cities_","").replace(".csv","").split("_")
    if len(parts) >= 1:
        dates_seen.add(parts[0])
print(f"  Unique collection dates: {sorted(dates_seen)}")

# Last collection time
if raw_files:
    latest = max(raw_files, key=os.path.getmtime)
    mtime = datetime.fromtimestamp(os.path.getmtime(latest))
    hours_ago = (datetime.now() - mtime).total_seconds() / 3600
    print(f"  Last file: {os.path.basename(latest)}")
    print(f"  Collected: {mtime.strftime('%Y-%m-%d %H:%M')}  ({hours_ago:.1f} hours ago)")
    if hours_ago > 2:
        print("  WARNING: Data is STALE. GitHub Actions may not be running or data is not synced locally.")
    else:
        print("  OK: Data is fresh.")

# --- LOAD LATEST WEATHER PER CITY ---
print("\n[LATEST WEATHER DATA]")
cities = ["bengaluru", "delhi", "mumbai", "hyderabad", "chennai", "pune"]
city_weather = {}
for city in cities:
    files = glob.glob(f"data/raw/{city}*.csv")
    if not files:
        print(f"  {city.upper():<12}: NO DATA FOUND")
        continue
    latest_file = max(files, key=os.path.getmtime)
    df = pd.read_csv(latest_file)
    if df.empty:
        continue
    row = df.iloc[-1]
    city_weather[city] = {
        "aqi": float(row.get("aqi", 50) or 50),
        "humidity": float(row.get("humidity", 50) or 50),
        "wind": float(row.get("wind", 0) or 0),
        "temperature": float(row.get("temperature", 25) or 25),
        "pm25": float(row.get("pm25", 50) or 50),
    }
    print(f"  {city.upper():<12}: AQI={city_weather[city]['aqi']:<6.0f} Temp={city_weather[city]['temperature']:<6.1f}C  Humidity={city_weather[city]['humidity']:.0f}%  Wind={city_weather[city]['wind']:.1f}km/h")

# --- LIVE RISK ASSESSMENT ---
print("\n[ROUTE RISK ASSESSMENT - General Cargo]")
if len(city_weather) >= 2:
    results = calculate_all_routes_risk(city_weather, "general")
    total_loss = 0
    for r in results:
        loss = r["financial_impact"]["adjusted_loss_inr"]
        total_loss += loss
        level = r["risk_level"]
        icon = {"LOW": "[LOW]   ", "MEDIUM": "[MED]   ", "HIGH": "[HIGH]  ", "SEVERE": "[SEVERE]"}.get(level, "[ ]")
        route_name_ascii = r['route_name'].replace('\u2192', '->')
        print(f"  {icon} {route_name_ascii:<30} Risk: {r['risk_score']:>5.1f}/100  Loss: Rs.{loss:>10,.0f}")
    print(f"\n  Total financial exposure: Rs.{total_loss:,.0f}")
    print(f"  Routes assessed: {len(results)}")
else:
    print("  Not enough city data for risk assessment.")

# --- DATA QUALITY CHECK ---
print("\n[DATA QUALITY FLAGS]")
for city, w in city_weather.items():
    issues = []
    if w["temperature"] < -10 or w["temperature"] > 55:
        issues.append(f"TEMP anomaly: {w['temperature']}C")
    if w["humidity"] < 0 or w["humidity"] > 100:
        issues.append(f"HUMIDITY anomaly: {w['humidity']}%")
    if w["aqi"] < 0 or w["aqi"] > 999:
        issues.append(f"AQI anomaly: {w['aqi']}")
    if issues:
        print(f"  {city.upper()}: ISSUES FOUND - {', '.join(issues)}")
    else:
        print(f"  {city.upper()}: Data looks clean")

print("\n" + "=" * 65)
print("  Status check complete.")
print("=" * 65)
