"""Check processed data and data uniqueness"""
import sys
sys.path.append('.')
import pandas as pd, glob, os

print("=== PROCESSED FILES ===")
proc = glob.glob("data/processed/*.csv")
print("Processed files:", proc if proc else "NONE - preprocess.py was never run properly")

print()
print("=== MODEL FILES ===")
models = glob.glob("models/*")
for m in models:
    size = os.path.getsize(m)
    print(f"  {os.path.basename(m)}: {size} bytes")

print()
print("=== DATA UNIQUENESS CHECK - Is data actually changing? ===")
files = sorted(glob.glob("data/raw/bengaluru*.csv"))
for f in files:
    df = pd.read_csv(f)
    name = os.path.basename(f)
    aqi_val = list(df["aqi"])
    fetched = list(df["fetched_at"])
    print(f"  {name}: AQI={aqi_val}  fetched={fetched}")

print()
print("=== DELHI DATA - AQI CHANGED BUT OTHERS DID NOT ===")
files = sorted(glob.glob("data/raw/delhi*.csv"))
for f in files:
    df = pd.read_csv(f)
    name = os.path.basename(f)
    aqi_val = list(df["aqi"])
    fetched = list(df["fetched_at"])
    print(f"  {name}: AQI={aqi_val}  fetched={fetched}")
