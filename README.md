# India air quality analysis: 7 cities, 2015-2026

An end-to-end analysis of daily AQI in Bengaluru, Chennai, Delhi, Kolkata, Lucknow, Mumbai and Patna. It merges CPCB data (2015-2020) with OpenAQ readings (2025-26) and weather, answers questions in pandas and SQL, and presents the results in a one-page Power BI dashboard.

![Dashboard overview](reports/screenshots/dashboard_overview.png)

## Key findings

- **Winter dominates.** Winter average AQI is 2.9x summer in Kolkata and 2.0x in Patna, against about 1.2x in Chennai and Bengaluru. Kolkata's 2.9x rests on about 40 months of data.
- **Delhi is the worst city.** 61% of its days are Poor, Very Poor or Severe; Bengaluru has 66% Good or Satisfactory days.
- **Delhi's days above 300** fell from 50% (2015) to 26% (2019) in the historical data.
- **Particulate matter sets the AQI** on most days in every city (PM2.5 or PM10 together about 72% or more).
- **Rain is associated with lower winter AQI** in Chennai, Bengaluru, Delhi and Lucknow (the cities with 20+ rainy winter days). This is an association, not proof of cause.
- **No weekday effect:** daily AQI varies by under 2% across weekdays.

## Data

| Source | Period | Used for |
|---|---|---|
| CPCB via Kaggle (`city_day`) | 2015-01-01 to 2020-07-01 | Historical AQI and pollutants |
| OpenAQ | 2025-08-01 to 2026-08-10 | Recent pollutants (AQI computed here) |
| Open-Meteo | both periods | Temperature, rain, wind, humidity |

There is no data between July 2020 and July 2025. Details, cleaning rules and corrections are in [`data/README.md`](data/README.md).

## Method

1. Standardise city names, parse dates, and handle missing data (40% threshold, measured from each station's first reading; short gaps forward-filled).
2. Pivot OpenAQ to one row per city-day, remove sensor errors, and compute AQI with the CPCB breakpoint formula (`src/aqi_calculator.py`).
3. Merge pollutants with weather (lossless for the 7 cities) and save `data/processed/aqi_weather_master.csv`.
4. Analyse in pandas (`reports/figures/`) and SQLite (`sql/`).
5. Build the Power BI dashboard (`dashboard/`).

## SQL queries

| File | Question |
|---|---|
| `sql/01_worst_months.sql` | Worst 5 months per city |
| `sql/02_days_above_300.sql` | Days above AQI 300 per year |
| `sql/03_winter_summer_ratio.sql` | Winter vs summer AQI |
| `sql/04_days_by_category.sql` | Days per CPCB category |
| `sql/05_rain_vs_dry_winter.sql` | Rainy vs dry winter days |

## Dashboard

[Delhi view](reports/screenshots/dashboard_delhi.png) | [Bengaluru view](reports/screenshots/dashboard_bengaluru.png)

## Limitations

- **The two AQI sources differ.** Historical AQI is Kaggle's. Recent AQI is calculated here. On 10,674 overlapping historical days our calculation is about 11 points lower on average (correlation 0.94, typical gap about 27 points). Compare within each period, not across.
- **Kolkata and Mumbai start in 2018**, so their trends are thin.
- **Dominant pollutant** is the highest CPCB sub-index among six pollutants, not the official driver.
- Lucknow has no 2015-20 PM10, and Patna's recent NO2, SO2 and CO were excluded for missing data.

## Reproduce

```bash
python -m venv .venv
.venv\Scripts\activate
pip install pandas numpy matplotlib notebook python-dotenv requests
```
Put your OpenAQ key in `.env` as `OPENAQ_API_KEY=...` (not committed), then run `notebooks/data_cleaning.ipynb`, `02_analysis.ipynb` and `03_sql_queries.ipynb` in order, and open the dashboard in Power BI Desktop.