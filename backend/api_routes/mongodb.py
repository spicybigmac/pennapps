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

# AIS Data Functions
def logAISPosition(position_data: dict):
    """Log AIS position data to MongoDB"""
    try:
        # Add timestamp if not present
        if 'timestamp' not in position_data:
            position_data['timestamp'] = datetime.utcnow()
        
        # Add created_at timestamp
        position_data['created_at'] = datetime.utcnow()
        
        # Insert into vessel_positions collection
        result = vessel_positions.insert_one(position_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error logging AIS position: {e}")
        raise e

def getAISPositions(source: str = None, zone_name: str = None, hours_back: int = 24):
    """Get AIS positions with optional filtering"""
    try:
        # Build query
        query = {}
        
        # Time filter
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        query['timestamp'] = {'$gte': time_threshold}
        
        # Source filter
        if source:
            query['source'] = source
        
        # Zone filter
        if zone_name:
            query['zone_name'] = zone_name
        
        # Execute query
        positions = list(vessel_positions.find(query).sort('timestamp', -1))
        
        return positions
    except Exception as e:
        print(f"Error getting AIS positions: {e}")
        raise e

def getUnmatchedSAR(zone_name: str = None, hours_back: int = 24):
    """Get SAR positions that didn't match with AIS"""
    try:
        # Build query for unmatched SAR positions
        query = {
            'source': 'SAR',
            'ais_matched': {'$ne': True}  # Not matched or null
        }
        
        # Time filter
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        query['timestamp'] = {'$gte': time_threshold}
        
        # Zone filter
        if zone_name:
            query['zone_name'] = zone_name
        
        # Execute query
        positions = list(vessel_positions.find(query).sort('timestamp', -1))
        
        return positions
    except Exception as e:
        print(f"Error getting unmatched SAR positions: {e}")
        raise e

def getAISSummary():
    """Get AIS data summary statistics"""
    try:
        # Get total counts
        total_positions = vessel_positions.count_documents({})
        sar_positions = vessel_positions.count_documents({'source': 'SAR'})
        ais_positions = vessel_positions.count_documents({'source': 'AIS'})
        matched_positions = vessel_positions.count_documents({'ais_matched': True})
        unmatched_positions = vessel_positions.count_documents({'ais_matched': {'$ne': True}})
        
        # Get recent activity (last 24 hours)
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        recent_positions = vessel_positions.count_documents({'timestamp': {'$gte': time_threshold}})
        
        # Get zone distribution
        zone_pipeline = [
            {'$group': {'_id': '$zone_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        zone_distribution = list(vessel_positions.aggregate(zone_pipeline))
        
        return {
            'total_positions': total_positions,
            'sar_positions': sar_positions,
            'ais_positions': ais_positions,
            'matched_positions': matched_positions,
            'unmatched_positions': unmatched_positions,
            'recent_positions_24h': recent_positions,
            'zone_distribution': zone_distribution,
            'last_updated': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error getting AIS summary: {e}")
        raise e

def getVesselDataForHotspotAnalysis(start_date: datetime = None, end_date: datetime = None):
    """Get vessel data specifically formatted for hotspot analysis"""
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Convert datetime objects to ISO format strings for query
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        # Build query with string timestamps
        query = {
            'timestamp': {
                '$gte': start_date_str,
                '$lte': end_date_str
            }
        }
        
        # Get all positions
        positions = list(vessel_positions.find(query))
        
        # Separate by source and matching status
        tracked_vessels = []
        untracked_vessels = []
        
        for pos in positions:
            vessel_data = {
                'id': str(pos.get('_id', '')),
                'lat': pos.get('lat', 0),
                'lon': pos.get('lon', 0),
                'timestamp': pos.get('timestamp'),
                'source': pos.get('source', ''),
                'zone_name': pos.get('zone_name', ''),
                'mmsi': pos.get('mmsi'),
                'vessel_name': pos.get('vessel_name'),
                'vessel_type': pos.get('vessel_type'),
                'flag': pos.get('flag'),
                'is_fishing': pos.get('is_fishing'),
                'confidence': pos.get('confidence'),
                'raw_data': pos.get('raw_data', {})
            }
            
            # Categorize based on source and matching status
            if pos.get('source') == 'AIS' or pos.get('ais_matched') == True:
                tracked_vessels.append(vessel_data)
            else:
                untracked_vessels.append(vessel_data)
        
        return {
            'tracked_vessels': tracked_vessels,
            'untracked_vessels': untracked_vessels,
            'total_vessels': len(positions),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    except Exception as e:
        print(f"Error getting vessel data for hotspot analysis: {e}")
        raise e


