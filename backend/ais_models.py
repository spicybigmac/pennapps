#!/usr/bin/env python3
"""
AIS Data Models and Core Classes
Simplified models for Global Fishing Watch data integration
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Data Models for AIS Integration
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

# Default North American monitoring zones
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