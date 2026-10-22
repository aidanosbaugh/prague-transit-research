
import json
from pathlib import Path

import pandas as pd


# FILE PATHS
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "cleaned"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def process_file(input_file):
    """Convert one raw vehicle collection into a separate cleaned CSV."""

    with open(input_file, "r", encoding="utf-8") as file:
        snapshots = json.load(file)

    rows = []

    for snapshot in snapshots:
        timestamp = snapshot.get("timestamp")
        data = snapshot.get("data", {})

        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            coordinates = geometry.get("coordinates", [None, None])

            longitude = coordinates[0] if len(coordinates) > 0 else None
            latitude = coordinates[1] if len(coordinates) > 1 else None

            rows.append({
                "timestamp": timestamp,
                "vehicle_id": properties.get("vehicle_id"),
                "trip_id": properties.get("gtfs_trip_id"),
                "route": properties.get("gtfs_route_short_name"),
                "mode": properties.get("route_type"),
                "delay_seconds": properties.get("delay"),
                "status": properties.get("state_position"),
                "bearing": properties.get("bearing"),
                "longitude": longitude,
                "latitude": latitude,
            })

    columns = [
        "timestamp", "vehicle_id", "trip_id", "route", "mode",
        "delay_seconds", "status", "bearing", "longitude", "latitude"
    ]

    df = pd.DataFrame(rows, columns=columns)

    # Create a separate CSV using the raw session's filename
    session_name = input_file.stem.replace("vehicle_collection_", "")
    output_file = OUTPUT_DIR / f"vehicle_data_{session_name}.csv"

    df.to_csv(output_file, index=False)

    print(f"Processed: {input_file.name}")
    print(f"Rows: {len(df):,}")
    print(f"Saved: {output_file}")


def main():
    # Process each raw collection separately
    raw_files = sorted(DATA_DIR.glob("vehicle_collection_*.json"))

    if not raw_files:
        print("No raw collection files found.")
        return

    for input_file in raw_files:
        process_file(input_file)

    print(f"\nFinished processing {len(raw_files)} collection file(s).")


if __name__ == "__main__":
    main()
