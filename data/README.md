# AQI Weather Master Dataset — Data Documentation

## Data Sources
- `data/raw/kaggle/city_day.csv` — CPCB historical air quality data (city-day granularity),
  covering 2015-01-01 to 2020-07-01, 26 Indian cities.
- `data/raw/openaq/openaq_recent.csv` — OpenAQ recent air quality data, long format
  (one row per sensor-parameter-day), covering 2025-08-01 to 2026-08-10, 7 target cities.
- `data/raw/weather/weather_historical.csv` — Open-Meteo weather data matching the Kaggle date range.
- `data/raw/weather/weather_recent.csv` — Open-Meteo weather data matching the OpenAQ date range.

## Target Cities
Bengaluru, Chennai, Delhi, Kolkata, Lucknow, Mumbai, Patna

`weather_historical.csv` originally covered 26 cities nationally; it was filtered down to
the 7 target cities early in the pipeline, since the other 19 have no corresponding
pollutant data in the OpenAQ track.

## City Name Standardization
City names were inconsistent in spelling/format across sources (e.g. "Bangalore" vs
"Bengaluru"). A single mapping dictionary (`city_mapping`) was applied identically to all
four raw dataframes before any merging, to avoid silent row loss from mismatched keys.

## Date Parsing & Derived Features
All date columns were converted to `datetime64`. From each date, the following were
derived and reused throughout: `year`, `month`, `day_of_week` (0=Monday), and `season`
(winter = Nov-Feb, summer = Mar-Jun, monsoon = Jul-Sep, post_monsoon = Oct).

## OpenAQ Reshaping
`openaq_recent.csv` was supplied in long format (one row per sensor-parameter-day).
It was pivoted to wide format (one row per city-day, one column per pollutant) to match
the Kaggle schema, averaging across multiple sensors/readings within the same city-day
(`aggfunc='mean'`). Pollutant parameter names were mapped to Kaggle's naming convention
(e.g. `pm25` -> `PM2.5`, `no2` -> `NO2`) for consistency.

## Historical vs Recent: No Date Overlap
The Kaggle/weather_historical track (2015-2020) and the OpenAQ/weather_recent track
(2025-2026) do not overlap in time at all. They were therefore cleaned and merged as two
independent tracks, each merged against its matching weather file, then concatenated
into one master table with a `data_source` column (`kaggle_historical` /
`openaq_recent`) to preserve provenance. This gap is a known structural feature of the
project's data, not a bug.

## Missing Data Policy
A two-tier rule was applied per city-pollutant pair:
1. **Active-window scoping**: missing % is computed only from a pollutant's first valid
   reading onward for that city, not from the dataset's global start date. This avoids
   penalizing a pollutant for the period before its monitoring station existed. City-
   pollutant pairs with no valid reading at all are dropped outright (100% missing).
2. **Threshold**: pairs with >=40% missing within their active window are excluded from
   analysis (set to NaN). Pairs below the threshold have short gaps (<=2 consecutive days)
   forward-filled per city; longer gaps are left as NaN rather than fabricated.

### Why active-window scoping mattered (concrete example)
Under a naive "missing % from the dataset's start date" rule, Mumbai's PM2.5, PM10, NO,
NO2, SO2, and O3 all showed 60-62% missing and would have been dropped entirely -
removing nearly all core pollutants for one of the 7 target cities. Investigation showed
these stations simply came online between Dec 2017 and Apr 2018; data from that point
onward is ~100% complete. Rescoping missing-% calculation to each pollutant's active
window correctly retained all six columns for Mumbai. Only Mumbai-Toluene (49.4%) and
Mumbai-Xylene (49.5%) remained excluded even within their active window.

### Dropped city-pollutant pairs (Kaggle track, final)
Includes: Ahmedabad-NH3, Bhopal-{Benzene,Toluene,Xylene}, several cities' Xylene columns
(mostly 100% missing - never measured), Jorapokhar-{NOx,CO}, Lucknow-PM10,
Mumbai-{Toluene,Xylene}, Talcher-Toluene, Thiruvananthapuram-{Benzene,Toluene}, and others.
Full list captured in the cleaning notebook's `dropped_kaggle_v2` output.

