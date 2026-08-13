import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENAQ_API_KEY")
HEADERS = {"X-API-Key": API_KEY}

sensors = pd.read_csv("data/processed/openaq_sensors_selected.csv")
DATE_FROM = "2025-08-01"
DATE_TO = "2026-08-11"

all_rows = []
dead_sensors = []

CHECKPOINT_EVERY = 50

for i, row in sensors.iterrows():
    sensor_id = int(row["sensor_id"])
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/days"
    page = 1
    got_any = False

    while True:
        resp = requests.get(url, headers=HEADERS,
                             params={"date_from": DATE_FROM, "date_to": DATE_TO, "limit": 1000, "page": page})
        if resp.status_code != 200:
            print(f"Sensor {sensor_id} error {resp.status_code}, skipping")
            break
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        got_any = True
        for r in results:
            all_rows.append({
                "sensor_id": sensor_id,
                "location_id": row["location_id"],
                "location_name": row["location_name"],
                "city": row["city"],
                "parameter": row["parameter"],
                "date": r["period"]["datetimeFrom"]["local"][:10],
                "value": r["value"],
                "coverage_pct": r["coverage"]["percentCoverage"],
            })
        page += 1
        time.sleep(0.3)

    if not got_any:
        dead_sensors.append(sensor_id)

    if i % CHECKPOINT_EVERY == 0:
        print(f"Progress: {i}/{len(sensors)} sensors processed, {len(all_rows)} rows so far")
        pd.DataFrame(all_rows).to_csv("data/raw/openaq/openaq_recent_checkpoint.csv", index=False)

    time.sleep(0.3)

df = pd.DataFrame(all_rows)
os.makedirs("data/raw/openaq", exist_ok=True)
df.to_csv("data/raw/openaq/openaq_recent.csv", index=False)

print(f"\nDone. Total rows: {len(df)}")
print(f"Dead/empty sensors: {len(dead_sensors)} out of {len(sensors)}")
df_dead = pd.DataFrame({"sensor_id": dead_sensors})
df_dead.to_csv("data/processed/dead_sensors.csv", index=False)