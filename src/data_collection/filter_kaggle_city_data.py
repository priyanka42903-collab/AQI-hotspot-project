import pandas as pd
import os

cities = ["Delhi", "Lucknow", "Patna", "Mumbai", "Bengaluru", "Chennai", "Kolkata"]

city_day = pd.read_csv("data/raw/kaggle/city_day.csv")
station_day = pd.read_csv("data/raw/kaggle/station_day.csv")
stations = pd.read_csv("data/raw/kaggle/stations.csv")

city_day_filtered = city_day[city_day["City"].isin(cities)]
print(city_day_filtered["City"].value_counts())

print(station_day.columns.tolist())  # confirm before merging — does it have City directly, or need the join?
station_day_merged = station_day.merge(stations[["StationId", "City"]], on="StationId", how="left")
station_day_filtered = station_day_merged[station_day_merged["City"].isin(cities)]
print(station_day_filtered["City"].value_counts())

os.makedirs("data/processed", exist_ok=True)
city_day_filtered.to_csv("data/processed/city_day_filtered.csv", index=False)
station_day_filtered.to_csv("data/processed/station_day_filtered.csv", index=False)
print("Saved filtered Kaggle datasets to data/processed/")