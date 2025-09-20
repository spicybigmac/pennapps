from pymongo.mongo_client import MongoClient
import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")
client = MongoClient(uri)
db = client["pennapps"]

voice_logs = db["voice_logs"]
pos_data = db["position_data"]
openAIS_data = db["openAIS_data"]

voice_logs.insert_one({
    "msg": "AAAAAA",
    "time": 19
})

"""
accessing position data will be used for 

voice logs format:

"""


client.close()