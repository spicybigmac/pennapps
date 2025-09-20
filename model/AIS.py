#!/usr/bin/env python3
"""
Global Fishing Watch Data Collector
Pulls SAR vessel detections and AIS data from GFW APIs and stores in MongoDB

This code:
1. Gets raw reports from GFW APIs
2. Extracts vessel position data (both SAR and AIS)
3. Preserves AIS matching status from API
4. Stores everything in MongoDB for later classification
"""

import asyncio
import aiohttp
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Models - Simplified for raw data storage
@dataclass
class VesselPosition:
    """Raw vessel position data from SAR or AIS"""
    id: str
    source: str  # 'SAR' or 'AIS'
    lat: float
    lon: float
    timestamp: datetime
    zone_name: str
    
    # Detection metadata
    confidence: Optional[float] = None  # For SAR detections
    
    # Vessel characteristics (when available)
    vessel_length_m: Optional[float] = None
    mmsi: Optional[str] = None
    vessel_type: Optional[str] = None
    vessel_name: Optional[str] = None
    flag: Optional[str] = None
    imo: Optional[str] = None
    callsign: Optional[str] = None
    
    # AIS correlation status (from API)
    ais_matched: Optional[bool] = None  # Only for SAR detections
    
    # Fishing classification (from API - if available)
    is_fishing: Optional[bool] = None
    
    # Storage metadata
    created_at: datetime = None
    raw_data: Optional[Dict] = None  # Store complete API response
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class MonitoringZone:
    """Geographic zone for monitoring"""
    name: str
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    description: str
    priority: str = 'medium'
    country: Optional[str] = None

