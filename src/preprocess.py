import pandas as pd
import numpy as np
import os
import glob
import joblib
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler

# ─── CONFIG ───────────────────────────────────────────────
# How many past hours LSTM looks at to make one prediction
SEQUENCE_LENGTH = 24  # last 24 hours

# How many hours ahead to predict
FORECAST_HORIZON = 24  # predict next 24 hours

# Features the model will use
FEATURE_COLUMNS = [
    "aqi", "pm25", "pm10", "no2", "co", "o3",
    "temperature", "humidity",
    "hour", "day_of_week", "month", "is_weekend",
    "aqi_lag_1", "aqi_lag_3", "aqi_lag_6", "aqi_lag_12",
    "aqi_rolling_mean_6", "aqi_rolling_mean_12"
]

# Target — what we're predicting
TARGET_COLUMN = "aqi"


# ─── STEP 1: LOAD ALL RAW FILES ───────────────────────────
def load_raw_data(city: str = None) -> pd.DataFrame:
    """
    Loads all raw CSV files from data/raw/.
    Optionally filter by city name.
    """
    pattern = "data/raw/*.csv"
    files = glob.glob(pattern)

    if not files:
        print("❌ No raw data files found. Run ingestion.py first.")
        return pd.DataFrame()

    dfs = []
    for f in files:
        # Filter by city if specified
        if city and city.lower() not in f.lower():
            continue
        try:
            df = pd.read_csv(f)
            df["source_file"] = os.path.basename(f)
            dfs.append(df)
        except Exception as e:
            print(f"⚠️  Could not read {f}: {e}")

    if not dfs:
        print(f"❌ No files found for city: {city}")
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    print(f"✅ Loaded {len(combined)} rows from {len(dfs)} files")
    return combined


# ─── STEP 2: CLEAN DATA ───────────────────────────────────
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw data:
    - Fix data types
    - Handle missing values
    - Remove duplicates
    - Remove impossible values
    """
    print("\n🔧 Cleaning data...")
    print(f"   Shape before: {df.shape}")

    # Convert fetched_at to datetime
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], errors="coerce")

    # Convert numeric columns — force to float, invalid becomes NaN
    numeric_cols = ["aqi", "pm25", "pm10", "no2", "co", "o3",
                    "so2", "temperature", "humidity", "wind"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove impossible values — AQI can't be negative or above 1000
    if "aqi" in df.columns:
        df = df[df["aqi"].between(0, 1000) | df["aqi"].isna()]

    # Remove impossible PM2.5 values
    if "pm25" in df.columns:
        df = df[df["pm25"].between(0, 999) | df["pm25"].isna()]

    # Remove impossible temperature values for India
    if "temperature" in df.columns:
        df = df[df["temperature"].between(-5, 60) | df["temperature"].isna()]

    # Remove duplicate rows (same city, same timestamp)
    df = df.drop_duplicates(subset=["city", "fetched_at"])

    # Sort by time
    df = df.sort_values("fetched_at").reset_index(drop=True)

    print(f"   Shape after:  {df.shape}")
    print(f"   Date range:   {df['fetched_at'].min()} → {df['fetched_at'].max()}")

    return df


# ─── STEP 3: HANDLE MISSING VALUES ────────────────────────
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing sensor readings intelligently:
    - Short gaps (1-3 hrs): interpolate linearly
    - Longer gaps: fill with rolling median
    - Still missing: fill with column median
    """
    print("\n🔧 Handling missing values...")

    numeric_cols = ["aqi", "pm25", "pm10", "no2", "co",
                    "o3", "so2", "temperature", "humidity"]

    for col in numeric_cols:
        if col not in df.columns:
            continue

        missing_before = df[col].isna().sum()

        if missing_before == 0:
            continue

        # Strategy 1: Linear interpolation for short gaps
        df[col] = df[col].interpolate(method="linear", limit=3)

        # Strategy 2: Rolling median for longer gaps
        rolling_median = df[col].rolling(window=12, min_periods=1).median()
        df[col] = df[col].fillna(rolling_median)

        # Strategy 3: Overall median for anything remaining
        df[col] = df[col].fillna(df[col].median())

        missing_after = df[col].isna().sum()
        print(f"   {col:<15} missing: {missing_before} → {missing_after}")

    return df


