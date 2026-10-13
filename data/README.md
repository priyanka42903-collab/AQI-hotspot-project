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

## Known Limitations (summary)
- No date overlap between historical (2015-2020) and recent (2025-2026) tracks - any
  trend analysis across the full period must account for this gap explicitly.
- Historical AQI missingness is uneven across cities (worst: Mumbai, Patna) due to
  staggered real-world station installation dates, not random data loss.
- Historical and recent AQI come from two different computation paths (Kaggle's own vs.
  our CPCB implementation) and have not been cross-validated against each other.
- Patna's NO2/SO2/CO (OpenAQ track) and Mumbai's Toluene/Xylene (Kaggle track) are
  excluded entirely due to persistently high missingness even within their active
  monitoring windows.
