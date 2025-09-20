from api_routes import mongodb
import os
import json

folder = "raw_data"

for filename in os.listdir(folder):
    filepath = os.path.join(folder, filename)
    with open(filepath, "r") as f:
        data = json.load(f)
        for region in data["regions"].values():
            print("new region started")
            total = (len(region["dark_vessels"])+len(region["matched_vessels"]))
            for i,vessel in enumerate(region["dark_vessels"]):
                print(f"{i/total*100}%")
                mongodb.logPos(vessel)
            for i,vessel in enumerate(region["matched_vessels"]):
                print(f"{(i+len(region["dark_vessels"]))/total*100}%")
                mongodb.logPos(vessel)
    