#!/usr/bin/env python3
"""
Simple Hotspot Detector

A clean, simplified hotspot detection system that:
- Uses MongoDB data directly
- Implements simple density-based clustering
- Provides clean data structures for frontend
- Minimal dependencies
- Real-time processing
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Import MongoDB functions
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from api_routes.mongodb import getVesselDataForHotspotAnalysis

logger = logging.getLogger(__name__)

@dataclass
class SimpleHotspot:
    """Simplified hotspot data structure for frontend"""
    id: str
    lat: float
    lon: float
    risk_score: float
    risk_level: str
    vessel_count: int
    untracked_ratio: float
    size: float
    color: str
    created_at: datetime

class SimpleHotspotDetector:
    """
    Simplified hotspot detector using basic density clustering
    """
    
    def __init__(self):
        # Risk level thresholds
        self.risk_thresholds = {
            "CRITICAL": 0.8,
            "HIGH": 0.6,
            "MEDIUM": 0.4,
            "LOW": 0.2
        }
        
        # Clustering parameters
        self.cluster_radius_km = 50  # 50km radius for clustering
        self.min_vessels = 3  # Minimum vessels to form a hotspot
        self.max_hotspots = 100  # Limit total hotspots
        
    def detect_hotspots(self, start_date: datetime = None, end_date: datetime = None) -> List[SimpleHotspot]:
        """
        Main hotspot detection function
        """
        try:
            logger.info("🔍 Starting simple hotspot detection...")
            
            # Get vessel data from MongoDB
            vessel_data = getVesselDataForHotspotAnalysis(start_date, end_date)
            
            if vessel_data['total_vessels'] == 0:
                logger.warning("No vessel data available for hotspot detection")
                return []
            
            logger.info(f"📊 Processing {vessel_data['total_vessels']} vessels")
            
            # Separate tracked and untracked vessels
            tracked_vessels = vessel_data['tracked_vessels']
            untracked_vessels = vessel_data['untracked_vessels']
            
            # Find clusters of untracked vessels
            untracked_clusters = self._find_clusters(untracked_vessels)
            
            # Find clusters of tracked vessels for comparison
            tracked_clusters = self._find_clusters(tracked_vessels)
            
            # Calculate hotspots based on untracked vessel clusters
            hotspots = self._calculate_hotspots(untracked_clusters, tracked_clusters)
            
            # Sort by risk score and limit
            hotspots.sort(key=lambda x: x.risk_score, reverse=True)
            hotspots = hotspots[:self.max_hotspots]
            
            logger.info(f"🎯 Detected {len(hotspots)} hotspots")
            return hotspots
            
        except Exception as e:
            logger.error(f"Error in hotspot detection: {e}")
            return []
    
    def _find_clusters(self, vessels: List[Dict]) -> List[Dict]:
        """
        Find clusters of vessels using simple distance-based clustering
        """
        if not vessels:
            return []
        
        clusters = []
        processed = set()
        
        for i, vessel in enumerate(vessels):
            if i in processed:
                continue
                
            # Start new cluster
            cluster = {
                'vessels': [vessel],
                'center_lat': vessel['lat'],
                'center_lon': vessel['lon'],
                'bounds': {
                    'min_lat': vessel['lat'],
                    'max_lat': vessel['lat'],
                    'min_lon': vessel['lon'],
                    'max_lon': vessel['lon']
                }
            }
            processed.add(i)
            
            # Find nearby vessels
            for j, other_vessel in enumerate(vessels):
                if j in processed or i == j:
                    continue
                    
                distance = self._calculate_distance(
                    vessel['lat'], vessel['lon'],
                    other_vessel['lat'], other_vessel['lon']
                )
                
                if distance <= self.cluster_radius_km:
                    cluster['vessels'].append(other_vessel)
                    processed.add(j)
                    
                    # Update cluster bounds
                    cluster['bounds']['min_lat'] = min(cluster['bounds']['min_lat'], other_vessel['lat'])
                    cluster['bounds']['max_lat'] = max(cluster['bounds']['max_lat'], other_vessel['lat'])
                    cluster['bounds']['min_lon'] = min(cluster['bounds']['min_lon'], other_vessel['lon'])
                    cluster['bounds']['max_lon'] = max(cluster['bounds']['max_lon'], other_vessel['lon'])
            
            # Calculate cluster center
            if len(cluster['vessels']) >= self.min_vessels:
                cluster['center_lat'] = sum(v['lat'] for v in cluster['vessels']) / len(cluster['vessels'])
                cluster['center_lon'] = sum(v['lon'] for v in cluster['vessels']) / len(cluster['vessels'])
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in kilometers using Haversine formula
        """
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _calculate_hotspots(self, untracked_clusters: List[Dict], tracked_clusters: List[Dict]) -> List[SimpleHotspot]:
        """
        Calculate hotspot risk scores based on untracked vs tracked vessel clusters
        """
        hotspots = []
        
        for i, untracked_cluster in enumerate(untracked_clusters):
            # Count vessels in cluster
            vessel_count = len(untracked_cluster['vessels'])
            
            # Find nearby tracked clusters for comparison
            nearby_tracked = self._find_nearby_tracked_clusters(
                untracked_cluster, tracked_clusters
            )
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                untracked_cluster, nearby_tracked
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Calculate untracked ratio
            total_nearby_vessels = vessel_count + sum(len(c['vessels']) for c in nearby_tracked)
            untracked_ratio = vessel_count / total_nearby_vessels if total_nearby_vessels > 0 else 1.0
            
            # Create hotspot
            hotspot = SimpleHotspot(
                id=f"hotspot_{i+1}",
                lat=untracked_cluster['center_lat'],
                lon=untracked_cluster['center_lon'],
                risk_score=risk_score,
                risk_level=risk_level,
                vessel_count=vessel_count,
                untracked_ratio=untracked_ratio,
                size=self._calculate_size(risk_score),
                color=self._get_risk_color(risk_level),
                created_at=datetime.utcnow()
            )
            
            hotspots.append(hotspot)
        
        return hotspots
    
    def _find_nearby_tracked_clusters(self, untracked_cluster: Dict, tracked_clusters: List[Dict]) -> List[Dict]:
        """
        Find tracked vessel clusters near an untracked cluster
        """
        nearby = []
        search_radius = self.cluster_radius_km * 2  # Search in larger radius
        
        for tracked_cluster in tracked_clusters:
            distance = self._calculate_distance(
                untracked_cluster['center_lat'], untracked_cluster['center_lon'],
                tracked_cluster['center_lat'], tracked_cluster['center_lon']
            )
            
            if distance <= search_radius:
                nearby.append(tracked_cluster)
        
        return nearby
    
    def _calculate_risk_score(self, untracked_cluster: Dict, nearby_tracked: List[Dict]) -> float:
        """
        Calculate risk score based on vessel density and isolation
        """
        # Base score from untracked vessel count
        base_score = min(len(untracked_cluster['vessels']) / 10.0, 1.0)
        
        # Isolation factor (higher if no nearby tracked vessels)
        isolation_factor = 1.0
        if not nearby_tracked:
            isolation_factor = 1.5  # Higher risk if no tracked vessels nearby
        else:
            # Lower risk if there are tracked vessels nearby
            tracked_count = sum(len(c['vessels']) for c in nearby_tracked)
            isolation_factor = max(0.5, 1.0 - (tracked_count / 20.0))
        
        # Density factor (higher density = higher risk)
        cluster_area = self._calculate_cluster_area(untracked_cluster)
        density_factor = len(untracked_cluster['vessels']) / max(cluster_area, 1.0)
        density_factor = min(density_factor, 2.0)  # Cap at 2.0
        
        # Combine factors
        risk_score = base_score * isolation_factor * density_factor
        
        # Normalize to 0-1 range
        return min(risk_score, 1.0)
    
    def _calculate_cluster_area(self, cluster: Dict) -> float:
        """
        Calculate approximate area of cluster in square kilometers
        """
        bounds = cluster['bounds']
        lat_range = bounds['max_lat'] - bounds['min_lat']
        lon_range = bounds['max_lon'] - bounds['min_lon']
        
        # Convert to kilometers (approximate)
        lat_km = lat_range * 111.0  # 1 degree latitude ≈ 111 km
        lon_km = lon_range * 111.0 * math.cos(math.radians(cluster['center_lat']))
        
        return max(lat_km * lon_km, 1.0)  # Minimum 1 km²
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """
        Determine risk level based on score
        """
        if risk_score >= self.risk_thresholds["CRITICAL"]:
            return "CRITICAL"
        elif risk_score >= self.risk_thresholds["HIGH"]:
            return "HIGH"
        elif risk_score >= self.risk_thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_size(self, risk_score: float) -> float:
        """
        Calculate hotspot size based on risk score
        """
        # Scale from 0.01 to 0.05 based on risk score
        return 0.01 + (risk_score * 0.04)
    
    def _get_risk_color(self, risk_level: str) -> str:
        """
        Get color for risk level
        """
        colors = {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff6600", 
            "MEDIUM": "#ffaa00",
            "LOW": "#00ff00"
        }
        return colors.get(risk_level, "#00ff00")
    
    def get_hotspots_by_region(self, min_lat: float, max_lat: float, 
                              min_lon: float, max_lon: float) -> List[SimpleHotspot]:
        """
        Get hotspots within a geographic region
        """
        all_hotspots = self.detect_hotspots()
        
        return [
            hotspot for hotspot in all_hotspots
            if (min_lat <= hotspot.lat <= max_lat and 
                min_lon <= hotspot.lon <= max_lon)
        ]
    
    def get_hotspots_by_risk_level(self, risk_level: str) -> List[SimpleHotspot]:
        """
        Get hotspots by risk level
        """
        all_hotspots = self.detect_hotspots()
        
        return [
            hotspot for hotspot in all_hotspots
            if hotspot.risk_level == risk_level.upper()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get hotspot statistics
        """
        all_hotspots = self.detect_hotspots()
        
        if not all_hotspots:
            return {
                "total_hotspots": 0,
                "by_risk_level": {},
                "average_risk": 0,
                "total_vessels": 0
            }
        
        # Count by risk level
        by_risk_level = {}
        for hotspot in all_hotspots:
            level = hotspot.risk_level
            by_risk_level[level] = by_risk_level.get(level, 0) + 1
        
        # Calculate averages
        avg_risk = sum(h.risk_score for h in all_hotspots) / len(all_hotspots)
        total_vessels = sum(h.vessel_count for h in all_hotspots)
        
        return {
            "total_hotspots": len(all_hotspots),
            "by_risk_level": by_risk_level,
            "average_risk": round(avg_risk, 3),
            "total_vessels": total_vessels,
            "last_updated": datetime.utcnow().isoformat()
        }

# Global detector instance
simple_hotspot_detector = SimpleHotspotDetector()
