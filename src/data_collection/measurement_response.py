import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENAQ_API_KEY")
HEADERS = {"X-API-Key": API_KEY}

sensors = pd.read_csv("data/processed/openaq_sensors_selected.csv")
test_id = int(sensors.iloc[0]["sensor_id"])
print("Testing with sensor_id:", test_id)

resp = requests.get(
    f"https://api.openaq.org/v3/sensors/{test_id}/days",
    headers=HEADERS,
    params={"date_from": "2023-01-01", "date_to": "2026-08-11", "limit": 1000}
)
print(resp.status_code)
print(resp.json())

resp2 = requests.get(f"https://api.openaq.org/v3/sensors/{test_id}", headers=HEADERS)
print(resp2.json())

live_sensors = sensors[sensors["location_name"].str.contains("R K Puram", case=False, na=False)]
print(live_sensors[["sensor_id", "parameter", "units"]])

test_id = 12234787
resp = requests.get(
    f"https://api.openaq.org/v3/sensors/{test_id}/days",
    headers=HEADERS,
    params={"date_from": "2025-08-01", "date_to": "2025-08-11", "limit": 100}
)
print(resp.status_code)
print(resp.json())

print(
