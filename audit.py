"""Deep audit of all collected data and code issues"""
import pandas as pd, glob, os

print("=== MUMBAI TEMPERATURE ACROSS ALL FILES ===")
files = sorted(glob.glob("data/raw/mumbai*.csv"))
for f in files:
    df = pd.read_csv(f)
    name = os.path.basename(f)
    temps = list(df["temperature"])
    print(f"  {name}: temp={temps}")

print()
print("=== ALL CITIES - ALL COLLECTED DATA ===")
files = sorted(glob.glob("data/raw/all_cities*.csv"))
for f in files:
    df = pd.read_csv(f)
    name = os.path.basename(f)
    print(f"\nFile: {name}")
    cols = ["city","aqi","temperature","humidity","wind","pm25"]
    available = [c for c in cols if c in df.columns]
    print(df[available].to_string(index=False))

print()
print("=== DATA GAPS: DATES WITH DATA ===")
all_files = sorted(glob.glob("data/raw/all_cities*.csv"))
print(f"Total combined snapshots: {len(all_files)}")
for f in all_files:
    name = os.path.basename(f)
    mtime = pd.Timestamp(os.path.getmtime(f), unit='s')
    print(f"  {name}  (modified: {mtime.strftime('%Y-%m-%d %H:%M')})")

print()
print("=== PUNE DATA CHECK ===")
pune_files = glob.glob("data/raw/pune*.csv")
print(f"Pune files found: {len(pune_files)}")
if not pune_files:
    print("  PROBLEM: Pune is in route_config.py (BLR_PUN) but NEVER in CITIES list in ingestion.py!")

print()
print("=== GITHUB ACTIONS - IS IT ACTUALLY RUNNING? ===")
import datetime
latest_file = max(glob.glob("data/raw/*.csv"), key=os.path.getmtime)
mtime = datetime.datetime.fromtimestamp(os.path.getmtime(latest_file))
now = datetime.datetime.now()
hours_gap = (now - mtime).total_seconds() / 3600
days_gap = hours_gap / 24
print(f"Latest file: {os.path.basename(latest_file)}")
print(f"Last updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
print(f"Gap: {hours_gap:.1f} hours ({days_gap:.1f} days)")
if days_gap > 1:
    print("  CRITICAL: GitHub Actions hourly collection is NOT working properly.")
    print("  Possible reasons:")
    print("    1. WAQI_TOKEN secret not set in GitHub repo settings")
    print("    2. GitHub Actions scheduled workflows may be disabled (idle repos)")
    print("    3. Data IS being collected on GitHub but NOT pulled locally")
    print("    4. Workflow is failing silently")
