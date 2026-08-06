import requests
import pandas as pd
import time

API_KEY = "27e149993ebccb4ad00339b2f11291c5c9fd4d727447d3b7fe098cbc6d617212"
HEADERS = {"X-API-Key": API_KEY}
BASE_URL = "https://api.openaq.org/v3/locations"

# Step 1: quick sanity check
resp = requests.get(BASE_URL, headers=HEADERS, params={"iso": "IN", "limit": 5, "page": 1})
print(resp.status_code)
print(resp.json())

# Step 2: full pagination pull (only run this once step 1 looks correct)
all_results = []
page = 1

while True:
    params = {"iso": "IN", "limit": 1000, "page": page}
    resp = requests.get(BASE_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    data = resp.json()
    results = data["results"]
    if not results:
        break
    all_results.extend(results)
    print(f"Page {page}: {len(results)} results (total so far: {len(all_results)})")
    page += 1
    time.sleep(1)  # be polite to the API

print(f"\nTotal India locations fetched: {len(all_results)}")

# Step 3: flatten into rows
rows = []
for loc in all_results:
    rows.append({
        "location_id": loc["id"],
        "name": loc["name"],
        "locality": loc.get("locality"),
        "latitude": loc["coordinates"]["latitude"],
        "longitude": loc["coordinates"]["longitude"],
        "sensor_ids": [s["id"] for s in loc["sensors"]],
        "parameters": [s["parameter"]["name"] for s in loc["sensors"]],
        "is_mobile": loc["isMobile"],
        "is_monitor": loc["isMonitor"],
        "provider": loc["provider"]["name"],
    })

df = pd.DataFrame(rows)
print(df.head())
print(f"\nUnique localities: {df['locality'].nunique()}")

# Step 4: save
df.to_csv("data/raw/openaq/openaq_locations.csv", index=False)
print("Saved to data/raw/openaq/openaq_locations.csv")