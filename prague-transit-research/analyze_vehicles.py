import pandas as pd

df = pd.read_csv("data/vehicle_data_clean.csv")

# Pick one vehicle that appears multiple times
vehicle_counts = df["vehicle_id"].value_counts()

vehicle_id = vehicle_counts.index[0]

vehicle = df[df["vehicle_id"] == vehicle_id].copy()

vehicle["timestamp"] = pd.to_datetime(vehicle["timestamp"])

vehicle = vehicle.sort_values("timestamp")

print("Vehicle:", vehicle_id)
print()
print(vehicle[
    [
        "timestamp",
        "route",
        "mode",
        "delay_seconds",
        "status"
    ]
].to_string(index=False))
