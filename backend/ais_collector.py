#!/usr/bin/env python3
"""
AIS Data Collector for PennApps
Simplified integration with existing MongoDB setup
"""

import asyncio
import aiohttp
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import os
from pathlib import Path

# Import our MongoDB functions
from api_routes import mongodb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringZone:
    """Geographic zone for monitoring"""
    def __init__(self, name: str, bbox: List[float], description: str, 
                 priority: str = 'medium', country: Optional[str] = None):
        self.name = name
        self.bbox = bbox  # [min_lon, min_lat, max_lon, max_lat]
        self.description = description
        self.priority = priority
        self.country = country

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
        import time
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
                                   start_date: str, end_date: str) -> List[Dict]:
        """Get raw SAR vessel detections from API using correct v3 format"""
        self._check_rate_limit()
        
        # Use the correct v3 API format based on working test
        url = f"{self.base_url}/v3/4wings/report"
        
        # Query parameters (not JSON body)
        params = {
            "spatial-resolution": "HIGH",
            "temporal-resolution": "DAILY", 
            "datasets[0]": "public-global-sar-presence:latest",
            "date-range": f"{start_date},{end_date}",
            "format": "JSON",
            "group-by": "VESSEL_ID"
        }
        
        # JSON body for region specification - use bbox format like in working test
        bbox = zone.bbox
        data = {
            "region": {
                "dataset": "public-eez-areas",
                "id": 8465  # Use a specific EEZ area ID like in the working test
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, params=params, json=data) as response:
                    self.requests_this_minute += 1
                    
                    if response.status == 200:
                        response_data = await response.json()
                        logger.info(f"SAR Response structure: {list(response_data.keys())}")
                        if response_data.get("entries"):
                            logger.info(f"First entry keys: {list(response_data['entries'][0].keys()) if response_data['entries'] else 'No entries'}")
                        positions = self._parse_sar_positions(response_data, zone)
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
                                  start_date: str, end_date: str) -> List[Dict]:
        """Get raw AIS vessel presence from API using correct v3 format"""
        self._check_rate_limit()
        
        # Use the correct v3 API format
        url = f"{self.base_url}/v3/4wings/report"
        
        # Query parameters (not JSON body)
        params = {
            "spatial-resolution": "HIGH",
            "temporal-resolution": "DAILY",
            "datasets[0]": "public-ais-vessel-presence:latest", 
            "date-range": f"{start_date},{end_date}",
            "format": "JSON",
            "group-by": "VESSEL_ID"
        }
        
        # JSON body for region specification - use bbox format like in working test
        bbox = zone.bbox
        data = {
            "region": {
                "dataset": "public-eez-areas",
                "id": 8465  # Use a specific EEZ area ID like in the working test
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, params=params, json=data) as response:
                    self.requests_this_minute += 1
                    
                    if response.status == 200:
                        response_data = await response.json()
                        positions = self._parse_ais_positions(response_data, zone)
                        logger.info(f"Retrieved {len(positions)} AIS positions for {zone.name}")
                        return positions
                    else:
                        error_text = await response.text()
                        logger.error(f"AIS API error for {zone.name}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching AIS data for {zone.name}: {e}")
            return []
    
    def _parse_sar_positions(self, data: Dict, zone: MonitoringZone) -> List[Dict]:
        """Parse SAR detection API response into position dictionaries"""
        positions = []
        
        # The new API response structure has entries with dataset-specific data
        for entry in data.get("entries", []):
            try:
                logger.info(f"Processing entry: {entry}")
                # Each entry contains dataset-specific data
                for dataset_name, dataset_entries in entry.items():
                    logger.info(f"Found dataset: {dataset_name}, entries type: {type(dataset_entries)}")
                    if "sar-presence" in dataset_name.lower() or "public-global-sar-presence" in dataset_name:
                        logger.info(f"Processing SAR dataset: {dataset_name} with {len(dataset_entries) if dataset_entries else 0} entries")
                        if dataset_entries:  # Check if dataset_entries is not None
                            for sar_entry in dataset_entries:
                                # Generate unique ID for SAR detection
                                timestamp_str = sar_entry.get("date", "")
                                lat = float(sar_entry.get("lat", 0))
                                lon = float(sar_entry.get("lon", 0))
                                position_id = f"sar_{zone.name}_{timestamp_str}_{lat:.6f}_{lon:.6f}"
                            
                                position = {
                                    "id": position_id,
                                    "source": "SAR",
                                    "lat": lat,
                                    "lon": lon,
                                    "timestamp": self._parse_timestamp(timestamp_str),
                                    "zone_name": zone.name,
                                    "confidence": sar_entry.get("confidence"),
                                    "vessel_length_m": sar_entry.get("vessel_length_m"),
                                    "mmsi": sar_entry.get("mmsi", ""),
                                    "vessel_type": sar_entry.get("vesselType", ""),
                                    "vessel_name": sar_entry.get("shipName", ""),
                                    "flag": sar_entry.get("flag", ""),
                                    "imo": sar_entry.get("imo", ""),
                                    "callsign": sar_entry.get("callsign", ""),
                                    "ais_matched": bool(sar_entry.get("mmsi")),  # Has MMSI = AIS matched
                                    "is_fishing": sar_entry.get("is_fishing", False),
                                    "detections": sar_entry.get("detections", 1),
                                    "raw_data": sar_entry
                                }
                                positions.append(position)
                
            except Exception as e:
                logger.warning(f"Error parsing SAR position: {e}")
                continue
        
        return positions
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        try:
            # Try ISO format first
            if "T" in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Try date only format
            elif len(timestamp_str) == 10:
                return datetime.strptime(timestamp_str, "%Y-%m-%d")
            else:
                return datetime.fromisoformat(timestamp_str)
        except:
            # Fallback to current time
            return datetime.utcnow()
    
    def _parse_ais_positions(self, data: Dict, zone: MonitoringZone) -> List[Dict]:
        """Parse AIS presence API response into position dictionaries"""
        positions = []
        
        # The new API response structure has entries with dataset-specific data
        for entry in data.get("entries", []):
            try:
                # Each entry contains dataset-specific data
                for dataset_name, dataset_entries in entry.items():
                    if "ais-presence" in dataset_name.lower() or "public-ais-vessel-presence" in dataset_name:
                        for ais_entry in dataset_entries:
                            # Generate unique ID for AIS position
                            timestamp_str = ais_entry.get("date", "")
                            mmsi = ais_entry.get("mmsi", "unknown")
                            position_id = f"ais_{zone.name}_{timestamp_str}_{mmsi}"
                            
                            position = {
                                "id": position_id,
                                "source": "AIS",
                                "lat": float(ais_entry.get("lat", 0)),
                                "lon": float(ais_entry.get("lon", 0)),
                                "timestamp": self._parse_timestamp(timestamp_str),
                                "zone_name": zone.name,
                                "confidence": 1.0,  # AIS is always high confidence
                                "vessel_length_m": ais_entry.get("vessel_length_m"),
                                "mmsi": ais_entry.get("mmsi", ""),
                                "vessel_type": ais_entry.get("vesselType", ""),
                                "vessel_name": ais_entry.get("shipName", ""),
                                "flag": ais_entry.get("flag", ""),
                                "imo": ais_entry.get("imo", ""),
                                "callsign": ais_entry.get("callsign", ""),
                                "ais_matched": True,  # AIS is by definition matched
                                "is_fishing": ais_entry.get("is_fishing", False),
                                "raw_data": ais_entry
                            }
                            positions.append(position)
                
            except Exception as e:
                logger.warning(f"Error parsing AIS position: {e}")
                continue
        
        return positions

class AISDataCollector:
    """Main AIS data collection orchestrator"""
    
    def __init__(self, api_key: str):
        self.api = GlobalFishingWatchAPI(api_key)
        self.zones = self._get_default_zones()
    
    def _get_default_zones(self) -> List[MonitoringZone]:
        """Get default North American monitoring zones"""
        return [
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
                mongodb.store_vessel_positions_bulk(sar_positions)
                results["sar_positions"] = len(sar_positions)
                results["sar_matched"] = len([p for p in sar_positions if p.get("ais_matched", False)])
                results["sar_unmatched"] = len([p for p in sar_positions if not p.get("ais_matched", False)])
            
            # Get AIS vessel presence
            ais_positions = await self.api.get_ais_presence_raw(zone, start_str, end_str)
            if ais_positions:
                mongodb.store_vessel_positions_bulk(ais_positions)
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

# Usage function
async def collect_ais_data(api_key: str, days_back: int = 7):
    """Collect AIS data and store in MongoDB"""
    collector = AISDataCollector(api_key)
    results = await collector.collect_all_zones(days_back)
    return results

if __name__ == "__main__":
    # Example usage
    api_key = os.getenv("GFW_API_KEY")
    asyncio.run(collect_ais_data(api_key))
