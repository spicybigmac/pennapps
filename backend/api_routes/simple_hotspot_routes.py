#!/usr/bin/env python3
"""
Simple Hotspot API Routes

Clean, simplified API endpoints for hotspot detection
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

# Import new analysis system
import sys
from pathlib import Path
sys.path.append('/Users/ibuddhar/Dev/F2025/pennapps')
from model.hotspot_analysis.hotspot_analyzer import HotspotAnalyzer
from model.hotspot_analysis.enhanced_hotspot_analyzer import EnhancedHotspotAnalyzer

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

@router.get("/")
async def get_hotspots(
    limit: int = Query(50, description="Maximum number of hotspots to return"),
    min_risk: float = Query(0.0, description="Minimum risk score threshold"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: CRITICAL, HIGH, MEDIUM, LOW")
):
    """Get all hotspots with optional filtering"""
    try:
        # Use the new analysis system
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze_hotspots()
        
        # Apply filters
        if min_risk > 0:
            hotspots = [h for h in hotspots if h['risk_score'] >= min_risk]
        
        if risk_level:
            hotspots = [h for h in hotspots if h['risk_level'] == risk_level.upper()]
        
        # Sort by risk score and limit
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        hotspots = hotspots[:limit]
        
        # Add rank to each hotspot
        for i, hotspot in enumerate(hotspots):
            hotspot['rank'] = i + 1
        
        return {
            "hotspots": hotspots,
            "total": len(hotspots),
            "filters": {
                "limit": limit,
                "min_risk": min_risk,
                "risk_level": risk_level
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/globe-data")
async def get_globe_hotspots():
    """Get hotspots formatted for globe visualization"""
    try:
        # Get top 20 hotspots for globe using new analysis system
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze_hotspots()
        hotspots = hotspots[:20]  # Limit for performance
        
        # Format for Three.js globe
        globe_data = {
            "hotspots": [],
            "metadata": {
                "total_hotspots": len(hotspots),
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "MongoDB AIS Analysis"
            }
        }
        
        for i, hotspot in enumerate(hotspots):
            globe_hotspot = {
                "id": hotspot.get('id', f'hotspot_{i}'),
                "rank": i + 1,
                "position": {
                    "lat": hotspot['lat'],
                    "lon": hotspot['lon']
                },
                "risk": {
                    "score": hotspot['risk_score'],
                    "level": hotspot['risk_level'],
                    "color": hotspot.get('color', '#ff4444'),
                    "size": hotspot.get('size', 1.0)
                },
                "metadata": {
                    "vessel_count": hotspot['vessel_count'],
                    "untracked_ratio": hotspot.get('untracked_ratio', 0.0),
                    "created_at": hotspot.get('created_at', datetime.utcnow().isoformat())
                },
                "name": f"{hotspot['risk_level']} Risk Hotspot #{i+1}",
                "description": f"Risk Score: {hotspot['risk_score']:.2f} | Vessels: {hotspot['vessel_count']}"
            }
            globe_data["hotspots"].append(globe_hotspot)
        
        return globe_data
    
    except Exception as e:
        logger.error(f"Error getting globe hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/region")
async def get_hotspots_by_region(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lon: float = Query(..., description="Maximum longitude")
):
    """Get hotspots within a geographic region"""
    try:
        hotspots = simple_hotspot_detector.get_hotspots_by_region(
            min_lat, max_lat, min_lon, max_lon
        )
        
        # Convert to dict
        hotspot_dicts = []
        for hotspot in hotspots:
            hotspot_dict = {
                "id": hotspot.id,
                "lat": hotspot.lat,
                "lon": hotspot.lon,
                "risk_score": hotspot.risk_score,
                "risk_level": hotspot.risk_level,
                "vessel_count": hotspot.vessel_count,
                "untracked_ratio": hotspot.untracked_ratio,
                "size": hotspot.size,
                "color": hotspot.color,
                "created_at": hotspot.created_at.isoformat()
            }
            hotspot_dicts.append(hotspot_dict)
        
        return {
            "hotspots": hotspot_dicts,
            "count": len(hotspot_dicts),
            "region": {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting regional hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/risk-level/{risk_level}")
async def get_hotspots_by_risk_level(risk_level: str):
    """Get hotspots by risk level"""
    try:
        if risk_level.upper() not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            raise HTTPException(status_code=400, detail="Invalid risk level")
        
        hotspots = simple_hotspot_detector.get_hotspots_by_risk_level(risk_level.upper())
        
        # Convert to dict
        hotspot_dicts = []
        for hotspot in hotspots:
            hotspot_dict = {
                "id": hotspot.id,
                "lat": hotspot.lat,
                "lon": hotspot.lon,
                "risk_score": hotspot.risk_score,
                "risk_level": hotspot.risk_level,
                "vessel_count": hotspot.vessel_count,
                "untracked_ratio": hotspot.untracked_ratio,
                "size": hotspot.size,
                "color": hotspot.color,
                "created_at": hotspot.created_at.isoformat()
            }
            hotspot_dicts.append(hotspot_dict)
        
        return {
            "hotspots": hotspot_dicts,
            "count": len(hotspot_dicts),
            "risk_level": risk_level.upper()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hotspots by risk level: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics")
async def get_hotspot_statistics():
    """Get hotspot statistics"""
    try:
        stats = simple_hotspot_detector.get_statistics()
        return stats
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/real-time")
async def get_real_time_hotspots(
    hours_back: int = Query(24, description="Hours back to analyze"),
    min_risk_threshold: float = Query(0.3, description="Minimum risk threshold")
):
    """Get real-time hotspots based on recent data"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Detect hotspots for time range
        hotspots = simple_hotspot_detector.detect_hotspots(start_time, end_time)
        
        # Filter by risk threshold
        filtered_hotspots = [
            h for h in hotspots 
            if h.risk_score >= min_risk_threshold
        ]
        
        # Convert to dict
        hotspot_dicts = []
        for i, hotspot in enumerate(filtered_hotspots):
            hotspot_dict = {
                "id": hotspot.id,
                "lat": hotspot.lat,
                "lon": hotspot.lon,
                "risk_score": hotspot.risk_score,
                "risk_level": hotspot.risk_level,
                "vessel_count": hotspot.vessel_count,
                "untracked_ratio": hotspot.untracked_ratio,
                "size": hotspot.size,
                "color": hotspot.color,
                "created_at": hotspot.created_at.isoformat(),
                "rank": i + 1
            }
            hotspot_dicts.append(hotspot_dict)
        
        return {
            "hotspots": hotspot_dicts,
            "total_hotspots": len(hotspot_dicts),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "filters": {
                "hours_back": hours_back,
                "min_risk_threshold": min_risk_threshold
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting real-time hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for hotspot API"""
    return {
        "status": "healthy",
        "service": "Simple Hotspot API",
        "timestamp": datetime.utcnow().isoformat()
    }
