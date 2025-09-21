# Hotspot Analysis Module

This module provides clean, efficient hotspot analysis for illegal fishing detection.

## Overview

The hotspot analysis system identifies areas of high illegal fishing activity by:
- Analyzing vessel clustering patterns
- Comparing tracked vs untracked vessel densities
- Calculating risk scores based on isolation and density
- Generating statistical reports and visualizations

## Files

- `hotspot_analyzer.py` - Main analysis engine
- `run_analysis.py` - Simple script to run analysis
- `README.md` - This documentation

## Generated Files

When analysis runs, it creates:
- `hotspot_analysis_YYYYMMDD_HHMMSS.json` - Full analysis results
- `top_hotspots.json` - Top 50 hotspots for quick access
- `hotspot_summary.json` - Summary statistics

## Usage

### Run Analysis
```bash
cd model/hotspot_analysis
python run_analysis.py
```

### Use in Code
```python
from hotspot_analyzer import hotspot_analyzer

# Run analysis
results = hotspot_analyzer.analyze_hotspots()

# Get top hotspots
top_hotspots = hotspot_analyzer.get_top_hotspots(limit=20)

# Load latest analysis
latest = hotspot_analyzer.load_latest_analysis()
```

## Analysis Parameters

- **Cluster Radius**: 50km (configurable)
- **Min Vessels**: 3 vessels minimum to form hotspot
- **Risk Thresholds**:
  - CRITICAL: ≥ 0.8
  - HIGH: ≥ 0.6
  - MEDIUM: ≥ 0.4
  - LOW: ≥ 0.2

## Risk Score Calculation

Risk scores are calculated using:
1. **Base Score**: Untracked vessel count (normalized)
2. **Isolation Factor**: Higher if no tracked vessels nearby
3. **Density Factor**: Vessels per square kilometer
4. **Combined**: `base_score × isolation_factor × density_factor`

## Output Format

Each hotspot includes:
- `id`: Unique identifier
- `lat/lon`: Geographic coordinates
- `risk_score`: Calculated risk (0-1)
- `risk_level`: CRITICAL/HIGH/MEDIUM/LOW
- `vessel_count`: Number of vessels in cluster
- `untracked_ratio`: Ratio of untracked to total vessels
- `size`: Visual size for display
- `color`: Color code for risk level
- `bounds`: Geographic bounds of cluster
- `created_at`: Timestamp

## Integration

This module integrates with:
- MongoDB vessel data via `api_routes.mongodb`
- Frontend visualization systems
- Backend API endpoints
- Statistical reporting tools