# MongoDB Storage Implementation
class MongoDBStorage:
    """MongoDB storage for vessel position data"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        
    async def connect(self):
        """Initialize MongoDB connection"""
        try:
            # Import here to avoid dependency if not using MongoDB
            from motor.motor_asyncio import AsyncIOMotorClient
            
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
            # Create indexes for efficient queries
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Create database indexes for efficient queries"""
        try:
            vessel_positions = self.db.vessel_positions
            
            # Geospatial index for location queries
            await vessel_positions.create_index([("lat", 1), ("lon", 1)])
            
            # Time-based index for temporal queries
            await vessel_positions.create_index([("timestamp", -1)])
            
            # Zone and source indexes
            await vessel_positions.create_index([("zone_name", 1)])
            await vessel_positions.create_index([("source", 1)])
            
            # AIS matching index for quick filtering
            await vessel_positions.create_index([("ais_matched", 1)])
            
            # MMSI index for vessel tracking
            await vessel_positions.create_index([("mmsi", 1)])
            
            # Compound index for common queries
            await vessel_positions.create_index([
                ("zone_name", 1), 
                ("timestamp", -1), 
                ("source", 1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    async def store_vessel_positions(self, positions: List[VesselPosition]) -> bool:
        """Store vessel positions in MongoDB"""
        if not positions:
            return True
            
        try:
            vessel_positions = self.db.vessel_positions
            
            # Convert to documents
            documents = []
            for position in positions:
                doc = asdict(position)
                # Convert datetime to MongoDB-compatible format
                doc['timestamp'] = position.timestamp
                doc['created_at'] = position.created_at
                documents.append(doc)
            
            # Insert with upsert to handle duplicates
            operations = []
            for doc in documents:
                operations.append({
                    "updateOne": {
                        "filter": {"id": doc["id"]},
                        "update": {"$set": doc},
                        "upsert": True
                    }
                })
            
            if operations:
                result = await vessel_positions.bulk_write(operations)
                logger.info(f"Stored {len(positions)} vessel positions "
                           f"({result.upserted_count} new, {result.modified_count} updated)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing vessel positions: {e}")
            return False
    
    async def get_positions_by_zone_and_time(self, zone_name: str, 
                                           start_time: datetime, 
                                           end_time: datetime,
                                           source: Optional[str] = None) -> List[Dict]:
        """Get vessel positions for a zone and time range"""
        try:
            vessel_positions = self.db.vessel_positions
            
            query = {
                "zone_name": zone_name,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            if source:
                query["source"] = source
            
            cursor = vessel_positions.find(query).sort("timestamp", -1)
            positions = await cursor.to_list(length=None)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error querying positions: {e}")
            return []
    
    async def get_unmatched_sar_positions(self, zone_name: Optional[str] = None,
                                        hours_back: int = 24) -> List[Dict]:
        """Get SAR positions that didn't match with AIS"""
        try:
            vessel_positions = self.db.vessel_positions
            
            query = {
                "source": "SAR",
                "ais_matched": False,
                "timestamp": {
                    "$gte": datetime.utcnow() - timedelta(hours=hours_back)
                }
            }
            
            if zone_name:
                query["zone_name"] = zone_name
            
            cursor = vessel_positions.find(query).sort("timestamp", -1)
            positions = await cursor.to_list(length=None)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error querying unmatched SAR positions: {e}")
            return []
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# North American monitoring zones
NORTH_AMERICAN_ZONES = [
    MonitoringZone(
        name="alaska_bering_sea",
        bbox=[-180, 54, -158, 66],
        description="Bering Sea - Commercial fishing waters",
        priority="high",
        country="USA"
    ),
    MonitoringZone(
        name="gulf_of_maine", 
        bbox=[-71, 42, -66, 45],
        description="Gulf of Maine - Lobster and groundfish",
        priority="high",
        country="USA"
    ),
    MonitoringZone(
        name="pacific_northwest",
        bbox=[-130, 45, -123, 49],
        description="Pacific Northwest - Salmon waters",
        priority="high",
        country="USA"
    ),
    MonitoringZone(
        name="gulf_of_mexico",
        bbox=[-98, 26, -88, 30],
        description="Gulf of Mexico - Shrimp waters",
        priority="medium",
        country="USA"
    ),
    MonitoringZone(
        name="southern_california",
        bbox=[-125, 32, -117, 35],
        description="Southern California - Tuna waters",
        priority="medium",
        country="USA"
    ),
    MonitoringZone(
        name="canadian_atlantic",
        bbox=[-65, 42, -55, 52],
        description="Canadian Atlantic waters",
        priority="medium",
        country="Canada"
    )
]
class GlobalFishingWatchAPI:
    """Client for Global Fishing Watch APIs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gateway.api.globalfishingwatch.org"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.requests_this_minute = 0
        self.minute_start = datetime.now()
        self.max_requests_per_minute = 60
    
    def _check_rate_limit(self):
        """Simple rate limiting"""
        now = datetime.now()
        if (now - self.minute_start).total_seconds() > 60:
            self.requests_this_minute = 0
            self.minute_start = now
        
        if self.requests_this_minute >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.minute_start).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.requests_this_minute = 0
                self.minute_start = datetime.now()
    
    async def get_sar_detections_raw(self, zone: MonitoringZone, 
                                   start_date: str, end_date: str) -> List[VesselPosition]:
        """Get raw SAR vessel detections from API"""
        self._check_rate_limit()
        
        url = f"{self.base_url}/v1/4wings/report"
        bbox_str = f"{zone.bbox[0]},{zone.bbox[1]},{zone.bbox[2]},{zone.bbox[3]}"
        
        payload = {
            "datasets": ["public-sar-vessel-detections:v20231026"],
            "bbox": bbox_str,
            "start-date": start_date,
            "end-date": end_date,
            "format": "json",
            "spatial-resolution": "high",
            "temporal-resolution": "daily"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    self.requests_this_minute += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        positions = self._parse_sar_positions(data, zone)
                        logger.info(f"Retrieved {len(positions)} SAR positions for {zone.name}")
                        return positions
                    else:
                        error_text = await response.text()
                        logger.error(f"SAR API error for {zone.name}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching SAR data for {zone.name}: {e}")
            return []
    
    async def get_ais_presence_raw(self, zone: MonitoringZone,
                                  start_date: str, end_date: str) -> List[VesselPosition]:
        """Get raw AIS vessel presence from API"""
        self._check_rate_limit()
        
        url = f"{self.base_url}/v1/4wings/report"
        bbox_str = f"{zone.bbox[0]},{zone.bbox[1]},{zone.bbox[2]},{zone.bbox[3]}"
        
        payload = {
            "datasets": ["public-ais-vessel-presence:v20231026"],
            "bbox": bbox_str,
            "start-date": start_date,
            "end-date": end_date,
            "format": "json",
            "spatial-resolution": "high",
            "temporal-resolution": "daily"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    self.requests_this_minute += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        positions = self._parse_ais_positions(data, zone)
                        logger.info(f"Retrieved {len(positions)} AIS positions for {zone.name}")
                        return positions
                    else:
                        error_text = await response.text()
                        logger.error(f"AIS API error for {zone.name}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching AIS data for {zone.name}: {e}")
            return []
    
    def _parse_sar_positions(self, data: Dict, zone: MonitoringZone) -> List[VesselPosition]:
        """Parse SAR detection API response into VesselPosition objects"""
        positions = []
        
        for entry in data.get("entries", []):
            try:
                # Generate unique ID for SAR detection
                timestamp_str = entry.get("date", "")
                lat = float(entry.get("lat", 0))
                lon = float(entry.get("lon", 0))
                position_id = f"sar_{zone.name}_{timestamp_str}_{lat:.6f}_{lon:.6f}"
                
                position = VesselPosition(
                    id=position_id,
                    source="SAR",
                    lat=lat,
                    lon=lon,
                    timestamp=datetime.fromisoformat(entry.get("date", "")),
                    zone_name=zone.name,
                    confidence=entry.get("confidence"),
                    vessel_length_m=entry.get("vessel_length_m"),
                    mmsi=entry.get("mmsi"),  # May be None if no AIS match
                    vessel_type=entry.get("vessel_type"),
                    vessel_name=entry.get("vessel_name"),
                    flag=entry.get("flag"),
                    imo=entry.get("imo"),
                    callsign=entry.get("callsign"),
                    ais_matched=entry.get("ais_matched", False),  # Key field for classification
                    is_fishing=entry.get("is_fishing"),
                    raw_data=entry  # Store complete API response
                )
                positions.append(position)
                
            except Exception as e:
                logger.warning(f"Error parsing SAR position: {e}")
                continue
        
        return positions
    
    def _parse_ais_positions(self, data: Dict, zone: MonitoringZone) -> List[VesselPosition]:
        """Parse AIS presence API response into VesselPosition objects"""
        positions = []
        
        for entry in data.get("entries", []):
            try:
                # Generate unique ID for AIS position
                timestamp_str = entry.get("date", "")
                mmsi = entry.get("mmsi", "unknown")
                position_id = f"ais_{zone.name}_{timestamp_str}_{mmsi}"
                
                position = VesselPosition(
                    id=position_id,
                    source="AIS",
                    lat=float(entry.get("lat", 0)),
                    lon=float(entry.get("lon", 0)),
                    timestamp=datetime.fromisoformat(entry.get("date", "")),
                    zone_name=zone.name,
                    confidence=1.0,  # AIS is always high confidence
                    vessel_length_m=entry.get("vessel_length_m"),
                    mmsi=entry.get("mmsi"),
                    vessel_type=entry.get("vessel_type"),
                    vessel_name=entry.get("vessel_name"),
                    flag=entry.get("flag"),
                    imo=entry.get("imo"),
                    callsign=entry.get("callsign"),
                    ais_matched=True,  # AIS is by definition matched
                    is_fishing=entry.get("is_fishing"),
                    raw_data=entry  # Store complete API response
                )
                positions.append(position)
                
            except Exception as e:
                logger.warning(f"Error parsing AIS position: {e}")
                continue
        
        return positions

class GFWDataCollector:
    """Main data collection orchestrator"""
    
    def __init__(self, api_key: str, mongodb_connection: str, database_name: str):
        self.api = GlobalFishingWatchAPI(api_key)
        self.storage = MongoDBStorage(mongodb_connection, database_name)
        self.zones = NORTH_AMERICAN_ZONES
    
    async def initialize(self):
        """Initialize storage connections"""
        await self.storage.connect()
    
    async def collect_zone_data(self, zone: MonitoringZone, days_back: int = 7) -> Dict[str, int]:
        """Collect raw position data for a single zone"""
        logger.info(f"Collecting raw data for zone: {zone.name}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        results = {
            "sar_positions": 0,
            "ais_positions": 0,
            "sar_matched": 0,
            "sar_unmatched": 0
        }
        
        try:
            # Get SAR vessel detections (includes AIS matching status)
            sar_positions = await self.api.get_sar_detections_raw(zone, start_str, end_str)
            if sar_positions:
                await self.storage.store_vessel_positions(sar_positions)
                results["sar_positions"] = len(sar_positions)
                results["sar_matched"] = len([p for p in sar_positions if p.ais_matched])
                results["sar_unmatched"] = len([p for p in sar_positions if not p.ais_matched])
            
            # Get AIS vessel presence
            ais_positions = await self.api.get_ais_presence_raw(zone, start_str, end_str)
            if ais_positions:
                await self.storage.store_vessel_positions(ais_positions)
                results["ais_positions"] = len(ais_positions)
            
            logger.info(f"Zone {zone.name} - SAR: {results['sar_positions']} "
                       f"(matched: {results['sar_matched']}, unmatched: {results['sar_unmatched']}), "
                       f"AIS: {results['ais_positions']}")
            
        except Exception as e:
            logger.error(f"Error collecting data for zone {zone.name}: {e}")
        
        return results
    
    async def collect_all_zones(self, days_back: int = 7) -> Dict[str, Any]:
        """Collect raw data for all North American zones"""
        logger.info(f"Starting raw data collection for {len(self.zones)} zones")
        start_time = datetime.now()
        
        total_results = {
            "zones_processed": 0,
            "total_sar_positions": 0,
            "total_ais_positions": 0,
            "total_sar_matched": 0,
            "total_sar_unmatched": 0,
            "zone_details": {}
        }
        
        # Process each zone
        for zone in self.zones:
            try:
                zone_results = await self.collect_zone_data(zone, days_back)
                
                total_results["zones_processed"] += 1
                total_results["total_sar_positions"] += zone_results["sar_positions"]
                total_results["total_ais_positions"] += zone_results["ais_positions"]
                total_results["total_sar_matched"] += zone_results["sar_matched"]
                total_results["total_sar_unmatched"] += zone_results["sar_unmatched"]
                total_results["zone_details"][zone.name] = zone_results
                
                # Small delay between zones to be respectful to API
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process zone {zone.name}: {e}")
        
        duration = datetime.now() - start_time
        total_results["collection_duration_seconds"] = duration.total_seconds()
        
        logger.info(f"Raw data collection complete in {duration}")
        logger.info(f"Total SAR: {total_results['total_sar_positions']} "
                   f"(matched: {total_results['total_sar_matched']}, "
                   f"unmatched: {total_results['total_sar_unmatched']})")
        logger.info(f"Total AIS: {total_results['total_ais_positions']}")
        
        return total_results
    
    async def close(self):
        """Close connections"""
        await self.storage.close()

# Usage Example
async def main():
    """Example usage of the raw data collector"""
    
    # Configuration
    api_key = os.getenv("GFW_API_KEY", "your_api_key_here")
    mongodb_connection = os.getenv("MONGODB_CONNECTION", "mongodb://localhost:27017")
    database_name = "fishing_surveillance"
    
    # Initialize collector
    collector = GFWDataCollector(api_key, mongodb_connection, database_name)
    
    try:
        # Initialize connections
        await collector.initialize()
        
        # Collect raw data for last 7 days
        logger.info("Starting raw data collection...")
        results = await collector.collect_all_zones(days_back=7)
        
        # Print summary
        print("\n" + "="*50)
        print("RAW DATA COLLECTION SUMMARY")
        print("="*50)
        print(f"Zones processed: {results['zones_processed']}")
        print(f"SAR positions: {results['total_sar_positions']}")
        print(f"  - AIS matched: {results['total_sar_matched']}")
        print(f"  - AIS unmatched: {results['total_sar_unmatched']}")
        print(f"AIS positions: {results['total_ais_positions']}")
        print(f"Duration: {results['collection_duration_seconds']:.1f} seconds")
        
        # Show what's ready for classification
        unmatched_ratio = results['total_sar_unmatched'] / max(1, results['total_sar_positions'])
        print(f"\nReady for classification:")
        print(f"Unmatched SAR positions: {results['total_sar_unmatched']} ({unmatched_ratio:.1%})")
        print("These are stored in MongoDB with lat/lon/timestamp for your models")
        
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
