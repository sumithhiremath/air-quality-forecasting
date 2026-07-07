import sys
import os

# Fix: Windows PowerShell uses cp1252 — force UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
from datetime import datetime
from src.routes.route_config import ROUTES, CARGO_TYPES

# ─── RISK LEVELS ──────────────────────────────────────────
RISK_LEVELS = {
    "LOW":    {"min": 0,  "max": 30,  "color": "🟢", "action": "Clear to dispatch"},
    "MEDIUM": {"min": 30, "max": 60,  "color": "🟡", "action": "Monitor closely"},
    "HIGH":   {"min": 60, "max": 80,  "color": "🔴", "action": "Delay or reroute"},
    "SEVERE": {"min": 80, "max": 100, "color": "⚫", "action": "Do not dispatch"}
}

# ─── WEATHER RISK ─────────────────────────────────────────
def calculate_weather_risk(weather_data: dict) -> float:
    risk = 0

    humidity = weather_data.get("humidity", 50)
    if humidity > 90:   risk += 30
    elif humidity > 80: risk += 20
    elif humidity > 70: risk += 10

    wind = weather_data.get("wind", 0)
    if wind > 50:   risk += 25
    elif wind > 30: risk += 15
    elif wind > 20: risk += 5

    aqi = weather_data.get("aqi", 50)
    if aqi > 300:   risk += 25
    elif aqi > 200: risk += 15
    elif aqi > 150: risk += 10
    elif aqi > 100: risk += 5

    temp = weather_data.get("temperature", 25)
    if temp > 42:   risk += 15
    elif temp > 38: risk += 8
    elif temp < 5:  risk += 10

    return min(risk, 100)


# ─── SEASONAL RISK ────────────────────────────────────────
def get_season_risk(route_id: str) -> float:
    month = datetime.now().month
    route = ROUTES.get(route_id, {})

    if month in [6, 7, 8, 9]:
        season = "monsoon"
    elif month in [12, 1, 2]:
        season = "winter"
    elif month in [3, 4, 5]:
        season = "summer"
    else:
        season = "post_monsoon"

    level = route.get("seasonal_risk", {}).get(season, "MEDIUM")
    return {"LOW": 10, "MEDIUM": 25, "HIGH": 40}.get(level, 25)


# ─── FINANCIAL IMPACT ─────────────────────────────────────
def calculate_financial_impact(route_id: str,
                                delay_probability: float,
                                cargo_type: str = "general") -> dict:
    route  = ROUTES.get(route_id, {})
    avg_hrs      = route.get("avg_transit_hrs", 12)
    cost_per_hr  = route.get("truck_cost_per_hr", 3500)
    cargo        = CARGO_TYPES.get(cargo_type, {})
    sensitivity  = cargo.get("delay_sensitivity", 1.0)

    expected_delay_hrs = avg_hrs * (delay_probability / 100) * 0.5
    base_loss          = expected_delay_hrs * cost_per_hr
    adjusted_loss      = base_loss * sensitivity

    return {
        "expected_delay_hrs": round(expected_delay_hrs, 1),
        "base_loss_inr":      round(base_loss, 0),
        "adjusted_loss_inr":  round(adjusted_loss, 0),
        "cargo_type":         cargo.get("name", cargo_type),
        "sensitivity":        sensitivity
    }


# ─── MAIN RISK CALCULATOR ─────────────────────────────────
def calculate_route_risk(route_id: str,
                          origin_weather: dict,
                          destination_weather: dict,
                          cargo_type: str = "general") -> dict:

    route = ROUTES.get(route_id, {})
    if not route:
        return {"error": f"Route {route_id} not found"}

    origin_risk      = calculate_weather_risk(origin_weather)
    destination_risk = calculate_weather_risk(destination_weather)
    weather_risk     = (origin_risk * 0.5) + (destination_risk * 0.5)
    seasonal_risk    = get_season_risk(route_id)
    total_risk       = min((weather_risk * 0.7) + (seasonal_risk * 0.3), 100)

    risk_level = "LOW"
    for level, bounds in RISK_LEVELS.items():
        if bounds["min"] <= total_risk < bounds["max"]:
            risk_level = level
            break

    financial = calculate_financial_impact(route_id, total_risk, cargo_type)

    return {
        "route_id":           route_id,
        "route_name":         route["name"],
        "highway":            route["highway"],
        "distance_km":        route["distance_km"],
        "risk_score":         round(total_risk, 1),
        "risk_level":         risk_level,
        "risk_color":         RISK_LEVELS[risk_level]["color"],
        "recommended_action": RISK_LEVELS[risk_level]["action"],
        "weather_risk":       round(weather_risk, 1),
        "seasonal_risk":      round(seasonal_risk, 1),
        "financial_impact":   financial,
        "timestamp":          datetime.utcnow().isoformat()
    }


# ─── ALL ROUTES RISK ──────────────────────────────────────
def calculate_all_routes_risk(city_weather: dict,
                               cargo_type: str = "general") -> list:
    """
    Calculate risk for all 5 routes at once.
    city_weather = dict of city -> weather data
    """
    results = []
    for route_id, route in ROUTES.items():
        origin      = route["origin"]
        destination = route["destination"]

        origin_w = city_weather.get(origin, {})
        dest_w   = city_weather.get(destination, {})

        if origin_w and dest_w:
            result = calculate_route_risk(
                route_id, origin_w, dest_w, cargo_type
            )
            results.append(result)

    # Sort by risk score highest first
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


# ─── TEST ─────────────────────────────────────────────────
if __name__ == "__main__":

    # Simulate current weather from collected data
    city_weather = {
        "bengaluru": {"aqi": 142, "humidity": 85, "wind": 15, "temperature": 28},
        "mumbai":    {"aqi": 158, "humidity": 92, "wind": 25, "temperature": 30},
        "chennai":   {"aqi": 89,  "humidity": 78, "wind": 12, "temperature": 34},
        "hyderabad": {"aqi": 76,  "humidity": 65, "wind": 8,  "temperature": 32},
        "delhi":     {"aqi": 210, "humidity": 55, "wind": 18, "temperature": 38},
        "pune":      {"aqi": 95,  "humidity": 80, "wind": 10, "temperature": 29},
    }

    print("\n" + "="*60)
    print("  CLIMA — All Routes Risk Assessment")
    print("="*60)

    results = calculate_all_routes_risk(city_weather, "automotive")

    for r in results:
        rname = r['route_name'].replace('\u2192', '->')
        print(f"\n  {rname}")
        print(f"     Highway:  {r['highway']}")
        print(f"     Risk:     {r['risk_score']}/100 — {r['risk_level']}")
        print(f"     Action:   {r['recommended_action']}")
        print(f"     Est Loss: ₹{r['financial_impact']['adjusted_loss_inr']:,.0f}")

    print("\n" + "="*60)