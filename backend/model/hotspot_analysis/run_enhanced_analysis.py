#!/usr/bin/env python3
"""
Run Enhanced Hotspot Analysis

Script to run enhanced hotspot analysis with auxiliary data
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from enhanced_hotspot_analyzer import enhanced_hotspot_analyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Run enhanced hotspot analysis
    """
    print("🔍 Starting Enhanced Hotspot Analysis...")
    print("📊 Using auxiliary data: Ports, Fishing Seasons, Environmental Factors")
    
    # Run analysis for last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    print(f"📅 Analyzing data from {start_time} to {end_time}")
    
    # Run enhanced analysis
    results = enhanced_hotspot_analyzer.analyze_hotspots(start_time, end_time)
    
    # Print summary
    print("\n📊 Enhanced Analysis Results:")
    print(f"  Total Hotspots: {results['statistics']['total_hotspots']}")
    print(f"  Average Risk: {results['statistics']['average_risk']}")
    print(f"  Max Risk: {results['statistics']['max_risk']}")
    print(f"  Total Vessels: {results['statistics']['total_vessels']}")
    
    print(f"\n🌍 Auxiliary Data:")
    print(f"  Ports Loaded: {results['auxiliary_data']['ports_loaded']}")
    print(f"  Fishing Seasons: {results['auxiliary_data']['fishing_seasons_loaded']}")
    
    print("\n🎯 Risk Distribution:")
    for level, count in results['risk_distribution'].items():
        print(f"  {level}: {count}")
    
    print(f"\n💾 Results saved to: {enhanced_hotspot_analyzer.analysis_dir}")
    
    # Show top 5 hotspots with enhanced details
    if results['hotspots']:
        print("\n🔥 Top 5 Enhanced Hotspots:")
        for i, hotspot in enumerate(results['hotspots'][:5], 1):
            print(f"  {i}. {hotspot['risk_level']} Risk - Score: {hotspot['risk_score']}")
            print(f"     Vessels: {hotspot['vessel_count']} | Location: ({hotspot['lat']:.3f}, {hotspot['lon']:.3f})")
            print(f"     Nearby Ports: {len(hotspot['nearby_ports'])} | Fishing Factor: {hotspot['fishing_season_factor']}")
            if hotspot['nearby_ports']:
                closest_port = hotspot['nearby_ports'][0]
                print(f"     Closest Port: {closest_port['name']} ({closest_port['distance_km']}km)")
            print()

if __name__ == "__main__":
    main()
