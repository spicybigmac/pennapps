from pymongo.mongo_client import MongoClient
import os

"""
position data will be accessed by the frontend, position data will contain:
json of each individual boat that includes their longitude and latitude, fishing/not fishing

voice logs will be used to memorize the previous prompts and answers in order to inform
future voice logs
"""

uri = os.getenv("mongouri")
client = MongoClient(uri)
db = client["pennapps"]

prompt_logs = db["prompt_logs"]
pos_data = db["position_data"]

def logPos():

    pos_data.insert_one({
        "latitude": 38.2,
        "longitude": 58.3,
        "isfishing": True,
        "legal": False,
    })
def logPrompt(user, prompt, answer):
    prompt_logs.insert_one({
        "user": "spicybigmac",
        "prompt": "hello",
        "reply": "world",
    })

def closedb():
    client.close()