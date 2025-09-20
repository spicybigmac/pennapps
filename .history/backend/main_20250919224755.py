from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import dotenv
dotenv.load_dotenv()

import mongodb

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/getChat")
async def chat():
    pass

@app.post("/getPositions")
async def positions():
    pass

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)

mongodb.closedb()