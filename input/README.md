# Input Data

This directory is a placeholder. The raw data files are not included in the repository, but are freely available online (links are included in this document).

## What goes here

### `turdata/`
Oslo Bysykkel trip data, downloaded from [oslo.bysykkel.no/en/open-data](https://oslo.bysykkel.no/en/open-data).

Expected structure:
```
turdata/
├── 2021/
│   ├── 2021-01.csv
│   ├── 2021-02.csv
│   └── ...
├── 2022/
│   └── ...
└── 2025/
    └── ...
```

Each CSV contains one row per trip with at minimum: `started_at`, `ended_at`, `duration`.

### `seklima/`
Hourly weather observations for Oslo Blindern from [seklima.met.no](https://seklima.met.no).

Expected files:
```
seklima/
├── lufttemp.csv          # air temperature
├── nedbør.csv            # precipitation
├── middelvind.csv        # mean wind speed
└── skydekke.csv          # cloud cover
```

Download station **18700 – Oslo Blindern** for the same date range as your trip data.

### `oslo_holidays_2020_2027.csv`
Already included — a manually curated CSV of Oslo school holidays and Norwegian national holidays used as model features.
