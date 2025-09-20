from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

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

def logPos(lat, long, fishing, legal):
    pos_data.insert_one({
        "latitude": lat,
        "longitude": long,
        "isfishing": fishing,
        "legal": legal,
    })

def logPrompt(user, prompt, answer):
    prompt_logs.insert_one({
        "user": user,
        "prompt": prompt,
        "answer": answer,
    })


def logAISPosition(position_data):
    """Log one AIS position (SAR or AIS)"""
    vessel_positions.insert_one(position_data)

def getAISPositions(source=None, zone_name=None, hours_back=24):
    """Get AIS positions with optional filters"""
    query = {}
    
    if source:
        query["source"] = source
    if zone_name:
        query["zone_name"] = zone_name
    if hours_back:
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        query["timestamp"] = {"$gte": start_time}
    
    return list(vessel_positions.find(query).sort("timestamp", -1))

def getAISSummary():
    """Get AIS data summary counts"""
    total = vessel_positions.count_documents({})
    sar_count = vessel_positions.count_documents({"source": "SAR"})
    ais_count = vessel_positions.count_documents({"source": "AIS"})
    sar_matched = vessel_positions.count_documents({"source": "SAR", "ais_matched": True})
    sar_unmatched = vessel_positions.count_documents({"source": "SAR", "ais_matched": False})
    
    return {
        "total_positions": total,
        "sar_positions": sar_count,
        "ais_positions": ais_count,
        "sar_matched": sar_matched,
        "sar_unmatched": sar_unmatched
    }

def getUnmatchedSAR(zone_name=None, hours_back=24):
    """Get SAR positions ready for classification"""
    query = {
        "source": "SAR",
        "ais_matched": False
    }
    
    if zone_name:
        query["zone_name"] = zone_name
    if hours_back:
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        query["timestamp"] = {"$gte": start_time}
    
    return list(vessel_positions.find(query).sort("timestamp", -1))

def getPos():
    return list(pos_data.find())

def closedb():
    client.close()


