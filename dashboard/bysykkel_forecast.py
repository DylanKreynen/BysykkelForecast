#!/usr/bin/env python3
"""
Oslo Bysykkel — Automated 9-Day Forecast
=========================================
Fetches the MET Norway Locationforecast 2.0 weather data for Blindern,
engineers the same features used during model training, generates hourly
trip-count predictions, and saves the result to output/forecasts/.

Usage
-----
  python dashboard/bysykkel_forecast.py          # run once
  (scheduled via .github/workflows/update_forecast.yml)
"""

import warnings
warnings.filterwarnings("ignore")

import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import joblib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR           = Path(__file__).parent.parent          # repo root
MODEL_WEEKDAY_PATH = BASE_DIR / "output" / "model_weekday.joblib"
MODEL_WEEKEND_PATH = BASE_DIR / "output" / "model_weekend.joblib"
FORECAST_DIR       = BASE_DIR / "output" / "forecasts"
HOLIDAYS_PATH      = BASE_DIR / "input" / "oslo_holidays_2020_2027.csv"

LAT, LON, ALT  = 59.9423, 10.7200, 94         # Blindern weather station
USER_AGENT     = os.environ.get("MET_USER_AGENT", "BysykkelForecast")
FORECAST_DAYS  = 9

# Total trips taken in the previous calendar year.
# Update this value each January once the annual Bysykkel data is available.
# (hardcoded here because the dataset is not included on the GitHub repo)
PREV_YEAR_TRIPS = 1112055   # 2025 total


# ── Model ──────────────────────────────────────────────────────────────────────
def load_model(path: Path):
    bundle       = joblib.load(path)
    model        = bundle["model"]
    feature_cols = bundle["features"]
    log.info(f"Model loaded: {bundle.get('name', 'XGBoost')}  "
             f"({len(feature_cols)} features)")
    return model, feature_cols


# ── Weather fetch ──────────────────────────────────────────────────────────────
def fetch_forecast() -> tuple[pd.DataFrame, pd.Timestamp]:
    """Return (hourly_df, fetch_timestamp_oslo)."""
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/complete"
        f"?lat={LAT:.4f}&lon={LON:.4f}&altitude={ALT}"
    )
    fetch_time = pd.Timestamp.now(tz="Europe/Oslo")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()

    rows = []
    for entry in resp.json()["properties"]["timeseries"]:
        t       = pd.Timestamp(entry["time"]).tz_convert("Europe/Oslo").tz_localize(None)
        instant = entry["data"]["instant"]["details"]

        precip = None
        for window in ("next_1_hours", "next_6_hours", "next_12_hours"):
            if window in entry["data"]:
                precip = entry["data"][window]["details"].get("precipitation_amount")
                break

        rows.append({
            "hour":                t,
            "temp_c":              instant.get("air_temperature"),
            "wind_speed_ms":       instant.get("wind_speed"),
            "cloud_area_fraction": instant.get("cloud_area_fraction"),
            "precip_mm":           precip,
        })

    df = pd.DataFrame(rows).set_index("hour")
    df["precip_mm"] = df["precip_mm"].ffill()

    start    = df.index[0]
    end      = start + pd.Timedelta(days=FORECAST_DAYS)
    df       = df.loc[start:end]
    full_idx = pd.date_range(start, end, freq="h", inclusive="left")
    df       = df.reindex(full_idx).interpolate("time")
    df.index.name = "hour"

    log.info(f"Fetched: {len(df)} hours  ({df.index[0]} → {df.index[-1]})")
    return df.reset_index(), fetch_time


# ── Feature engineering ────────────────────────────────────────────────────────
def load_holidays(path: Path) -> tuple[set, set]:
    hol = pd.read_csv(path)
    hol["date"] = pd.to_datetime(hol["date"], format="%d-%m-%Y").dt.date
    school   = set(hol.loc[hol["oslo_school_holiday"],  "date"])
    national = set(hol.loc[hol["national_holiday"],     "date"])
    log.info(f"Holidays: {len(school)} school days, {len(national)} national days")
    return school, national


def cyclical(series: pd.Series, period: int) -> tuple[pd.Series, pd.Series]:
    rad = 2 * np.pi * series / period
    return np.sin(rad), np.cos(rad)


def engineer_features(df: pd.DataFrame, school_hols: set, national_hols: set) -> pd.DataFrame:
    df = df.copy()

    # Calendar
    df["hour_of_day"] = df["hour"].dt.hour
    df["day_of_week"] = df["hour"].dt.dayofweek
    df["month"]       = df["hour"].dt.month

    # Cyclical encodings
    df["hour_sin"],  df["hour_cos"]  = cyclical(df["hour_of_day"], 24)
    df["month_sin"], df["month_cos"] = cyclical(df["month"],       12)
    df["day_of_year"]                = df["hour"].dt.dayofyear
    df["doy_sin"],   df["doy_cos"]   = cyclical(df["day_of_year"], 365)

    # 1-hour precipitation lag
    df["precip_mm_lag1h"] = df["precip_mm"].shift(1).bfill()

    # Annual trip total (previous calendar year)
    df["prev_year_trips"] = PREV_YEAR_TRIPS

    # Holiday flags
    df["is_school_holiday"]   = df["hour"].dt.date.map(lambda d: int(d in school_hols))
    df["is_national_holiday"] = df["hour"].dt.date.map(lambda d: int(d in national_hols))

    return df


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)

    weekday_model, weekday_features = load_model(MODEL_WEEKDAY_PATH)
    weekend_model, weekend_features = load_model(MODEL_WEEKEND_PATH)
    school_hols, national_hols = load_holidays(HOLIDAYS_PATH)

    log.info("Fetching weather forecast from MET Norway...")
    raw, fetch_time = fetch_forecast()

    features = engineer_features(raw, school_hols, national_hols)

    for label, feat_cols in [("weekday", weekday_features), ("weekend", weekend_features)]:
        missing = features[feat_cols].isna().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            log.warning(f"Missing {label} feature values — will predict with NaN:\n{missing}")

    is_closed  = features["hour"].dt.hour.isin([1, 2, 3, 4])  # 01:00–04:59 Oslo time
    is_weekend = features["hour"].dt.dayofweek.isin([5, 6])

    predicted = np.zeros(len(features))   # closed hours stay at 0

    open_weekday = ~is_closed & ~is_weekend
    open_weekend = ~is_closed &  is_weekend
    predicted[open_weekday] = weekday_model.predict(features.loc[open_weekday, weekday_features].values)
    predicted[open_weekend] = weekend_model.predict(features.loc[open_weekend,  weekend_features].values)
    predicted = np.clip(predicted, 0, None).round().astype(int)

    forecast = features[["hour"]].copy()
    forecast["predicted_trips"] = predicted
    for col in ["temp_c", "precip_mm", "wind_speed_ms", "cloud_area_fraction",
                "is_school_holiday", "is_national_holiday"]:
        forecast[col] = features[col].values

    out_path = FORECAST_DIR / f"9day_{fetch_time:%d%m%y-%H.%M}.csv"
    forecast.to_csv(out_path, index=False)
    log.info(f"Saved  → {out_path}  ({forecast.shape[0]} rows × {forecast.shape[1]} cols)")
    log.info(f"Total predicted trips: {forecast['predicted_trips'].sum():,}")


if __name__ == "__main__":
    main()
