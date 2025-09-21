from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

# Import enhanced services
import sys
sys.path.append(str(Path(__file__).parent.parent))
from services.enhanced_hotspot_service import enhanced_hotspot_detector
from services.hotspot_service import hotspot_service
from .mongodb import getVesselDataForHotspotAnalysis, getAISSummary

# Set up logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

def load_hotspot_data():
    """Load hotspot data from files."""
    try:
        data_dir = Path("model/hotspot_analysis")
        hotspots_file = data_dir / "top_hotspots.json"
        
        if not hotspots_file.exists():
            logger.warning(f"Hotspot data file not found: {hotspots_file}")
            return []
        
        with open(hotspots_file, 'r') as f:
            hotspots = json.load(f)
        
        logger.info(f"Loaded {len(hotspots)} hotspots")
        return hotspots
        
    except Exception as e:
        logger.error(f"Error loading hotspot data: {e}")
        return []

def get_risk_level(risk_score: float) -> Dict[str, Any]:
    """Determine risk level based on score."""
    if risk_score >= 80:
        return {"level": "CRITICAL", "color": "#ff0000", "size": 0.03}
    elif risk_score >= 60:
        return {"level": "HIGH", "color": "#ff6600", "size": 0.02}
    elif risk_score >= 40:
        return {"level": "MEDIUM", "color": "#ffaa00", "size": 0.015}
    else:
        return {"level": "LOW", "color": "#00ff00", "size": 0.01}

@router.get("/")
async def get_all_hotspots(
    limit: int = Query(100, description="Maximum number of hotspots to return"),
    min_risk: float = Query(0, description="Minimum risk score threshold"),
    month: Optional[int] = Query(None, description="Filter by specific month")
):
    """Get all hotspots with optional filtering."""
    try:
        hotspots = hotspot_service.hotspots
        
        # Apply filters
        if min_risk > 0:
            hotspots = [h for h in hotspots if h.get('risk_score', 0) >= min_risk]
        
        if month is not None:
            hotspots = [h for h in hotspots if h.get('month') == month]
        
        # Sort by risk score and limit
        hotspots = sorted(hotspots, key=lambda x: x.get('risk_score', 0), reverse=True)
        hotspots = hotspots[:limit]
        
        return {
            "hotspots": hotspots,
            "total": len(hotspots),
            "filters": {
                "limit": limit,
                "min_risk": min_risk,
                "month": month
            },
            "last_updated": hotspot_service.last_updated.isoformat() if hotspot_service.last_updated else None
        }
    
    except Exception as e:
        logger.error(f"Error getting hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/top")
