from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")

client = MongoClient(uri)

# todo: 
# voice logs
# position data
# open AIS

voice_logs = client["voice_logs"]
pos_data = client["position_data"]
openAIS = 