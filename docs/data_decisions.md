# Data Collection Decisions

This document tracks key data-scoping decisions made during Phase 0, and the reasoning behind them. Each entry follows: **situation → decision → why → downstream impact**.

---

## 1. City subset: 7 cities, not 8

**Situation:** Original plan targeted 8 cities including Kochi for geographic spread.

**Decision:** Dropped Kochi, finalized on 7 cities: Delhi, Lucknow, Patna, Mumbai, Bengaluru, Chennai, Kolkata.

**Why:** Kochi had only 1 OpenAQ station (checked under "Kochi," "Cochin," and "Ernakulam" — all point to the same single station). A single station can't support spatial clustering or any within-city comparison, so it would have added a city to the project without adding analytical value.

**Impact:** No loss of regional coverage — Chennai already represents coastal south India. 7 cities gives clean geographic spread (north, central, west, south x2, east) without a token city that can't be meaningfully analyzed.

---

## 2. Sensor deduplication: one sensor per station per parameter

**Situation:** OpenAQ locations sometimes report the same pollutant from multiple sensors in different units (e.g., R K Puram had both `co µg/m³` and `co ppb` sensors simultaneously).

**Decision:** For each station + parameter combination, kept only the µg/m³ sensor, dropped duplicates in other units.

**Why:** CPCB's official AQI breakpoint formula is defined in µg/m³. Keeping duplicate unit-readings risked double-counting or averaging incompatible units if not caught downstream.

**Impact:** Reduced from 2,160 raw sensor entries to 974 after deduplication and filtering to AQI-relevant parameters only (dropped wind/temperature/humidity sensors — covered separately via Open-Meteo — and NO/NOx, which aren't part of the CPCB AQI formula).

---

## 3. Two-tier city analysis: spatial clustering vs. trend-only

**Situation:** After pulling live OpenAQ measurements (Aug 2025–Aug 2026), active station density varied sharply by city:

| City | Historical stations (CPCB 2015-2020) | Live stations (OpenAQ, current) |
|---|---|---|
| Delhi | 38 | 42 |
| Mumbai | 10 | 29 |
| Bengaluru | 10 | 12 |
| Chennai | 4 | 8 |
| Kolkata | 7 | 7 |
| Lucknow | 5 | 5 |
| Patna | 6 | 4 |

**Decision:** Split cities into two analytical tiers:
- **Tier 1 (spatial hotspot detection via DBSCAN):** Delhi, Mumbai, Bengaluru, Chennai, Kolkata — all have 7+ live stations, sufficient density for meaningful spatial clustering.
- **Tier 2 (trend/time-series analysis only):** Lucknow, Patna — consistently sparse in both historical and current data; not enough spatial density to support reliable clustering.

**Why:** DBSCAN and other spatial hotspot methods need multiple nearby points to form clusters. With only 4-5 stations spread across a city, clustering output would be either one meaningless mega-cluster or mostly noise — not a reliable signal.

**Note on network growth:** Contrary to an initial hypothesis of network *contraction*, most cities' monitoring networks have actually grown since 2020 (Mumbai nearly tripled, Chennai doubled). Patna is the exception — the only city with a station count decline (6 → 4). Station density correlates with city tier/population rather than reflecting a general infrastructure decline.

**Impact:** Forecasting (Prophet) and cross-city comparison apply to all 7 cities. Spatial hotspot detection (DBSCAN, Folium mapping) is scoped to the 5 Tier 1 cities, with Lucknow and Patna's limitation stated explicitly in the final write-up rather than glossed over.

---

## 4. Sensor freshness: no separate pre-filter, handled in-loop

**Situation:** Considered adding a dedicated "is this sensor still active" filter before pulling measurements, to avoid wasting API calls on dead sensors.

**Decision:** Skipped the pre-filter. Instead, the measurement-pull script treats any sensor returning zero results as dead and logs it, without requiring extra API calls upfront.

**Why:** A separate freshness check would have required ~974 additional API calls (one per sensor) just to check `datetimeLast`. Since dead sensors simply return `found: 0` when queried directly, no extra cost is incurred by just handling this in the main pull loop.

**Impact:** 653 of 974 sensors (67%) returned no data in the Aug 2025–Aug 2026 window and were logged to `data/processed/dead_sensors.csv`. Final working dataset: 321 active sensors across 107 stations.