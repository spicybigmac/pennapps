#!/usr/bin/env python3
"""
Enhanced Hotspot Service

Advanced hotspot detection service that integrates:
- MongoDB AIS data (reported and unreported)
- Seasonal fishing information APIs
- Real-time timestamp processing
- Enhanced statistical models for hotspot detection
"""

import asyncio
import aiohttp
import logging
import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import requests
from scipy import stats
from scipy.spatial.distance import cdist
from scipy.ndimage import gaussian_filter
from sklearn.neighbors import KernelDensity
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point, Polygon
import warnings
warnings.filterwarnings('ignore')

# Import MongoDB functions
import sys
sys.path.append(str(Path(__file__).parent.parent))
from api_routes.mongodb import getVesselDataForHotspotAnalysis, getAISSummary

logger = logging.getLogger(__name__)

class SeasonalFishingAPI:
    """API client for seasonal fishing information"""
    
    def __init__(self):
        self.fishbase_api = "https://fishbase.ropensci.org/"
        self.noaa_fisheries_api = "https://www.fisheries.noaa.gov/"
        self.fao_fishing_areas = "http://www.fao.org/fishery/area/"
        
    async def get_seasonal_fishing_patterns(self, lat: float, lon: float, month: int) -> Dict[str, Any]:
        """Get seasonal fishing patterns for a location and month"""
        try:
            # This would integrate with real APIs in production
            # For now, return mock data based on known patterns
            
            # Determine fishing season based on location and month
            fishing_season = self._determine_fishing_season(lat, lon, month)
            
            # Get species-specific patterns
            species_patterns = await self._get_species_patterns(lat, lon, month)
            
            return {
                'fishing_season': fishing_season,
                'species_patterns': species_patterns,
                'expected_activity': self._calculate_expected_activity(lat, lon, month),
                'fishing_gear_types': self._get_gear_types(lat, lon, month),
                'regulatory_periods': self._get_regulatory_periods(lat, lon, month)
            }
        except Exception as e:
            logger.error(f"Error getting seasonal fishing patterns: {e}")
            return self._get_default_patterns()
    
    def _determine_fishing_season(self, lat: float, lon: float, month: int) -> str:
        """Determine fishing season based on location and month"""
        # Northern hemisphere patterns
        if lat > 0:
            if month in [12, 1, 2]:  # Winter
                return "low_season"
            elif month in [6, 7, 8]:  # Summer
                return "peak_season"
            else:
                return "moderate_season"
        else:  # Southern hemisphere
            if month in [6, 7, 8]:  # Winter
                return "low_season"
            elif month in [12, 1, 2]:  # Summer
                return "peak_season"
            else:
                return "moderate_season"
    
    async def _get_species_patterns(self, lat: float, lon: float, month: int) -> Dict[str, Any]:
        """Get species-specific fishing patterns"""
        # Mock data - in production, this would query real fisheries databases
        species_data = {
            'tuna': {
                'peak_months': [6, 7, 8, 9],
                'activity_level': 0.8 if month in [6, 7, 8, 9] else 0.3,
                'preferred_depth': (50, 200),
                'gear_types': ['longline', 'purse_seine']
            },
            'cod': {
                'peak_months': [3, 4, 5, 10, 11, 12],
                'activity_level': 0.9 if month in [3, 4, 5, 10, 11, 12] else 0.2,
                'preferred_depth': (100, 300),
                'gear_types': ['trawl', 'gillnet']
            },
            'salmon': {
                'peak_months': [5, 6, 7, 8],
                'activity_level': 0.7 if month in [5, 6, 7, 8] else 0.1,
                'preferred_depth': (10, 100),
                'gear_types': ['gillnet', 'troll']
            }
        }
        
        return species_data
    
    def _calculate_expected_activity(self, lat: float, lon: float, month: int) -> float:
        """Calculate expected fishing activity level (0-1)"""
        base_activity = 0.5
        
        # Seasonal adjustment
        season = self._determine_fishing_season(lat, lon, month)
        if season == "peak_season":
            base_activity *= 1.5
        elif season == "low_season":
            base_activity *= 0.3
        
        # Add some randomness
        noise = np.random.normal(0, 0.1)
        return max(0, min(1, base_activity + noise))
    
    def _get_gear_types(self, lat: float, lon: float, month: int) -> List[str]:
        """Get expected fishing gear types for location and month"""
        # Mock data - would be based on real fisheries data
        if lat > 50:  # High latitude
            return ['trawl', 'gillnet', 'longline']
        elif lat > 30:  # Mid latitude
            return ['purse_seine', 'trawl', 'longline']
        else:  # Low latitude
            return ['purse_seine', 'longline', 'handline']
    
    def _get_regulatory_periods(self, lat: float, lon: float, month: int) -> Dict[str, Any]:
        """Get regulatory periods and restrictions"""
        # Mock data - would integrate with real regulatory databases
        return {
            'closed_seasons': [],
            'gear_restrictions': [],
            'size_limits': {},
            'catch_limits': {}
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Get default patterns when API fails"""
        return {
            'fishing_season': 'moderate_season',
            'species_patterns': {},
            'expected_activity': 0.5,
            'fishing_gear_types': ['trawl', 'gillnet'],
            'regulatory_periods': {}
        }

class EnhancedHotspotDetector:
    """
    Enhanced hotspot detector that integrates MongoDB data and seasonal information
    """
    
    def __init__(self):
        self.seasonal_api = SeasonalFishingAPI()
        self.spatial_grid = None
        self.grid_resolution = 0.01  # ~1km resolution
        self.bounds = None
        
        # Model parameters
        self.risk_weights = {
            'density_ratio': 0.4,
            'seasonal_deviation': 0.3,
            'isolation_score': 0.2,
            'environmental_context': 0.1
        }
    
    async def analyze_hotspots(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Main analysis pipeline for hotspot detection"""
        try:
            logger.info("🚀 Starting enhanced hotspot analysis...")
            
            # Get vessel data from MongoDB
            vessel_data = getVesselDataForHotspotAnalysis(start_date, end_date)
            logger.info(f"📊 Retrieved {vessel_data['total_vessels']} vessels from MongoDB")
            
            if vessel_data['total_vessels'] == 0:
                logger.warning("No vessel data found for analysis")
                return {'hotspots': [], 'analysis_metadata': {'error': 'No data available'}}
            
            # Create spatial grid
            self._create_spatial_grid(vessel_data)
            
            # Process monthly data
            monthly_results = {}
            for month in range(1, 13):  # Process all 12 months
                month_data = self._filter_data_by_month(vessel_data, month)
                if len(month_data['tracked_vessels']) > 0 or len(month_data['untracked_vessels']) > 0:
                    month_result = await self._analyze_month(month_data, month)
                    if month_result:
                        monthly_results[month] = month_result
            
            # Identify top hotspots across all months
            all_hotspots = self._consolidate_hotspots(monthly_results)
            
            # Generate analysis report
            analysis_report = self._generate_analysis_report(vessel_data, monthly_results, all_hotspots)
            
            logger.info(f"🎯 Analysis complete: {len(all_hotspots)} hotspots identified")
            
            return {
                'hotspots': all_hotspots,
                'monthly_results': monthly_results,
                'analysis_metadata': analysis_report
            }
            
        except Exception as e:
            logger.error(f"Error in hotspot analysis: {e}")
            raise e
    
    def _create_spatial_grid(self, vessel_data: Dict):
        """Create spatial grid for analysis"""
        all_vessels = vessel_data['tracked_vessels'] + vessel_data['untracked_vessels']
        
        if not all_vessels:
            raise ValueError("No vessel data available for grid creation")
        
        # Calculate bounds
        lats = [v['lat'] for v in all_vessels]
        lons = [v['lon'] for v in all_vessels]
        
        self.bounds = {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons)
        }
        
        # Create grid
        lats_grid = np.arange(
            self.bounds['min_lat'], 
            self.bounds['max_lat'] + self.grid_resolution, 
            self.grid_resolution
        )
        lons_grid = np.arange(
            self.bounds['min_lon'], 
            self.bounds['max_lon'] + self.grid_resolution, 
            self.grid_resolution
        )
        
        lon_mesh, lat_mesh = np.meshgrid(lons_grid, lats_grid)
        
        self.spatial_grid = {
            'lats': lats_grid,
            'lons': lons_grid,
            'lat_mesh': lat_mesh,
            'lon_mesh': lon_mesh,
            'shape': lat_mesh.shape
        }
        
        logger.info(f"🗺️ Created spatial grid: {lat_mesh.shape[0]}x{lat_mesh.shape[1]} points")
    
    def _filter_data_by_month(self, vessel_data: Dict, month: int) -> Dict:
        """Filter vessel data by month"""
        tracked = []
        untracked = []
        
        for vessel in vessel_data['tracked_vessels']:
            if vessel['timestamp'] and vessel['timestamp'].month == month:
                tracked.append(vessel)
        
        for vessel in vessel_data['untracked_vessels']:
            if vessel['timestamp'] and vessel['timestamp'].month == month:
                untracked.append(vessel)
        
        return {
            'tracked_vessels': tracked,
            'untracked_vessels': untracked,
            'total_vessels': len(tracked) + len(untracked)
        }
    
    async def _analyze_month(self, month_data: Dict, month: int) -> Optional[Dict]:
        """Analyze hotspots for a specific month"""
        try:
            if month_data['total_vessels'] < 5:
                logger.warning(f"Month {month}: Insufficient data ({month_data['total_vessels']} vessels)")
                return None
            
            logger.info(f"📅 Analyzing month {month} with {month_data['total_vessels']} vessels")
            
            # Get seasonal fishing patterns
            center_lat = (self.bounds['min_lat'] + self.bounds['max_lat']) / 2
            center_lon = (self.bounds['min_lon'] + self.bounds['max_lon']) / 2
            seasonal_patterns = await self.seasonal_api.get_seasonal_fishing_patterns(
                center_lat, center_lon, month
            )
            
            # Calculate density surfaces
            tracked_density = self._calculate_density_surface(month_data['tracked_vessels'])
            untracked_density = self._calculate_density_surface(month_data['untracked_vessels'])
            
            # Calculate risk surface
            risk_surface = self._calculate_risk_surface(
                tracked_density, 
                untracked_density, 
                seasonal_patterns
            )
            
            # Identify hotspots
            hotspots = self._identify_hotspots(risk_surface, month)
            
            return {
                'month': month,
                'tracked_density': tracked_density,
                'untracked_density': untracked_density,
                'risk_surface': risk_surface,
                'hotspots': hotspots,
                'seasonal_patterns': seasonal_patterns,
                'vessel_counts': {
                    'tracked': len(month_data['tracked_vessels']),
                    'untracked': len(month_data['untracked_vessels'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing month {month}: {e}")
            return None
    
    def _calculate_density_surface(self, vessels: List[Dict]) -> np.ndarray:
        """Calculate kernel density surface for vessels"""
        if not vessels:
            return np.zeros(self.spatial_grid['shape'])
        
        # Extract coordinates
        coords = np.array([[v['lat'], v['lon']] for v in vessels])
        
        # Create KDE
        kde = KernelDensity(bandwidth=0.1, kernel='gaussian')
        kde.fit(coords)
        
        # Evaluate on grid
        grid_coords = np.column_stack([
            self.spatial_grid['lat_mesh'].ravel(),
            self.spatial_grid['lon_mesh'].ravel()
        ])
        
        density = np.exp(kde.score_samples(grid_coords))
        density = density.reshape(self.spatial_grid['shape'])
        
        return density
    
    def _calculate_risk_surface(self, tracked_density: np.ndarray, 
                              untracked_density: np.ndarray, 
                              seasonal_patterns: Dict) -> np.ndarray:
        """Calculate enhanced risk surface"""
        # Base density ratio
        density_ratio = untracked_density / (tracked_density + 0.001)
        
        # Seasonal deviation factor
        expected_activity = seasonal_patterns.get('expected_activity', 0.5)
        seasonal_deviation = np.abs(untracked_density - expected_activity) / (expected_activity + 0.001)
        
        # Isolation score
        isolation_score = self._calculate_isolation_score(untracked_density)
        
        # Environmental context (simplified)
        environmental_context = np.ones_like(untracked_density)  # Placeholder
        
        # Weighted combination
        risk_surface = (
            self.risk_weights['density_ratio'] * density_ratio +
            self.risk_weights['seasonal_deviation'] * seasonal_deviation +
            self.risk_weights['isolation_score'] * isolation_score +
            self.risk_weights['environmental_context'] * environmental_context
        )
        
        # Normalize
        risk_surface = (risk_surface - risk_surface.min()) / (risk_surface.max() - risk_surface.min() + 0.001)
        
        return risk_surface
    
    def _calculate_isolation_score(self, density: np.ndarray) -> np.ndarray:
        """Calculate isolation score for density surface"""
        # Find local maxima
        from scipy.ndimage import maximum_filter
        local_maxima = (density == maximum_filter(density, size=3))
        
        # Calculate distance to nearest maximum
        maxima_coords = np.where(local_maxima)
        if len(maxima_coords[0]) == 0:
            return np.zeros_like(density)
        
        # For each grid point, calculate distance to nearest maximum
        grid_coords = np.column_stack([
            self.spatial_grid['lat_mesh'].ravel(),
            self.spatial_grid['lon_mesh'].ravel()
        ])
        
        maxima_points = np.column_stack([
            self.spatial_grid['lat_mesh'][maxima_coords],
            self.spatial_grid['lon_mesh'][maxima_coords]
        ])
        
        distances = cdist(grid_coords, maxima_points)
        min_distances = np.min(distances, axis=1)
        min_distances = min_distances.reshape(self.spatial_grid['shape'])
        
        # Convert to isolation score (higher for more isolated)
        scale = 0.1
        isolation_score = np.exp(-min_distances / scale)
        
        return isolation_score
    
    def _identify_hotspots(self, risk_surface: np.ndarray, month: int) -> List[Dict]:
        """Identify hotspot locations from risk surface"""
        # Find local maxima above threshold
        from scipy.ndimage import maximum_filter
        local_maxima = (risk_surface == maximum_filter(risk_surface, size=3))
        
        # Apply threshold (top 5% of risk values)
        threshold = np.percentile(risk_surface, 95)
        hotspot_mask = local_maxima & (risk_surface > threshold)
        
        hotspot_indices = np.where(hotspot_mask)
        hotspots = []
        
        for i, j in zip(hotspot_indices[0], hotspot_indices[1]):
            lat = self.spatial_grid['lats'][i]
            lon = self.spatial_grid['lons'][j]
            risk_score = risk_surface[i, j]
            
            hotspot = {
                'lat': lat,
                'lon': lon,
                'risk_score': float(risk_score),
                'month': month,
                'relative_size': self._calculate_relative_size(risk_score),
                'confidence': min(1.0, risk_score * 1.2)  # Cap at 1.0
            }
            hotspots.append(hotspot)
        
        # Sort by risk score
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return hotspots
    
    def _calculate_relative_size(self, risk_score: float) -> float:
        """Calculate relative size based on risk score"""
        # Scale risk score to size (0.01 to 0.05)
        return 0.01 + (risk_score * 0.04)
    
    def _consolidate_hotspots(self, monthly_results: Dict) -> List[Dict]:
        """Consolidate hotspots across all months"""
        all_hotspots = []
        
        for month, result in monthly_results.items():
            for hotspot in result['hotspots']:
                all_hotspots.append(hotspot)
        
        # Sort by risk score
        all_hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Add ranking
        for i, hotspot in enumerate(all_hotspots):
            hotspot['rank'] = i + 1
        
        return all_hotspots
    
    def _generate_analysis_report(self, vessel_data: Dict, monthly_results: Dict, hotspots: List[Dict]) -> Dict:
        """Generate comprehensive analysis report"""
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'data_period': {
                'start': vessel_data['date_range']['start'],
                'end': vessel_data['date_range']['end']
            },
            'vessel_statistics': {
                'total_vessels': vessel_data['total_vessels'],
                'tracked_vessels': len(vessel_data['tracked_vessels']),
                'untracked_vessels': len(vessel_data['untracked_vessels'])
            },
            'hotspot_statistics': {
                'total_hotspots': len(hotspots),
                'months_analyzed': len(monthly_results),
                'average_risk_score': np.mean([h['risk_score'] for h in hotspots]) if hotspots else 0,
                'max_risk_score': max([h['risk_score'] for h in hotspots]) if hotspots else 0
            },
            'geographic_bounds': self.bounds,
            'grid_resolution': self.grid_resolution
        }

# Global service instance
enhanced_hotspot_detector = EnhancedHotspotDetector()
