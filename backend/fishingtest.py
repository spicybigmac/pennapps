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
    "filters[0]": "matched='false'",
    "group-by": "VESSEL_ID"
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

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"Response Text: {response.text[:1000]}...")

# Check the response structure
if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Try to find the data
    if 'entries' in data:
        print(f"Found 'entries' with {len(data['entries'])} items")
    elif 'data' in data:
        print(f"Found 'data' with {len(data['data'])} items")
    elif 'results' in data:
        print(f"Found 'results' with {len(data['results'])} items")
    else:
        print("Available keys in response:")
        for key, value in data.items():
            print(f"  {key}: {type(value)} - {str(value)[:100]}...")
else:
    print(f"Error: {response.status_code} - {response.text}")

# python3 backend/fishingtest.py