async def get_top_hotspots(
    limit: int = Query(5, description="Number of top hotspots to return"),
    min_risk: float = Query(0, description="Minimum risk score threshold")
):
    """Get top N hotspots by risk score."""
    try:
        hotspots = hotspot_service.get_top_hotspots(limit=limit, min_risk=min_risk)
        
        # Add ranking information
        for i, hotspot in enumerate(hotspots):
            hotspot['rank'] = i + 1
            hotspot['risk_level'] = get_risk_level(hotspot.get('risk_score', 0))
        
        return {
            "top_hotspots": hotspots,
            "count": len(hotspots),
            "filters": {
                "limit": limit,
                "min_risk": min_risk
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting top hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/region")
async def get_hotspots_by_region(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lon: float = Query(..., description="Maximum longitude")
):
    """Get hotspots within a geographic region."""
    try:
        hotspots = hotspot_service.get_hotspots_by_region(min_lat, max_lat, min_lon, max_lon)
        
        return {
            "hotspots": hotspots,
            "count": len(hotspots),
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

@router.get("/month/{month}")
async def get_hotspots_by_month(month: int):
    """Get hotspots for a specific month."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        hotspots = hotspot_service.get_hotspots_by_month(month)
        
        return {
            "hotspots": hotspots,
            "count": len(hotspots),
            "month": month
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly hotspots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics")
async def get_hotspot_statistics():
    """Get comprehensive hotspot statistics."""
    try:
        stats = hotspot_service.get_statistics()
        
        # Add monthly breakdown
        monthly_stats = {}
        for month in range(1, 6):  # 5 months of data
            month_hotspots = hotspot_service.get_hotspots_by_month(month)
            if month_hotspots:
                monthly_stats[month] = {
                    "count": len(month_hotspots),
                    "avg_risk": sum(h.get('risk_score', 0) for h in month_hotspots) / len(month_hotspots),
                    "max_risk": max(h.get('risk_score', 0) for h in month_hotspots)
                }
        
        stats["monthly_breakdown"] = monthly_stats
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/globe-data")
async def get_globe_integration_data():
    """Get data specifically formatted for Three.js globe integration."""
    try:
        # Get top 5 hotspots
        top_hotspots = hotspot_service.get_top_hotspots(limit=5)
        
        # Format for Three.js
        globe_data = {
            "hotspots": [],
            "metadata": {
                "total_hotspots": len(hotspot_service.hotspots),
                "last_updated": hotspot_service.last_updated.isoformat() if hotspot_service.last_updated else None,
                "data_source": "Global Fishing Watch SAR Analysis"
            }
        }
        
        for i, hotspot in enumerate(top_hotspots):
            risk_level = get_risk_level(hotspot.get('risk_score', 0))
            
            globe_hotspot = {
                "id": f"hotspot_{i+1}",
                "rank": i + 1,
                "position": {
                    "lat": hotspot.get('lat', 0),
                    "lon": hotspot.get('lon', 0)
                },
                "risk": {
                    "score": hotspot.get('risk_score', 0),
                    "level": risk_level['level'],
                    "color": risk_level['color'],
                    "size": risk_level['size']
                },
                "metadata": {
                    "month": hotspot.get('month', 0),
                    "relative_risk": hotspot.get('relative_risk', 0),
                    "isolation_score": hotspot.get('isolation_score', 0),
                    "tracked_density": hotspot.get('tracked_density', 0),
                    "untracked_density": hotspot.get('untracked_density', 0)
                },
                "name": f"{risk_level['level']} Risk Hotspot #{i+1}",
                "description": f"Risk Score: {hotspot.get('risk_score', 0):.1f} | Month: {hotspot.get('month', 0)}"
            }
            
            globe_data["hotspots"].append(globe_hotspot)
        
        return globe_data
    
    except Exception as e:
        logger.error(f"Error getting globe data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/risk-levels")
async def get_risk_levels():
    """Get risk level definitions and thresholds."""
    return {
        "risk_levels": {
            "CRITICAL": {
                "threshold": 80,
                "color": "#ff0000",
                "size_multiplier": 0.03,
                "description": "Extremely high risk - immediate attention required"
            },
            "HIGH": {
                "threshold": 60,
                "color": "#ff6600", 
                "size_multiplier": 0.02,
                "description": "High risk - priority monitoring"
            },
            "MEDIUM": {
                "threshold": 40,
                "color": "#ffaa00",
                "size_multiplier": 0.015,
                "description": "Medium risk - regular monitoring"
            },
            "LOW": {
                "threshold": 20,
                "color": "#00ff00",
                "size_multiplier": 0.01,
                "description": "Low risk - routine monitoring"
            }
        },
        "thresholds": [20, 40, 60, 80]
    }

@router.post("/refresh")
async def refresh_hotspot_data():
    """Refresh hotspot data from files."""
    try:
        hotspot_service.load_data()
        
        return {
            "message": "Hotspot data refreshed successfully",
            "hotspots_loaded": len(hotspot_service.hotspots),
            "last_updated": hotspot_service.last_updated.isoformat() if hotspot_service.last_updated else None
        }
    
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh hotspot data")

# Enhanced endpoints with MongoDB integration

@router.post("/analyze")
async def analyze_hotspots_enhanced(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    force_refresh: bool = Query(False, description="Force refresh analysis")
):
    """Run enhanced hotspot analysis with MongoDB data and seasonal information."""
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Run enhanced analysis
        logger.info("🚀 Starting enhanced hotspot analysis...")
        results = await enhanced_hotspot_detector.analyze_hotspots(start_dt, end_dt)
        
        return {
            "status": "success",
            "message": "Enhanced hotspot analysis completed",
            "results": results,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in enhanced analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/mongodb-data")
async def get_mongodb_hotspot_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    source: Optional[str] = Query(None, description="Filter by source: SAR or AIS")
):
    """Get vessel data from MongoDB for hotspot analysis."""
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Get vessel data
        vessel_data = getVesselDataForHotspotAnalysis(start_dt, end_dt)
        
        # Filter by source if specified
        if source:
            vessel_data['tracked_vessels'] = [
                v for v in vessel_data['tracked_vessels'] 
                if v.get('source', '').upper() == source.upper()
            ]
            vessel_data['untracked_vessels'] = [
                v for v in vessel_data['untracked_vessels'] 
                if v.get('source', '').upper() == source.upper()
            ]
            vessel_data['total_vessels'] = len(vessel_data['tracked_vessels']) + len(vessel_data['untracked_vessels'])
        
        return {
            "vessel_data": vessel_data,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "source": source
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting MongoDB data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MongoDB data: {str(e)}")

@router.get("/seasonal-patterns")
async def get_seasonal_fishing_patterns(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    month: int = Query(..., description="Month (1-12)")
):
    """Get seasonal fishing patterns for a specific location and month."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        patterns = await enhanced_hotspot_detector.seasonal_api.get_seasonal_fishing_patterns(lat, lon, month)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "month": month,
            "patterns": patterns,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting seasonal patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get seasonal patterns: {str(e)}")

@router.get("/ais-summary")
async def get_ais_data_summary():
    """Get AIS data summary from MongoDB."""
    try:
        summary = getAISSummary()
        return {
            "summary": summary,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting AIS summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AIS summary: {str(e)}")

@router.get("/enhanced-statistics")
async def get_enhanced_hotspot_statistics():
    """Get enhanced statistics combining file-based and MongoDB data."""
    try:
        # Get file-based statistics
        file_stats = hotspot_service.get_statistics()
        
        # Get MongoDB summary
        ais_summary = getAISSummary()
        
        # Combine statistics
        enhanced_stats = {
            "file_based_hotspots": file_stats,
            "mongodb_ais_data": ais_summary,
            "data_sources": {
                "file_based": "Static analysis from JSON files",
                "mongodb": "Real-time AIS data from MongoDB"
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return enhanced_stats
    
    except Exception as e:
        logger.error(f"Error getting enhanced statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced statistics: {str(e)}")

@router.get("/real-time")
async def get_real_time_hotspots(
    hours_back: int = Query(24, description="Hours back to analyze"),
    min_risk_threshold: float = Query(0.5, description="Minimum risk threshold")
):
    """Get real-time hotspots based on recent MongoDB data."""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get recent vessel data
        vessel_data = getVesselDataForHotspotAnalysis(start_time, end_time)
        
        if vessel_data['total_vessels'] == 0:
            return {
                "hotspots": [],
                "message": "No recent vessel data available",
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        
        # Run quick analysis
        results = await enhanced_hotspot_detector.analyze_hotspots(start_time, end_time)
        
        # Filter by risk threshold
        filtered_hotspots = [
            h for h in results['hotspots'] 
            if h['risk_score'] >= min_risk_threshold
        ]
        
        return {
            "hotspots": filtered_hotspots,
            "total_hotspots": len(filtered_hotspots),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "vessel_data": {
                "total_vessels": vessel_data['total_vessels'],
                "tracked_vessels": len(vessel_data['tracked_vessels']),
                "untracked_vessels": len(vessel_data['untracked_vessels'])
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting real-time hotspots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get real-time hotspots: {str(e)}")

def get_risk_level(risk_score: float) -> Dict[str, Any]:
    """Determine risk level based on score."""
    if risk_score >= 80:
        return {
            "level": "CRITICAL",
            "color": "#ff0000",
            "size": 0.03,
            "priority": 1
        }
    elif risk_score >= 60:
        return {
            "level": "HIGH", 
            "color": "#ff6600",
            "size": 0.02,
            "priority": 2
        }
    elif risk_score >= 40:
        return {
            "level": "MEDIUM",
            "color": "#ffaa00", 
            "size": 0.015,
            "priority": 3
        }
    else:
        return {
            "level": "LOW",
            "color": "#00ff00",
            "size": 0.01,
            "priority": 4
        }
