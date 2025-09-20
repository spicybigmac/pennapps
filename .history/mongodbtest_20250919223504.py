from pymongo.mongo_client import MongoClient
import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")
client = MongoClient(uri)
db = client["pennapps"]

prompt_logs = db["prompt_logs"]
pos_data = db["position_data"]
openAIS_data = db["openAIS_data"]

prompt_logs.insert_one({
    "prompt": "hello",
    "answer": ""
    "time": 19
})

"""
position data will be accessed by the frontend, position data will contain:
json of each individual boat that includes their longitude and latitude, fishing/not fishing

openAIS data?????

voice logs will be used to memorize the previous prompts and answers

"""


client.close()