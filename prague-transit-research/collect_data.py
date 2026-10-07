import os
import json
import time
from datetime import datetime
import requests
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

start_time = time.time()
snapshots = []

while time.time() - start_time < collection_length:

    timestamp = datetime.now().isoformat()

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
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
    else:
        print(
            f"Error: {response.status_code}"
        )
    time.sleep(interval)

## SAVE DATA AFTER COLLECTION

filename = (
    f"data/vehicle_collection_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)

with open(filename, "w") as file:
    json.dump(snapshots, file)

print("Data Collected")