### Dropped city-pollutant pairs (OpenAQ track, final)
Patna-NO2, Patna-SO2, Patna-CO — all ~87-100% missing throughout their active window
(not a late-start issue; this sensor appears to have been unreliable for its full
operating period, unlike Mumbai's case above).

## Sensor Error Cleanup (OpenAQ track only)
Before AQI computation, raw OpenAQ values were checked against physically plausible
bounds:
- Negative concentrations (impossible): 2 rows each for NO2, CO, O3 (~0.1% of rows).
- Extreme outliers: PM2.5 > 1000 ug/m3 (11 rows, 0.4%), PM10 > 1000 ug/m3 (12 rows, 0.5%).
All flagged values were set to NaN and passed back through the same missing-data rule
above (short-gap forward-fill / threshold-drop). No new city-pollutant pairs crossed the
drop threshold as a result.

## Merge (Step 5)
Two separate inner joins on `(city, date)`:
- `city_day` (filtered to 7 target cities) x `weather_hist` -> 12,717 rows, 0 rows dropped
  (lossless once scoped to target cities; the pre-filter version showed a 57% drop that
  was entirely attributable to the 19 out-of-scope cities, not a real data gap).
- `openaq_wide` x `weather_recent` -> 2,566 rows, 0 rows dropped (lossless).

## AQI Calculation (Step 6)
- **Historical track**: AQI is Kaggle's own precomputed value, carried through the merge
  as-is. It has its own missingness (16.1% of historical rows overall), heavily
  concentrated in Mumbai (61.4% missing) and Patna (21.5% missing) - both explained by
  the same late-station-start pattern documented above. Other cities show <8% missing.
- **Recent track**: AQI was computed from scratch using the CPCB breakpoint formula
  (`aqi_calculator.py` / `compute_aqi`), taking the max of all available pollutant
  sub-indices per row (CPCB methodology - AQI reflects the worst pollutant, not an
  average). Validated against known reference points (15 ug/m3 PM2.5 -> sub-index 25;
  45 ug/m3 -> 74.66; values beyond all breakpoints cap at 500). Result: 0 rows with
  uncomputable AQI across all 2,566 recent rows.
- **Known limitation**: historical and recent AQI were not cross-validated against each
  other using the same formula on the same data, so exact numerical consistency between
  the two tracks' AQI methodology is assumed, not independently verified.
- **Sanity check**: city-level recent-track AQI means ranged from 77 (Bengaluru) to 203
  (Delhi), consistent with Delhi's known status as India's most polluted major city -
  treated as a validation signal that the calculation is behaving correctly.

## Final Master Table
Saved to `data/processed/aqi_weather_master.csv` - 15,283 rows total
(12,717 kaggle_historical + 2,566 openaq_recent).

Columns: `city`, `date`, `year`, `month`, `season`, `day_of_week`, `PM2.5`, `PM10`,
`NO2`, `SO2`, `CO`, `O3`, `AQI`, `data_source`, `temperature_2m_max`,
`temperature_2m_min`, `precipitation_sum`, `windspeed_10m_max`,
`relative_humidity_2m_mean`.

Only the 6 pollutants common to both tracks (PM2.5, PM10, NO2, SO2, CO, O3) are included
in the master table for cross-track comparability. Kaggle-only pollutants (NO, NOx, NH3,
Benzene, Toluene, Xylene) remain available in the intermediate `merged_historical`
dataframe for historical-only analysis if needed later, but were not carried into the
unified master file.

## Corrections made after the first cleaning pass

- **CPCB gap-band bug.** The first AQI function skipped concentrations that fall in the small gaps between CPCB bands (for example PM2.5 of 30.5). It affected 58 of 2,566 recent rows (mean change 24 points, max 147). Fixed in `src/aqi_calculator.py`.
- **Recent-track AQI rule.** A day needs at least one pollutant and a PM value (PM2.5 or PM10). 5 Bengaluru days (2025-11-29 to 2025-12-10) had only O3 and have no AQI. 3 Delhi days with only PM2.5 are kept.
- **Historical CO cleaning.** 213 historical CO readings above 10 mg/m3 (Lucknow 73, Bengaluru 65, Delhi 65, Chennai 10) were set to NaN as implausible. Mumbai's historical CO median is 0.00, which suggests zeros stand in for missing values. This was not corrected.
- **Out-of-scale AQI.** 88 Kaggle AQI values exceed 500. They are kept and counted as Severe.

## Dominant pollutant

`dominant_pollutant` is the pollutant with the highest CPCB sub-index among PM2.5, PM10, NO2, SO2, CO and O3. Historical rows need at least 3 pollutants including a PM value; recent rows need at least 1 including a PM value. Kaggle's own AQI may use pollutants outside these six, so this is "dominant among six", not the official driver. Lucknow has no historical PM10. PM10 leads in every recent city while PM2.5 leads in several historical ones. That shift looks like a measurement difference between OpenAQ and CPCB stations, not a change in the air.

## Cross-check: our AQI vs Kaggle's

On 10,674 historical days where both exist: correlation 0.944, mean difference (ours minus Kaggle's) -11.5, mean absolute difference 26.9, and about 30% of days within 10 points. The two follow the same pattern but differ in level, so no chart compares a historical value directly with a recent one.

## SQL analysis

The master table is loaded into SQLite (`db/aqi.db`, not committed, regenerate it from the CSV) and queried from `notebooks/03_sql_queries.ipynb`. Dates are stored as text, so month and year use `strftime`. Each query is saved in `sql/`.

| File | Question | Main result |
|---|---|---|
| `01_worst_months.sql` | Worst 5 months per city (months with 20+ days of AQI) | Delhi's worst is Nov 2016 (474.8). Delhi, Lucknow, Patna and Kolkata peak Oct-Feb. Bengaluru and Chennai have no winter spike. Only Chennai (Dec 2025) and Mumbai (Oct and Nov 2025) have recent months in their top 5. |
| `02_days_above_300.sql` | Days above AQI 300, per city and year | Delhi 50.1% of days in 2015, 26.0% in 2019. Lucknow peaks near 42% (2016-17). Bengaluru, Mumbai and Chennai rarely exceed 300. 2020, 2025 and 2026 are partial years. |
| `03_winter_summer_ratio.sql` | Average AQI, winter (Nov-Feb) vs summer (Mar-Jun) | Kolkata 2.92, Patna 2.00, Lucknow 1.77, Mumbai 1.68, Delhi 1.59, Chennai 1.18, Bengaluru 1.18. |
| `04_days_by_category.sql` | Days per CPCB category | Delhi 61.0% Poor or worse. Bengaluru 66.3% Good or Satisfactory. |
| `05_rain_vs_dry_winter.sql` | AQI on rainy (2.5 mm or more) vs dry (under 0.1 mm) winter days | Lower on rainy days in all 7 cities. Reliable only where there are 20+ rainy days: Chennai 94.9 vs 138.4, Bengaluru 91.0 vs 109.1, Delhi 301.7 vs 358.8, Lucknow 262.8 vs 313.7. |

Caveats: Kolkata's ratio rests on about 40 months of data. Patna's 2015 and 2017 percentages in Query 2 come from only 81 and 144 days. Rain is associated with lower AQI, not shown to cause it. Wind and temperature move with rain.

## Power BI dashboard

Files: `dashboard/aqi_dashboard.pbix`, `dashboard/aqi_theme.json`, data from `data/dashboard/aqi_dashboard.csv` (15,213 rows; drops the 70 rows after 2026-07-31 and adds `aqi_category`, `track`, `month_name`).

Page: 3 slicers (city, period, season), 4 KPI cards, monthly trend, city-by-month heatmap, category mix, dominant pollutant by period, winter vs summer, rain vs dry, and a footer with caveats.

Design decisions:
- The trend line uses a continuous date axis with one line per period, so the 2020-2025 gap shows as empty space.
- Dominant pollutant uses small multiples to keep the two periods apart.
- The rain chart blanks any bar with fewer than 20 days.
- Heatmap and category colours use the CPCB bands.

Measures: `Average AQI`, `Pct Poor or Worse` (days above 200 divided by days with AQI), `Days Above 300`, `Days With AQI`, `Dominant Share`.

Validation against SQL: with no filter the cards show 13,165 days with AQI, 2,124 days above 300 and 28.2% Poor or worse. With Delhi selected they show 2,364 days, 866 days above 300 (the sum of Query 2's Delhi rows) and 61.2% Poor or worse (Query 4 gives 61.0% because it includes 10 extra days after the dashboard cut-off).

## Known limitations (summary)

- No data between July 2020 and July 2025, so cross-period trends need care.
- Historical AQI is Kaggle's. Recent AQI is our CPCB calculation, about 11 points lower on average (correlation 0.94). Compare within each period.
- Historical AQI missingness is uneven (Mumbai 61%, Patna 22%) because stations started at different times.
- Kolkata and Mumbai start in 2018.
- Excluded: Patna's recent NO2, SO2 and CO; Mumbai's Toluene and Xylene; Lucknow's historical PM10.
- Dominant pollutant is among six pollutants only, and OpenAQ and CPCB shares are not comparable.

## Station Coverage Limitation
- Stations were selected by city name, so neighbouring towns (Noida, Ghaziabad, Thane and others) and some real city stations without the city name (for example Delhi’s IGI Airport and Civil Lines) are not included. 
- 27% to 71% of selected stations per city were also dropped by the dead-sensor step, which has not been verified. 
- Patna’s recent figures rest on a single PM station.