# ─── STEP 4: ENGINEER TIME FEATURES ──────────────────────
def engineer_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts meaningful time features from timestamp.
    LSTM needs to understand time context — not just raw numbers.
    """
    print("\n🔧 Engineering time features...")

    df["hour"]        = df["fetched_at"].dt.hour
    df["day_of_week"] = df["fetched_at"].dt.dayofweek   # 0=Monday, 6=Sunday
    df["month"]       = df["fetched_at"].dt.month
    df["day_of_year"] = df["fetched_at"].dt.dayofyear
    df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)

    # Season (India-specific)
    # Winter: Dec-Feb, Summer: Mar-May, Monsoon: Jun-Sep, Post: Oct-Nov
    def get_season(month):
        if month in [12, 1, 2]:  return 0  # Winter
        elif month in [3, 4, 5]: return 1  # Summer
        elif month in [6, 7, 8, 9]: return 2  # Monsoon
        else: return 3  # Post-monsoon

    df["season"] = df["month"].apply(get_season)

    # Rush hour flag — traffic peaks = pollution peaks in Bengaluru
    df["is_rush_hour"] = df["hour"].apply(
        lambda h: 1 if h in [7, 8, 9, 17, 18, 19] else 0
    )

    print(f"   Added: hour, day_of_week, month, is_weekend, season, is_rush_hour")
    return df


# ─── STEP 5: ENGINEER LAG FEATURES ───────────────────────
def engineer_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates lag features — AQI values from past hours.
    These are critical for LSTM to learn temporal patterns.

    lag_1  = AQI 1 hour ago
    lag_3  = AQI 3 hours ago
    lag_6  = AQI 6 hours ago
    lag_12 = AQI 12 hours ago
    """
    print("\n🔧 Engineering lag features...")

    # Group by city so lags don't bleed across cities
    dfs_by_city = []

    for city in df["city"].unique():
        city_df = df[df["city"] == city].copy()

        # Lag features
        city_df["aqi_lag_1"]  = city_df["aqi"].shift(1)
        city_df["aqi_lag_3"]  = city_df["aqi"].shift(3)
        city_df["aqi_lag_6"]  = city_df["aqi"].shift(6)
        city_df["aqi_lag_12"] = city_df["aqi"].shift(12)

        # Rolling statistics — captures trend
        city_df["aqi_rolling_mean_6"]  = city_df["aqi"].rolling(6,  min_periods=1).mean()
        city_df["aqi_rolling_mean_12"] = city_df["aqi"].rolling(12, min_periods=1).mean()
        city_df["aqi_rolling_std_6"]   = city_df["aqi"].rolling(6,  min_periods=1).std()

        # AQI change rate — is it getting better or worse?
        city_df["aqi_change_1h"] = city_df["aqi"].diff(1)
        city_df["aqi_change_3h"] = city_df["aqi"].diff(3)

        dfs_by_city.append(city_df)

    df = pd.concat(dfs_by_city, ignore_index=True)

    # Fill NaN created by shift/diff with 0
    lag_cols = ["aqi_lag_1", "aqi_lag_3", "aqi_lag_6", "aqi_lag_12",
                "aqi_rolling_mean_6", "aqi_rolling_mean_12",
                "aqi_rolling_std_6", "aqi_change_1h", "aqi_change_3h"]

    for col in lag_cols:
        df[col] = df[col].fillna(0)

    print(f"   Added: lag_1, lag_3, lag_6, lag_12, rolling_mean_6/12, change_1h/3h")
    return df


