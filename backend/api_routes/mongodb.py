from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import dotenv

dotenv.load_dotenv()

"""
position data will be accessed by the frontend, position data will contain:
json of each individual boat that includes their longitude and latitude, fishing/not fishing

voice logs will be used to memorize the previous prompts and answers in order to inform
future voice logs

AIS data collections for Global Fishing Watch integration:
- vessel_positions: Raw vessel position data from SAR and AIS sources
- monitoring_zones: Geographic zones for monitoring
- ais_metadata: AIS matching and classification metadata
"""

uri = os.getenv("mongouri")
client = MongoClient(uri)
db = client["pennapps"]

# Existing collections
prompt_logs = db["prompt_logs"]
pos_data = db["position_data"]

# AIS data collections
vessel_positions = db["vessel_positions"]
monitoring_zones = db["monitoring_zones"]
ais_metadata = db["ais_metadata"]

def logPos(vessel):
    pos_data.insert_one({
        "date": vessel["date"],
        "latitude": vessel["lat"],
        "longitude": vessel["lon"],
        "matched": vessel["matched"],
        "mmsi": vessel["mmsi"],
        "imo": vessel["imo"],
        "flag": vessel["flag"],
        "shipName": vessel["shipName"],
        "geartype": vessel["geartype"],
    })

def logPrompt(user, prompt, answer):
    prompt_logs.insert_one({
        "user": user,
        "prompt": prompt,
        "answer": answer,
    })

def getPos():
    return list(pos_data.find())

def closedb():
    client.close()


