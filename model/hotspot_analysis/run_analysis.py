#!/usr/bin/env python3
"""
Run Hotspot Analysis

Simple script to run hotspot analysis and generate results
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from hotspot_analyzer import hotspot_analyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Run hotspot analysis
    """
    print("🔍 Starting Hotspot Analysis...")
    
    # Run analysis for last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    print(f"📅 Analyzing data from {start_time} to {end_time}")
    
    # Run analysis
    results = hotspot_analyzer.analyze_hotspots(start_time, end_time)
    
    # Print summary
    print("\n📊 Analysis Results:")
    print(f"  Total Hotspots: {results['statistics']['total_hotspots']}")
    print(f"  Average Risk: {results['statistics']['average_risk']}")
    print(f"  Max Risk: {results['statistics']['max_risk']}")
    print(f"  Total Vessels: {results['statistics']['total_vessels']}")
    
    print("\n🎯 Risk Distribution:")
    for level, count in results['risk_distribution'].items():
        print(f"  {level}: {count}")
    
    print(f"\n💾 Results saved to: {hotspot_analyzer.analysis_dir}")
    
    # Show top 5 hotspots
    if results['hotspots']:
        print("\n🔥 Top 5 Hotspots:")
        for i, hotspot in enumerate(results['hotspots'][:5], 1):
            print(f"  {i}. {hotspot['risk_level']} Risk - "
                  f"Score: {hotspot['risk_score']} - "
                  f"Vessels: {hotspot['vessel_count']} - "
                  f"Location: ({hotspot['lat']:.3f}, {hotspot['lon']:.3f})")

if __name__ == "__main__":
    main()
