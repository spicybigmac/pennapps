import dotenv
dotenv.load_dotenv("backend/.env")
dotenv.load_dotenv()

import os
import requests

import requests

url = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"

params = {
    "spatial-resolution": "HIGH",
    "spatial-aggregation": "false",
    "temporal-resolution": "HOURLY",
    "datasets[0]": "public-global-sar-presence:latest",
    "date-range": "2025-09-01,2025-09-29",
    "format": "JSON",
    "filters[0]": "matched='false'"
}

headers = {
    "Authorization": f"Bearer {os.getenv('GFW_API_KEY')}",
    "Content-Type": "application/json"
}

data = {
    "region": {
        "dataset": "public-eez-areas",
        "id": 8465
    }
}

response = requests.post(url, headers=headers, params=params, json=data)

with open("fishingtest.csv", "w") as f:
    for value in response.json()['entries']:
        f.write(str(value)+"\n")
        # print(value["registryInfo"][0]["shipname"])

# python3 backend/fishingtest.py