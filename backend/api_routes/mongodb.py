from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import dotenv
import json

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
report_logs = db["report_logs"]

# AIS data collections
vessel_positions = db["vessel_positions"]
monitoring_zones = db["monitoring_zones"]
ais_metadata = db["ais_metadata"]

def logPos(lat, lon, matched, vessel):
    pos_data.insert_one({
        "date": vessel["date"],
        "latitude": lat,
        "longitude": lon,
        "matched": matched,
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

def logReport(user, report):
    report_logs.insert_one({
        "user": user,
        "report": report
    })

def getPos():
    return list(pos_data.find())

def get_report_by_title(title: str) -> Optional[Dict[str, Any]]:
    """
    Fuzzy search for a report by its title.
    This is a placeholder and may need a more robust search implementation.
    """
    # In MongoDB, the report is a JSON string in the 'report' field.
    # We can't easily query by title inside the JSON string without more complex queries or database structure changes.
    # For now, we fetch recent reports and check the title.
    recent_reports = list(report_logs.find().sort([("_id", -1)]).limit(20))
    for report_doc in recent_reports:
        try:
            report_data = json.loads(report_doc.get("report", "{}"))
            # This assumes a title field might be part of the logged report data, which it isn't currently.
            # Let's pivot: the user can't summarize a report by a name that isn't stored.
            # The prompt a user gives would be "summarize my latest report".
            # So let's just get the latest report for that user.
            pass # We'll implement this in the main.py logic instead.
        except json.JSONDecodeError:
            continue
    return None # Logic will be in main.py for now.

def get_latest_report_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Gets the most recent report for a given user."""
    report = report_logs.find_one({"user": user_id}, sort=[("_id", -1)])
    return report


def closedb():
    client.close()


