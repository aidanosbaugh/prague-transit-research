
import os
import json
import time
from datetime import datetime
import requests
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


# LOAD API KEY
load_dotenv()
API_KEY = os.getenv("GOLEMIO_API_KEY")

if not API_KEY:
    raise SystemExit("ERROR: GOLEMIO_API_KEY is missing.")

# GOLEMIO API
URL = "https://api.golemio.cz/v2/public/vehiclepositions"

HEADERS = {
    "X-Access-Token": API_KEY
}

# COLLECTION SETTINGS
INTERVAL = 20
TZ = ZoneInfo("Europe/Prague")

# DEFINE COLLECTION WINDOW
now = datetime.now(TZ)

start_at = now.replace(
    hour=7, minute=0, second=0, microsecond=0
)

stop_at = now.replace(
    hour=9, minute=0, second=0, microsecond=0
)

# EXIT IF ALREADY PAST COLLECTION WINDOW
if now >= stop_at:
    print("Outside collection window (07:00-09:00 Prague time).")
    raise SystemExit(0)

# WAIT IF STARTED BEFORE 07:00
if now < start_at:
    wait_seconds = (start_at - now).total_seconds()
    print(f"Waiting until 07:00 Prague time ({wait_seconds:.0f}s).")
    time.sleep(wait_seconds)

print("Starting Prague tram data collection.")

snapshots = []

try:
    next_collection = time.monotonic()

    while datetime.now(TZ) < stop_at:

        timestamp = datetime.now(TZ).isoformat()

        try:
            response = requests.get(
                URL,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise ValueError("Unexpected API response format.")

            snapshot = {
                "timestamp": timestamp,
                "data": data
            }

            snapshots.append(snapshot)

            vehicle_count = len(data.get("features", []))

            print(
                f"{timestamp} | "
                f"Vehicles collected: {vehicle_count}"
            )

        except (requests.RequestException, ValueError) as error:
            print(f"{timestamp} | API/data error: {error}")

        # MAINTAIN 20-SECOND COLLECTION INTERVAL
        next_collection += INTERVAL

        sleep_time = next_collection - time.monotonic()

        remaining = (
            stop_at - datetime.now(TZ)
        ).total_seconds()

        if remaining > 0 and sleep_time > 0:
            time.sleep(min(sleep_time, remaining))

except KeyboardInterrupt:
    print("Collection interrupted manually.")

finally:
    # SAVE DATA EVEN IF COLLECTION IS INTERRUPTED
    os.makedirs("data/raw", exist_ok=True)

    end_time = datetime.now(TZ)

    filename = (
        "data/raw/vehicle_collection_"
        f"{end_time.strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(filename, "w") as file:
        json.dump(snapshots, file)

    print("--------------------------------")
    print("COLLECTION FINISHED")
    print(f"Snapshots collected: {len(snapshots)}")
    print(f"File saved: {filename}")
    print("--------------------------------")
