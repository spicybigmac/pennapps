#!/usr/bin/env python3
"""
Populate Test Data for Hotspot Analysis

Creates sample vessel data for testing hotspot analysis
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import math

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from api_routes.mongodb import logAISPosition

def generate_test_vessels():
    """
    Generate test vessel data for hotspot analysis
    """
    print("🚢 Generating test vessel data...")
    
    # Define some hotspot areas (lat, lon, radius_km)
    hotspot_areas = [
        (37.7749, -122.4194, 20),  # San Francisco Bay
        (40.7128, -74.0060, 25),   # New York Harbor
        (51.5074, -0.1278, 30),    # London
        (-33.8688, 151.2093, 35),  # Sydney
        (35.6762, 139.6503, 40),   # Tokyo Bay
    ]
    
    vessel_count = 0
    
    for area_lat, area_lon, radius_km in hotspot_areas:
        # Generate 10-20 vessels per area
        num_vessels = random.randint(10, 20)
        
        for i in range(num_vessels):
            # Generate random position within area
            angle = random.uniform(0, 2 * math.pi)
            distance_km = random.uniform(0, radius_km)
            
            # Convert to lat/lon offset
            lat_offset = (distance_km * math.cos(angle)) / 111.0  # 1 degree ≈ 111 km
            lon_offset = (distance_km * math.sin(angle)) / (111.0 * math.cos(math.radians(area_lat)))
            
            vessel_lat = area_lat + lat_offset
            vessel_lon = area_lon + lon_offset
            
            # Random timestamp within last 24 hours
            timestamp = datetime.utcnow() - timedelta(hours=random.uniform(0, 24))
            
            # Random vessel type (70% untracked, 30% tracked)
            is_tracked = random.random() < 0.3
            
            vessel_data = {
                "mmsi": f"{random.randint(100000000, 999999999)}",
                "lat": vessel_lat,
                "lon": vessel_lon,
                "timestamp": timestamp.isoformat(),
                "source": "AIS" if is_tracked else "SAR",
                "vessel_type": random.choice(["Fishing", "Cargo", "Tanker", "Unknown"]),
                "speed": random.uniform(0, 15),
                "heading": random.uniform(0, 360),
                "registered": is_tracked
            }
            
            try:
                logAISPosition(vessel_data)
                vessel_count += 1
            except Exception as e:
                print(f"Error logging vessel {i}: {e}")
    
    print(f"✅ Generated {vessel_count} test vessels")
    return vessel_count

def main():
    """
    Main function
    """
    print("🔧 Populating test data for hotspot analysis...")
    
    try:
        vessel_count = generate_test_vessels()
        print(f"\n📊 Test data populated successfully!")
        print(f"   Total vessels: {vessel_count}")
        print(f"   Areas: 5 hotspot regions")
        print(f"   Time range: Last 24 hours")
        
        print("\n🧪 You can now run hotspot analysis:")
        print("   python3 run_analysis.py")
        
    except Exception as e:
        print(f"❌ Error populating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
