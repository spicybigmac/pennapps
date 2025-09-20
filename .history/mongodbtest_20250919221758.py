from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import os
import dotenv
dotenv.load_dotenv()

uri = os.getenv("mongouri")

client = MongoClient(uri)
print(client)

# todo: 
# voice logs
# position data
# open AIS

voicelogs = client