import dotenv
dotenv.load_dotenv()
from mongodb import *
import random
for _ in range(30):
    lat = random.uniform(-90, 90)
    long = random.uniform(-180, 180)
    fishing = random.choice([True, False])
    legal = random.choice([True, False])
    logPos(lat, long, fishing, legal)
closedb()