import asyncio
import aiohttp
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import os
from pathlib import Path

# Import our MongoDB functions
from api_routes import mongodb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



