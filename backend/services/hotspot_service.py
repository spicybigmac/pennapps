#!/usr/bin/env python3
"""
Hotspot Service

Core service for managing hotspot data, analysis, and real-time updates.
Provides business logic for hotspot detection and risk assessment.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class Hotspot:
    """Hotspot data structure."""
    id: str
    lat: float
    lon: float
    risk_score: float
    relative_risk: float
    isolation_score: float
    month: int
    tracked_density: float
    untracked_density: float
    rank: Optional[int] = None
    risk_level: Optional[str] = None
    color: Optional[str] = None
    size: Optional[float] = None

class HotspotService:
    """Core service for hotspot management and analysis."""
    
    def __init__(self, data_dir: str = "model/hotspot_analysis"):
        self.data_dir = Path(data_dir)
        self.hotspots: List[Hotspot] = []
        self.last_updated: Optional[datetime] = None
        self.risk_thresholds = {
            "CRITICAL": 80,
            "HIGH": 60, 
            "MEDIUM": 40,
            "LOW": 20
        }
        self.load_data()
    
    def load_data(self) -> bool:
        """Load hotspot data from files."""
        try:
            hotspots_file = self.data_dir / "top_hotspots.json"
            if not hotspots_file.exists():
                logger.warning(f"Hotspot data file not found: {hotspots_file}")
                return False
            
            with open(hotspots_file, 'r') as f:
                raw_hotspots = json.load(f)
            
            # Convert to Hotspot objects
            self.hotspots = []
            for i, raw_hotspot in enumerate(raw_hotspots):
                hotspot = Hotspot(
                    id=f"hotspot_{i+1}",
                    lat=raw_hotspot.get('lat', 0),
                    lon=raw_hotspot.get('lon', 0),
                    risk_score=raw_hotspot.get('risk_score', 0),
                    relative_risk=raw_hotspot.get('relative_risk', 0),
                    isolation_score=raw_hotspot.get('isolation_score', 0),
                    month=raw_hotspot.get('month', 0),
                    tracked_density=raw_hotspot.get('tracked_density', 0),
                    untracked_density=raw_hotspot.get('untracked_density', 0)
                )
                
                # Calculate derived properties
                self._calculate_hotspot_properties(hotspot)
                self.hotspots.append(hotspot)
            
            # Sort by risk score
            self.hotspots.sort(key=lambda x: x.risk_score, reverse=True)
            
            # Assign ranks
            for i, hotspot in enumerate(self.hotspots):
                hotspot.rank = i + 1
            
            self.last_updated = datetime.now()
            logger.info(f"Loaded {len(self.hotspots)} hotspots")
            return True
            
        except Exception as e:
            logger.error(f"Error loading hotspot data: {e}")
            return False
    
    def _calculate_hotspot_properties(self, hotspot: Hotspot):
        """Calculate derived properties for a hotspot."""
        # Determine risk level
        if hotspot.risk_score >= self.risk_thresholds["CRITICAL"]:
            hotspot.risk_level = "CRITICAL"
            hotspot.color = "#ff0000"
            hotspot.size = 0.03
        elif hotspot.risk_score >= self.risk_thresholds["HIGH"]:
            hotspot.risk_level = "HIGH"
            hotspot.color = "#ff6600"
            hotspot.size = 0.02
        elif hotspot.risk_score >= self.risk_thresholds["MEDIUM"]:
            hotspot.risk_level = "MEDIUM"
            hotspot.color = "#ffaa00"
            hotspot.size = 0.015
        else:
            hotspot.risk_level = "LOW"
            hotspot.color = "#00ff00"
            hotspot.size = 0.01
    
    def get_top_hotspots(self, limit: int = 5, min_risk: float = 0) -> List[Hotspot]:
        """Get top hotspots with optional filtering."""
        filtered_hotspots = [
            h for h in self.hotspots 
            if h.risk_score >= min_risk
        ]
        return filtered_hotspots[:limit]
    
    def get_hotspots_by_region(self, min_lat: float, max_lat: float, 
                              min_lon: float, max_lon: float) -> List[Hotspot]:
        """Get hotspots within a geographic region."""
        return [
            h for h in self.hotspots
            if (min_lat <= h.lat <= max_lat and 
                min_lon <= h.lon <= max_lon)
        ]
    
    def get_hotspots_by_month(self, month: int) -> List[Hotspot]:
        """Get hotspots for a specific month."""
        return [h for h in self.hotspots if h.month == month]
    
    def get_hotspots_by_risk_level(self, risk_level: str) -> List[Hotspot]:
        """Get hotspots by risk level."""
        return [h for h in self.hotspots if h.risk_level == risk_level.upper()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        if not self.hotspots:
            return {}
        
        risk_scores = [h.risk_score for h in self.hotspots]
        
        # Calculate risk distribution
        risk_distribution = {}
        for level, threshold in self.risk_thresholds.items():
            if level == "LOW":
                count = len([r for r in risk_scores if r < threshold])
            else:
                next_threshold = min([t for t in self.risk_thresholds.values() if t > threshold], default=float('inf'))
                count = len([r for r in risk_scores if threshold <= r < next_threshold])
            risk_distribution[level.lower()] = count
        
        # Monthly breakdown
        monthly_stats = {}
        for month in range(1, 6):
            month_hotspots = self.get_hotspots_by_month(month)
            if month_hotspots:
                monthly_stats[month] = {
                    "count": len(month_hotspots),
                    "avg_risk": sum(h.risk_score for h in month_hotspots) / len(month_hotspots),
                    "max_risk": max(h.risk_score for h in month_hotspots),
                    "top_hotspot": max(month_hotspots, key=lambda x: x.risk_score).id
                }
        
        return {
            "total_hotspots": len(self.hotspots),
            "average_risk": np.mean(risk_scores),
            "max_risk": np.max(risk_scores),
            "min_risk": np.min(risk_scores),
            "risk_distribution": risk_distribution,
            "monthly_breakdown": monthly_stats,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    def get_globe_integration_data(self) -> Dict[str, Any]:
        """Get data formatted for Three.js globe integration."""
        top_hotspots = self.get_top_hotspots(limit=5)
        
        return {
            "hotspots": [
                {
                    "id": hotspot.id,
                    "rank": hotspot.rank,
                    "position": {
                        "lat": hotspot.lat,
                        "lon": hotspot.lon
                    },
                    "risk": {
                        "score": hotspot.risk_score,
                        "level": hotspot.risk_level,
                        "color": hotspot.color,
                        "size": hotspot.size
                    },
                    "metadata": {
                        "month": hotspot.month,
                        "relative_risk": hotspot.relative_risk,
                        "isolation_score": hotspot.isolation_score,
                        "tracked_density": hotspot.tracked_density,
                        "untracked_density": hotspot.untracked_density
                    },
                    "name": f"{hotspot.risk_level} Risk Hotspot #{hotspot.rank}",
                    "description": f"Risk Score: {hotspot.risk_score:.1f} | Month: {hotspot.month}"
                }
                for hotspot in top_hotspots
            ],
            "metadata": {
                "total_hotspots": len(self.hotspots),
                "last_updated": self.last_updated.isoformat() if self.last_updated else None,
                "data_source": "Global Fishing Watch SAR Analysis",
                "analysis_period": "5 months (April-September 2025)"
            }
        }
    
    def search_hotspots(self, query: str) -> List[Hotspot]:
        """Search hotspots by various criteria."""
        query_lower = query.lower()
        results = []
        
        for hotspot in self.hotspots:
            # Search by risk level
            if query_lower in hotspot.risk_level.lower():
                results.append(hotspot)
                continue
            
            # Search by month
            if query_lower in f"month {hotspot.month}":
                results.append(hotspot)
                continue
            
            # Search by coordinates (approximate)
            if any(char.isdigit() for char in query):
                try:
                    # Try to parse as coordinates
                    if ',' in query:
                        lat_str, lon_str = query.split(',')
                        lat, lon = float(lat_str.strip()), float(lon_str.strip())
                        if abs(hotspot.lat - lat) < 1 and abs(hotspot.lon - lon) < 1:
                            results.append(hotspot)
                except:
                    pass
        
        return results
    
    def get_risk_trends(self) -> Dict[str, Any]:
        """Get risk trends over time."""
        monthly_data = {}
        
        for month in range(1, 6):
            month_hotspots = self.get_hotspots_by_month(month)
            if month_hotspots:
                monthly_data[month] = {
                    "count": len(month_hotspots),
                    "avg_risk": np.mean([h.risk_score for h in month_hotspots]),
                    "max_risk": max([h.risk_score for h in month_hotspots]),
                    "risk_levels": {
                        level: len([h for h in month_hotspots if h.risk_level == level])
                        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                    }
                }
        
        return {
            "monthly_trends": monthly_data,
            "overall_trend": self._calculate_overall_trend(monthly_data)
        }
    
    def _calculate_overall_trend(self, monthly_data: Dict) -> str:
        """Calculate overall risk trend."""
        if len(monthly_data) < 2:
            return "insufficient_data"
        
        months = sorted(monthly_data.keys())
        first_month_avg = monthly_data[months[0]]["avg_risk"]
        last_month_avg = monthly_data[months[-1]]["avg_risk"]
        
        if last_month_avg > first_month_avg * 1.1:
            return "increasing"
        elif last_month_avg < first_month_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def refresh_data(self) -> bool:
        """Refresh data from files."""
        return self.load_data()
    
    def get_hotspot_by_id(self, hotspot_id: str) -> Optional[Hotspot]:
        """Get a specific hotspot by ID."""
        for hotspot in self.hotspots:
            if hotspot.id == hotspot_id:
                return hotspot
        return None
    
    def get_nearby_hotspots(self, lat: float, lon: float, radius: float = 1.0) -> List[Hotspot]:
        """Get hotspots within a radius of a given point."""
        nearby = []
        for hotspot in self.hotspots:
            # Simple distance calculation (not accurate for large distances)
            distance = np.sqrt((hotspot.lat - lat)**2 + (hotspot.lon - lon)**2)
            if distance <= radius:
                nearby.append(hotspot)
        return nearby

# Global service instance
hotspot_service = HotspotService()
