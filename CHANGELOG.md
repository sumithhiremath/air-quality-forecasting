# CLIMA — Project Changelog

All significant changes to this project are documented here.
Format: `[DayN] YYYY-MM-DD — Description`

---

## [Day 4] 2026-07-07 — Foundation Hardening & Bug Fixes

### Bugs Fixed
- **FIXED**: `src/ingestion.py` — Added `"pune"` to CITIES list.
  Pune was missing despite BLR_PUN route existing in route_config.py.
  The Bengaluru→Pune route was silently never scored.

- **FIXED**: `src/ingestion.py` — Temperature validation added.
  Mumbai WAQI station was returning -19.2°C (bad sensor / unit mismatch).
  All readings now validated against India-realistic physical bounds.
  Bad readings are logged as `data_quality_flags` and set to `None`
  rather than silently stored as corrupt values.

- **FIXED**: All Python scripts — Windows encoding crash resolved.
  Scripts were crashing on Windows with `UnicodeEncodeError` due to emoji
  in print statements. Added `sys.stdout.reconfigure(encoding="utf-8")`
  guard at top of all scripts.

- **FIXED**: `src/risk/live_risk.py` — Now tracked by git (was untracked).
  Also fixed absolute path resolution so script runs from any directory.

- **FIXED**: `src/risk/live_risk.py` — Data quality gate added.
  Cities with flagged sensor data are skipped from risk scoring
  rather than passed through with corrupted values.

- **FIXED**: `src/risk/risk_engine.py` — ASCII arrow fix in route names.
  Unicode arrow `→` was crashing on Windows terminals.

- **FIXED**: `.github/workflows/collect_data.yml` — Added WAQI_TOKEN
  validation step. Workflow now fails loudly with a clear error message
  if the secret is not set, instead of silently collecting no data.

### Data Collected
- First ever collection of **Pune** AQI data (AQI=232, Very Poor)
- Fresh snapshot collected for all 6 cities: 2026-07-07 14:01 UTC

### Risk Assessment Results (Day 4 — General Cargo)
| Route | Risk Score | Level | Est. Loss |
|-------|-----------|-------|-----------|
| Bengaluru → Pune | 27.8/100 | LOW | Rs. 7,284 |
| Bengaluru → Delhi | 19.0/100 | LOW | Rs. 13,300 |
| Bengaluru → Hyderabad | 12.0/100 | LOW | Rs. 2,100 |
| Bengaluru → Chennai | 11.0/100 | LOW | Rs. 1,155 |
| Total exposure | — | — | Rs. 23,839 |

Note: Bengaluru→Mumbai not scored (Mumbai temp sensor flagged, data excluded).

### What Still Needs Work
- Mumbai WAQI station returns stale/corrupt temperature. Need alternate source.
- Only 4 collections so far — need 30+ days for LSTM training.
- `src/train.py`, `src/predict.py`, `api/main.py`, `dashboard/app.py` still empty.

---

## [Day 3] 2026-07-05 — Risk Engine + Preprocessing

### Added
- `src/risk/risk_engine.py` — Weather-based risk scoring engine
  - AQI, humidity, wind, temperature risk factors
  - Seasonal risk overlay per route
  - Financial impact calculator (Rs. exposure per route)
  - 4 risk levels: LOW / MEDIUM / HIGH / SEVERE

- `src/routes/route_config.py` — Route and cargo database
  - 5 Indian highway routes (Bengaluru hub)
  - 5 cargo types with delay sensitivity multipliers
  - Seasonal risk profiles per route

- `src/risk/live_risk.py` — End-to-end live risk pipeline
  (was never committed to git — fixed in Day 4)

- `src/preprocess.py` — 8-step LSTM preprocessing pipeline
  - Data cleaning, missing value imputation
  - Time feature engineering (hour, day, season, rush hour)
  - Lag features (AQI lag 1h, 3h, 6h, 12h)
  - Rolling statistics (mean, std)
  - MinMaxScaler normalization
  - 3D sequence builder for LSTM input

- `.github/workflows/collect_data.yml` — Hourly GitHub Actions workflow
  (had permissions bug, fixed later in Day 3)

### Issues (Fixed in Day 4)
- Pune missing from CITIES list
- Mumbai temperature corruption stored without validation
- `live_risk.py` never committed to git
- Terminal encoding crashes on Windows

---

## [Day 2] 2026-07-03 — Live Data Ingestion

### Added
- `src/ingestion.py` — WAQI API integration
  - Fetches AQI, PM2.5, PM10, NO2, CO, O3, SO2, temperature, humidity, wind
  - Saves per-city CSV + combined all_cities CSV
  - Uses `.env` for API token management

### Issues (Fixed in Day 4)
- Pune not included in city list
- No data validation (bad sensor values stored silently)
- Emoji in print statements crash on Windows

---

## [Day 1] 2026-07-02 — Project Structure

### Added
- Initial folder structure: `src/`, `data/`, `models/`, `api/`, `dashboard/`, `reports/`
- `requirements.txt` with all planned dependencies
- `.env` file for secrets
- `.gitignore`
- Initial `README.md`
- Git repository initialized and pushed to GitHub
