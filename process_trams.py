
from pathlib import Path
import pandas as pd

# PATHS
PROJECT_DIR = Path(__file__).parent
INPUT_DIR = PROJECT_DIR / "data" / "cleaned"
OUTPUT_DIR = PROJECT_DIR / "data" / "trams"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ROUTES TO KEEP
tram_routes = ["9", "17", "22"]


def process_tram_file(input_file):
    """Filter one cleaned session to the selected tram lines."""

    df = pd.read_csv(input_file)

    # Standardize filtering columns
    df["mode"] = df["mode"].astype("string").str.strip().str.lower()
    df["route"] = df["route"].astype("string").str.strip()

    # Keep only trams on routes 9, 17, and 22
    trams = df[
        (df["mode"] == "tram")
        & (df["route"].isin(tram_routes))
    ].copy()

    # Convert data types
    trams["timestamp"] = pd.to_datetime(
        trams["timestamp"], errors="coerce"
    )
    trams["delay_seconds"] = pd.to_numeric(
        trams["delay_seconds"], errors="coerce"
    )

    # Sort observations by time
    trams = trams.sort_values("timestamp")

    # Preserve the session identifier in the output filename
    session_name = input_file.stem.replace("vehicle_data_", "")
    output_file = OUTPUT_DIR / f"tram_data_{session_name}.csv"

    trams.to_csv(output_file, index=False)

    print(f"\nProcessed: {input_file.name}")
    print(f"Tram observations: {len(trams):,}")
    print("Observations by route:")
    print(trams["route"].value_counts().sort_index())
    print(f"Saved: {output_file}")


def main():
    input_files = sorted(INPUT_DIR.glob("vehicle_data_*.csv"))

    if not input_files:
        print(f"No cleaned CSV files found in {INPUT_DIR}")
        return

    for input_file in input_files:
        process_tram_file(input_file)

    print(f"\nFinished processing {len(input_files)} session(s).")


if __name__ == "__main__":
    main()
