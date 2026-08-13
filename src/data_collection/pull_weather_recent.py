import requests
import pandas as pd
import os
import time

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

city_coords = {
    "Delhi": (28.6139, 77.2090),
    "Lucknow": (26.8467, 80.9462),
    "Patna": (25.5941, 85.1376),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
}

START_DATE = "2025-08-01"
END_DATE = "2026-08-10"  # matches your openaq_recent.csv max date

all_weather = []

for city, (lat, lon) in city_coords.items():
    print(f"Fetching weather for {city}...")
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,relative_humidity_2m_mean",
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        print(f"  Failed for {city}: {resp.status_code} - {resp.text}")
        continue
    data = resp.json()["daily"]

    df = pd.DataFrame(data)
    df["city"] = city
    all_weather.append(df)
    time.sleep(1)

weather_df = pd.concat(all_weather, ignore_index=True)
weather_df = weather_df.rename(columns={"time": "date"})

os.makedirs("data/raw/weather", exist_ok=True)
weather_df.to_csv("data/raw/weather/weather_recent.csv", index=False)
print(f"\nSaved {len(weather_df)} rows to data/raw/weather/weather_recent.csv")
print(weather_df.head())