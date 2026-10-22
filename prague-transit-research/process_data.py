import json
import pandas as pd
from pathlib import Path

## FIND RECENT COLLECTION
data_folder = Path("data")

files = list(data_folder.glob("vehicle_collection_*.json"))

if not files: 
    print("No collection files found")
    exit()

latest_file = max(files, key=lambda file: file.stat().st_mtime)

print(f"Reading: {latest_file}")

## LOAD JSON
with open(latest_file, "r") as file:
    snapshots = json.load(file)

## CONVERT TO ROWS
rows = []

for snapshot in snapshots:

    timestamp = snapshot["timestamp"]
    vehicles = snapshot["data"].get("features", [])

    for vehicle in vehicles:
        properties = vehicle.get("properties", {})
        coordinates = vehicle.get("geometry", {}).get("coordinates", [])

        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None

        row = {
            "timestamp": timestamp,
            "vehicle_id": properties.get("vehicle_id"),
            "trip_id": properties.get("gtfs_trip_id"),
            "route": properties.get("gtfs_route_short_name"),
            "mode": properties.get("route_type"),
            "delay_seconds": properties.get("delay"),
            "status": properties.get("state_position"),
            "bearing": properties.get("bearing"),
            "longitude": longitude,
            "latitude": latitude
        }

        rows.append(row)

## CREATE DATAFRAME
df = pd.DataFrame(rows)

## SAVE CLEANED DATA
output_file = data_folder / "vehicle_data_clean.csv"

df.to_csv(output_file, index=False)

## PRINT SUMMARY
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved to: {output_file}")

print()
print("First five rows:")
print(df.head())
