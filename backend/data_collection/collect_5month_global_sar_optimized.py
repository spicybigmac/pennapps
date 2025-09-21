#!/usr/bin/env python3
"""
Optimized 5-Month Global SAR Data Collection
Uses tested working regions for comprehensive global coverage
"""

import asyncio
import aiohttp
import logging
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
import time

# Load environment variables
load_dotenv("backend/.env")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sar_5month_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedSARCollector5Month:
    """Optimized 5-month SAR data collector using working regions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gateway.api.globalfishingwatch.org"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.requests_made = 0
        self.max_requests_per_minute = 15  # Conservative limit
        self.minute_start = time.time()
        
        # Create output directory
        self.output_dir = Path("sar_data_5month_optimized")
        self.output_dir.mkdir(exist_ok=True)
        
        # Working regions (tested and verified)
        self.working_regions = [
            {
                "name": "Primary_Region_8465", 
                "id": "8465", 
                "type": "eez", 
                "description": "Primary Region 8465 (High Volume)",
                "priority": 1
            },
            {
                "name": "Secondary_Region_8466", 
                "id": "8466", 
                "type": "eez", 
                "description": "Secondary Region 8466 (Additional Coverage)",
                "priority": 2
            }
        ]
        
        # Progress tracking
        self.progress_file = self.output_dir / "collection_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """Load collection progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                "completed_months": [],
                "completed_regions": {},
                "total_vessels_collected": 0,
                "start_time": datetime.utcnow().isoformat(),
                "collection_stats": {
                    "total_unmatched_vessels": 0,
                    "total_matched_vessels": 0,
                    "total_requests_made": 0
                }
            }
    
    def save_progress(self):
        """Save collection progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2, default=str)
    
    def get_month_ranges(self):
        """Get 5 months of date ranges (going backwards from current date)"""
        end_date = datetime.now().date() - timedelta(days=1)  # Yesterday
        
        months = []
        for i in range(5):
            month_end = end_date - timedelta(days=i * 30)
            month_start = month_end - timedelta(days=30)
            
            months.append({
                "month_number": i + 1,
                "start_date": month_start.strftime("%Y-%m-%d"),
                "end_date": month_end.strftime("%Y-%m-%d"),
                "description": f"Month {i + 1} ({month_start} to {month_end})"
            })
        
        return months
    
    async def collect_5month_data(self):
        """Main collection method for 5 months of data"""
        
        logger.info("🌍 Starting optimized 5-month global SAR data collection")
        logger.info(f"📁 Output directory: {self.output_dir}")
        logger.info(f"🌊 Using {len(self.working_regions)} working regions")
        
        months = self.get_month_ranges()
        
        for month in months:
            if month["month_number"] in self.progress["completed_months"]:
                logger.info(f"⏭️ Skipping {month['description']} (already completed)")
                continue
            
            logger.info("=" * 80)
            logger.info(f"📅 Processing {month['description']}")
            logger.info("=" * 80)
            
            month_results = await self.collect_month_data(month)
            
            # Mark month as completed
            self.progress["completed_months"].append(month["month_number"])
            self.save_progress()
            
            logger.info(f"✅ Completed {month['description']}")
            logger.info(f"📊 Month {month['month_number']} Summary:")
            logger.info(f"   Unmatched Vessels: {month_results['total_unmatched_vessels']}")
            logger.info(f"   Matched Vessels: {month_results['total_matched_vessels']}")
            logger.info(f"   Total: {month_results['total_vessels']}")
            
            # Update global stats
            self.progress["collection_stats"]["total_unmatched_vessels"] += month_results["total_unmatched_vessels"]
            self.progress["collection_stats"]["total_matched_vessels"] += month_results["total_matched_vessels"]
            self.progress["total_vessels_collected"] += month_results["total_vessels"]
            self.save_progress()
            
            # Delay between months
            await asyncio.sleep(5)
        
        logger.info("🎉 5-month collection complete!")
        self.print_final_summary()
    
    async def collect_month_data(self, month):
        """Collect data for a single month across all working regions"""
        
        month_results = {
            "month_number": month["month_number"],
            "start_date": month["start_date"],
            "end_date": month["end_date"],
            "regions": {},
            "total_unmatched_vessels": 0,
            "total_matched_vessels": 0,
            "total_vessels": 0
        }
        
        for region in self.working_regions:
            region_key = f"{region['name']}_{region['id']}"
            
            if region_key in self.progress["completed_regions"].get(str(month["month_number"]), []):
                logger.info(f"⏭️ Skipping {region['name']} for month {month['month_number']} (already completed)")
                continue
            
            logger.info(f"🌊 Processing {region['description']} (ID: {region['id']})")
            
            region_results = await self.collect_region_month_data(month, region)
            month_results["regions"][region_key] = region_results
            
            # Update totals
            month_results["total_unmatched_vessels"] += len(region_results.get("unmatched_vessels", []))
            month_results["total_matched_vessels"] += len(region_results.get("matched_vessels", []))
            month_results["total_vessels"] += len(region_results.get("all_vessels", []))
            
            # Mark region as completed
            if str(month["month_number"]) not in self.progress["completed_regions"]:
                self.progress["completed_regions"][str(month["month_number"])] = []
            self.progress["completed_regions"][str(month["month_number"])].append(region_key)
            self.save_progress()
            
            # Rate limiting - wait between regions
            await asyncio.sleep(3)
        
        # Save month results
        month_file = self.output_dir / f"month_{month['month_number']}_complete.json"
        with open(month_file, 'w') as f:
            json.dump(month_results, f, indent=2, default=str)
        
        return month_results
    
    async def collect_region_month_data(self, month, region):
        """Collect data for a specific region and month"""
        
        region_results = {
            "region_name": region["name"],
            "region_id": region["id"],
            "month": month["month_number"],
            "all_vessels": [],
            "matched_vessels": [],
            "unmatched_vessels": [],
            "collection_errors": []
        }
        
        # Collect ALL vessels (both matched and unmatched) in one call
        logger.info(f"  🌍 Collecting ALL vessels for {region['name']}")
        try:
            all_vessels = await self.collect_sar_data(
                month["start_date"], month["end_date"],
                region["id"], region["type"], filters=[]  # No filters = get everything
            )
            
            # Separate matched and unmatched vessels
            matched_vessels = [v for v in all_vessels if v.get("matched", False)]
            unmatched_vessels = [v for v in all_vessels if not v.get("matched", False)]
            
            region_results["all_vessels"] = all_vessels
            region_results["matched_vessels"] = matched_vessels
            region_results["unmatched_vessels"] = unmatched_vessels
            
            logger.info(f"  ✅ Found {len(all_vessels)} total vessels:")
            logger.info(f"     📡 Matched: {len(matched_vessels)}")
            logger.info(f"     🕳️ Unmatched: {len(unmatched_vessels)}")
        except Exception as e:
            error_msg = f"All vessels collection failed: {e}"
            logger.error(f"  ❌ {error_msg}")
            region_results["collection_errors"].append(error_msg)
        
        return region_results
    
    async def collect_sar_data(self, start_date, end_date, region_id, region_type, filters):
        """Collect SAR data with specific parameters"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        url = f"{self.base_url}/v3/4wings/report"
        
        # Build query parameters
        params = {
            "spatial-resolution": "HIGH",
            "temporal-resolution": "DAILY",
            "datasets[0]": "public-global-sar-presence:latest",
            "date-range": f"{start_date},{end_date}",
            "format": "JSON",
            "group-by": "VESSEL_ID"
        }
        
        # Add filters
        for i, filter_dict in enumerate(filters):
            for key, value in filter_dict.items():
                params[f"filters[{i}]"] = f"{key}='{value}'"
        
        # Region specification
        data = {
            "region": {
                "dataset": "public-eez-areas",
                "id": region_id
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, params=params, json=data) as response:
                    self.requests_made += 1
                    self.progress["collection_stats"]["total_requests_made"] += 1
                    
                    if response.status == 200:
                        response_data = await response.json()
                        vessels = self._parse_sar_response(response_data)
                        return vessels
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Collection error: {e}")
            raise
    
    def _parse_sar_response(self, data):
        """Parse SAR API response using documented field structure"""
        vessels = []
        
        for entry in data.get("entries", []):
            try:
                for dataset_name, dataset_entries in entry.items():
                    if "sar-presence" in dataset_name.lower() or "public-global-sar-presence" in dataset_name:
                        if dataset_entries:
                            for sar_entry in dataset_entries:
                                vessel = {
                                    # Core fields from documentation
                                    "date": sar_entry.get("date", ""),
                                    "detections": sar_entry.get("detections", 0),
                                    "lat": sar_entry.get("lat", 0),
                                    "lon": sar_entry.get("lon", 0),
                                    "vessel_id": sar_entry.get("vessel_id", ""),
                                    "vesselIDs": sar_entry.get("vesselIDs", 0),
                                    "entryTimestamp": sar_entry.get("entryTimestamp", ""),
                                    "exitTimestamp": sar_entry.get("exitTimestamp", ""),
                                    
                                    # Vessel identification fields
                                    "mmsi": sar_entry.get("mmsi", ""),
                                    "flag": sar_entry.get("flag", ""),
                                    "shipName": sar_entry.get("shipName", ""),
                                    "geartype": sar_entry.get("geartype", ""),
                                    "vessel_type": sar_entry.get("vessel_type", ""),
                                    "imo": sar_entry.get("imo", ""),
                                    "callsign": sar_entry.get("callsign", ""),
                                    "firstTransmissionDate": sar_entry.get("firstTransmissionDate", ""),
                                    "lastTransmissionDate": sar_entry.get("lastTransmissionDate", ""),
                                    "dataset": sar_entry.get("dataset", ""),
                                    
                                    # Derived fields
                                    "matched": bool(sar_entry.get("mmsi")),
                                    "is_dark_vessel": not bool(sar_entry.get("mmsi")),
                                    
                                    # Raw data for debugging
                                    "raw_data": sar_entry
                                }
                                vessels.append(vessel)
            except Exception as e:
                logger.warning(f"Error parsing SAR entry: {e}")
                continue
        
        return vessels
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter if a minute has passed
        if current_time - self.minute_start >= 60:
            self.requests_made = 0
            self.minute_start = current_time
        
        # Wait if we've hit the limit
        if self.requests_made >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.minute_start)
            if wait_time > 0:
                logger.info(f"⏳ Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                self.requests_made = 0
                self.minute_start = time.time()
    
    def print_final_summary(self):
        """Print final collection summary"""
        logger.info("=" * 80)
        logger.info("📊 FINAL COLLECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"📁 Data directory: {self.output_dir}")
        logger.info(f"📅 Months completed: {len(self.progress['completed_months'])}/5")
        logger.info(f"🌊 Regions processed: {sum(len(regions) for regions in self.progress['completed_regions'].values())}")
        logger.info(f"🕳️ Total unmatched vessels: {self.progress['collection_stats'].get('total_unmatched_vessels', self.progress['collection_stats'].get('total_dark_vessels', 0))}")
        logger.info(f"📡 Total matched vessels: {self.progress['collection_stats']['total_matched_vessels']}")
        logger.info(f"📊 Total vessels: {self.progress['total_vessels_collected']}")
        logger.info(f"🔢 Total API requests: {self.progress['collection_stats']['total_requests_made']}")
        logger.info(f"📄 Progress file: {self.progress_file}")
        logger.info("=" * 80)

async def main():
    """Main collection function"""
    
    # Get API key
    api_key = os.getenv("GFW_API_KEY")
    if not api_key:
        logger.error("❌ GFW_API_KEY not found in environment")
        return
    print("key is good")
    
    # Create collector
    collector = OptimizedSARCollector5Month(api_key)
    
    # Start collection
    await collector.collect_5month_data()

if __name__ == "__main__":
    asyncio.run(main())