# ─── STEP 6: NORMALIZE ────────────────────────────────────
def normalize_features(df: pd.DataFrame, fit: bool = True):
    """
    Scales all numeric features to range [0, 1].
    LSTM trains much better on normalized data.

    fit=True  → fit scaler on training data (first time)
    fit=False → use existing scaler (for new incoming data)
    """
    print("\n🔧 Normalizing features...")

    # Only scale these columns
    cols_to_scale = [c for c in FEATURE_COLUMNS if c in df.columns]

    os.makedirs("models", exist_ok=True)
    scaler_path = "models/scaler.pkl"

    if fit:
        scaler = MinMaxScaler()
        df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
        # Save scaler — needed to inverse transform predictions later
        joblib.dump(scaler, scaler_path)
        print(f"   ✅ Scaler fitted and saved → {scaler_path}")
    else:
        if not os.path.exists(scaler_path):
            print("   ❌ No saved scaler found. Run with fit=True first.")
            return df, None
        scaler = joblib.load(scaler_path)
        df[cols_to_scale] = scaler.transform(df[cols_to_scale])
        print(f"   ✅ Existing scaler applied")

    return df, scaler


# ─── STEP 7: BUILD LSTM SEQUENCES ─────────────────────────
def build_sequences(df: pd.DataFrame, city: str = None):
    """
    Converts flat DataFrame into 3D sequences for LSTM.

    LSTM input shape: (samples, sequence_length, features)
    - samples = number of training examples
    - sequence_length = 24 (last 24 hours)
    - features = number of input columns

    Example:
    Row 0-23  → X[0], y[0]   (hours 0-23 predict hour 24)
    Row 1-24  → X[1], y[1]   (hours 1-24 predict hour 25)
    Row 2-25  → X[2], y[2]   (hours 2-25 predict hour 26)
    ... sliding window
    """
    print(f"\n🔧 Building LSTM sequences (window={SEQUENCE_LENGTH})...")

    if city:
        df = df[df["city"] == city].copy()

    # Keep only feature columns that exist
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    target_col   = TARGET_COLUMN

    if target_col not in df.columns:
        print(f"❌ Target column '{target_col}' not found")
        return None, None

    data = df[feature_cols].values
    target = df[target_col].values

    X, y = [], []

    for i in range(len(data) - SEQUENCE_LENGTH - FORECAST_HORIZON + 1):
        # Input: rows i to i+SEQUENCE_LENGTH
        X.append(data[i : i + SEQUENCE_LENGTH])
        # Target: AQI value SEQUENCE_LENGTH steps ahead
        y.append(target[i + SEQUENCE_LENGTH])

    X = np.array(X)
    y = np.array(y)

    print(f"   X shape: {X.shape}  →  (samples, sequence_length, features)")
    print(f"   y shape: {y.shape}  →  (samples,)")

    return X, y


# ─── STEP 8: SAVE PROCESSED DATA ──────────────────────────
def save_processed(df: pd.DataFrame, X: np.ndarray,
                   y: np.ndarray, city: str = "all"):
    """
    Saves cleaned DataFrame and LSTM sequences to data/processed/
    """
    os.makedirs("data/processed", exist_ok=True)

    # Save clean DataFrame
    csv_path = f"data/processed/{city}_clean.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Clean data saved → {csv_path}")

    # Save sequences as numpy arrays
    if X is not None and y is not None:
        np.save(f"data/processed/{city}_X.npy", X)
        np.save(f"data/processed/{city}_y.npy", y)
        print(f"✅ Sequences saved → data/processed/{city}_X.npy")
        print(f"✅ Targets saved  → data/processed/{city}_y.npy")


# ─── MAIN PIPELINE ────────────────────────────────────────
def run_pipeline(city: str = "bengaluru"):
    """
    Runs the full preprocessing pipeline for a city.
    """
    print(f"\n{'='*55}")
    print(f"  Preprocessing Pipeline — {city.upper()}")
    print(f"{'='*55}")

    # 1. Load
    df = load_raw_data(city)
    if df.empty:
        return

    # 2. Clean
    df = clean_data(df)

    # 3. Handle missing
    df = handle_missing_values(df)

    # 4. Time features
    df = engineer_time_features(df)

    # 5. Lag features
    df = engineer_lag_features(df)

    # 6. Normalize
    df, scaler = normalize_features(df, fit=True)

    # 7. Build sequences
    X, y = build_sequences(df, city=city)

    # 8. Save
    save_processed(df, X, y, city=city)

    print(f"\n{'='*55}")
    print(f"  ✅ Pipeline complete for {city.upper()}")
    print(f"{'='*55}\n")

    return df, X, y


# ─── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline("bengaluru")