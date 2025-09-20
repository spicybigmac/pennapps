from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from . import mongodb

router = APIRouter(prefix="/api/ais", tags=["ais"])

class AISPositionRequest(BaseModel):
    id: str
    source: str  # 'SAR' or 'AIS'
    lat: float
    lon: float
    timestamp: datetime
    zone_name: str
    confidence: Optional[float] = None
    vessel_length_m: Optional[float] = None
    mmsi: Optional[str] = None
    vessel_type: Optional[str] = None
    vessel_name: Optional[str] = None
    flag: Optional[str] = None
    imo: Optional[str] = None
    callsign: Optional[str] = None
    ais_matched: Optional[bool] = None
    is_fishing: Optional[bool] = None
    raw_data: Optional[dict] = None

@router.get("/")
async def root():
    """AIS API root endpoint"""
    return {
        "message": "AIS Data API",
        "status": "running",
        "endpoints": {
            "summary": "/api/ais/summary",
            "positions": "/api/ais/positions",
            "unmatched-sar": "/api/ais/unmatched-sar",
            "zones": "/api/ais/zones"
        }
    }

@router.get("/summary")
async def get_ais_summary():
    """Get AIS data summary statistics"""
    try:
        summary = mongodb.getAISSummary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AIS summary: {str(e)}")

@router.get("/positions")
async def get_ais_positions(
    source: Optional[str] = Query(None, description="Filter by source: SAR or AIS"),
    zone_name: Optional[str] = Query(None, description="Filter by monitoring zone"),
    hours_back: int = Query(24, description="Hours back to query")
):
    """Get AIS vessel positions with optional filtering"""
    try:
        positions = mongodb.getAISPositions(
            source=source,
            zone_name=zone_name,
            hours_back=hours_back
        )
        
        # Convert ObjectId to string for JSON serialization
        for pos in positions:
            if "_id" in pos:
                pos["_id"] = str(pos["_id"])
        
        return {
            "positions": positions,
            "count": len(positions),
            "filters": {
                "source": source,
                "zone_name": zone_name,
                "hours_back": hours_back
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AIS positions: {str(e)}")

@router.get("/unmatched-sar")
async def get_unmatched_sar_positions(
    zone_name: Optional[str] = Query(None, description="Filter by monitoring zone"),
    hours_back: int = Query(24, description="Hours back to query")
):
    """Get SAR positions that didn't match with AIS (ready for classification)"""
    try:
        positions = mongodb.getUnmatchedSAR(
            zone_name=zone_name,
            hours_back=hours_back
        )
        
        # Convert ObjectId to string for JSON serialization
        for pos in positions:
            if "_id" in pos:
                pos["_id"] = str(pos["_id"])
        
        return {
            "unmatched_sar_positions": positions,
            "count": len(positions),
            "filters": {
                "zone_name": zone_name,
                "hours_back": hours_back
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unmatched SAR positions: {str(e)}")

@router.post("/positions")
async def log_ais_position(position: AISPositionRequest):
    """Log a new AIS position (SAR or AIS)"""
    try:
        position_data = position.dict()
        mongodb.logAISPosition(position_data)
        return {
            "message": "AIS position logged successfully",
            "status": "success",
            "position_id": position.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log AIS position: {str(e)}")

@router.get("/zones")
async def get_monitoring_zones():
    """Get all monitoring zones"""
    try:
        # For now, return the predefined zones from ais_models
        from ..ais_models import NORTH_AMERICAN_ZONES
        
        zones = []
        for zone in NORTH_AMERICAN_ZONES:
            zones.append({
                "name": zone.name,
                "bbox": zone.bbox,
                "description": zone.description,
                "priority": zone.priority,
                "country": zone.country
            })
        
        return {
            "zones": zones,
            "count": len(zones)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring zones: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for AIS API"""
    return {
        "status": "healthy",
        "service": "AIS API",
        "timestamp": datetime.utcnow().isoformat()
    }
