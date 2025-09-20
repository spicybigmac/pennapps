from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

class message(BaseModel):
    prompt: str

@app.post("/geminiChat")
async def chat(msg: message):
    # do whatever with gemini here
    

@app.get("/getPositions")
async def positions():
    

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)

mongodb.closedb()