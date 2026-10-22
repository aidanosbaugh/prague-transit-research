import os
import json
import time
from datetime import datetime
from datetime import timedelta
import requests
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


## LOAD FROM .ENV
load_dotenv()

API_KEY = os.getenv("GOLEMIO_API_KEY")

## GOLEMIO ENDPOINT
url = "https://api.golemio.cz/v2/public/vehiclepositions"

headers = {
    "X-Access-Token": API_KEY
}

## COLLECTION SETTINGS
collection_length = 20 * 180
interval = 20 ##<-seconds

## START/TIMEZONE SETTINGS
tz = ZoneInfo("Europe/Prague")
start_time = datetime.now(tz)
now = datetime.now(tz)
##stop_at = now.replace(hour=9, minute=0, second=0, microsecond=0)
stop_at = start_time + timedelta(minutes=2)

# ONLY COLLECT B/W 7-9
##if start_time.hour < 7 or start_time.hour > 9:
    ##print("Outside collection window (07:00-09:00 Prague time).")
    ##raise SystemExit(0)

snapshots = []

try:
    while datetime.now(tz) < stop_at:

        timestamp = datetime.now(tz).isoformat()

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

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

        # Sleep for 20 seconds, or until 09:00 if sooner
        remaining = (
            stop_at - datetime.now(tz)
        ).total_seconds()

        if remaining > 0:
            time.sleep(min(interval, remaining))

except KeyboardInterrupt:
    print("Collection interrupted manually.")

finally:
    end_time = datetime.now(tz)

## SAVE DATA AFTER COLLECTION

filename = (
    f"data/vehicle_collection_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)

with open(filename, "w") as file:
    json.dump(snapshots, file)

print("Data Collected")
