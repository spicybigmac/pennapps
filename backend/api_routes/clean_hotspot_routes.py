#!/usr/bin/env python3
"""
Clean Hotspot API Routes

Essential endpoints for hotspot data:
1. GET /api/hotspots/ - Get top hotspots list
2. GET /api/hotspots/globe-data - Get hotspots for globe visualization
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/ibuddhar/Dev/F2025/pennapps')

# Import analysis system
from model.hotspot_analysis.hotspot_analyzer import HotspotAnalyzer
from api_routes.mongodb import getVesselDataForHotspotAnalysis

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

@router.get("/")
async def get_hotspots(
    limit: int = Query(20, description="Maximum number of hotspots to return"),
    min_risk: float = Query(0.0, description="Minimum risk score threshold")
):
    """Get top hotspots list for the frontend"""
    try:
        logger.info(f"Getting hotspots: limit={limit}, min_risk={min_risk}")
        
        # Get vessel data from MongoDB
        vessel_data = getVesselDataForHotspotAnalysis()
        logger.info(f"Retrieved {vessel_data['total_vessels']} vessels from MongoDB")
        
        if vessel_data['total_vessels'] == 0:
            return {
                "hotspots": [],
                "total": 0,
                "message": "No vessel data available",
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Run hotspot analysis
        analyzer = HotspotAnalyzer()
        analysis_result = analyzer.analyze_hotspots()
        hotspots = analysis_result.get('hotspots', [])
        logger.info(f"Analysis complete: {len(hotspots)} hotspots detected")
        
        # Apply filters
        if min_risk > 0:
            hotspots = [h for h in hotspots if h['risk_score'] >= min_risk]
        
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
                "min_risk": min_risk
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting hotspots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotspots: {str(e)}")

@router.get("/globe-data")
async def get_globe_hotspots(
    limit: int = Query(10, description="Maximum number of hotspots for globe")
):
    """Get hotspots formatted for globe visualization"""
    try:
        logger.info(f"Getting globe hotspots: limit={limit}")
        
        # Get vessel data from MongoDB
        vessel_data = getVesselDataForHotspotAnalysis()
        logger.info(f"Retrieved {vessel_data['total_vessels']} vessels from MongoDB")
        
        if vessel_data['total_vessels'] == 0:
            return {
                "hotspots": [],
                "metadata": {
                    "total_hotspots": 0,
                    "last_updated": datetime.utcnow().isoformat(),
                    "data_source": "MongoDB AIS Analysis",
                    "message": "No vessel data available"
                }
            }
        
        # Run hotspot analysis
        analyzer = HotspotAnalyzer()
        analysis_result = analyzer.analyze_hotspots()
        hotspots = analysis_result.get('hotspots', [])
        logger.info(f"Analysis complete: {len(hotspots)} hotspots detected")
        
        # Limit for performance
        hotspots = hotspots[:limit]
        
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
        raise HTTPException(status_code=500, detail=f"Failed to get globe hotspots: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        vessel_data = getVesselDataForHotspotAnalysis()
        
        return {
            "status": "healthy",
            "mongodb_connected": True,
            "vessel_count": vessel_data['total_vessels'],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "mongodb_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
