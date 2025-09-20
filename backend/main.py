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
async def chat(request: message):
    msg = request.prompt
    # do whatever with gemini here
    response = "geminis response"
    mongodb.logPrompt(msg, response)

    return response

def serializedoc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@app.get("/getPositions")
async def positions():
    docs = mongodb.getPos()
    docs = [serializedoc(x) for x in docs]
    print(docs)
    return docs

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)