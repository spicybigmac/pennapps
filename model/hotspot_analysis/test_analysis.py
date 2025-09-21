#!/usr/bin/env python3
"""
Test Hotspot Analysis

Simple test to verify hotspot analysis is working
"""

import sys
from pathlib import Path
import logging

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from hotspot_analyzer import hotspot_analyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_analysis():
    """
    Test hotspot analysis with minimal data
    """
    print("🧪 Testing Hotspot Analysis...")
    
    try:
        # Test with no time range (should use default)
        print("📊 Running analysis...")
        results = hotspot_analyzer.analyze_hotspots()
        
        print(f"✅ Analysis completed successfully!")
        print(f"   Hotspots found: {results['statistics']['total_hotspots']}")
        print(f"   Total vessels: {results['data_summary']['total_vessels']}")
        
        # Test loading results
        print("\n📁 Testing result loading...")
        top_hotspots = hotspot_analyzer.get_top_hotspots(10)
        print(f"   Top hotspots loaded: {len(top_hotspots)}")
        
        latest = hotspot_analyzer.load_latest_analysis()
        if latest:
            print(f"   Latest analysis loaded: {latest['statistics']['total_hotspots']} hotspots")
        else:
            print("   No latest analysis found")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis()
