from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")

client = MongoClient(uri)
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


# todo: 
# voice logs
# position data
# open AIS
