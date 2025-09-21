#!/usr/bin/env python3
"""
Enhanced Hotspot Analysis Module

Advanced hotspot analysis that incorporates:
- Port proximity data
- Fishing season information
- Environmental factors
- Historical patterns
- Risk scoring with multiple factors
"""

import json
import logging
import math
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys

# Add backend to path for MongoDB imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
from api_routes.mongodb import getVesselDataForHotspotAnalysis

logger = logging.getLogger(__name__)

class EnhancedHotspotAnalyzer:
    """
    Enhanced hotspot analysis with auxiliary data integration
    """
    
    def __init__(self, analysis_dir: str = None):
        self.analysis_dir = Path(analysis_dir) if analysis_dir else Path(__file__).parent
        self.analysis_dir.mkdir(exist_ok=True)
        
        # Load auxiliary data
        self.port_data = self._load_port_data()
        self.fishing_seasons = self._load_fishing_seasons()
        
        # Analysis parameters
        self.cluster_radius_km = 50
        self.min_vessels_for_hotspot = 3
        self.port_proximity_km = 100  # Consider ports within 100km
        self.risk_thresholds = {
            "CRITICAL": 0.8,
            "HIGH": 0.6,
            "MEDIUM": 0.4,
            "LOW": 0.2
        }
        
        logger.info(f"📊 Loaded {len(self.port_data)} ports and {len(self.fishing_seasons)} fishing seasons")
    
    def _load_port_data(self) -> List[Dict]:
        """
        Load port data from CSV file
        """
        try:
            port_file = Path(__file__).parent.parent / "aux_data" / "UpdatedPub150.csv"
            if not port_file.exists():
                logger.warning("Port data file not found")
                return []
            
            ports = []
            with open(port_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat = float(row.get('Latitude', 0))
                        lon = float(row.get('Longitude', 0))
                        if lat != 0 and lon != 0:  # Valid coordinates
                            ports.append({
                                'name': row.get('Main Port Name', ''),
                                'country': row.get('Country Code', ''),
                                'lat': lat,
                                'lon': lon,
                                'harbor_type': row.get('Harbor Type', ''),
                                'harbor_size': row.get('Harbor Size', ''),
                                'facilities': {
                                    'oil_terminal': row.get('Oil Terminal Depth (m)', '0') != '0',
                                    'container': row.get('Facilities - Container', '') == 'Yes',
                                    'fishing': row.get('Harbor Use', '').lower().find('fishing') != -1
                                }
                            })
                    except (ValueError, KeyError) as e:
                        continue  # Skip invalid rows
            
            logger.info(f"Loaded {len(ports)} ports")
            return ports
            
        except Exception as e:
            logger.error(f"Error loading port data: {e}")
            return []
    
    def _load_fishing_seasons(self) -> Dict[str, Dict]:
        """
        Load fishing season data (simplified for now)
        """
        # This would typically load from a database or API
        # For now, return a simplified structure
        return {
            "north_atlantic": {
                "name": "North Atlantic",
                "seasons": {
                    "spring": {"start": "03-01", "end": "05-31", "intensity": 0.8},
                    "summer": {"start": "06-01", "end": "08-31", "intensity": 1.0},
                    "fall": {"start": "09-01", "end": "11-30", "intensity": 0.9},
                    "winter": {"start": "12-01", "end": "02-28", "intensity": 0.6}
                }
            },
            "south_pacific": {
                "name": "South Pacific",
                "seasons": {
                    "summer": {"start": "12-01", "end": "02-28", "intensity": 1.0},
                    "fall": {"start": "03-01", "end": "05-31", "intensity": 0.8},
                    "winter": {"start": "06-01", "end": "08-31", "intensity": 0.7},
                    "spring": {"start": "09-01", "end": "11-30", "intensity": 0.9}
                }
            }
        }
    
    def analyze_hotspots(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Enhanced hotspot analysis with auxiliary data
        """
        try:
            logger.info("🔍 Starting enhanced hotspot analysis...")
            
            # Get vessel data
            vessel_data = getVesselDataForHotspotAnalysis(start_date, end_date)
            
            if vessel_data['total_vessels'] == 0:
                logger.warning("No vessel data available for analysis")
                return self._empty_analysis_result()
            
            logger.info(f"📊 Analyzing {vessel_data['total_vessels']} vessels")
            
            # Find clusters
            untracked_clusters = self._find_clusters(vessel_data['untracked_vessels'])
            tracked_clusters = self._find_clusters(vessel_data['tracked_vessels'])
            
            # Calculate enhanced hotspots
            hotspots = self._calculate_enhanced_hotspots(untracked_clusters, tracked_clusters, start_date)
            
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
                "auxiliary_data": {
                    "ports_loaded": len(self.port_data),
                    "fishing_seasons_loaded": len(self.fishing_seasons)
                },
                "hotspots": hotspots,
                "statistics": self._calculate_statistics(hotspots),
                "risk_distribution": self._calculate_risk_distribution(hotspots)
            }
            
            # Save analysis results
            self._save_analysis_results(analysis_result)
            
            logger.info(f"✅ Enhanced analysis complete: {len(hotspots)} hotspots detected")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in enhanced hotspot analysis: {e}")
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
    
    def _calculate_enhanced_hotspots(self, untracked_clusters: List[Dict], tracked_clusters: List[Dict], analysis_date: datetime = None) -> List[Dict]:
        """
        Calculate enhanced hotspots with auxiliary data factors
        """
        hotspots = []
        
        for i, untracked_cluster in enumerate(untracked_clusters):
            # Find nearby tracked clusters
            nearby_tracked = self._find_nearby_tracked_clusters(untracked_cluster, tracked_clusters)
            
            # Find nearby ports
            nearby_ports = self._find_nearby_ports(untracked_cluster)
            
            # Calculate fishing season factor
            fishing_factor = self._calculate_fishing_season_factor(untracked_cluster, analysis_date)
            
            # Calculate enhanced risk score
            risk_score = self._calculate_enhanced_risk_score(
                untracked_cluster, nearby_tracked, nearby_ports, fishing_factor
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Calculate metadata
            vessel_count = len(untracked_cluster['vessels'])
            total_nearby_vessels = vessel_count + sum(len(c['vessels']) for c in nearby_tracked)
            untracked_ratio = vessel_count / total_nearby_vessels if total_nearby_vessels > 0 else 1.0
            
            # Create enhanced hotspot
            hotspot = {
                "id": f"enhanced_hotspot_{i+1}",
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
                "nearby_ports": nearby_ports,
                "fishing_season_factor": round(fishing_factor, 3),
                "enhanced_factors": {
                    "port_proximity": len(nearby_ports),
                    "fishing_season": fishing_factor,
                    "isolation": 1.0 - (len(nearby_tracked) / 10.0) if nearby_tracked else 1.0,
                    "density": vessel_count / max(self._calculate_cluster_area(untracked_cluster), 1.0)
                },
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
    
    def _find_nearby_ports(self, cluster: Dict) -> List[Dict]:
        """
        Find ports near a cluster
        """
        nearby_ports = []
        
        for port in self.port_data:
            distance = self._calculate_distance(
                cluster['center_lat'], cluster['center_lon'],
                port['lat'], port['lon']
            )
            
            if distance <= self.port_proximity_km:
                port_info = port.copy()
                port_info['distance_km'] = round(distance, 2)
                nearby_ports.append(port_info)
        
        # Sort by distance
        nearby_ports.sort(key=lambda x: x['distance_km'])
        return nearby_ports[:5]  # Return top 5 closest ports
    
    def _calculate_fishing_season_factor(self, cluster: Dict, analysis_date: datetime = None) -> float:
        """
        Calculate fishing season factor based on location and time
        """
        if not analysis_date:
            analysis_date = datetime.utcnow()
        
        # Determine region based on latitude
        lat = cluster['center_lat']
        if lat > 30:  # Northern hemisphere
            region = "north_atlantic"
        elif lat < -30:  # Southern hemisphere
            region = "south_pacific"
        else:  # Tropical region
            return 0.8  # Moderate fishing activity year-round
        
        # Get current season
        month_day = analysis_date.strftime("%m-%d")
        seasons = self.fishing_seasons.get(region, {}).get("seasons", {})
        
        for season_name, season_data in seasons.items():
            if season_data["start"] <= month_day <= season_data["end"]:
                return season_data["intensity"]
        
        # Default to moderate activity if no season matches
        return 0.6
    
    def _calculate_enhanced_risk_score(self, untracked_cluster: Dict, nearby_tracked: List[Dict], 
                                     nearby_ports: List[Dict], fishing_factor: float) -> float:
        """
        Calculate enhanced risk score with multiple factors
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
        
        # Port proximity factor (higher risk if far from ports)
        port_factor = 1.0
        if nearby_ports:
            closest_port_distance = nearby_ports[0]['distance_km']
            port_factor = max(0.5, 1.0 - (closest_port_distance / 200.0))  # Normalize to 200km
        else:
            port_factor = 1.2  # Higher risk if no ports nearby
        
        # Fishing season factor
        season_factor = 0.8 + (fishing_factor * 0.4)  # Scale from 0.8 to 1.2
        
        # Combine all factors
        risk_score = (base_score * isolation_factor * density_factor * 
                     port_factor * season_factor)
        
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
        analysis_file = self.analysis_dir / f"enhanced_hotspot_analysis_{timestamp}.json"
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
            "data_summary": analysis_result['data_summary'],
            "auxiliary_data": analysis_result['auxiliary_data']
        }
        summary_file = self.analysis_dir / "hotspot_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Enhanced analysis results saved to {self.analysis_dir}")
    
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
            "auxiliary_data": {
                "ports_loaded": len(self.port_data),
                "fishing_seasons_loaded": len(self.fishing_seasons)
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

# Global enhanced analyzer instance
enhanced_hotspot_analyzer = EnhancedHotspotAnalyzer()
