#!/usr/bin/env python3
"""
Hotspot Analysis Module

Clean hotspot analysis system that:
- Analyzes vessel data for illegal fishing patterns
- Generates hotspot reports and visualizations
- Provides statistical analysis
- Exports data in various formats
"""

import json
import logging
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys

# Add backend to path for MongoDB imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
from api_routes.mongodb import getVesselDataForHotspotAnalysis

logger = logging.getLogger(__name__)

class HotspotAnalyzer:
    """
    Main hotspot analysis class
    """
    
    def __init__(self, analysis_dir: str = None):
        self.analysis_dir = Path(analysis_dir) if analysis_dir else Path(__file__).parent
        self.analysis_dir.mkdir(exist_ok=True)
        
        # Analysis parameters
        self.cluster_radius_km = 50
        self.min_vessels_for_hotspot = 3
        self.risk_thresholds = {
            "CRITICAL": 0.8,
            "HIGH": 0.6,
            "MEDIUM": 0.4,
            "LOW": 0.2
        }
        
    def analyze_hotspots(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Main analysis function - detects and analyzes hotspots
        """
        try:
            logger.info("🔍 Starting hotspot analysis...")
            
            # Get vessel data
            vessel_data = getVesselDataForHotspotAnalysis(start_date, end_date)
            
            if vessel_data['total_vessels'] == 0:
                logger.warning("No vessel data available for analysis")
                return self._empty_analysis_result()
            
            logger.info(f"📊 Analyzing {vessel_data['total_vessels']} vessels")
            
            # Find clusters
            untracked_clusters = self._find_clusters(vessel_data['untracked_vessels'])
            tracked_clusters = self._find_clusters(vessel_data['tracked_vessels'])
            
            # Calculate hotspots
            hotspots = self._calculate_hotspots(untracked_clusters, tracked_clusters)
            
            # Generate analysis report
            analysis_result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "time_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "data_summary": {
                    "total_vessels": vessel_data['total_vessels'],
                    "tracked_vessels": len(vessel_data['tracked_vessels']),
                    "untracked_vessels": len(vessel_data['untracked_vessels']),
                    "untracked_ratio": len(vessel_data['untracked_vessels']) / vessel_data['total_vessels']
                },
                "hotspots": hotspots,
                "statistics": self._calculate_statistics(hotspots),
                "risk_distribution": self._calculate_risk_distribution(hotspots)
            }
            
            # Save analysis results
            self._save_analysis_results(analysis_result)
            
            logger.info(f"✅ Analysis complete: {len(hotspots)} hotspots detected")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in hotspot analysis: {e}")
            return self._empty_analysis_result()
    
    def _find_clusters(self, vessels: List[Dict]) -> List[Dict]:
        """
        Find clusters of vessels using distance-based clustering
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
            
            # Only keep clusters with minimum vessel count
            if len(cluster['vessels']) >= self.min_vessels_for_hotspot:
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
    
    def _calculate_hotspots(self, untracked_clusters: List[Dict], tracked_clusters: List[Dict]) -> List[Dict]:
        """
        Calculate hotspot risk scores and metadata
        """
        hotspots = []
        
        for i, untracked_cluster in enumerate(untracked_clusters):
            # Find nearby tracked clusters
            nearby_tracked = self._find_nearby_tracked_clusters(untracked_cluster, tracked_clusters)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(untracked_cluster, nearby_tracked)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Calculate metadata
            vessel_count = len(untracked_cluster['vessels'])
            total_nearby_vessels = vessel_count + sum(len(c['vessels']) for c in nearby_tracked)
            untracked_ratio = vessel_count / total_nearby_vessels if total_nearby_vessels > 0 else 1.0
            
            # Create hotspot
            hotspot = {
                "id": f"hotspot_{i+1}",
                "lat": untracked_cluster['center_lat'],
                "lon": untracked_cluster['center_lon'],
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "vessel_count": vessel_count,
                "untracked_ratio": round(untracked_ratio, 3),
                "size": self._calculate_size(risk_score),
                "color": self._get_risk_color(risk_level),
                "bounds": untracked_cluster['bounds'],
                "nearby_tracked_count": len(nearby_tracked),
                "created_at": datetime.utcnow().isoformat()
            }
            
            hotspots.append(hotspot)
        
        # Sort by risk score
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        return hotspots
    
    def _find_nearby_tracked_clusters(self, untracked_cluster: Dict, tracked_clusters: List[Dict]) -> List[Dict]:
        """
        Find tracked vessel clusters near an untracked cluster
        """
        nearby = []
        search_radius = self.cluster_radius_km * 2
        
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
        
        # Isolation factor
        isolation_factor = 1.0
        if not nearby_tracked:
            isolation_factor = 1.5  # Higher risk if no tracked vessels nearby
        else:
            tracked_count = sum(len(c['vessels']) for c in nearby_tracked)
            isolation_factor = max(0.5, 1.0 - (tracked_count / 20.0))
        
        # Density factor
        cluster_area = self._calculate_cluster_area(untracked_cluster)
        density_factor = len(untracked_cluster['vessels']) / max(cluster_area, 1.0)
        density_factor = min(density_factor, 2.0)
        
        # Combine factors
        risk_score = base_score * isolation_factor * density_factor
        return min(risk_score, 1.0)
    
    def _calculate_cluster_area(self, cluster: Dict) -> float:
        """
        Calculate approximate area of cluster in square kilometers
        """
        bounds = cluster['bounds']
        lat_range = bounds['max_lat'] - bounds['min_lat']
        lon_range = bounds['max_lon'] - bounds['min_lon']
        
        # Convert to kilometers (approximate)
        lat_km = lat_range * 111.0
        lon_km = lon_range * 111.0 * math.cos(math.radians(cluster['center_lat']))
        
        return max(lat_km * lon_km, 1.0)
    
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
    
    def _calculate_statistics(self, hotspots: List[Dict]) -> Dict[str, Any]:
        """
        Calculate hotspot statistics
        """
        if not hotspots:
            return {
                "total_hotspots": 0,
                "average_risk": 0,
                "max_risk": 0,
                "total_vessels": 0
            }
        
        risk_scores = [h['risk_score'] for h in hotspots]
        
        return {
            "total_hotspots": len(hotspots),
            "average_risk": round(sum(risk_scores) / len(risk_scores), 3),
            "max_risk": round(max(risk_scores), 3),
            "total_vessels": sum(h['vessel_count'] for h in hotspots)
        }
    
    def _calculate_risk_distribution(self, hotspots: List[Dict]) -> Dict[str, int]:
        """
        Calculate distribution of hotspots by risk level
        """
        distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for hotspot in hotspots:
            level = hotspot['risk_level']
            distribution[level] = distribution.get(level, 0) + 1
        
        return distribution
    
    def _save_analysis_results(self, analysis_result: Dict[str, Any]):
        """
        Save analysis results to files
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save full analysis
        analysis_file = self.analysis_dir / f"hotspot_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis_result, f, indent=2)
        
        # Save top hotspots for quick access
        top_hotspots = analysis_result['hotspots'][:50]  # Top 50
        top_hotspots_file = self.analysis_dir / "top_hotspots.json"
        with open(top_hotspots_file, 'w') as f:
            json.dump(top_hotspots, f, indent=2)
        
        # Save summary
        summary = {
            "timestamp": analysis_result['analysis_timestamp'],
            "total_hotspots": analysis_result['statistics']['total_hotspots'],
            "risk_distribution": analysis_result['risk_distribution'],
            "data_summary": analysis_result['data_summary']
        }
        summary_file = self.analysis_dir / "hotspot_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Analysis results saved to {self.analysis_dir}")
    
    def _empty_analysis_result(self) -> Dict[str, Any]:
        """
        Return empty analysis result
        """
        return {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "time_range": {"start": None, "end": None},
            "data_summary": {
                "total_vessels": 0,
                "tracked_vessels": 0,
                "untracked_vessels": 0,
                "untracked_ratio": 0
            },
            "hotspots": [],
            "statistics": {
                "total_hotspots": 0,
                "average_risk": 0,
                "max_risk": 0,
                "total_vessels": 0
            },
            "risk_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }
    
    def load_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent analysis results
        """
        try:
            # Look for the most recent analysis file
            analysis_files = list(self.analysis_dir.glob("hotspot_analysis_*.json"))
            if not analysis_files:
                return None
            
            latest_file = max(analysis_files, key=os.path.getctime)
            
            with open(latest_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading latest analysis: {e}")
            return None
    
    def get_top_hotspots(self, limit: int = 50) -> List[Dict]:
        """
        Get top hotspots from latest analysis
        """
        try:
            top_hotspots_file = self.analysis_dir / "top_hotspots.json"
            if not top_hotspots_file.exists():
                return []
            
            with open(top_hotspots_file, 'r') as f:
                hotspots = json.load(f)
            
            return hotspots[:limit]
            
        except Exception as e:
            logger.error(f"Error loading top hotspots: {e}")
            return []

# Global analyzer instance
hotspot_analyzer = HotspotAnalyzer()
