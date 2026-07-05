# ─── CLIMA Route Configuration ────────────────────────────

ROUTES = {
    "BLR_MUM": {
        "name": "Bengaluru → Mumbai",
        "origin": "bengaluru",
        "destination": "mumbai",
        "highway": "NH48",
        "distance_km": 984,
        "avg_transit_hrs": 18,
        "truck_cost_per_hr": 3500,
        "risk_cities": ["bengaluru", "pune", "mumbai"],
        "coordinates": {
            "origin": (12.9716, 77.5946),
            "destination": (19.0760, 72.8777)
        },
        "seasonal_risk": {
            "monsoon": "HIGH",
            "winter": "LOW",
            "summer": "MEDIUM",
            "post_monsoon": "MEDIUM"
        }
    },
    "BLR_CHN": {
        "name": "Bengaluru → Chennai",
        "origin": "bengaluru",
        "destination": "chennai",
        "highway": "NH48",
        "distance_km": 346,
        "avg_transit_hrs": 6,
        "truck_cost_per_hr": 3500,
        "risk_cities": ["bengaluru", "chennai"],
        "coordinates": {
            "origin": (12.9716, 77.5946),
            "destination": (13.0827, 80.2707)
        },
        "seasonal_risk": {
            "monsoon": "MEDIUM",
            "winter": "MEDIUM",
            "summer": "LOW",
            "post_monsoon": "HIGH"
        }
    },
    "BLR_HYD": {
        "name": "Bengaluru → Hyderabad",
        "origin": "bengaluru",
        "destination": "hyderabad",
        "highway": "NH44",
        "distance_km": 574,
        "avg_transit_hrs": 10,
        "truck_cost_per_hr": 3500,
        "risk_cities": ["bengaluru", "hyderabad"],
        "coordinates": {
            "origin": (12.9716, 77.5946),
            "destination": (17.3850, 78.4867)
        },
        "seasonal_risk": {
            "monsoon": "HIGH",
            "winter": "LOW",
            "summer": "LOW",
            "post_monsoon": "MEDIUM"
        }
    },
    "BLR_PUN": {
        "name": "Bengaluru → Pune",
        "origin": "bengaluru",
        "destination": "pune",
        "highway": "NH48",
        "distance_km": 840,
        "avg_transit_hrs": 15,
        "truck_cost_per_hr": 3500,
        "risk_cities": ["bengaluru", "pune"],
        "coordinates": {
            "origin": (12.9716, 77.5946),
            "destination": (18.5204, 73.8567)
        },
        "seasonal_risk": {
            "monsoon": "HIGH",
            "winter": "LOW",
            "summer": "MEDIUM",
            "post_monsoon": "LOW"
        }
    },
    "BLR_DEL": {
        "name": "Bengaluru → Delhi",
        "origin": "bengaluru",
        "destination": "delhi",
        "highway": "NH44",
        "distance_km": 2150,
        "avg_transit_hrs": 40,
        "truck_cost_per_hr": 3500,
        "risk_cities": ["bengaluru", "hyderabad", "delhi"],
        "coordinates": {
            "origin": (12.9716, 77.5946),
            "destination": (28.6139, 77.2090)
        },
        "seasonal_risk": {
            "monsoon": "HIGH",
            "winter": "HIGH",
            "summer": "MEDIUM",
            "post_monsoon": "MEDIUM"
        }
    }
}

CARGO_TYPES = {
    "perishable": {
        "name": "Perishables (Fruits, Vegetables, Flowers)",
        "delay_sensitivity": 3.0,
        "max_acceptable_delay_hrs": 4,
        "examples": "Tomatoes, Roses, Fish"
    },
    "pharma": {
        "name": "Pharmaceuticals (Temperature Sensitive)",
        "delay_sensitivity": 2.5,
        "max_acceptable_delay_hrs": 6,
        "examples": "Vaccines, Insulin, Biologics"
    },
    "electronics": {
        "name": "Electronics & Components",
        "delay_sensitivity": 1.5,
        "max_acceptable_delay_hrs": 24,
        "examples": "Mobile phones, PCBs, Chips"
    },
    "automotive": {
        "name": "Automotive Parts",
        "delay_sensitivity": 2.0,
        "max_acceptable_delay_hrs": 12,
        "examples": "Tyres, Engine parts, Assembly kits"
    },
    "general": {
        "name": "General Merchandise",
        "delay_sensitivity": 1.0,
        "max_acceptable_delay_hrs": 48,
        "examples": "FMCG, Clothing, Furniture"
    }
}

def get_route(route_id: str) -> dict:
    return ROUTES.get(route_id, {})

def get_all_routes() -> list:
    return list(ROUTES.keys())

def get_cargo_sensitivity(cargo_type: str) -> float:
    return CARGO_TYPES.get(cargo_type, {}).get("delay_sensitivity", 1.0)

if __name__ == "__main__":
    print("\nCLIMA — Registered Routes:")
    print("="*50)
    for rid, route in ROUTES.items():
        print(f"  {rid}: {route['name']}")
        print(f"       Highway:  {route['highway']}")
        print(f"       Distance: {route['distance_km']} km")
        print(f"       Transit:  {route['avg_transit_hrs']} hrs")
        print()