#!/usr/bin/env python3
"""
Simple Global SAR Vessel Data Collection
Collects SAR vessel data from Global Fishing Watch API using global GeoJSON polygon
"""

from dotenv import load_dotenv
load_dotenv(".env")

import os
import requests
import json
from datetime import datetime, timedelta

# API Configuration
url = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"

# Calculate date range (7-14 days ago to avoid future dates)
end_date = datetime.now().date() - timedelta(days=7)
start_date = end_date - timedelta(days=7)

# Query parameters
params = {
    "spatial-resolution": "HIGH",
    "temporal-resolution": "DAILY",
    "datasets[0]": "public-global-sar-presence:latest",
    "date-range": f"{start_date},{end_date}",
    "format": "JSON",
    "group-by": "VESSEL_ID"
}

# Headers
api_key = os.getenv('GFW_API_KEY')

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Global GeoJSON polygon (entire world - both hemispheres)
data = {
    "geojson": {
        "type": "Polygon",
        "coordinates": [[
            [-180, -85],   # min_lon, min_lat
            [180, -85],    # max_lon, min_lat (eastern hemisphere)
            [180, 85],     # max_lon, max_lat
            [-180, 85],    # min_lon, max_lat
            [-180, -85]    # close polygon
        ]]
    }
}

print(f"🌍 Collecting SAR vessel data for {start_date} to {end_date}")
print(f"📡 Using global GeoJSON polygon (both hemispheres)")

# Make API request
try:
    response = requests.post(url, headers=headers, params=params, json=data)
    
    if response.status_code == 200:
        raw_data = response.json()
        
        # Save raw response
        with open('raw_response_global.json', 'w') as f:
            json.dump(raw_data, f, indent=2)
        print("✅ Raw response saved to raw_response_global.json")
        
        # Process vessel data
        vessels = []
        total_vessels = 0
        matched_vessels = 0
        vessels_with_mmsi = 0
        
        for entry in raw_data.get("entries", []):
            for dataset_name, dataset_entries in entry.items():
                if "sar-presence" in dataset_name.lower():
                    if dataset_entries:
                        for vessel_data in dataset_entries:
                            total_vessels += 1
                            
                            # Check if vessel has MMSI (matched)
                            has_mmsi = bool(vessel_data.get("mmsi"))
                            if has_mmsi:
                                vessels_with_mmsi += 1
                                matched_vessels += 1
                            
                            # Extract vessel metadata
                            vessel = {
                                "vessel_id": vessel_data.get("vessel_id", ""),
                                "mmsi": vessel_data.get("mmsi", ""),
                                "ship_name": vessel_data.get("shipName", ""),
                                "flag": vessel_data.get("flag", ""),
                                "vessel_type": vessel_data.get("vessel_type", ""),
                                "lat": vessel_data.get("lat", 0),
                                "lon": vessel_data.get("lon", 0),
                                "detections": vessel_data.get("detections", 0),
                                "date": vessel_data.get("date", ""),
                                "matched": has_mmsi,
                                "raw_data": vessel_data
                            }
                            vessels.append(vessel)
        
        # Save processed vessel data
        with open('vessels_global.json', 'w') as f:
            json.dump(vessels, f, indent=2)
        print("✅ Processed vessel data saved to vessels_global.json")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 GLOBAL COLLECTION SUMMARY")
        print("="*60)
        print(f"Total vessels found: {total_vessels}")
        print(f"Vessels with MMSI: {vessels_with_mmsi}")
        print(f"Matched vessels: {matched_vessels}")
        print(f"Unmatched vessels: {total_vessels - matched_vessels}")
        print("="*60)
        
        # Show sample coordinates to verify global coverage
        if vessels:
            print("\n📍 Sample coordinates (first 10 vessels):")
            for i, vessel in enumerate(vessels[:10]):
                hemisphere = "East" if vessel['lon'] >= 0 else "West"
                print(f"  {i+1}. Lat: {vessel['lat']}, Lon: {vessel['lon']} ({hemisphere}) - {vessel['ship_name'] or 'Unknown'}")
        
        # Check longitude distribution
        west_count = len([v for v in vessels if v['lon'] < 0])
        east_count = len([v for v in vessels if v['lon'] >= 0])
        print(f"\n🌍 Hemisphere Distribution:")
        print(f"  Western Hemisphere: {west_count} vessels")
        print(f"  Eastern Hemisphere: {east_count} vessels")
        
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
