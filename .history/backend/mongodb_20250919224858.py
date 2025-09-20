from pymongo.mongo_client import MongoClient
import os

uri = os.getenv("mongouri")
client = MongoClient(uri)
db = client["pennapps"]

prompt_logs = db["prompt_logs"]
pos_data = db["position_data"]

def insertPos():
    prompt_logs.insert_one({
        "user": "spicybigmac",
        "id": 0,
        "prompt": "hello",
        "reply": "world",
    })

    pos_data.insert_one({
        "latitude": 38.2,
        "longitude": 58.3,
        "isfishing": True,
        "legal": False,
    })

def closedb():
    client.close()