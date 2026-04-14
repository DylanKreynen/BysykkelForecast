# Oslo Bysykkel — 9-Day Trip Forecast

Predicts hourly Oslo city bike trip counts up to 9 days ahead using XGBoost and live weather forecasts from MET Norway.

A GitHub Actions workflow runs every morning to fetch the latest weather forecast and update the predictions automatically — no manual intervention needed.

---

## How it works

**1. Data** (`01_data_exploration.ipynb`)  
Five years of Bysykkel trip data (2021–2025) are merged with hourly weather observations from Oslo Blindern and explored for seasonal patterns and weather correlations.

**2. Model** (`02_model.ipynb`)  
An XGBoost model is trained on engineered features: cyclical time encodings, weather lags, threshold flags, holiday indicators, and a consecutive-dry-days streak. Two separate models are trained — one for weekday hours (Mon–Fri) and one for weekends — and evaluated with time-series cross-validation. Final test MAE: ~13 trips/hour.

**3. Forecast** (`03_forecast.ipynb`)  
The trained models are applied to a 9-day hourly weather forecast fetched from the [MET Norway Locationforecast 2.0 API](https://api.met.no/) for Blindern (lat 59.9423, lon 10.7200).

**4. Dashboard** (`dashboard/`)  
A Streamlit dashboard visualises the forecast alongside temperature and precipitation. A GitHub Actions workflow (`update_forecast.yml`) re-runs the forecast script every morning at 04:00 Oslo time and commits the new CSV to the repository.

---

## Repository structure

```
├── 01_data_exploration.ipynb   # data loading, merging, correlation analysis
├── 02_model.ipynb              # feature engineering, training, evaluation
├── 03_forecast.ipynb           # generate and visualise a 9-day forecast
├── input/                      # raw trip + weather data (see input/README.md)
├── output/
│   ├── model_weekday.joblib    # trained XGBoost model (Mon–Fri)
│   ├── model_weekend.joblib    # trained XGBoost model (Sat–Sun)
│   └── forecasts/              # forecast CSVs updated daily by GitHub Actions
└── dashboard/
    ├── dashboard.py            # Streamlit dashboard
    ├── bysykkel_forecast.py    # forecast script (called by GitHub Actions)
    └── requirements.txt
```

---

## Running locally

```bash
pip install -r dashboard/requirements.txt

# Generate a forecast
python dashboard/bysykkel_forecast.py

# Launch the dashboard
streamlit run dashboard/dashboard.py
```

To reproduce the full pipeline from raw data, place your input files in `input/` as described in [`input/README.md`](input/README.md), then run the three notebooks in order.

---

## Data sources

- **Trip data:** [Oslo Bysykkel open data](https://oslo.bysykkel.no/en/open-data)
- **Weather observations:** [Seklima (MET Norway)](https://seklima.met.no) — station 18700, Oslo Blindern
- **Weather forecast:** [MET Norway Locationforecast 2.0](https://api.met.no/)
