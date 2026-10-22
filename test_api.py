import os 
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

## LOAD FROM .ENV
load_dotenv()

API_KEY = os.getenv("GOLEMIO_API_KEY")

## GOLEMIO ENDPOINT
url = "https://api.golemio.cz/v2/public/vehiclepositions"

headers = {
    "X-Access-Token": API_KEY
}

## REQUEST DATA
response = requests.get(url, headers=headers)

print("Status:", response.status_code)

##IF SUCCESSFUL, SAVE DATA
if response.status_code == 200:
    data = response.json()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"data/vehicle_positions_{timestamp}.json"

    with open(filename, "w") as file:
        json.dump(data, file, indent=2)

    print(f"Saved data to: {filename}")
else:
    print("Error:")
    print(response.text)