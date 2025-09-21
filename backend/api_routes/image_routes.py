#!/usr/bin/env python3
"""
Image API Routes

Simple endpoint to serve random SAR images for vessel popups
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import random
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/images", tags=["images"])

# SAR images directory - use absolute path
SAR_IMAGES_DIR = Path("/Users/ibuddhar/Dev/F2025/pennapps/backend/data_collection/SAR")

@router.get("/vessel-image")
async def get_vessel_image():
    """Get a random SAR image for vessel popup"""
    try:
        logger.info(f"Looking for images in: {SAR_IMAGES_DIR}")
        logger.info(f"Directory exists: {SAR_IMAGES_DIR.exists()}")
        
        # Check if SAR directory exists
        if not SAR_IMAGES_DIR.exists():
            logger.error(f"SAR images directory not found: {SAR_IMAGES_DIR}")
            raise HTTPException(status_code=404, detail="SAR images directory not found")
        
        # Get all PNG files in the SAR directory
        image_files = list(SAR_IMAGES_DIR.glob("*.png"))
        logger.info(f"Found {len(image_files)} PNG files")
        
        if not image_files:
            logger.error("No PNG images found in SAR directory")
            raise HTTPException(status_code=404, detail="No images available")
        
        # Select a random image
        random_image = random.choice(image_files)
        
        logger.info(f"Serving random SAR image: {random_image.name} (selected from {len(image_files)} available images)")
        
        # Return the image file with no-cache headers
        return FileResponse(
            path=str(random_image),
            media_type="image/png",
            filename=random_image.name,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving vessel image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
