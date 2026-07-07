# ─────────────────────────────────────────────────────────────
# CLIMA — Live Risk Assessment
# Reads latest collected CSV data, runs full risk scoring pipeline.
# Fixes  : Windows encoding, path handling, Pune support added
# ─────────────────────────────────────────────────────────────

import sys
import os

# Fix: Force UTF-8 on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow running from any working directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

import glob
import pandas as pd
from datetime import datetime
from src.risk.risk_engine import calculate_all_routes_risk


# ─── LOAD LATEST WEATHER PER CITY ─────────────────────────────
def get_latest_weather() -> dict:
    """
    Reads the most recently collected CSV for each city.
    Returns a dict: { city_name: { aqi, humidity, wind, temperature, pm25 } }
    Only returns readings where quality_ok == 1 (or flag not present).
    """
    city_weather = {}
    cities = ["bengaluru", "delhi", "mumbai",
              "hyderabad", "chennai", "pune"]

    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "raw"
    )

    for city in cities:
        pattern = os.path.join(data_dir, f"{city}*.csv")
        files   = glob.glob(pattern)

        if not files:
            print(f"  [WARN] No data for {city} — skipping")
            continue

        latest_file = max(files, key=os.path.getmtime)
        df = pd.read_csv(latest_file)

        if df.empty:
            print(f"  [WARN] Empty file for {city}")
            continue

        row = df.iloc[-1]

        # Skip if data was flagged as bad quality
        if "quality_ok" in row and row["quality_ok"] == 0:
            print(f"  [SKIP] {city.upper()}: data flagged as bad quality — not used in risk scoring")
            continue

        # Safely extract weather fields
        def safe_float(val, default):
            try:
                v = float(val)
                return v if not pd.isna(v) else default
            except (TypeError, ValueError):
                return default

        city_weather[city] = {
            "aqi":         safe_float(row.get("aqi"),         50),
            "humidity":    safe_float(row.get("humidity"),    50),
            "wind":        safe_float(row.get("wind"),         0),
            "temperature": safe_float(row.get("temperature"), 25),
            "pm25":        safe_float(row.get("pm25"),        50),
        }

        age_h = (datetime.utcnow() - pd.Timestamp(latest_file.split("_")[-2][:8] +
                 " " + latest_file.split("_")[-1].replace(".csv","")[:4],
                 ).to_pydatetime()).total_seconds() / 3600 \
                if False else 0   # placeholder — just print file name

        print(f"  {city.upper():<12} "
              f"AQI:{city_weather[city]['aqi']:<6.0f} "
              f"Temp:{city_weather[city]['temperature']:<6.1f}C  "
              f"Humidity:{city_weather[city]['humidity']:.0f}%  "
              f"Wind:{city_weather[city]['wind']:.1f}km/h  "
              f"| {os.path.basename(latest_file)}")

    return city_weather


# ─── MAIN ASSESSMENT FUNCTION ─────────────────────────────────
def run_live_risk_assessment(cargo_type: str = "general") -> list:
    """
    Full pipeline:
    Latest CSV data  -->  Weather extraction  -->  Risk scoring  -->  Results
    """
    print("\n" + "=" * 65)
    print("  CLIMA - Live Route Risk Assessment")
    print(f"  Cargo: {cargo_type.upper()}  |  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)

    print("\n  Loading latest city weather data...\n")
    city_weather = get_latest_weather()

    if len(city_weather) < 2:
        print("\n  [ERROR] Not enough city data. Run src/ingestion.py first.")
        return []

    print(f"\n  Scoring {len(city_weather)} cities across all routes...\n")
    results = calculate_all_routes_risk(city_weather, cargo_type)

    if not results:
        print("  [WARN] No routes could be scored — cities may not overlap with route endpoints.")
        return []

    # Print results table
    print(f"  {'Route':<32} {'Risk':>6}  {'Level':<8} {'Est. Loss (INR)':>16}")
    print(f"  {'-'*32} {'-'*6}  {'-'*8} {'-'*16}")
    total_loss = 0
    for r in results:
        loss       = r["financial_impact"]["adjusted_loss_inr"]
        total_loss += loss
        level      = r["risk_level"]
        icon       = {"LOW": "[L]", "MEDIUM": "[M]", "HIGH": "[H]", "SEVERE": "[!]"}.get(level, "[ ]")
        name       = r["route_name"].replace("\u2192", "->")
        print(f"  {icon} {name:<30} {r['risk_score']:>5.1f}  {level:<8} Rs.{loss:>12,.0f}")

    print(f"\n  {'-'*65}")
    print(f"  Total financial exposure  : Rs.{total_loss:>12,.0f}")
    print(f"  Routes assessed           : {len(results)}")
    print(f"  Action recommended        : See individual route levels")
    print("=" * 65 + "\n")

    return results


# ─── CLI ENTRY POINT ──────────────────────────────────────────
if __name__ == "__main__":
    cargo = sys.argv[1] if len(sys.argv) > 1 else "general"
    run_live_risk_assessment(cargo)