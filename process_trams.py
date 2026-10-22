
from pathlib import Path
import pandas as pd

## CREATE PATH
DATA_DIR = Path(__file__).parent / "data"
INPUT_FILE = DATA_DIR / "vehicle_data_clean.csv"
OUTPUT_FILE = DATA_DIR / "tram_data.csv"

## LOAD DATA
df = pd.read_csv(INPUT_FILE)

## FORMAT CHECK
df["mode"] = df["mode"].astype("string").str.strip().str.lower()
df["route"] = df["route"].astype("string").str.strip()

# KEEP TRAMS ROUTES 9,17,22
tram_routes = ["9", "17", "22"]

trams = df[
    (df["mode"] == "tram")
    & (df["route"].isin(tram_routes))
].copy()

## CONVERT UNITS
trams["timestamp"] = pd.to_datetime(
    trams["timestamp"], errors="coerce"
)
trams["delay_seconds"] = pd.to_numeric(
    trams["delay_seconds"], errors="coerce"
)

## SORT BY TIME
trams = trams.sort_values("timestamp")

## SAVE TO SECOND FILE
trams.to_csv(OUTPUT_FILE, index=False)

## SANITY CHECKS
print(f"Original observations: {len(df):,}")
print(f"Selected tram observations: {len(trams):,}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nObservations by route:")
print(trams["route"].value_counts().sort_index())

print("\nMissing values:")
print(trams.isna().sum())

print("\nDelay summary by route (seconds):")
print(
    trams.groupby("route")["delay_seconds"]
    .agg(["count", "mean", "median", "std", "min", "max"])
    .round(2)
)

print("\nObservation time range:")
print(trams["timestamp"].min())
print(trams["timestamp"].max())
