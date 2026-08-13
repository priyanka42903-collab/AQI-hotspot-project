from dotenv import load_dotenv
import os
import requests
import pandas as pd
import os
import time



load_dotenv()
API_KEY = os.environ.get("OPENAQ_API_KEY")
print("Key loaded:", API_KEY[:6] + "..." if API_KEY else "NOT FOUND")
HEADERS = {"X-API-Key": API_KEY}
BASE_URL = "https://api.openaq.org/v3/locations"
cities = ["Delhi", "Lucknow", "Patna", "Mumbai", "Bengaluru", "Chennai", "Kolkata"]

def match_city(name, cities):
    for city in cities:
        if city.lower() in str(name).lower():
            return city
    return None


all_results = []
page = 1
while True:
    resp = requests.get(BASE_URL, headers=HEADERS, params={"iso": "IN", "limit": 1000, "page": page})
    resp.raise_for_status()
    results = resp.json()["results"]
    if not results:
        break
    all_results.extend(results)
    page += 1
    time.sleep(1)


sensor_rows = []
for loc in all_results:
    city = match_city(loc["name"], cities)
    if city is None:
        continue
    for s in loc["sensors"]:
        sensor_rows.append({
            "location_id": loc["id"],
            "location_name": loc["name"],
            "city": city,
            "latitude": loc["coordinates"]["latitude"],
            "longitude": loc["coordinates"]["longitude"],
            "sensor_id": s["id"],
            "parameter": s["parameter"]["name"],
            "units": s["parameter"]["units"],
        })

sensors_df = pd.DataFrame(sensor_rows)

sensors_df["unit_priority"] = sensors_df["units"].apply(lambda u: 0 if u == "µg/m³" else 1)
sensors_df = sensors_df.sort_values("unit_priority")
sensors_dedup = sensors_df.drop_duplicates(subset=["location_id", "parameter"], keep="first")

os.makedirs("data/processed", exist_ok=True)
aqi_parameters = ["pm25", "pm10", "no2", "so2", "co", "o3"]
sensors_dedup = sensors_dedup[sensors_dedup["parameter"].isin(aqi_parameters)]

print(f"Sensors after filtering to AQI-relevant parameters: {len(sensors_dedup)}")
print(sensors_dedup["parameter"].value_counts())
sensors_dedup.to_csv("data/processed/openaq_sensors_selected.csv", index=False)
print(f"Total sensors before dedup: {len(sensors_df)}")
print(f"Selected sensors after dedup: {len(sensors_dedup)}")
print(sensors_dedup["parameter"].value_counts())