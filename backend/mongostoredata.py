from api_routes import mongodb
import os
import json

filepath = "SAR_Raw_data/vessels.json"
with open(filepath, "r") as f:
    data = json.load(f)
    total = len(data)
    for i,vessel in enumerate(data):
        print(f"{i/total*100}%")
        mongodb.logPos(vessel["lat"],vessel["lon"],vessel["matched"],vessel["raw_data"])
