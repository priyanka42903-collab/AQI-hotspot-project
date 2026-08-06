import pandas as pd
import os
df_raw = pd.read_csv("data/raw/openaq/openaq_locations.csv")
cities = ["Delhi", "Lucknow", "Patna", "Mumbai", "Bengaluru", "Chennai","Kolkata"]
for city in cities:
    count = df_raw["name"].str.contains(city, case=False, na=False).sum()
    print(f"{city}: {count} stations")

# tag each station with which city it matched
def match_city(name, cities):
    for city in cities:
        if city.lower() in str(name).lower():
            return city
    return None

df_raw["city"] = df_raw["name"].apply(lambda x: match_city(x, cities))
df_filtered = df_raw[df_raw["city"].notna()].copy()

print(df_filtered["city"].value_counts())
print(f"\nTotal stations across 7 cities: {len(df_filtered)}")

os.makedirs("data/processed", exist_ok=True)
df_filtered.to_csv("data/processed/openaq_locations_filtered.csv", index=False)
print("Saved filtered station list to data/processed/openaq_locations_filtered.csv")

