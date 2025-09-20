from pymongo.mongo_client import MongoClient

import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")

client = MongoClient(uri)

# todo: 
# voice logs
# position data
# open AIS

db = client["pennapps"]

voice_logs = db["voice_logs"]
pos_data = db["position_data"]
openAIS_data = db["openAIS_data"]

client.close()