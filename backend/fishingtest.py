import dotenv
dotenv.load_dotenv("backend/.env")
dotenv.load_dotenv()

import os
import requests

url = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"
params = {
    "query": "000",
    "datasets[0]": "public-global-vessel-identity:latest",
    "includes[0]": "MATCH_CRITERIA",
    "includes[1]": "OWNERSHIP",
    "includes[2]": "AUTHORIZATIONS"
}
print(os.getenv('GFW_API_KEY'))
headers = {
    "Authorization": f"Bearer {os.getenv('GFW_API_KEY')}"
}
response = requests.get(url, headers=headers, params=params)
print(response.json())
